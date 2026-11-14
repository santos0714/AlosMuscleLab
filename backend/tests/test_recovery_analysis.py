"""Análisis de recuperación: cohortes, calibración de acoplamientos y estadística."""
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from musclesense.exercise_protocol.model import load_physiology_reference
from musclesense.recovery_analysis import (
    NO_COUPLING, CohortSpec, CouplingLevel, calibrate_damage_flow, dissociation_table, evaluate,
    feature_associations, feature_columns, generate_cohort, nirs_gain, simulate_cohort,
)
from musclesense.recovery_analysis.cohort import PHYSIOLOGY_VARIABILITY, _desde_datos, _rest_smo2
from musclesense.recovery_analysis.couplings import resting_saturation_increase_pct
from musclesense.recovery_analysis.dataset import RECOVERY_MARKS
from musclesense.signal_processing import processing


# --- cohortes ------------------------------------------------------------------------------------
def test_cohorte_reproducible_coherente_y_dentro_de_intervalos():
    spec = CohortSpec(n_subjects=40, seed=3)
    a, b = generate_cohort(spec), generate_cohort(spec)
    assert [s.physiology for s in a] == [s.physiology for s in b]
    assert [s.protocol for s in a] == [s.protocol for s in b]
    assert len(a) == 40 and 0.3 < a.acceptance_rate <= 1.0
    lo, hi = load_physiology_reference()["smo2_reposo"]["rango"]
    for s in a:
        assert lo <= _rest_smo2(s.physiology) <= hi
        for campo, (clave, escala) in PHYSIOLOGY_VARIABILITY.items():
            d = _desde_datos(clave, escala)
            assert d.low - 1e-12 <= getattr(s.physiology, campo) <= d.high + 1e-12
        if s.protocol.contraction == "eccentric":
            assert s.protocol.intensity_pct_mvc == 100.0
    tipos = {s.protocol.contraction for s in a}
    assert tipos == {"isometric", "dynamic", "eccentric"}
    assert generate_cohort(replace(spec, seed=4)).subjects[0].physiology != a.subjects[0].physiology


def test_especificacion_invalida():
    with pytest.raises(ValueError):
        CohortSpec(physiology=("no_existe",))
    with pytest.raises(ValueError):
        CohortSpec(n_subjects=0)
    with pytest.raises(ValueError):
        CouplingLevel("x", {"coupling_inventado": 1.0})


# --- acoplamientos -------------------------------------------------------------------------------
def test_calibracion_dano_flujo_reproduce_el_aumento_publicado():
    assert calibrate_damage_flow(0.0) == 0.0
    c5, c9, c22 = (calibrate_damage_flow(p) for p in (5.0, 9.0, 22.0))
    assert 0.0 < c5 < c9 < c22
    assert resting_saturation_increase_pct(c22) == pytest.approx(22.0, abs=0.05)
    assert resting_saturation_increase_pct(c9) == pytest.approx(9.0, abs=0.05)


@pytest.fixture(scope="module")
def cohorte_pequena():
    return generate_cohort(CohortSpec(n_subjects=6, seed=5, contraction_weights=(("isometric", 0.5), ("eccentric", 0.5))))


@pytest.fixture(scope="module")
def datos_fisiologicos(cohorte_pequena):
    dano = CouplingLevel("dano", {"coupling_damage_flow": calibrate_damage_flow(22.0)})
    return simulate_cohort(cohorte_pequena, [NO_COUPLING, dano], optics=False)


def test_cohorte_sin_optica_estructura(datos_fisiologicos, cohorte_pequena):
    df = datos_fisiologicos
    assert df.attrs["fallos"] == []
    assert len(df) == len(cohorte_pequena) * 2 * len(RECOVERY_MARKS)
    assert not any(c.startswith("nirs_") for c in df.columns)
    assert set(feature_columns("verdad")) <= set(df.columns)
    assert df["fuerza"].between(0.0, 1.0).all()
    # el acoplamiento cambia la hemodinámica; la fuerza solo lo nota de forma indirecta y mínima
    # (más flujo -> más O2 -> resíntesis de PCr algo más rápida)
    piv = df.pivot_table(index=["sujeto", "marca"], columns="nivel", values="fuerza")
    assert np.allclose(piv["ninguno"], piv["dano"], atol=0.01)


def test_reoxigenacion_no_es_recuperacion(datos_fisiologicos):
    sin = datos_fisiologicos[datos_fisiologicos["nivel"] == "ninguno"]
    tarde = sin[sin["marca"] == "rec_30min"]
    # sin acoplamientos la oxigenación volvió al basal y la fuerza no
    assert (tarde["verdad_marca_d_diff_uM"].abs() < 1.0).all()
    assert (tarde.loc[tarde["contraccion"] == "eccentric", "fuerza"] < 0.9).all()
    tabla = dissociation_table(sin)
    fila = tabla[tabla["marca"] == "rec_30min"].iloc[0]
    assert fila["reoxigenados"] == 1.0 and fila["reox_sin_fuerza"] > 0.4


def test_el_acoplamiento_dano_flujo_deja_huella_solo_tras_excentrico(datos_fisiologicos):
    tarde = datos_fisiologicos[datos_fisiologicos["marca"] == "rec_30min"].set_index(["sujeto", "nivel"])
    for sujeto, d in tarde.groupby(level="sujeto"):
        delta = d.xs("dano", level="nivel")["verdad_marca_d_diff_uM"].iloc[0] - \
            d.xs("ninguno", level="nivel")["verdad_marca_d_diff_uM"].iloc[0]
        if d["contraccion"].iloc[0] == "eccentric":
            assert delta > 10.0
        else:
            assert abs(delta) < 1e-6


def test_cohorte_con_optica_comparte_transporte_y_ruido():
    cohorte = generate_cohort(CohortSpec(n_subjects=2, seed=8, contraction_weights=(("isometric", 1.0),)))
    dano = CouplingLevel("dano", {"coupling_damage_flow": 1.0})
    df = simulate_cohort(cohorte, [NO_COUPLING, dano])
    assert set(feature_columns("nirs")) <= set(df.columns)
    assert df[["saturado", "snr_min_db", "fraccion_musculo"]].notna().all().all()
    # isométrico: no hay daño, así que ambos niveles deben dar exactamente las mismas medidas
    cols = feature_columns("nirs")
    a = df[df["nivel"] == "ninguno"][cols].to_numpy()
    b = df[df["nivel"] == "dano"][cols].to_numpy()
    assert np.allclose(a, b, equal_nan=True)


# --- estadística sobre datos sintéticos con estructura conocida ----------------------------------
def _sinteticos(n=80, informativo=True, seed=0):
    rng = np.random.default_rng(seed)
    filas = []
    for i in range(n):
        intensidad, duracion = rng.uniform(20, 80), rng.uniform(30, 180)
        susceptibilidad = rng.normal(0.0, 0.08)  # parte de la fatiga que la dosis no explica
        for minutos, marca in zip((0, 5, 15, 30), RECOVERY_MARKS):
            dosis = 0.004 * intensidad + 0.001 * duracion
            fuerza = float(np.clip(1.0 - dosis * np.exp(-minutos / 20.0) - susceptibilidad - 0.05, 0.0, 1.0))
            fila = {"sujeto": f"S{i:03d}", "nivel": "x", "marca": marca, "minutos": minutos,
                    "intensidad_pct_mvc": intensidad, "duracion_s": duracion, "es_dinamico": 0.0,
                    "es_excentrico": 0.0, "fuerza": fuerza}
            for prefijo, ruido in (("nirs", 0.03), ("verdad", 0.0)):
                for j, col in enumerate(feature_columns(prefijo)):
                    fila[col] = rng.normal()
                if informativo:
                    fila[f"{prefijo}_marca_d_diff_uM"] = 100.0 * (susceptibilidad + rng.normal(0.0, ruido))
            filas.append(fila)
    return pd.DataFrame(filas)


def test_evaluacion_detecta_informacion_real():
    ev = evaluate(_sinteticos(informativo=True), models=("ridge",))
    g = nirs_gain(ev).set_index("alcance")
    for marca in RECOVERY_MARKS:
        assert g.loc[marca, "r2_nulo"] < 0.05
        assert g.loc[marca, "ganancia_nirs"] > 0.2
        assert g.loc[marca, "ganancia_oraculo"] >= g.loc[marca, "ganancia_nirs"] - 0.02
    glob = ev[(ev["alcance"] == "global") & (ev["conjunto"] == "dosis_nirs")].iloc[0]
    assert glob["auc_no_recuperado"] > 0.8 and glob["n"] == 80 * 4


def test_evaluacion_no_inventa_informacion():
    g = nirs_gain(evaluate(_sinteticos(informativo=False), models=("ridge",))).set_index("alcance")
    for marca in RECOVERY_MARKS:
        assert g.loc[marca, "ganancia_nirs"] < 0.05


def test_asociaciones_y_disociacion_sinteticas():
    df = _sinteticos(informativo=True)
    asoc = feature_associations(df, prefixes=("verdad",))
    fila = asoc[(asoc["marca"] == "rec_30min") & (asoc["rasgo"] == "verdad_marca_d_diff_uM")].iloc[0]
    assert fila["rho"] < -0.9 and fila["rho_parcial"] < -0.9
    df["verdad_reox_frac"] = 1.0
    tabla = dissociation_table(df).set_index("marca")
    assert (tabla["reoxigenados"] == 1.0).all()
    assert tabla.loc["rec_0min", "reox_sin_fuerza"] == pytest.approx(1.0 - tabla.loc["rec_0min", "recuperados"])


# --- procesado: filtrar antes del logaritmo -------------------------------------------------------
def test_filtrar_la_intensidad_antes_del_logaritmo_reduce_el_error_con_pocas_cuentas():
    fs, t = 10.0, np.arange(0.0, 300.0, 0.1)
    ventana_basal, tarde = (5.0, 115.0), (t >= 250.0) & (t < 260.0)
    err_viejo, err_nuevo = [], []
    for semilla in range(30):
        cuentas = np.clip(np.round(30.0 + 15.0 * np.random.default_rng(semilla).normal(size=t.size)), 0, None)[:, None]
        viejo = processing.lowpass(processing.counts_to_attenuation(cuentas, t, ventana_basal), fs, 0.5)
        nuevo = processing.counts_to_attenuation(processing.lowpass(cuentas, fs, 0.5), t, ventana_basal)
        err_viejo.append(viejo[tarde].mean())
        err_nuevo.append(nuevo[tarde].mean())
    rms = lambda x: float(np.sqrt(np.mean(np.square(x))))  # noqa: E731
    assert rms(err_nuevo) < 0.5 * rms(err_viejo)
    assert rms(err_nuevo) < 0.08  # del orden del ruido de una ventana de 10 s, sin sesgo añadido
