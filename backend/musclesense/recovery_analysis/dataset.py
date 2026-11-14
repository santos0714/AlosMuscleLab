"""Simulación de cohortes: una fila por sujeto, nivel de acoplamiento y marca de recuperación.

Cada fila reúne lo que el experimentador conoce (marca de tiempo, dosis de ejercicio), lo que
mide el sensor (rasgos NIRS estimados con Beer-Lambert, prefijo ``nirs_``), lo que vería un
sensor perfecto (los mismos rasgos calculados con los cambios reales en el músculo, prefijo
``verdad_``) y la capacidad de fuerza verdadera del modelo, que es lo que se quiere estimar.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Callable, Iterable

import numpy as np
import pandas as pd

from ..exercise_protocol.model import simulate_protocol
from ..pipeline import Pipeline, Scenario, SimulationSettings, true_concentration_changes
from ..sensor_designer.device import SensorDesign
from ..signal_processing.processing import extract_features
from .cohort import Cohort

__all__ = ["CouplingLevel", "COUPLING_FIELDS", "NO_COUPLING", "SESSION_FEATURES", "MARK_FEATURES",
           "simulate_cohort", "feature_columns"]

COUPLING_FIELDS = ("coupling_damage_flow", "coupling_slow_hyperemia", "coupling_slow_mvo2")
SESSION_FEATURES = ("caida_diff_uM", "pico_deoxy_uM", "t_medio_reox_s", "hiperemia_pico_total_uM", "hiperemia_t_pico_s")
MARK_FEATURES = ("marca_d_oxy_uM", "marca_d_deoxy_uM", "marca_d_total_uM", "marca_d_diff_uM", "reox_frac")
RECOVERY_MARKS = ("rec_0min", "rec_5min", "rec_15min", "rec_30min")


@dataclass(frozen=True)
class CouplingLevel:
    """Intensidades de los acoplamientos fatiga -> hemodinámica aplicadas a toda la cohorte."""

    name: str
    values: dict = field(default_factory=dict, hash=False)
    description: str = ""

    def __post_init__(self):
        desconocidos = set(self.values) - set(COUPLING_FIELDS)
        if desconocidos:
            raise ValueError(f"acoplamientos desconocidos: {sorted(desconocidos)}")


NO_COUPLING = CouplingLevel("ninguno", {}, "fatiga lenta y daño sin huella hemodinámica")


def feature_columns(prefix: str) -> list:
    """Columnas de rasgos con el prefijo dado ('nirs' o 'verdad')."""
    return [f"{prefix}_{c}" for c in SESSION_FEATURES + MARK_FEATURES]


def _rasgos_de_marca(prefijo: str, rasgos: dict, marca: str) -> dict:
    fila = {f"{prefijo}_{c}": rasgos.get(c, np.nan) for c in SESSION_FEATURES}
    for clave in ("d_oxy", "d_deoxy", "d_total", "d_diff"):
        fila[f"{prefijo}_marca_{clave}_uM"] = rasgos.get(f"{marca}_{clave}_uM", np.nan)
    caida = fila[f"{prefijo}_caida_diff_uM"]
    # fracción de la caída de (O2 - desoxi) del ejercicio ya recuperada en la marca
    fila[f"{prefijo}_reox_frac"] = (1.0 - fila[f"{prefijo}_marca_d_diff_uM"] / caida) if caida < 0 else np.nan
    return fila


def simulate_cohort(cohort: Cohort, levels: Iterable[CouplingLevel] | None = None, sensor: SensorDesign | None = None,
                    settings: SimulationSettings | None = None, optics: bool = True,
                    progress: Callable[[int, int], None] | None = None) -> pd.DataFrame:
    """Simula la cohorte en cada nivel de acoplamiento y devuelve la tabla larga de observaciones.

    Con ``optics=False`` solo se integra la fisiología (mucho más rápido) y faltan las columnas
    ``nirs_*``. Los niveles de un mismo sujeto comparten tejido, transporte de luz y semilla de
    ruido, de modo que las diferencias entre niveles se deben solo a los acoplamientos.
    Los sujetos que fallan se omiten y quedan en ``df.attrs["fallos"]``.
    """
    niveles = list(levels) if levels is not None else [NO_COUPLING]
    nombres = [n.name for n in niveles]
    if len(set(nombres)) != len(nombres):
        raise ValueError("los niveles de acoplamiento deben tener nombres distintos")
    sensor = sensor or SensorDesign()
    settings = settings or SimulationSettings()
    filas, fallos = [], []
    for i, sujeto in enumerate(cohort):
        tuberia = Pipeline() if optics else None  # una por sujeto: reutiliza su transporte entre niveles
        for nivel in niveles:
            fisiologia = replace(sujeto.physiology, **nivel.values)
            protocolo = sujeto.protocol
            try:
                if optics:
                    esc = Scenario(physiology=fisiologia, protocol=protocolo, sensor=sensor,
                                   settings=replace(settings, seed=sujeto.seed), tissue=sujeto.tissue(fisiologia))
                    res = tuberia.run(esc)
                    phys, rasgos = res.physiology, res.features
                    extra = {"saturado": res.saturated, "snr_min_db": float(res.snr_db.min()),
                             "fraccion_musculo": float(res.muscle_path_fraction.mean())}
                else:
                    phys = simulate_protocol(fisiologia, protocolo)
                    rasgos = {"verdad": extract_features(phys.t, true_concentration_changes(phys), protocolo)}
                    extra = {}
            except (ValueError, RuntimeError) as error:
                fallos.append({"sujeto": sujeto.subject_id, "nivel": nivel.name, "error": str(error)})
                continue
            marcas = protocolo.marks()
            for marca in RECOVERY_MARKS:
                if marca not in marcas:
                    continue
                estado = phys.at(marcas[marca])
                fila = {
                    "sujeto": sujeto.subject_id, "nivel": nivel.name, "marca": marca,
                    "minutos": float(marca[4:-3]),
                    "contraccion": protocolo.contraction, "intensidad_pct_mvc": protocolo.intensity_pct_mvc,
                    "duracion_s": protocolo.exercise_s,
                    "es_dinamico": float(protocolo.contraction == "dynamic"),
                    "es_excentrico": float(protocolo.contraction == "eccentric"),
                    **{f"tejido_{k}": v for k, v in sujeto.tissue_kwargs.items()},
                    "fuerza": estado["force_capacity"], "fuerza_rapida": estado["force_fast"],
                    "fuerza_lenta": estado["force_slow"], "fuerza_dano": estado["force_damage"],
                    "smo2_verdad": estado["smo2"], "flujo_relativo": estado["flow"] / phys.flow[0],
                    **extra,
                }
                for prefijo, clave in (("nirs", "estimado"), ("verdad", "verdad")):
                    if clave in rasgos:
                        fila.update(_rasgos_de_marca(prefijo, rasgos[clave], marca))
                filas.append(fila)
        if progress is not None:
            progress(i + 1, len(cohort))
    df = pd.DataFrame(filas)
    for m in RECOVERY_MARKS[1:]:
        if not df.empty:
            df[f"es_{m}"] = (df["marca"] == m).astype(float)
    df.attrs["fallos"] = fallos
    df.attrs["niveles"] = {n.name: dict(n.values) for n in niveles}
    return df
