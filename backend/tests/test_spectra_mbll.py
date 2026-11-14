"""Espectros de cromóforos y ley de Beer-Lambert modificada."""
import numpy as np
import pytest

from musclesense.optical_physics import mbll, spectra


def test_tabla_cubre_650_a_950_nm_sin_huecos():
    tabla = spectra.load_spectra()
    assert tabla["lambda_nm"][0] == 650 and tabla["lambda_nm"][-1] == 950
    assert np.all(np.diff(tabla["lambda_nm"]) == 2)
    for columna, valores in tabla.items():
        assert np.all(np.isfinite(valores)) and np.all(valores > 0), columna


def test_valores_de_prahl_en_las_tres_longitudes_de_onda():
    # Compilación de S. Prahl (datos de Gratzer y Kollias), cm^-1/M por tetrámero
    tabla = spectra.load_spectra()
    esperado = {760: (586.0, 1548.52), 810: (864.0, 717.08), 850: (1058.0, 691.32)}
    for lam, (oxi, desoxi) in esperado.items():
        i = int(np.flatnonzero(tabla["lambda_nm"] == lam)[0])
        assert tabla["eps_hbo2_cm1_M1"][i] == pytest.approx(oxi)
        assert tabla["eps_hhb_cm1_M1"][i] == pytest.approx(desoxi)


def test_conversion_de_unidades_de_la_sangre_entera():
    # Sangre con 150 g/L de Hb (2.326 mM de tetrámero = 9.30 mM de hemo), totalmente oxigenada:
    # mua(810) = ln(10) · 864 cm^-1/M · 2.326e-3 M = 4.63 cm^-1 = 0.463 mm^-1
    oxi, _ = spectra.heme_absorption(810.0)
    assert oxi * 9.302 == pytest.approx(0.4627, rel=1e-3)


def test_punto_isosbestico_cerca_de_800_nm():
    lam = np.arange(780.0, 821.0, 1.0)
    oxi, desoxi = spectra.heme_absorption(lam)
    cruce = lam[np.argmin(np.abs(oxi - desoxi))]
    assert 795 <= cruce <= 805


def test_espectro_del_led_normalizado_y_centrado():
    lam, pesos = spectra.led_spectrum(760.0, 30.0)
    assert pesos.sum() == pytest.approx(1.0)
    assert np.sum(lam * pesos) == pytest.approx(760.0, abs=1e-6)
    assert spectra.band_average(lambda x: x, 810.0, 0.0) == 810.0


def test_el_ancho_del_led_cambia_la_extincion_efectiva_a_760_nm():
    # 760 nm cae sobre un máximo local de la HHb: promediar sobre el LED lo rebaja.
    e_linea = mbll.extinction_matrix([760.0])
    e_led = mbll.extinction_matrix([760.0], fwhm_nm=30.0)
    assert e_led[0, 1] < e_linea[0, 1]
    assert abs(e_led[0, 1] / e_linea[0, 1] - 1) > 0.01


@pytest.mark.parametrize("longitudes", [(760.0, 850.0), (760.0, 810.0, 850.0)])
def test_la_inversion_recupera_los_cambios_de_concentracion(longitudes):
    cambios = np.array([[-0.010, 0.012], [0.004, -0.001], [0.0, 0.0]])  # mM de hemo
    trayectoria = 120.0
    d_a = mbll.forward_delta_attenuation(cambios, trayectoria, longitudes)
    assert d_a.shape == (3, len(longitudes))
    recuperado = mbll.solve_concentration_changes(d_a, trayectoria, longitudes)
    assert recuperado == pytest.approx(cambios, abs=1e-12)


def test_trayectoria_mal_supuesta_escala_el_resultado():
    cambios = np.array([-0.010, 0.012])
    d_a = mbll.forward_delta_attenuation(cambios, 120.0, (760.0, 850.0))
    estimado = mbll.solve_concentration_changes(d_a, 150.0, (760.0, 850.0))
    assert estimado == pytest.approx(cambios * 120.0 / 150.0)


def test_numero_de_condicion_razonable():
    assert mbll.condition_number((760.0, 850.0)) < 10
    assert mbll.condition_number((800.0, 805.0)) > mbll.condition_number((760.0, 850.0))
