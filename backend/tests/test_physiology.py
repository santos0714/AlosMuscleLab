"""Modelo fisiológico: reposo, ejercicio, recuperación y disociación entre oxigenación y fuerza."""
from dataclasses import replace

import numpy as np
import pytest

from musclesense.exercise_protocol.model import PhysiologyParams, ProtocolSpec, hill_po2, hill_saturation, simulate_protocol


@pytest.fixture(scope="module")
def referencia():
    return simulate_protocol(PhysiologyParams(), ProtocolSpec())


def test_hill_y_su_inversa():
    assert hill_saturation(26.9, 26.9, 2.7) == pytest.approx(0.5)
    assert hill_po2(hill_saturation(40.0, 26.9, 2.7), 26.9, 2.7) == pytest.approx(40.0)


def test_el_reposo_es_un_estado_estacionario(referencia):
    basal = referencia.t < referencia.protocol.t_exercise_start - 1
    for serie in (referencia.smo2, referencia.smbo2, referencia.thb, referencia.mvo2):
        assert np.ptp(serie[basal]) < 1e-3 * abs(serie[0]) + 1e-9
    assert 0.55 < referencia.smo2[0] < 0.80  # intervalo publicado de SmO2 en reposo
    assert referencia.force_capacity[0] == 1.0


def test_el_ejercicio_desoxigena_y_la_recuperacion_reoxigena(referencia):
    pr = referencia.protocol
    fin = int(np.searchsorted(referencia.t, pr.t_exercise_end)) - 1
    assert referencia.smo2[fin] < referencia.smo2[0] - 0.2
    assert referencia.smbo2.min() < referencia.smbo2[0]
    post = referencia.smo2[fin:]
    mitad = referencia.smo2[fin] + 0.5 * (referencia.smo2[0] - referencia.smo2[fin])
    t_medio = referencia.t[fin + int(np.argmax(post >= mitad))] - pr.t_exercise_end
    assert 8.0 < t_medio < 55.0  # tiempo medio de reoxigenación publicado: 10 a 55 s
    assert post.max() > referencia.smo2[0]  # sobreimpulso hiperémico
    assert referencia.thb.max() > referencia.thb[0]


def test_la_oxigenacion_se_recupera_antes_que_la_fuerza(referencia):
    """Disociación: a los 5 min la SmO2 ya está en el basal y la fuerza no."""
    t5 = referencia.protocol.t_exercise_end + 300.0
    a5 = referencia.at(t5)
    assert abs(a5["smo2"] - referencia.smo2[0]) < 0.04
    assert a5["force_capacity"] < 0.95
    a30 = referencia.at(referencia.protocol.t_exercise_end + 1800.0)
    assert a5["force_capacity"] < a30["force_capacity"] < 1.0


def test_contraccion_sostenida_de_baja_intensidad_en_biceps():
    """15 % MVC durante 43 min: la fuerza cae a cerca del 59 % y solo vuelve a cerca del 85 %."""
    r = simulate_protocol(PhysiologyParams(), ProtocolSpec(intensity_pct_mvc=15, exercise_s=2580))
    fin = r.protocol.t_exercise_end
    assert r.at(fin - 1)["force_capacity"] == pytest.approx(0.59, abs=0.10)
    assert r.at(fin + 1800)["force_capacity"] == pytest.approx(0.85, abs=0.08)
    assert abs(r.at(fin + 120)["smo2"] - r.smo2[0]) < 0.03


def test_sin_acoplamientos_el_dano_no_deja_huella_hemodinamica():
    p = PhysiologyParams()
    comun = dict(intensity_pct_mvc=60, exercise_s=120, duty_cycle=0.5)
    dinamico = simulate_protocol(p, ProtocolSpec(contraction="dynamic", **comun))
    excentrico = simulate_protocol(p, ProtocolSpec(contraction="eccentric", **comun))
    assert np.allclose(dinamico.smo2, excentrico.smo2) and np.allclose(dinamico.thb, excentrico.thb)
    assert excentrico.force_capacity[-1] < dinamico.force_capacity[-1] - 0.1


def test_con_acoplamiento_el_dano_eleva_la_saturacion_de_reposo():
    p = replace(PhysiologyParams(), coupling_damage_flow=0.6)
    pr = ProtocolSpec(contraction="eccentric", intensity_pct_mvc=80, exercise_s=120)
    r = simulate_protocol(p, pr)
    assert r.at(pr.t_exercise_end + 1500)["smo2"] > r.smo2[0] + 0.01


def test_oclusion_de_prueba_hace_caer_la_saturacion():
    pr = ProtocolSpec(occlusion_test_s=20.0)
    r = simulate_protocol(PhysiologyParams(), pr)
    a, b = pr.occlusion_windows()[0]
    assert r.at(b - 0.5)["smo2"] < r.at(a - 1.0)["smo2"] - 0.005
    assert r.at(b - 0.5)["thb"] == pytest.approx(r.at(a - 1.0)["thb"], rel=1e-3)


def test_integracion_segura_entre_hilos():
    # LSODA guarda estado global; sin el candado, dos hilos a la vez lanzan IntegratorConcurrencyError
    from concurrent.futures import ThreadPoolExecutor
    from dataclasses import replace as _replace

    from musclesense.exercise_protocol.model import PhysiologyParams, ProtocolSpec, simulate_protocol

    protocolos = [ProtocolSpec(intensity_pct_mvc=20.0 + 10.0 * i, recovery_s=300.0) for i in range(6)]
    with ThreadPoolExecutor(max_workers=6) as ex:
        resultados = list(ex.map(lambda pr: simulate_protocol(_replace(PhysiologyParams()), pr), protocolos))
    secuenciales = [simulate_protocol(PhysiologyParams(), pr) for pr in protocolos]
    for a, b in zip(resultados, secuenciales):
        assert np.allclose(a.force_capacity, b.force_capacity)
