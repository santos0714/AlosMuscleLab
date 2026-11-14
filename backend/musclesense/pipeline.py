"""Cadena completa de simulación con caché por etapas y propagación de cambios.

Cada etapa se guarda con la huella (hash) de los parámetros de los que depende. Al ejecutar
un escenario solo se recalculan las etapas cuya huella cambió; ``SimulationResult.recomputed``
dice cuáles fueron.
"""
from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from dataclasses import asdict, dataclass, field

import numpy as np

from .exercise_protocol.model import PhysiologyParams, PhysiologyResult, ProtocolSpec, simulate_protocol
from .optical_physics import spectra
from .optical_physics.diffusion import LayerOptics, layered_partial_pathlengths, layered_reflectance
from .optical_physics.montecarlo import run_layered_monte_carlo
from .sensor_designer.device import SensorDesign
from .signal_processing import processing
from .tissue_simulator.model import TissueModel

__all__ = ["SimulationSettings", "Scenario", "SimulationResult", "Pipeline", "STAGES", "baseline_window",
           "true_concentration_changes"]

STAGES = ("optics", "transport", "physiology", "absorption", "optical_signal", "electronics", "processing", "features")
_GRID = np.geomspace(0.3, 3.0, 16)  # factores sobre la absorción basal del músculo


def baseline_window(protocol: ProtocolSpec) -> tuple:
    """Ventana basal (t0, t1) usada como referencia de los cambios de concentración."""
    return 5.0, max(protocol.baseline_s - 5.0, 10.0)


def true_concentration_changes(phys: PhysiologyResult) -> dict:
    """Cambios reales en el músculo (hemoglobina + mioglobina) respecto al basal, en uM de hemo."""
    t0, t1 = baseline_window(phys.protocol)
    base = (phys.t >= t0) & (phys.t < t1)
    oxi = (phys.o2hb + phys.o2mb) * 1e3
    desoxi = (phys.hhb + phys.hmb) * 1e3
    verdad = {"d_oxy": oxi - oxi[base].mean(), "d_deoxy": desoxi - desoxi[base].mean()}
    verdad["d_total"] = verdad["d_oxy"] + verdad["d_deoxy"]
    verdad["d_diff"] = verdad["d_oxy"] - verdad["d_deoxy"]
    return verdad


@dataclass(frozen=True)
class SimulationSettings:
    engine: str = "diffusion"  # "diffusion", "montecarlo" (propio) o "mcx" (MCX-CL, requiere OpenCL)
    n_photons: int = 300_000
    seed: int = 1234
    noise: bool = True
    led_spectrum_points: int = 5
    assumed_dpf: float = 4.16  # DPF de antebrazo (Duncan et al. 1995)
    use_led_spectrum_in_mbll: bool = True
    lowpass_hz: float = 0.5


@dataclass(frozen=True)
class Scenario:
    physiology: PhysiologyParams = field(default_factory=PhysiologyParams)
    protocol: ProtocolSpec = field(default_factory=ProtocolSpec)
    sensor: SensorDesign = field(default_factory=SensorDesign)
    settings: SimulationSettings = field(default_factory=SimulationSettings)
    tissue: TissueModel | None = None  # None = tejido de referencia coherente con la fisiología

    def resolved_tissue(self) -> TissueModel:
        return self.tissue if self.tissue is not None else TissueModel.default(physiology=self.physiology)


@dataclass
class SimulationResult:
    t: np.ndarray
    physiology: PhysiologyResult
    wavelengths: tuple
    reflectance: np.ndarray  # (T, n_led) 1/mm^2
    photocurrent_A: np.ndarray  # (T, n_led)
    counts: np.ndarray  # (T, n_led)
    snr_db: np.ndarray  # (n_led,) mediana
    saturated: bool
    delta_attenuation: np.ndarray  # (T, n_led)
    estimated: dict  # cambios estimados, uM de hemo
    truth: dict  # cambios reales en el músculo, uM de hemo
    partial_pathlengths_mm: np.ndarray  # (n_led, 3) en el basal
    features: dict
    recomputed: list
    fingerprints: dict

    @property
    def muscle_path_fraction(self) -> np.ndarray:
        return self.partial_pathlengths_mm[:, 2] / self.partial_pathlengths_mm.sum(axis=1)


def _fingerprint(*objetos) -> str:
    def plano(o):
        if hasattr(o, "__dataclass_fields__"):
            return asdict(o)
        return o
    texto = json.dumps([plano(o) for o in objetos], sort_keys=True, default=str)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]


class Pipeline:
    """Ejecuta escenarios reutilizando las etapas que no cambian.

    ``max_entries`` acota la caché en memoria (se descartan primero las entradas menos usadas).
    ``store`` es un almacén persistente opcional con ``get(etapa, huella)`` y
    ``put(etapa, huella, valor)``; solo se usa para las etapas de ``persistent_stages`` (por
    defecto el transporte de luz, la única etapa que tarda segundos).
    """

    def __init__(self, max_entries: int | None = None, store=None, persistent_stages=("transport",)):
        self._cache: OrderedDict = OrderedDict()
        self.max_entries = max_entries
        self.store = store
        self.persistent_stages = tuple(persistent_stages)

    def _stage(self, nombre: str, huella: str, calcular, recomputed: list):
        clave = (nombre, huella)
        if clave in self._cache:
            self._cache.move_to_end(clave)
            return self._cache[clave]
        persistente = self.store is not None and nombre in self.persistent_stages
        valor = self.store.get(nombre, huella) if persistente else None
        if valor is None:
            valor = calcular()
            recomputed.append(nombre)
            if persistente:
                self.store.put(nombre, huella, valor)
        self._cache[clave] = valor
        if self.max_entries is not None:
            while len(self._cache) > self.max_entries:
                self._cache.popitem(last=False)
        return valor

    # -- etapas ------------------------------------------------------------------------------
    @staticmethod
    def _optics(tissue: TissueModel, sensor: SensorDesign, n_points: int) -> dict:
        leds = []
        for led in sensor.leds:
            lam, pesos = spectra.led_spectrum(led.peak_nm, led.fwhm_nm, n_points)
            leds.append({
                "lam": lam, "w": pesos, "resp": sensor.photodiode.responsivity(lam),
                "mua_skin": tissue.skin.mua(lam), "mua_fat": tissue.fat.mua(lam),
                "mua_muscle0": tissue.muscle.mua(lam), "static_muscle": tissue.muscle.static_absorption(lam),
                "heme": spectra.heme_absorption(lam),
            })
        return {"leds": leds}

    @staticmethod
    def _capas(tissue: TissueModel, lam: float, mua: tuple) -> list:
        return [LayerOptics(c.thickness_mm if i < 2 else np.inf, float(m), float(c.musp(lam)), c.n, c.g)
                for i, (c, m) in enumerate(zip(tissue.layers, mua))]

    def _transport(self, tissue: TissueModel, sensor: SensorDesign, optics: dict, st: SimulationSettings) -> dict:
        rho = sensor.sds_mm
        tablas, parciales = [], []
        for k, (led, o) in enumerate(zip(sensor.leds, optics["leds"])):
            n_sub = o["lam"].size
            ln_r = np.empty((n_sub, _GRID.size))
            if st.engine in ("montecarlo", "mcx"):
                base = self._capas(tissue, led.peak_nm, (o["mua_skin"].min(), o["mua_fat"].min(), o["mua_muscle0"].min()))
                if st.engine == "montecarlo":
                    piso = [0.9 * base[0].mua, 0.9 * base[1].mua, 0.25 * base[2].mua]
                    lib = run_layered_monte_carlo(base, st.n_photons, seed=st.seed + k, mua_floor=piso,
                                                  use_similarity=True, store_rho_range=(max(rho - 3.0, 0.0), rho + 3.0))
                else:  # MCX-CL en blanco: la absorción se aplica después
                    from .optical_physics.mcx_engine import run_layered_mcx
                    lib = run_layered_mcx(base, st.n_photons, rho, seed=st.seed + k, detector_radius_mm=2.0)
                for i in range(n_sub):
                    for j, f in enumerate(_GRID):
                        r, _, _ = lib.reflectance([o["mua_skin"][i], o["mua_fat"][i], f * o["mua_muscle0"][i]], rho, 2.0)
                        ln_r[i, j] = np.log(max(r, 1e-300))
                c = n_sub // 2
                parciales.append(lib.mean_partial_pathlengths([o["mua_skin"][c], o["mua_fat"][c], o["mua_muscle0"][c]], rho, 2.0))
            elif st.engine == "diffusion":
                for i in range(n_sub):
                    for j, f in enumerate(_GRID):
                        capas = self._capas(tissue, o["lam"][i], (o["mua_skin"][i], o["mua_fat"][i], f * o["mua_muscle0"][i]))
                        ln_r[i, j] = np.log(layered_reflectance(rho, capas))
                c = n_sub // 2
                capas = self._capas(tissue, o["lam"][c], (o["mua_skin"][c], o["mua_fat"][c], o["mua_muscle0"][c]))
                parciales.append(layered_partial_pathlengths(rho, capas))
            else:
                raise ValueError(f"motor de transporte desconocido: {st.engine!r}")
            tablas.append(ln_r)
        return {"ln_r": tablas, "partial": np.array(parciales)}

    # -- ejecución -----------------------------------------------------------------------------
    def run(self, scenario: Scenario) -> SimulationResult:
        sc, st = scenario, scenario.settings
        tissue = sc.resolved_tissue()
        rec: list = []
        f_opt = _fingerprint(tissue, sc.sensor.leds, sc.sensor.photodiode, st.led_spectrum_points)
        optics = self._stage("optics", f_opt, lambda: self._optics(tissue, sc.sensor, st.led_spectrum_points), rec)
        estocastico = st.engine in ("montecarlo", "mcx")
        f_tr = _fingerprint(f_opt, sc.sensor.sds_mm, st.engine, st.n_photons if estocastico else 0,
                            st.seed if estocastico else 0)
        transport = self._stage("transport", f_tr, lambda: self._transport(tissue, sc.sensor, optics, st), rec)
        f_ph = _fingerprint(sc.physiology, sc.protocol)
        phys: PhysiologyResult = self._stage("physiology", f_ph, lambda: simulate_protocol(sc.physiology, sc.protocol), rec)

        def _absorption():
            salida = []
            for o in optics["leds"]:
                oxi, desoxi = o["heme"]
                v, s, sm = phys.blood_volume_fraction[:, None], phys.smo2[:, None], phys.smbo2[:, None]
                mua = (v * tissue.muscle.hb_heme_mM * (s * oxi + (1 - s) * desoxi)
                       + tissue.muscle.myoglobin_mM * (sm * oxi + (1 - sm) * desoxi) + o["static_muscle"])
                salida.append(mua)  # (T, n_sub)
            return salida
        f_abs = _fingerprint(f_opt, f_ph)
        absorption = self._stage("absorption", f_abs, _absorption, rec)

        def _optical():
            refl = np.empty((phys.t.size, len(sc.sensor.leds)))
            corriente = np.empty_like(refl)
            for k, (o, mua) in enumerate(zip(optics["leds"], absorption)):
                factor = mua / o["mua_muscle0"]
                if factor.min() < _GRID[0] or factor.max() > _GRID[-1]:
                    raise ValueError("la absorción del músculo sale del intervalo tabulado del transporte")
                r = np.empty_like(mua)
                for i in range(mua.shape[1]):
                    r[:, i] = np.exp(np.interp(np.log(factor[:, i]), np.log(_GRID), transport["ln_r"][k][i]))
                refl[:, k] = r @ o["w"]
                corriente[:, k] = sc.sensor.photocurrent(r, k, responsivity=o["resp"]) @ o["w"]
            return refl, corriente
        f_os = _fingerprint(f_tr, f_abs, sc.sensor.leds, sc.sensor.photodiode)
        refl, corriente = self._stage("optical_signal", f_os, _optical, rec)

        def _electronics():
            rng = np.random.default_rng(st.seed) if st.noise else None
            adq = [sc.sensor.acquire(corriente[:, k], rng) for k in range(corriente.shape[1])]
            return (np.column_stack([a["counts"] for a in adq]),
                    np.array([float(np.median(a["snr_db"])) for a in adq]),
                    bool(any(a["saturated"].any() for a in adq)))
        f_el = _fingerprint(f_os, sc.sensor.tia, sc.sensor.adc, sc.sensor.mcu, sc.sensor.ambient_photocurrent_nA, st.noise, st.seed)
        counts, snr, saturado = self._stage("electronics", f_el, _electronics, rec)

        wl = sc.sensor.wavelengths
        fwhm = [led.fwhm_nm for led in sc.sensor.leds] if st.use_led_spectrum_in_mbll else None

        def _processing():
            # se filtra la intensidad y después se toma el logaritmo: con pocas cuentas, el logaritmo
            # de una señal ruidosa está sesgado (desigualdad de Jensen) y el filtro no lo corrige
            filtradas = processing.lowpass(counts.astype(float), sc.protocol.sample_rate_hz, st.lowpass_hz)
            d_a = processing.counts_to_attenuation(filtradas, phys.t, baseline_window(sc.protocol))
            return d_a, processing.estimate_concentrations(d_a, wl, sc.sensor.sds_mm, st.assumed_dpf, fwhm)
        f_pr = _fingerprint(f_el, st.assumed_dpf, st.use_led_spectrum_in_mbll, st.lowpass_hz, sc.sensor.sds_mm)
        d_a, estimado = self._stage("processing", f_pr, _processing, rec)

        def _features():
            verdad = true_concentration_changes(phys)
            rasgos = processing.extract_features(phys.t, estimado, sc.protocol)
            rasgos_verdad = processing.extract_features(phys.t, verdad, sc.protocol)
            for nombre, tm in sc.protocol.marks().items():
                rasgos[f"{nombre}_fuerza"] = phys.at(tm)["force_capacity"]
            return verdad, {"estimado": rasgos, "verdad": rasgos_verdad}
        verdad, rasgos = self._stage("features", _fingerprint(f_pr, f_ph), _features, rec)

        return SimulationResult(
            t=phys.t, physiology=phys, wavelengths=wl, reflectance=refl, photocurrent_A=corriente, counts=counts,
            snr_db=snr, saturated=saturado, delta_attenuation=d_a, estimated=estimado, truth=verdad,
            partial_pathlengths_mm=transport["partial"], features=rasgos, recomputed=rec,
            fingerprints={"optics": f_opt, "transport": f_tr, "physiology": f_ph, "electronics": f_el, "processing": f_pr},
        )
