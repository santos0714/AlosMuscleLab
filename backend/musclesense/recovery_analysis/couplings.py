"""Acoplamientos entre fatiga y hemodinámica: calibración y barrido.

Con los acoplamientos en cero, la fatiga lenta y el daño no dejan huella en la oxigenación y
la NIRS solo puede ver la componente rápida (ligada a la PCr y a la acidosis). Cuánto aporta el
sensor depende, por tanto, de supuestos que hay que barrer en lugar de fijar.

* ``coupling_damage_flow`` tiene respaldo cuantitativo: tras ejercicio excéntrico máximo de los
  flexores del codo la saturación de reposo del bíceps sube 22 % de forma aguda y de 5 a 9 %
  durante días (``eimd_smo2_reposo_aumento_pct``, Ahmadi et al. 2008). Sus niveles se calibran
  para reproducir esos aumentos con el protocolo excéntrico de referencia.
* ``coupling_slow_hyperemia`` y ``coupling_slow_mvo2`` no tienen respaldo cuantitativo. Sus
  niveles se expresan por su efecto por cada 10 % de pérdida lenta de fuerza: un acoplamiento
  de 2.5 en la hiperemia la reduce 25 % por cada 0.1 de fatiga lenta; uno de 1 en el consumo
  de reposo lo aumenta 10 % por cada 0.1 de fatiga lenta.
"""
from __future__ import annotations

from dataclasses import replace
from functools import lru_cache

import pandas as pd
from scipy.optimize import brentq

from ..exercise_protocol.model import PhysiologyParams, ProtocolSpec, load_physiology_reference, simulate_protocol
from .cohort import Cohort
from .dataset import NO_COUPLING, CouplingLevel, simulate_cohort
from .statistics import evaluate, nirs_gain

__all__ = ["REFERENCE_ECCENTRIC", "resting_saturation_increase_pct", "calibrate_damage_flow", "default_levels",
           "coupling_sweep"]

# 70 contracciones excéntricas máximas ~ 210 s con ciclo de trabajo de 0.5 (Ahmadi et al. 2008)
REFERENCE_ECCENTRIC = ProtocolSpec(contraction="eccentric", intensity_pct_mvc=100.0, exercise_s=210.0, duty_cycle=0.5)


def resting_saturation_increase_pct(coupling: float, physiology: PhysiologyParams | None = None,
                                    protocol: ProtocolSpec = REFERENCE_ECCENTRIC, mark: str = "rec_30min") -> float:
    """Aumento relativo (%) de la SmO2 de reposo en ``mark`` respecto al basal."""
    p = replace(physiology or PhysiologyParams(), coupling_damage_flow=coupling)
    r = simulate_protocol(p, protocol)
    marcas = protocol.marks()
    return 100.0 * (r.at(marcas[mark])["smo2"] / r.at(marcas["basal"])["smo2"] - 1.0)


@lru_cache(maxsize=64)
def calibrate_damage_flow(target_pct: float, physiology: PhysiologyParams | None = None,
                          protocol: ProtocolSpec = REFERENCE_ECCENTRIC, upper: float = 20.0) -> float:
    """Acoplamiento daño -> flujo que produce un aumento ``target_pct`` de la SmO2 de reposo.

    El resultado se guarda en caché (los argumentos son inmutables).
    """
    if target_pct <= 0.0:
        return 0.0
    f = lambda c: resting_saturation_increase_pct(c, physiology, protocol) - target_pct  # noqa: E731
    if f(upper) < 0:
        raise ValueError(f"ni con un acoplamiento de {upper} se alcanza un aumento de {target_pct} %")
    return float(brentq(f, 0.0, upper, xtol=1e-4))


def default_levels() -> list:
    """Niveles del barrido: sin acoplamiento, cada acoplamiento por separado y uno combinado."""
    ref = load_physiology_reference()["eimd_smo2_reposo_aumento_pct"]
    agudo, (sost_min, _) = float(ref["valor_nominal"]), ref["rango"]
    sostenidos = (sost_min, 9.0)  # +5 a +9 % durante días
    niveles = [NO_COUPLING]
    for pct in (*sostenidos, agudo):
        c = calibrate_damage_flow(pct)
        niveles.append(CouplingLevel(f"dano_flujo_{pct:g}pct", {"coupling_damage_flow": c},
                                     f"daño -> flujo: +{pct:g} % de SmO2 de reposo tras excéntrico (c = {c:.3f})"))
    for c in (1.0, 2.5, 5.0):
        niveles.append(CouplingLevel(f"lenta_hiperemia_{c:g}", {"coupling_slow_hyperemia": c},
                                     f"supuesto: hiperemia -{10 * c:g} % por cada 10 % de fatiga lenta"))
    for c in (0.5, 1.0, 2.0):
        niveles.append(CouplingLevel(f"lenta_mvo2_{c:g}", {"coupling_slow_mvo2": c},
                                     f"supuesto: consumo de reposo +{10 * c:g} % por cada 10 % de fatiga lenta"))
    niveles.append(CouplingLevel("combinado", {"coupling_damage_flow": calibrate_damage_flow(9.0),
                                               "coupling_slow_hyperemia": 2.5, "coupling_slow_mvo2": 1.0},
                                 "daño +9 %, hiperemia -25 % y consumo +10 % por cada 10 % de fatiga lenta"))
    return niveles


def coupling_sweep(cohort: Cohort, levels=None, models=("ridge",), optics: bool = True, **kwargs) -> dict:
    """Simula la cohorte en cada nivel y evalúa. Devuelve datos, evaluación y ganancias."""
    niveles = list(levels) if levels is not None else default_levels()
    datos = simulate_cohort(cohort, niveles, optics=optics, **kwargs)
    evaluacion = evaluate(datos, models=models)
    descripcion = pd.DataFrame([{"nivel": n.name, "descripcion": n.description, **n.values} for n in niveles])
    return {"datos": datos, "evaluacion": evaluacion, "ganancia": nirs_gain(evaluacion, models[0]),
            "niveles": descripcion}
