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
from musclesense.recovery_analysis.cohort import PHYSIOLOGY_VARIABILITY, Triangular, _desde_datos, _rest_smo2
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


def test_triangular_ppf_es_la_inversa_de_la_distribucion():
    d = Triangular(18.0, 32.0, 68.0)
    assert d.ppf(0.0) == 18.0 and d.ppf(1.0) == 68.0
    assert d.ppf((32.0 - 18.0) / (68.0 - 18.0)) == pytest.approx(32.0)
    u = (np.arange(4000) + 0.5) / 4000
    x = np.array([d.ppf(v) for v in u])
    assert np.all(np.diff(x) > 0)
    # la media de la inversa sobre u uniforme es la media analítica de la triangular
    assert x.mean() == pytest.approx((18.0 + 32.0 + 68.0) / 3.0, rel=1e-4)
    muestra = np.random.default_rng(0).triangular(18.0, 32.0, 68.0, 200_000)
    assert np.quantile(muestra, [0.1, 0.5, 0.9]) == pytest.approx([d.ppf(0.1), d.ppf(0.5), d.ppf(0.9)], rel=5e-3)
    assert Triangular(2.0, 2.0, 2.0).ppf(0.3) == 2.0


def _tabla_parametros(cohorte):
    return pd.DataFrame([{**{c: getattr(s.physiology, c) for c in PHYSIOLOGY_VARIABILITY}, "z": s.phenotype}
                         for s in cohorte])


def test_fenotipo_oxidativo_correlaciona_sin_cambiar_las_marginales():
    from scipy import stats
    from musclesense.recovery_analysis.cohort import PHENOTYPE_SIGNS

    n = 600
    indep = _tabla_parametros(generate_cohort(CohortSpec(n_subjects=n, seed=5, phenotype_correlation=0.0)))
    corr = _tabla_parametros(generate_cohort(CohortSpec(n_subjects=n, seed=5, phenotype_correlation=0.5)))
    # marginales: mismos intervalos y misma distribución (Kolmogorov-Smirnov frente a la independiente)
    for campo in PHYSIOLOGY_VARIABILITY:
        d = _desde_datos(*PHYSIOLOGY_VARIABILITY[campo])
        assert d.low - 1e-12 <= corr[campo].min() and corr[campo].max() <= d.high + 1e-12
        assert stats.ks_2samp(indep[campo], corr[campo]).pvalue > 1e-3, campo
    # dependencia: signo y magnitud entre pares ligados; nula con r = 0 y para parámetros no ligados
    rho = corr.corr(method="spearman")
    rho0 = indep.corr(method="spearman")
    ligados = list(PHENOTYPE_SIGNS)
    for i, a in enumerate(ligados):
        assert np.sign(rho.loc[a, "z"]) == PHENOTYPE_SIGNS[a]
        for b in ligados[i + 1:]:
            esperado = PHENOTYPE_SIGNS[a] * PHENOTYPE_SIGNS[b] * 0.5
            assert rho.loc[a, b] == pytest.approx(esperado, abs=0.12), (a, b)
            assert abs(rho0.loc[a, b]) < 0.12, (a, b)
    assert abs(rho.loc["hb_blood_g_dl", "tau_pcr_s"]) < 0.12
    assert abs(rho.loc["tau_ph_s", "z"]) < 0.12


def test_fenotipo_comparacion_pareada_y_compatibilidad():
    base = generate_cohort(CohortSpec(n_subjects=12, seed=3))
    assert all(np.isnan(s.phenotype) for s in base)
    # el muestreo original no cambia al añadir la opción: cifras del estudio publicado (v0.1)
    publicado = generate_cohort(CohortSpec(n_subjects=150, seed=2026))
    assert publicado.rejected == 42
    assert sum(s.protocol.contraction == "isometric" for s in publicado) == 86
    assert publicado.subjects[7].physiology.tau_pcr_s == pytest.approx(46.33596141405443, rel=1e-12)
    a = generate_cohort(CohortSpec(n_subjects=12, seed=3, phenotype_correlation=0.0))
    b = generate_cohort(CohortSpec(n_subjects=12, seed=3, phenotype_correlation=0.75))
    for sa, sb in zip(a, b):
        # mismo fenotipo, protocolo, tejido y parámetros no ligados; solo cambia la dependencia
        assert sa.phenotype == sb.phenotype and sa.protocol == sb.protocol and sa.tissue_kwargs == sb.tissue_kwargs
        assert sa.physiology.hb_blood_g_dl == sb.physiology.hb_blood_g_dl
    assert any(sa.physiology.tau_pcr_s != sb.physiology.tau_pcr_s for sa, sb in zip(a, b))
    with pytest.raises(ValueError):
        CohortSpec(phenotype_correlation=1.0)
    with pytest.raises(ValueError):
        CohortSpec(phenotype_signs=(("tau_pcr_s", 0),))
