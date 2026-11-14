"""Tejido, sensor y cadena completa con propagación de cambios."""
from dataclasses import replace

import numpy as np
import pytest

from musclesense.exercise_protocol.model import ProtocolSpec
from musclesense.pipeline import Pipeline, Scenario, SimulationSettings
from musclesense.sensor_designer.device import SensorDesign, TiaSpec
from musclesense.tissue_simulator.model import PROFILES, TissueModel


def test_propiedades_opticas_en_intervalos_publicados():
    tejido = TissueModel.default()
    piel, grasa, musculo = tejido.optics(810.0)
    assert 0.015 < musculo.mua < 0.04  # 1/mm
    assert grasa.mua < musculo.mua
    assert piel.musp > grasa.musp > musculo.musp > 0.4
    assert 1.0 / (piel.mua + piel.musp) < piel.thickness_mm  # condición del modelo de difusión
    assert np.isinf(musculo.thickness_mm)


def test_mas_melanina_solo_cambia_la_piel():
    claro, oscuro = TissueModel.default(**PROFILES["referencia"]), TissueModel.default(**PROFILES["piel_oscura"])
    assert oscuro.skin.mua(760.0) > 2 * claro.skin.mua(760.0)
    assert oscuro.muscle.mua(760.0) == claro.muscle.mua(760.0)


def test_cadena_de_ruido_del_sensor():
    sensor = SensorDesign()
    i = np.full(2000, 2e-9)
    adq = sensor.acquire(i, np.random.default_rng(0))
    assert not adq["saturated"].any()
    medido = adq["counts"] * sensor.adc.lsb_V / sensor.tia.rf_ohm
    assert medido.mean() == pytest.approx(2e-9, rel=0.01)
    assert medido.std() == pytest.approx(adq["noise_rms_A"][0], rel=0.1)
    silencioso = replace(sensor, tia=TiaSpec(rf_ohm=1e7, cf_pF=1.0))
    assert silencioso.noise_current_rms(2e-9) < sensor.noise_current_rms(2e-9)
    assert sensor.acquire(np.array([1e-5]))["saturated"].all()


@pytest.fixture(scope="module")
def tuberia():
    return Pipeline()


@pytest.fixture(scope="module")
def base(tuberia):
    return tuberia.run(Scenario())


def test_escenario_de_referencia(base):
    assert base.counts.shape == (base.t.size, 3)
    assert not base.saturated and (base.snr_db > 20).all()
    assert (base.partial_pathlengths_mm > 0).all()
    assert 0.2 < base.muscle_path_fraction.mean() < 0.95
    # la estimación sigue a la verdad en forma, pero no en escala
    r = np.corrcoef(base.estimated["d_deoxy"], base.truth["d_deoxy"])[0, 1]
    assert r > 0.95
    escala = np.polyfit(base.truth["d_deoxy"], base.estimated["d_deoxy"], 1)[0]
    assert 0.05 < escala < 2.0
    assert 5.0 < base.features["estimado"]["t_medio_reox_s"] < 60.0


def test_repetir_el_escenario_no_recalcula_nada(tuberia, base):
    assert tuberia.run(Scenario()).recomputed == []


def test_cambiar_el_amplificador_no_repite_transporte_ni_fisiologia(tuberia, base):
    esc = Scenario(sensor=replace(SensorDesign(), tia=TiaSpec(rf_ohm=1e7, cf_pF=1.0)))
    rec = tuberia.run(esc).recomputed
    assert "electronics" in rec and "processing" in rec
    assert not {"optics", "transport", "physiology", "absorption", "optical_signal"} & set(rec)


def test_cambiar_el_ejercicio_no_repite_el_transporte(tuberia, base):
    rec = tuberia.run(Scenario(protocol=ProtocolSpec(intensity_pct_mvc=30.0))).recomputed
    assert "physiology" in rec and "features" in rec
    assert "transport" not in rec and "optics" not in rec


def test_cambiar_la_grasa_repite_el_transporte_y_reduce_la_sensibilidad(tuberia, base):
    esc = Scenario(tissue=TissueModel.default(att_mm=9.0))
    res = tuberia.run(esc)
    assert {"optics", "transport", "optical_signal"} <= set(res.recomputed)
    assert "physiology" not in res.recomputed
    assert res.muscle_path_fraction.mean() < base.muscle_path_fraction.mean()
    assert abs(res.features["estimado"]["caida_diff_uM"]) < abs(base.features["estimado"]["caida_diff_uM"])


def test_cambiar_la_distancia_repite_el_transporte(tuberia, base):
    res = tuberia.run(Scenario(sensor=SensorDesign(sds_mm=40.0)))
    assert "transport" in res.recomputed and "physiology" not in res.recomputed
    assert res.partial_pathlengths_mm.sum(axis=1).mean() > base.partial_pathlengths_mm.sum(axis=1).mean()


@pytest.mark.slow
def test_motor_monte_carlo_coherente_con_difusion(base):
    res = Pipeline().run(Scenario(settings=SimulationSettings(engine="montecarlo", n_photons=250_000)))
    assert res.muscle_path_fraction.mean() == pytest.approx(base.muscle_path_fraction.mean(), abs=0.15)
    assert np.corrcoef(res.estimated["d_deoxy"], base.estimated["d_deoxy"])[0, 1] > 0.95
