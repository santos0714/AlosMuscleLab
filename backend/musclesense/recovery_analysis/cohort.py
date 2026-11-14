"""Cohortes virtuales: sujetos con variabilidad fisiológica, anatómica y de protocolo.

Cada parámetro variable se muestrea de una distribución triangular (mínimo, nominal, máximo)
construida con el intervalo y el valor nominal de los archivos de datos. Es un supuesto
explícito: los intervalos publicados reúnen estudios distintos y no son distribuciones
poblacionales medidas, y no se modelan correlaciones entre parámetros.

Los sujetos fisiológicamente incoherentes se descartan y se vuelven a muestrear:

* flujo y consumo de reposo incompatibles (saturación venosa imposible), o
* saturación vascular de reposo fuera del intervalo publicado (``smo2_reposo``).

El número de descartes queda registrado en la cohorte.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

from ..exercise_protocol.model import PhysiologyParams, ProtocolSpec, _rest_state, load_physiology_reference
from ..tissue_simulator.model import TissueModel

__all__ = ["PHYSIOLOGY_VARIABILITY", "TISSUE_VARIABILITY", "Triangular", "CohortSpec", "VirtualSubject",
           "Cohort", "generate_cohort"]


@dataclass(frozen=True)
class Triangular:
    """Distribución triangular (low, mode, high)."""

    low: float
    mode: float
    high: float

    def __post_init__(self):
        if not self.low <= self.mode <= self.high:
            raise ValueError(f"distribución triangular incoherente: {self}")

    def sample(self, rng: np.random.Generator) -> float:
        if self.high == self.low:
            return float(self.mode)
        return float(rng.triangular(self.low, self.mode, self.high))


def _desde_datos(clave: str, escala: float = 1.0) -> Triangular:
    p = load_physiology_reference()[clave]
    lo, hi = p["rango"]
    nominal = float(p["valor_nominal"])
    return Triangular(min(lo, nominal) * escala, nominal * escala, max(hi, nominal) * escala)


# Campo de PhysiologyParams -> (id en parametros_fisiologicos.json, escala)
PHYSIOLOGY_VARIABILITY = {
    "hb_blood_g_dl": ("hb_sangre_g_dl", 1.0),
    "blood_volume_fraction": ("fraccion_sangre_musculo", 1.0),
    "myoglobin_mM": ("mb_musculo_mM", 1.0),
    "smbo2_rest": ("smbo2_reposo", 1.0),
    "mvo2_rest_uM_s": ("mvo2_reposo_uM_s", 1.0),
    "mvo2_max_factor": ("mvo2_ejercicio_vs_mvc", 1.0),
    "flow_rest_ml_min_100ml": ("flujo_reposo_ml_min_100g", 1.0),
    "flow_peak_ml_min_100ml": ("flujo_post_ejercicio_ml_min_100g", 1.0),
    "occlusion_full_pct_mvc": ("umbral_oclusion_pct_mvc", 1.0),
    "tau_pcr_s": ("tau_pcr_s", 1.0),
    "tau_ph_s": ("tau_ph_s", 1.0),
    "tau_force_fast_s": ("tau_mvc_rapida_s", 1.0),
    "tau_force_slow_s": ("tau_mvc_lenta_s", 1.0),
    "force_slow_fraction": ("fraccion_mvc_lenta", 1.0),
    "force_drop_reference": ("mvc_caida_pct_tras_fatiga", 0.01),
    "force_drop_eccentric": ("mvc_caida_pct_excentrico", 0.01),
    "volume_hyperemia_gain": ("sobreimpulso_thb_pct", 0.01),
}

# Argumento de TissueModel.default -> (id, escala)
TISSUE_VARIABILITY = {
    "att_mm": ("att_biceps_mm", 1.0),
    "skin_mm": ("piel_grosor_mm", 1.0),
    "melanosome_epidermis": ("melanina_epidermis", 1.0),
}


@dataclass(frozen=True)
class CohortSpec:
    """Qué varía entre sujetos y cómo. Las listas vacías dejan el valor nominal."""

    n_subjects: int = 40
    seed: int = 2026
    physiology: tuple = tuple(PHYSIOLOGY_VARIABILITY)
    tissue: tuple = tuple(TISSUE_VARIABILITY)
    intensity_pct_mvc: Triangular = Triangular(20.0, 50.0, 80.0)
    exercise_s: Triangular = Triangular(30.0, 60.0, 180.0)
    contraction_weights: tuple = (("isometric", 0.5), ("dynamic", 0.25), ("eccentric", 0.25))
    eccentric_intensity_pct_mvc: float = 100.0  # el excéntrico se hace a esfuerzo máximo
    recovery_s: float = 1900.0
    max_rejections: int = 20  # por sujeto

    def __post_init__(self):
        if self.n_subjects < 1:
            raise ValueError("n_subjects debe ser al menos 1")
        desconocidos = (set(self.physiology) - set(PHYSIOLOGY_VARIABILITY)) | (set(self.tissue) - set(TISSUE_VARIABILITY))
        if desconocidos:
            raise ValueError(f"parámetros sin distribución definida: {sorted(desconocidos)}")
        pesos = [w for _, w in self.contraction_weights]
        if min(pesos) < 0 or sum(pesos) <= 0:
            raise ValueError("pesos de contracción inválidos")


@dataclass(frozen=True)
class VirtualSubject:
    subject_id: str
    physiology: PhysiologyParams
    tissue_kwargs: dict = field(hash=False)
    protocol: ProtocolSpec = field(default_factory=ProtocolSpec)
    seed: int = 0

    def tissue(self, physiology: PhysiologyParams | None = None) -> TissueModel:
        """Tejido del sujeto; la composición del músculo sigue a la fisiología indicada."""
        return TissueModel.default(physiology=physiology or self.physiology, **self.tissue_kwargs)


@dataclass(frozen=True)
class Cohort:
    spec: CohortSpec
    subjects: tuple
    rejected: int

    def __len__(self) -> int:
        return len(self.subjects)

    def __iter__(self):
        return iter(self.subjects)

    @property
    def acceptance_rate(self) -> float:
        return len(self.subjects) / (len(self.subjects) + self.rejected)


def _rest_smo2(p: PhysiologyParams) -> float:
    sc_rest, _, _ = _rest_state(p)
    return p.arterial_volume_fraction * p.sao2 + (1.0 - p.arterial_volume_fraction) * sc_rest


def _is_coherent(p: PhysiologyParams) -> bool:
    lo, hi = load_physiology_reference()["smo2_reposo"]["rango"]
    try:
        return lo <= _rest_smo2(p) <= hi
    except ValueError:
        return False


def generate_cohort(spec: CohortSpec | None = None) -> Cohort:
    """Muestrea ``spec.n_subjects`` sujetos coherentes, de forma reproducible con ``spec.seed``."""
    spec = spec or CohortSpec()
    rng = np.random.default_rng(spec.seed)
    dist_fis = {campo: _desde_datos(*PHYSIOLOGY_VARIABILITY[campo]) for campo in spec.physiology}
    dist_tej = {arg: _desde_datos(*TISSUE_VARIABILITY[arg]) for arg in spec.tissue}
    tipos = [c for c, _ in spec.contraction_weights]
    pesos = np.array([w for _, w in spec.contraction_weights], dtype=float)
    pesos /= pesos.sum()
    sujetos, descartes = [], 0
    for i in range(spec.n_subjects):
        for intento in range(spec.max_rejections + 1):
            cambios = {campo: d.sample(rng) for campo, d in dist_fis.items()}
            fisiologia = replace(PhysiologyParams(), **cambios)
            if _is_coherent(fisiologia):
                break
            descartes += 1
        else:
            raise RuntimeError(f"no se encontró un sujeto coherente tras {spec.max_rejections} intentos")
        tejido = {arg: d.sample(rng) for arg, d in dist_tej.items()}
        tipo = str(rng.choice(tipos, p=pesos))
        intensidad = spec.eccentric_intensity_pct_mvc if tipo == "eccentric" else spec.intensity_pct_mvc.sample(rng)
        protocolo = ProtocolSpec(exercise_s=round(spec.exercise_s.sample(rng), 1), intensity_pct_mvc=round(intensidad, 1),
                                 contraction=tipo, recovery_s=spec.recovery_s)
        sujetos.append(VirtualSubject(f"S{i + 1:03d}", fisiologia, tejido, protocolo, seed=spec.seed * 1000 + i))
    return Cohort(spec, tuple(sujetos), descartes)
