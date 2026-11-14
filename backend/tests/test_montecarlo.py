"""Validación del Monte Carlo propio contra soluciones exactas y contra la difusión."""
import numpy as np
import pytest

from musclesense.optical_physics.diffusion import (
    LayerOptics,
    layered_partial_pathlengths,
    layered_reflectance,
    semi_infinite_mean_pathlength,
    semi_infinite_reflectance,
)
from musclesense.optical_physics.montecarlo import run_layered_monte_carlo


def test_losa_de_van_de_hulst():
    """Losa con índice igualado: mua = 10 /cm, mus = 90 /cm, g = 0.75, d = 0.02 cm.

    Valores de van de Hulst citados en Wang, Jacques y Zheng (1995), tabla 1:
    Rd = 0.09739 y Tt = 0.66096.
    """
    losa = [LayerOptics(0.2, 1.0, 9.0 * (1 - 0.75), n=1.0, g=0.75)]
    lib = run_layered_monte_carlo(losa, 400_000, seed=1, mua_floor=[1.0])
    assert lib.total_reflectance([1.0]) == pytest.approx(0.09739, abs=0.0015)
    assert lib.total_transmittance([1.0]) == pytest.approx(0.66096, abs=0.0025)


def test_semiinfinito_isotropo_con_indice_igualado_solucion_exacta():
    """Albedo 0.9, esparcimiento isótropo, n = 1: R = 1 - H(1)·sqrt(1 - a) = 0.41495.

    H es la función de Chandrasekhar; el valor se obtuvo resolviendo su ecuación integral.
    """
    lib = run_layered_monte_carlo([LayerOptics(np.inf, 1.0, 9.0, n=1.0, g=0.0)], 300_000, seed=3, mua_floor=[1.0])
    assert lib.total_reflectance([1.0]) == pytest.approx(0.41495, abs=0.003)


def test_semiinfinito_de_giovanelli_con_indice_desigual():
    """n = 1.5, isótropo, albedo 0.9: reflectancia total 0.2600 (Giovanelli) y 0.25907 (MCML).

    El valor tabulado incluye la reflexión especular (0.04); aquí se suma a la difusa.
    """
    lib = run_layered_monte_carlo([LayerOptics(np.inf, 1.0, 9.0, n=1.5, g=0.0)], 300_000, seed=2, mua_floor=[1.0])
    assert lib.specular_reflectance == pytest.approx(0.04)
    total = lib.total_reflectance([1.0]) + lib.specular_reflectance
    assert total == pytest.approx(0.2600, abs=0.003)


def test_la_reponderacion_reproduce_una_simulacion_con_otra_absorcion():
    """La misma biblioteca, reponderada, debe dar la reflectancia exacta para otra absorción."""
    lib = run_layered_monte_carlo([LayerOptics(np.inf, 0.5, 9.0, n=1.0, g=0.0)], 300_000, seed=5, mua_floor=[0.5])
    # con mua = 1 /mm y mus = 9 /mm el albedo vuelve a ser 0.9 y la solución exacta es 0.41495
    assert lib.total_reflectance([1.0]) == pytest.approx(0.41495, abs=0.003)
    with pytest.raises(ValueError):
        lib.total_reflectance([0.1])  # por debajo del mínimo de validez


@pytest.fixture(scope="module")
def biblioteca_homogenea():
    medio = [LayerOptics(np.inf, 0.02, 1.0, n=1.4, g=0.0)]
    return run_layered_monte_carlo(medio, 400_000, seed=11, mua_floor=[0.01], store_rho_range=(5.0, 40.0))


@pytest.mark.slow
@pytest.mark.parametrize("rho,tolerancia", [(10.0, 0.15), (15.0, 0.08), (20.0, 0.08), (25.0, 0.10)])
def test_monte_carlo_frente_a_difusion_en_medio_homogeneo(biblioteca_homogenea, rho, tolerancia):
    """La difusión sobrestima la reflectancia cerca de la fuente (+11 % a 10 mm) y converge
    al Monte Carlo a partir de unos 15 mm (diferencias de 0 a 4 %)."""
    r_mc, n_det, err = biblioteca_homogenea.reflectance([0.02], rho, half_width=1.0)
    r_dif = semi_infinite_reflectance(rho, 0.02, 1.0, 1.4, "kienle")
    assert n_det > 300
    assert r_mc == pytest.approx(r_dif, rel=max(tolerancia, 4 * err))
    l_mc = biblioteca_homogenea.mean_partial_pathlengths([0.02], rho, half_width=1.0)[0]
    assert l_mc == pytest.approx(semi_infinite_mean_pathlength(rho, 0.02, 1.0, 1.4), rel=0.06)


@pytest.mark.slow
def test_derivada_logaritmica_coincide_con_la_trayectoria_media(biblioteca_homogenea):
    """Identidad <L> = -d ln R / d mua, comprobada sobre la propia biblioteca."""
    rho, h = 20.0, 1e-4
    r_mas, _, _ = biblioteca_homogenea.reflectance([0.02 + h], rho)
    r_menos, _, _ = biblioteca_homogenea.reflectance([0.02 - h], rho)
    derivada = -(np.log(r_mas) - np.log(r_menos)) / (2 * h)
    media = biblioteca_homogenea.mean_partial_pathlengths([0.02], rho)[0]
    assert derivada == pytest.approx(media, rel=1e-4)


@pytest.mark.slow
def test_tres_capas_monte_carlo_frente_a_difusion():
    """Piel, grasa y músculo: la difusión de N capas debe aproximar al Monte Carlo."""
    capas = [
        LayerOptics(1.5, 0.020, 2.0, n=1.4, g=0.0),
        LayerOptics(4.0, 0.004, 1.1, n=1.4, g=0.0),
        LayerOptics(np.inf, 0.020, 0.7, n=1.4, g=0.0),
    ]
    mua = [0.020, 0.004, 0.020]
    lib = run_layered_monte_carlo(capas, 600_000, seed=21, mua_floor=[0.01, 0.002, 0.01],
                                  store_rho_range=(10.0, 40.0))
    rho = 25.0
    r_mc, n_det, err = lib.reflectance(mua, rho, half_width=1.5)
    assert n_det > 500
    assert r_mc == pytest.approx(layered_reflectance(rho, capas), rel=0.25)
    p_mc = lib.mean_partial_pathlengths(mua, rho, half_width=1.5)
    p_dif = layered_partial_pathlengths(rho, capas)
    # la fracción de trayectoria en el músculo es la magnitud que importa para la señal
    assert p_mc[2] / p_mc.sum() == pytest.approx(p_dif[2] / p_dif.sum(), abs=0.10)
