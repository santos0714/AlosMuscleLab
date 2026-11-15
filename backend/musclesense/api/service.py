"""Traducción entre peticiones JSON y objetos del simulador, y resúmenes de resultados."""
from __future__ import annotations

import math
import platform
from dataclasses import asdict, fields, replace

import numpy as np

from .. import __version__
from ..exercise_protocol.model import PhysiologyParams, ProtocolSpec, load_physiology_reference
from ..pipeline import Scenario, SimulationResult, SimulationSettings
from ..recovery_analysis.cohort import PHYSIOLOGY_VARIABILITY
from ..sensor_designer.device import AdcSpec, SensorDesign, TiaSpec
from ..tissue_simulator.model import PROFILES, TissueModel

__all__ = ["ScenarioError", "build_scenario", "summarize", "series", "parameter_catalog", "versions", "clean_json",
           "ASSUMED_PHYSIOLOGY", "PHYSIOLOGY_SOURCES"]

# Origen bibliográfico de cada campo de PhysiologyParams (id en parametros_fisiologicos.json)
PHYSIOLOGY_SOURCES = {
    **{campo: clave for campo, (clave, _) in PHYSIOLOGY_VARIABILITY.items()},
    "sao2": "sao2", "p50_hb": "p50_hb_mmHg", "hill_n": "hill_n_hb", "p50_mb": "p50_mb_mmHg",
    "occlusion_onset_pct_mvc": "umbral_flujo_suficiente_pct_mvc",
}
# Campos sin medida directa: calibrados para reproducir anclas publicadas o puestos a cero
ASSUMED_PHYSIOLOGY = (
    "arterial_volume_fraction", "p50_mito", "diffusion_recruitment", "tau_pcr_on_s", "tau_flow_s", "tau_volume_s",
    "tau_vasodilation_s", "reactive_hyperemia_factor", "volume_compression", "fatigue_reference_load",
    "coupling_damage_flow", "coupling_slow_hyperemia", "coupling_slow_mvo2",
)
_SETTINGS_PERMITIDOS = {"engine", "n_photons", "seed", "noise", "led_spectrum_points", "assumed_dpf",
                        "use_led_spectrum_in_mbll", "lowpass_hz"}


class ScenarioError(ValueError):
    """Petición de escenario inválida (se responde con 422)."""


def _reemplazar(objeto, cambios: dict, que: str):
    validos = {f.name for f in fields(objeto)}
    desconocidos = set(cambios) - validos
    if desconocidos:
        raise ScenarioError(f"{que}: campos desconocidos {sorted(desconocidos)}")
    try:
        return replace(objeto, **cambios)
    except (TypeError, ValueError) as error:
        raise ScenarioError(f"{que}: {error}") from error


def build_scenario(req: dict, saved_profiles: dict | None = None) -> Scenario:
    """Construye un ``Scenario`` a partir del cuerpo de la petición (ya validado por pydantic)."""
    fisiologia = _reemplazar(PhysiologyParams(), req.get("physiology") or {}, "fisiología")
    protocolo = _reemplazar(ProtocolSpec(), req.get("protocol") or {}, "protocolo")
    if protocolo.t_end > 7200.0:
        raise ScenarioError("protocolo: la simulación no puede pasar de 2 horas")

    ajustes_req = req.get("settings") or {}
    if set(ajustes_req) - _SETTINGS_PERMITIDOS:
        raise ScenarioError(f"ajustes: campos desconocidos {sorted(set(ajustes_req) - _SETTINGS_PERMITIDOS)}")
    ajustes = _reemplazar(SimulationSettings(), ajustes_req, "ajustes")
    if ajustes.engine not in ("diffusion", "montecarlo", "mcx"):
        raise ScenarioError("ajustes: engine debe ser 'diffusion', 'montecarlo' o 'mcx'")
    if ajustes.engine != "diffusion" and ajustes.n_photons > 2_000_000:
        raise ScenarioError("ajustes: como máximo 2 000 000 de fotones por petición")

    tej = req.get("tissue") or {}
    perfiles = {**PROFILES, **(saved_profiles or {})}
    nombre = tej.get("profile") or "referencia"
    if nombre not in perfiles:
        raise ScenarioError(f"tejido: perfil desconocido {nombre!r}")
    args = dict(perfiles[nombre])
    for clave in ("att_mm", "skin_mm", "melanosome_epidermis"):
        if tej.get(clave) is not None:
            args[clave] = tej[clave]
    try:
        tejido = TissueModel.default(physiology=fisiologia, **args)
    except (TypeError, ValueError) as error:
        raise ScenarioError(f"tejido: {error}") from error

    sen = req.get("sensor") or {}
    sensor = SensorDesign()
    try:
        if sen.get("tia_rf_ohm") is not None or sen.get("tia_cf_pF") is not None:
            sensor = replace(sensor, tia=replace(TiaSpec(), **{k: v for k, v in (("rf_ohm", sen.get("tia_rf_ohm")),
                                                                                 ("cf_pF", sen.get("tia_cf_pF")))
                                                              if v is not None}))
        if sen.get("adc_bits") is not None:
            sensor = replace(sensor, adc=replace(AdcSpec(), bits=int(sen["adc_bits"])))
        if sen.get("led_power_mW") is not None:
            potencias = list(sen["led_power_mW"])
            if len(potencias) != len(sensor.leds):
                raise ScenarioError(f"sensor: se esperan {len(sensor.leds)} potencias de LED")
            sensor = replace(sensor, leds=tuple(replace(led, radiant_power_mW=float(p))
                                                for led, p in zip(sensor.leds, potencias)))
        cambios = {k: sen[k] for k in ("sds_mm", "ambient_photocurrent_nA") if sen.get(k) is not None}
        if cambios:
            sensor = replace(sensor, **cambios)
    except (TypeError, ValueError) as error:
        if isinstance(error, ScenarioError):
            raise
        raise ScenarioError(f"sensor: {error}") from error
    return Scenario(physiology=fisiologia, protocol=protocolo, sensor=sensor, settings=ajustes, tissue=tejido)


def clean_json(valor):
    """Convierte NumPy a tipos de Python y NaN/inf a None (JSON estricto)."""
    if isinstance(valor, dict):
        return {str(k): clean_json(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [clean_json(v) for v in valor]
    if isinstance(valor, np.ndarray):
        return clean_json(valor.tolist())
    if isinstance(valor, (np.floating, float)):
        f = float(valor)
        return f if math.isfinite(f) else None
    if isinstance(valor, (np.integer,)):
        return int(valor)
    if isinstance(valor, np.bool_):
        return bool(valor)
    return valor


def summarize(res: SimulationResult, scenario: Scenario) -> dict:
    marcas = scenario.protocol.marks()
    return clean_json({
        "longitudes_onda_nm": list(res.wavelengths),
        "snr_db": res.snr_db,
        "saturado": res.saturated,
        "fotocorriente_basal_nA": res.photocurrent_A[0] * 1e9,
        "trayectorias_parciales_mm": {"piel": res.partial_pathlengths_mm[:, 0], "grasa": res.partial_pathlengths_mm[:, 1],
                                      "musculo": res.partial_pathlengths_mm[:, 2]},
        "fraccion_trayectoria_musculo": res.muscle_path_fraction,
        "rasgos_estimados": res.features["estimado"],
        "rasgos_verdaderos": res.features["verdad"],
        "fuerza_en_marcas": {m: res.physiology.at(t)["force_capacity"] for m, t in marcas.items()},
        "marcas_s": marcas,
        "tejido": {c.name: {"grosor_mm": c.thickness_mm} for c in scenario.resolved_tissue().layers},
    })


def series(res: SimulationResult, rate_hz: float = 1.0) -> dict:
    """Series temporales submuestreadas para graficar."""
    fs = res.physiology.protocol.sample_rate_hz
    paso = max(int(round(fs / rate_hz)), 1)
    s = slice(None, None, paso)
    ph = res.physiology
    return clean_json({
        "t_s": res.t[s],
        "fisiologia": {
            "smo2": ph.smo2[s], "smbo2": ph.smbo2[s], "saturacion_capilar": ph.sc[s],
            "volumen_sangre_rel": ph.blood_volume_fraction[s] / ph.blood_volume_fraction[0],
            "flujo_rel": ph.flow[s] / ph.flow[0], "consumo_o2_rel": ph.mvo2[s] / ph.mvo2[0],
            "deficit_pcr": ph.pcr_deficit[s],
            "fuerza": ph.force_capacity[s], "fuerza_rapida": ph.force_fast[s], "fuerza_lenta": ph.force_slow[s],
            "fuerza_dano": ph.force_damage[s],
        },
        "verdad_uM": {k: v[s] for k, v in res.truth.items()},
        "estimado_uM": {k: v[s] for k, v in res.estimated.items()},
        "atenuacion": {f"{lam:g}": res.delta_attenuation[s, k] for k, lam in enumerate(res.wavelengths)},
        "fotocorriente_nA": {f"{lam:g}": res.photocurrent_A[s, k] * 1e9 for k, lam in enumerate(res.wavelengths)},
    })


def parameter_catalog() -> dict:
    """Valores por defecto, origen y marca de supuesto de los parámetros editables."""
    ref = load_physiology_reference()
    fisiologia = []
    for f in fields(PhysiologyParams):
        valor = getattr(PhysiologyParams(), f.name)
        item = {"campo": f.name, "por_defecto": valor, "supuesto": f.name in ASSUMED_PHYSIOLOGY}
        clave = PHYSIOLOGY_SOURCES.get(f.name)
        if clave:
            p = ref[clave]
            item.update({"fuente": clave, "descripcion": p.get("descripcion"), "rango": p.get("rango"),
                         "unidades": p.get("unidades"), "verificado": p.get("verificado"),
                         "referencias": p.get("referencias")})
        fisiologia.append(item)
    return clean_json({
        "fisiologia": fisiologia,
        "protocolo": asdict(ProtocolSpec()),
        "ajustes": asdict(SimulationSettings()),
        "sensor": {"sds_mm": SensorDesign().sds_mm, "tia": asdict(TiaSpec()), "adc": asdict(AdcSpec()),
                   "leds": [asdict(led) for led in SensorDesign().leds],
                   "ambient_photocurrent_nA": SensorDesign().ambient_photocurrent_nA},
        "perfiles": PROFILES,
        "tejido": {"skin_mm": ref["piel_grosor_mm"]["valor_nominal"], "att_mm": ref["att_biceps_mm"]["valor_nominal"],
                   "melanosome_epidermis": ref["melanina_epidermis"]["valor_nominal"],
                   "musculo_mm": ref["musculo_grosor_mm"]["valor_nominal"],
                   "rangos": {"att_mm": ref["att_biceps_mm"]["rango"], "skin_mm": ref["piel_grosor_mm"]["rango"],
                              "melanosome_epidermis": ref["melanina_epidermis"]["rango"]}},
    })


def versions() -> dict:
    import scipy
    import sklearn
    return {"musclesense": __version__, "python": platform.python_version(), "numpy": np.__version__,
            "scipy": scipy.__version__, "scikit-learn": sklearn.__version__}
