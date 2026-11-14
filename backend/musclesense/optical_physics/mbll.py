"""Ley de Beer-Lambert modificada (Delpy et al. 1988).

Para un cambio pequeño de absorción a esparcimiento constante,

    dA(lambda) = sum_i alpha_i(lambda) · dc_i · L(lambda),        A = -ln(I/I0)

donde L es la trayectoria media de los fotones detectados. En tejido homogéneo L = DPF · rho;
en tejido en capas L es la trayectoria parcial en la capa donde ocurre el cambio.

Convención: atenuación en logaritmo natural, alpha en mm^-1 por mM de grupo hemo,
concentraciones en mM de grupo hemo. Las columnas de concentración son [oxigenada, desoxigenada].
"""
from __future__ import annotations

import numpy as np

from .spectra import band_average, heme_absorption

__all__ = ["extinction_matrix", "forward_delta_attenuation", "solve_concentration_changes", "condition_number"]


def extinction_matrix(wavelengths_nm, fwhm_nm=None) -> np.ndarray:
    """Matriz E (n_lambda x 2) de absorción específica; con fwhm_nm promedia sobre cada LED."""
    wavelengths_nm = np.atleast_1d(np.asarray(wavelengths_nm, dtype=float))
    if fwhm_nm is None:
        oxi, desoxi = heme_absorption(wavelengths_nm)
        return np.column_stack([oxi, desoxi])
    anchos = np.broadcast_to(np.asarray(fwhm_nm, dtype=float), wavelengths_nm.shape)
    filas = []
    for pico, ancho in zip(wavelengths_nm, anchos):
        filas.append([
            band_average(lambda lam: heme_absorption(lam)[0], pico, ancho),
            band_average(lambda lam: heme_absorption(lam)[1], pico, ancho),
        ])
    return np.asarray(filas)


def forward_delta_attenuation(delta_conc_mM, pathlength_mm, wavelengths_nm, fwhm_nm=None) -> np.ndarray:
    """Cambio de atenuación (..., n_lambda) para cambios de concentración (..., 2)."""
    e = extinction_matrix(wavelengths_nm, fwhm_nm)
    path = np.broadcast_to(np.asarray(pathlength_mm, dtype=float), (e.shape[0],))
    return np.asarray(delta_conc_mM, dtype=float) @ (e * path[:, None]).T


def solve_concentration_changes(delta_attenuation, pathlength_mm, wavelengths_nm, fwhm_nm=None) -> np.ndarray:
    """Invierte la ley: cambios de concentración (..., 2) en mM a partir de dA (..., n_lambda).

    Con dos longitudes de onda es una solución exacta; con tres, mínimos cuadrados.
    """
    e = extinction_matrix(wavelengths_nm, fwhm_nm)
    path = np.broadcast_to(np.asarray(pathlength_mm, dtype=float), (e.shape[0],))
    return np.asarray(delta_attenuation, dtype=float) @ np.linalg.pinv(e * path[:, None]).T


def condition_number(wavelengths_nm, fwhm_nm=None) -> float:
    """Número de condición de la matriz de extinción: cuánto amplifica el ruido la inversión."""
    return float(np.linalg.cond(extinction_matrix(wavelengths_nm, fwhm_nm)))
