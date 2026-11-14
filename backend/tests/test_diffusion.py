"""Validación matemática de la teoría de difusión (semiinfinito y N capas)."""
import numpy as np
import pytest

from musclesense.optical_physics.diffusion import (
    LayerOptics,
    boundary_factor_A,
    detection_coefficients,
    effective_reflection_coefficient,
    fresnel_reflectance,
    layered_partial_pathlengths,
    layered_reflectance,
    semi_infinite_mean_pathlength,
    semi_infinite_reflectance,
)

MUA, MUSP = 0.02, 0.8  # 1/mm, valores típicos de tejido en el NIR


def test_fresnel_incidencia_normal_y_reflexion_total():
    assert fresnel_reflectance(1.0, 1.4, 1.0) == pytest.approx(((1.4 - 1.0) / (1.4 + 1.0)) ** 2)
    cos_critico = np.sqrt(1 - 1 / 1.4**2)
    assert fresnel_reflectance(cos_critico - 0.01, 1.4, 1.0) == 1.0
    assert fresnel_reflectance(0.5, 1.4, 1.4) == 0.0


def test_coeficientes_de_frontera_para_n_1_4():
    # Haskell et al. 1994: R_eff = 0.493 para n = 1.40; Kienle y Patterson 1997: C1 = 0.118, C2 = 0.306
    assert effective_reflection_coefficient(1.4) == pytest.approx(0.493, abs=0.001)
    assert boundary_factor_A(1.4) == pytest.approx(2.95, abs=0.01)
    c1, c2 = detection_coefficients(1.4)
    assert c1 == pytest.approx(0.118, abs=0.001)
    assert c2 == pytest.approx(0.306, abs=0.001)
    assert boundary_factor_A(1.0) == 1.0


@pytest.mark.parametrize("rho", [5.0, 10.0, 20.0, 30.0, 40.0])
@pytest.mark.parametrize("model", ["flux", "farrell", "kienle"])
def test_capas_identicas_reproducen_el_medio_semiinfinito(rho, model):
    capas = [LayerOptics(1.5, MUA, MUSP), LayerOptics(4.0, MUA, MUSP), LayerOptics(np.inf, MUA, MUSP)]
    esperado = semi_infinite_reflectance(rho, MUA, MUSP, 1.4, model)
    assert layered_reflectance(rho, capas, 1.0, model) == pytest.approx(esperado, rel=1e-8)


def test_primera_capa_muy_gruesa_equivale_a_semiinfinito():
    capas = [LayerOptics(300.0, MUA, MUSP), LayerOptics(np.inf, 0.2, 2.0)]
    assert layered_reflectance(25.0, capas) == pytest.approx(semi_infinite_reflectance(25.0, MUA, MUSP), rel=1e-6)


def test_las_trayectorias_parciales_suman_la_trayectoria_total():
    capas = [LayerOptics(1.5, MUA, MUSP), LayerOptics(4.0, MUA, MUSP), LayerOptics(np.inf, MUA, MUSP)]
    parciales = layered_partial_pathlengths(30.0, capas)
    assert (parciales > 0).all()
    assert parciales.sum() == pytest.approx(semi_infinite_mean_pathlength(30.0, MUA, MUSP), rel=1e-4)


def test_dpf_en_el_intervalo_fisiologico():
    # Medidas in vivo en antebrazo y pantorrilla dan DPF entre 4 y 6 aproximadamente.
    dpf = semi_infinite_mean_pathlength(30.0, 0.02, 0.7) / 30.0
    assert 3.0 < dpf < 7.0


def test_mas_grasa_reduce_la_trayectoria_en_el_musculo():
    def fraccion_musculo(att_mm):
        capas = [
            LayerOptics(1.5, 0.02, 2.0),
            LayerOptics(att_mm, 0.004, 1.1),
            LayerOptics(np.inf, 0.02, 0.7),
        ]
        p = layered_partial_pathlengths(30.0, capas)
        return p[2] / p.sum()

    fracciones = [fraccion_musculo(a) for a in (2.0, 5.0, 10.0)]
    assert fracciones[0] > fracciones[1] > fracciones[2]


def test_mas_absorcion_en_el_musculo_reduce_la_reflectancia():
    def r(mua_musculo):
        return layered_reflectance(
            30.0, [LayerOptics(1.5, 0.02, 2.0), LayerOptics(4.0, 0.004, 1.1), LayerOptics(np.inf, mua_musculo, 0.7)]
        )

    assert r(0.015) > r(0.020) > r(0.025)


def test_fuente_fuera_de_la_primera_capa_se_rechaza():
    with pytest.raises(ValueError):
        layered_reflectance(20.0, [LayerOptics(0.3, 0.01, 1.0), LayerOptics(np.inf, 0.02, 0.7)])
