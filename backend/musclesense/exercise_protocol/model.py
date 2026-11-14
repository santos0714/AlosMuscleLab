"""Modelo dinámico de oxigenación y fatiga del músculo durante ejercicio y recuperación.

El modelo separa a propósito dos grupos de variables:

* **Hemodinámica y oxigenación** (lo que la NIRS puede ver): flujo, volumen de sangre,
  saturación microvascular de la hemoglobina, saturación de la mioglobina y consumo de O2.
* **Capacidad de fuerza** (lo que se quiere estimar): pérdida rápida ligada al estado
  metabólico, pérdida lenta (fatiga de baja frecuencia) y daño por contracciones excéntricas.

La reoxigenación se completa en decenas de segundos y la capacidad de fuerza puede seguir
deprimida mucho después; ambos grupos solo se comunican a través de acoplamientos explícitos
(``coupling_*``) cuya intensidad es un parámetro. Con todos en cero, la fatiga lenta y el daño
no dejan huella hemodinámica.

Balance de O2 por unidad de volumen de tejido (mM de O2 = mM de grupo hemo ocupado):

    d(V·Hb·Sc)/dt = Q·Hb·(Sa - Sc) - J            compartimento microvascular
    Mb·dSmb/dt    = J - M                         compartimento intracelular
    J = kd·(Pc(Sc) - Pt(Smb))                     difusión capilar-fibra
    M = M_demanda·Pt/(Pt + P50_mito)              consumo limitado por O2

con Pc de la ecuación de Hill y Pt de la curva hiperbólica de la mioglobina. La demanda sigue
el modelo lineal de control respiratorio: M_demanda = M_basal·(1 + (G_max - 1)·D), donde D es
el déficit normalizado de fosfocreatina.

Unidades: s, mM, mmHg; el flujo Q en mL de sangre por mL de tejido y por segundo.
Los valores por defecto proceden de ``data/parametros_fisiologicos.json``.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

__all__ = [
    "PhysiologyParams",
    "ProtocolSpec",
    "PhysiologyResult",
    "load_physiology_reference",
    "hill_saturation",
    "hill_po2",
    "simulate_protocol",
    "MARKS_MIN",
]

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MARKS_MIN = (0.0, 5.0, 15.0, 30.0)  # marcas de recuperación del protocolo, en minutos
_EPS = 1e-6


@lru_cache(maxsize=1)
def load_physiology_reference() -> dict:
    """Parámetros fisiológicos de la literatura, indexados por id."""
    with open(DATA_DIR / "parametros_fisiologicos.json", encoding="utf-8") as archivo:
        datos = json.load(archivo)
    return {p["id"]: p for p in datos["parametros"]}


def _ref(clave: str) -> float:
    return float(load_physiology_reference()[clave]["valor_nominal"])


def hill_saturation(po2, p50: float, n: float):
    """Saturación de la hemoglobina (Hill) para una presión parcial de O2 en mmHg."""
    x = (np.maximum(po2, 0.0) / p50) ** n
    return x / (1.0 + x)


def hill_po2(sat, p50: float, n: float):
    """Inversa de la ecuación de Hill."""
    s = np.clip(sat, _EPS, 1.0 - _EPS)
    return p50 * (s / (1.0 - s)) ** (1.0 / n)


@dataclass(frozen=True)
class PhysiologyParams:
    """Parámetros fisiológicos del sujeto. Los marcados (supuesto) no vienen de una medida."""

    # --- composición y transporte de O2
    hb_blood_g_dl: float = field(default_factory=lambda: _ref("hb_sangre_g_dl"))
    blood_volume_fraction: float = field(default_factory=lambda: _ref("fraccion_sangre_musculo"))
    myoglobin_mM: float = field(default_factory=lambda: _ref("mb_musculo_mM"))
    sao2: float = field(default_factory=lambda: _ref("sao2"))
    p50_hb: float = field(default_factory=lambda: _ref("p50_hb_mmHg"))
    hill_n: float = field(default_factory=lambda: _ref("hill_n_hb"))
    p50_mb: float = field(default_factory=lambda: _ref("p50_mb_mmHg"))
    smbo2_rest: float = field(default_factory=lambda: _ref("smbo2_reposo"))
    arterial_volume_fraction: float = 0.10  # (supuesto) parte arterial del volumen microvascular
    p50_mito: float = 0.5  # mmHg (supuesto) PO2 a la que el consumo cae a la mitad
    # --- metabolismo y flujo
    mvo2_rest_uM_s: float = field(default_factory=lambda: _ref("mvo2_reposo_uM_s"))
    mvo2_max_factor: float = field(default_factory=lambda: _ref("mvo2_ejercicio_vs_mvc"))
    flow_rest_ml_min_100ml: float = field(default_factory=lambda: _ref("flujo_reposo_ml_min_100g"))
    flow_peak_ml_min_100ml: float = field(default_factory=lambda: _ref("flujo_post_ejercicio_ml_min_100g"))
    occlusion_full_pct_mvc: float = field(default_factory=lambda: _ref("umbral_oclusion_pct_mvc"))
    occlusion_onset_pct_mvc: float = field(default_factory=lambda: _ref("umbral_flujo_suficiente_pct_mvc"))
    diffusion_recruitment: float = 11.0  # (supuesto) aumento de kd a déficit máximo de PCr
    # --- constantes de tiempo
    tau_pcr_on_s: float = 25.0  # (supuesto) caída de PCr al iniciar el ejercicio
    tau_pcr_s: float = field(default_factory=lambda: _ref("tau_pcr_s"))
    tau_flow_s: float = 6.0  # (supuesto) respuesta del flujo
    tau_volume_s: float = 5.0  # (supuesto) respuesta del volumen de sangre
    tau_vasodilation_s: float = 45.0  # (supuesto) lavado del estímulo vasodilatador
    reactive_hyperemia_factor: float = 2.0  # (supuesto) hiperemia reactiva inmediata por desoxigenación
    tau_ph_s: float = field(default_factory=lambda: _ref("tau_ph_s"))
    tau_force_fast_s: float = field(default_factory=lambda: _ref("tau_mvc_rapida_s"))
    tau_force_slow_s: float = field(default_factory=lambda: _ref("tau_mvc_lenta_s"))
    # --- volumen de sangre
    volume_hyperemia_gain: float = field(default_factory=lambda: _ref("sobreimpulso_thb_pct") / 100.0)
    volume_compression: float = 0.25  # (supuesto) caída relativa de volumen a oclusión completa
    # --- fatiga
    force_drop_reference: float = field(default_factory=lambda: _ref("mvc_caida_pct_tras_fatiga") / 100.0)
    force_slow_fraction: float = field(default_factory=lambda: _ref("fraccion_mvc_lenta"))
    force_drop_eccentric: float = field(default_factory=lambda: _ref("mvc_caida_pct_excentrico") / 100.0)
    fatigue_reference_load: float = 60.0  # (supuesto) carga (fracción MVC × s) que produce la caída de referencia
    # --- acoplamientos fatiga -> hemodinámica (0 = sin efecto)
    coupling_damage_flow: float = 0.0  # aumento relativo del flujo de reposo por unidad de daño
    coupling_slow_hyperemia: float = 0.0  # reducción relativa de la hiperemia por unidad de fatiga lenta
    coupling_slow_mvo2: float = 0.0  # aumento relativo del consumo de reposo por unidad de fatiga lenta

    @property
    def hb_heme_mM(self) -> float:
        """Concentración de grupos hemo en la sangre (64 500 g/mol por tetrámero)."""
        return self.hb_blood_g_dl * 10.0 / 64500.0 * 1000.0 * 4.0

    @property
    def flow_rest(self) -> float:
        return self.flow_rest_ml_min_100ml / 100.0 / 60.0

    @property
    def flow_peak(self) -> float:
        return self.flow_peak_ml_min_100ml / 100.0 / 60.0

    @property
    def mvo2_rest(self) -> float:
        return self.mvo2_rest_uM_s * 1e-3  # mM/s


@dataclass(frozen=True)
class ProtocolSpec:
    """Protocolo: basal, ejercicio y recuperación con marcas a 0, 5, 15 y 30 minutos."""

    baseline_s: float = 120.0
    exercise_s: float = 60.0
    intensity_pct_mvc: float = 50.0
    contraction: str = "isometric"  # "isometric", "dynamic" o "eccentric"
    duty_cycle: float = 0.5  # fracción del ciclo en contracción (dinámico y excéntrico)
    recovery_s: float = 1900.0
    occlusion_test_s: float = 0.0  # duración de la oclusión arterial en cada marca (0 = sin prueba)
    sample_rate_hz: float = 10.0

    def __post_init__(self):
        if self.contraction not in ("isometric", "dynamic", "eccentric"):
            raise ValueError("contraction debe ser 'isometric', 'dynamic' o 'eccentric'")
        if not 0.0 <= self.intensity_pct_mvc <= 100.0:
            raise ValueError("intensity_pct_mvc debe estar entre 0 y 100")

    @property
    def t_exercise_start(self) -> float:
        return self.baseline_s

    @property
    def t_exercise_end(self) -> float:
        return self.baseline_s + self.exercise_s

    @property
    def t_end(self) -> float:
        return self.t_exercise_end + self.recovery_s

    def marks(self) -> dict:
        """Instantes de medición: basal y marcas de recuperación que caben en el protocolo."""
        marcas = {"basal": max(self.baseline_s - 30.0, 0.0)}
        for minuto in MARKS_MIN:
            t = self.t_exercise_end + 60.0 * minuto
            if t <= self.t_end:
                marcas["rec_%dmin" % minuto] = t
        return marcas

    def occlusion_windows(self) -> list:
        """Ventanas de oclusión arterial de prueba (inicio, fin)."""
        if self.occlusion_test_s <= 0.0:
            return []
        ventanas = []
        for nombre, t in self.marks().items():
            inicio = t if nombre == "basal" else t + 20.0  # tras el ejercicio, deja ver la reoxigenación
            if nombre == "basal":
                inicio = max(t - self.occlusion_test_s - 40.0, 5.0)
            if inicio + self.occlusion_test_s < self.t_end:
                ventanas.append((inicio, inicio + self.occlusion_test_s))
        return ventanas


@dataclass
class PhysiologyResult:
    """Series temporales del modelo. Concentraciones en mM de grupo hemo por volumen de tejido."""

    t: np.ndarray
    sc: np.ndarray  # saturación microvascular (extremo venoso)
    smbo2: np.ndarray  # saturación de la mioglobina
    smo2: np.ndarray  # saturación vascular vista por NIRS (arterial + microvascular)
    blood_volume_fraction: np.ndarray
    flow: np.ndarray  # mL/mL/s
    mvo2: np.ndarray  # consumo real, mM/s
    pcr_deficit: np.ndarray
    acidosis: np.ndarray
    force_fast: np.ndarray
    force_slow: np.ndarray
    force_damage: np.ndarray
    params: PhysiologyParams
    protocol: ProtocolSpec

    @property
    def force_capacity(self) -> np.ndarray:
        """Capacidad de fuerza relativa (1 = descansado)."""
        return np.clip(1.0 - self.force_fast - self.force_slow - self.force_damage, 0.0, 1.0)

    @property
    def thb(self) -> np.ndarray:
        return self.blood_volume_fraction * self.params.hb_heme_mM

    @property
    def o2hb(self) -> np.ndarray:
        return self.thb * self.smo2

    @property
    def hhb(self) -> np.ndarray:
        return self.thb * (1.0 - self.smo2)

    @property
    def o2mb(self) -> np.ndarray:
        return self.params.myoglobin_mM * self.smbo2

    @property
    def hmb(self) -> np.ndarray:
        return self.params.myoglobin_mM * (1.0 - self.smbo2)

    def at(self, t_s: float) -> dict:
        """Valores interpolados de todas las series en el instante t_s."""
        salida = {}
        for nombre in ("sc", "smbo2", "smo2", "blood_volume_fraction", "flow", "mvo2", "pcr_deficit",
                       "acidosis", "force_fast", "force_slow", "force_damage", "force_capacity",
                       "thb", "o2hb", "hhb"):
            salida[nombre] = float(np.interp(t_s, self.t, getattr(self, nombre)))
        return salida


def _rest_state(p: PhysiologyParams):
    """Estado estacionario de reposo y constantes calibradas con él."""
    pt_rest = p.p50_mb * p.smbo2_rest / (1.0 - p.smbo2_rest)
    psi_rest = pt_rest / (pt_rest + p.p50_mito)
    m_basal = p.mvo2_rest / psi_rest
    sc_rest = p.sao2 - p.mvo2_rest / (p.flow_rest * p.hb_heme_mM)
    if not 0.05 < sc_rest < p.sao2:
        raise ValueError("flujo y consumo de reposo incompatibles: saturación venosa %.3f" % sc_rest)
    pc_rest = hill_po2(sc_rest, p.p50_hb, p.hill_n)
    if pc_rest <= pt_rest:
        raise ValueError("la PO2 capilar de reposo no supera a la intracelular; revisa SmbO2 de reposo")
    kd0 = p.mvo2_rest / (pc_rest - pt_rest)
    return sc_rest, m_basal, kd0


def _occlusion_level(intensity_pct: float, p: PhysiologyParams) -> float:
    """Fracción de oclusión del flujo por presión intramuscular durante la contracción."""
    span = max(p.occlusion_full_pct_mvc - p.occlusion_onset_pct_mvc, 1e-9)
    return float(np.clip((intensity_pct - p.occlusion_onset_pct_mvc) / span, 0.0, 1.0))


def simulate_protocol(params: PhysiologyParams | None = None, protocol: ProtocolSpec | None = None) -> PhysiologyResult:
    """Integra el modelo a lo largo del protocolo y devuelve las series temporales."""
    p = params or PhysiologyParams()
    pr = protocol or ProtocolSpec()
    sc_rest, m_basal, kd0 = _rest_state(p)
    hb, mb, v0 = p.hb_heme_mM, p.myoglobin_mM, p.blood_volume_fraction
    pt_rest = p.p50_mb * p.smbo2_rest / (1.0 - p.smbo2_rest)
    psi_rest = pt_rest / (pt_rest + p.p50_mito)
    intensity = pr.intensity_pct_mvc / 100.0
    duty = 1.0 if pr.contraction == "isometric" else float(np.clip(pr.duty_cycle, 0.0, 1.0))
    occl_exercise = _occlusion_level(pr.intensity_pct_mvc, p) * duty
    d_target = intensity * (duty if pr.contraction != "isometric" else 1.0) ** 0.5
    # Reparto de la caída de fuerza de referencia entre componentes
    load_rate = intensity * duty / p.fatigue_reference_load  # 1/s
    fast_gain = p.force_drop_reference * (1.0 - p.force_slow_fraction)
    slow_gain = p.force_drop_reference * p.force_slow_fraction
    dmg_gain = p.force_drop_eccentric if pr.contraction == "eccentric" else 0.0
    windows = pr.occlusion_windows()

    def forcing(t: float):
        exercising = pr.t_exercise_start <= t < pr.t_exercise_end
        cuff = any(a <= t < b for a, b in windows)
        return exercising, cuff

    # estado: Sc, Smb, V, Q, D, X, H, Ffast_load, Fslow, Fdmg
    def rhs(t, y):
        sc, smb, v, q, d, x, h, wload, fslow, fdmg = y
        exercising, cuff = forcing(t)
        sc_c = min(max(sc, _EPS), 1.0 - _EPS)
        smb_c = min(max(smb, _EPS), 1.0 - _EPS)
        pc = p.p50_hb * (sc_c / (1.0 - sc_c)) ** (1.0 / p.hill_n)
        pt = p.p50_mb * smb_c / (1.0 - smb_c)
        psi = pt / (pt + p.p50_mito)
        m_demand = m_basal * (1.0 + (p.mvo2_max_factor - 1.0) * d) * (1.0 + p.coupling_slow_mvo2 * fslow)
        m_real = m_demand * psi
        kd = kd0 * (1.0 + p.diffusion_recruitment * d)
        j = kd * (pc - pt)
        occl = occl_exercise if exercising else 0.0
        # flujo objetivo: reposo (modulado por daño) + hiperemia, restringido por la contracción
        q_rest = p.flow_rest * (1.0 + p.coupling_damage_flow * fdmg)
        # hiperemia: componente metabólica lenta (x) y componente reactiva inmediata, proporcional
        # a la desoxigenación microvascular; la fatiga lenta puede atenuarla (acoplamiento)
        debt = min(max((sc_rest - sc) / sc_rest, 0.0), 1.0)
        hyper = (max(x, 0.0) + p.reactive_hyperemia_factor * debt) * (1.0 - min(p.coupling_slow_hyperemia * fslow, 0.95))
        q_target = (q_rest + (p.flow_peak - p.flow_rest) * hyper) * (1.0 - occl)
        v_target = v0 * (1.0 + p.volume_hyperemia_gain * min(hyper, 2.0) - p.volume_compression * occl)
        if cuff:  # oclusión arterial de prueba: sin entrada ni salida de sangre
            q_eff, dq, dv = 0.0, (0.0 - q) / 1.0, 0.0
        else:
            q_eff, dq, dv = q, (q_target - q) / p.tau_flow_s, (v_target - v) / p.tau_volume_s
        dsc = (q_eff * hb * (p.sao2 - sc) - j) / (v * hb) - sc * dv / v
        dsmb = (j - m_real) / mb
        if exercising:
            dd = (d_target - d) / p.tau_pcr_on_s
        else:
            dd = -d / p.tau_pcr_s * psi  # la resíntesis de PCr necesita O2
        dx = (d + max(psi_rest - psi, 0.0) - x) / p.tau_vasodilation_s  # nulo en reposo
        dh = (intensity * (max(psi_rest - psi, 0.0) + occl) if exercising else 0.0) / 60.0 - h / p.tau_ph_s
        dw = load_rate if exercising else 0.0
        # la fatiga lenta y el daño se acumulan con la carga y saturan (máximos de 0.3 y 0.7)
        dfslow = (slow_gain * load_rate * max(1.0 - fslow / 0.3, 0.0) if exercising else 0.0) - fslow / p.tau_force_slow_s
        dfdmg = dmg_gain * load_rate * max(1.0 - fdmg / 0.7, 0.0) if exercising else 0.0
        return [dsc, dsmb, dv, dq, dd, dx, dh, dw, dfslow, dfdmg]

    y = np.array([sc_rest, p.smbo2_rest, v0, p.flow_rest, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    cortes = sorted({0.0, pr.t_exercise_start, pr.t_exercise_end, pr.t_end, *[w for win in windows for w in win]})
    t_out = np.arange(0.0, pr.t_end + 0.5 / pr.sample_rate_hz, 1.0 / pr.sample_rate_hz)
    out = np.empty((t_out.size, y.size))
    for a, b in zip(cortes[:-1], cortes[1:]):
        if b <= a:
            continue
        sol = solve_ivp(rhs, (a, b), y, method="LSODA", dense_output=True, rtol=1e-6, atol=1e-9, max_step=2.0)
        if not sol.success:
            raise RuntimeError("fallo al integrar el modelo fisiológico: " + sol.message)
        sel = (t_out >= a) & ((t_out < b) | (b == cortes[-1]))
        if sel.any():
            out[sel] = sol.sol(np.minimum(t_out[sel], b)).T
        y = sol.y[:, -1]

    sc, smb, v, q, d, x, h, wload, fslow, fdmg = out.T
    sc = np.clip(sc, 0.0, 1.0)
    smb = np.clip(smb, 0.0, 1.0)
    pt = p.p50_mb * np.clip(smb, _EPS, 1 - _EPS) / (1.0 - np.clip(smb, _EPS, 1 - _EPS))
    psi = pt / (pt + p.p50_mito)
    mvo2 = m_basal * (1.0 + (p.mvo2_max_factor - 1.0) * d) * (1.0 + p.coupling_slow_mvo2 * fslow) * psi
    # componente rápida: estado metabólico (déficit de PCr y acidosis), acotada por la carga acumulada
    reached = np.clip(wload, 0.0, 1.5)
    force_fast = fast_gain * np.clip(0.6 * d / max(d_target, 1e-9) + 0.4 * np.clip(h / max(h.max(), 1e-9), 0, 1), 0.0, 1.0) * np.minimum(reached, 1.0)
    force_fast = _relax_after(force_fast, t_out, pr.t_exercise_end, p.tau_force_fast_s)
    smo2 = p.arterial_volume_fraction * p.sao2 + (1.0 - p.arterial_volume_fraction) * sc
    return PhysiologyResult(
        t=t_out, sc=sc, smbo2=smb, smo2=smo2, blood_volume_fraction=v, flow=q, mvo2=mvo2, pcr_deficit=d,
        acidosis=h, force_fast=force_fast, force_slow=np.clip(fslow, 0.0, 1.0), force_damage=np.clip(fdmg, 0.0, 1.0),
        params=p, protocol=pr,
    )


def _relax_after(valores: np.ndarray, t: np.ndarray, t_end: float, tau: float) -> np.ndarray:
    """Tras el ejercicio, la componente rápida no puede recuperarse más deprisa que tau."""
    salida = valores.copy()
    i_end = int(np.searchsorted(t, t_end))
    if 0 < i_end < t.size:
        suelo = salida[i_end - 1] * np.exp(-(t[i_end:] - t[i_end - 1]) / tau)
        salida[i_end:] = np.maximum(salida[i_end:], suelo)
    return salida
