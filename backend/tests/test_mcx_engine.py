"""MCX-CL frente al Monte Carlo propio en un tejido de tres capas.

Ambos motores simulan la misma geometría (grosores ya redondeados a vóxeles, mismo índice,
relación de similitud g = 0, mus = mus') y se comparan en lo que mide un detector de disco:
reflectancia y trayectoria parcial media por capa, con absorciones distintas aplicadas después.
"""
import numpy as np
import pytest

from musclesense.optical_physics.diffusion import LayerOptics
from musclesense.optical_physics.mcx_engine import DetectorPathLibrary, mcx_available, run_layered_mcx
from musclesense.optical_physics.montecarlo import disk_acceptance, run_layered_monte_carlo

pytestmark = [pytest.mark.mcx, pytest.mark.slow,
              pytest.mark.skipif(not mcx_available(), reason="pmcxcl o un runtime OpenCL no disponibles")]

RHO, RADIO = 10.0, 1.5
CAPAS = (LayerOptics(1.0, 0.0, 2.0, 1.4, 0.9), LayerOptics(2.0, 0.0, 1.2, 1.4, 0.9), LayerOptics(np.inf, 0.0, 0.8, 1.4, 0.9))
ABSORCIONES = ([0.02, 0.005, 0.02], [0.03, 0.008, 0.04])


def test_aceptacion_de_disco():
    # anillo completamente dentro del disco solo si rho' = rho y el disco es enorme; aquí, valores límite
    assert disk_acceptance([10.0], 10.0, 1.5)[0] == pytest.approx(np.arccos(1 - 1.5**2 / 200.0) / np.pi)
    assert disk_acceptance([7.0, 13.0], 10.0, 1.5).tolist() == [0.0, 0.0]


@pytest.fixture(scope="module")
def bibliotecas():
    mcx = run_layered_mcx(CAPAS, 400_000, RHO, seed=11, voxel_mm=0.25, detector_radius_mm=RADIO, use_similarity=True)
    propio = run_layered_monte_carlo(CAPAS, 400_000, seed=12, mua_floor=[0.0, 0.0, 0.0], use_similarity=True,
                                     store_rho_range=(RHO - RADIO - 0.5, RHO + RADIO + 0.5))
    return mcx, propio


def test_mcx_devuelve_una_biblioteca_valida(bibliotecas):
    mcx, _ = bibliotecas
    assert isinstance(mcx, DetectorPathLibrary)
    assert mcx.ppath_mm.shape[1] == 3 and mcx.ppath_mm.shape[0] > 1000
    assert [c.thickness_mm for c in mcx.layers[:2]] == [1.0, 2.0]
    assert np.all(np.abs(mcx.exit_rho_mm - RHO) <= RADIO + 1e-4)  # solo fotones dentro de los discos
    assert mcx.outside_fraction < 0.001
    with pytest.raises(ValueError):
        mcx.reflectance(ABSORCIONES[0], 20.0)


@pytest.mark.parametrize("mua", ABSORCIONES)
def test_mcx_coincide_con_el_monte_carlo_propio(bibliotecas, mua):
    mcx, propio = bibliotecas
    r_mcx, n_mcx, e_mcx = mcx.reflectance(mua, RHO)
    r_mc, n_mc, e_mc = propio.disk_reflectance(mua, RHO, RADIO)
    sigma = np.hypot(e_mcx, e_mc)
    assert n_mcx > 1000 and n_mc > 1000
    assert abs(r_mcx / r_mc - 1.0) < max(4.0 * sigma, 0.03)
    l_mcx = mcx.mean_partial_pathlengths(mua, RHO)
    l_mc = propio.disk_partial_pathlengths(mua, RHO, RADIO)
    assert np.allclose(l_mcx, l_mc, rtol=0.06)
