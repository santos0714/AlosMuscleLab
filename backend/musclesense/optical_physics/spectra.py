"""Espectros de absorción de los cromóforos del tejido en el infrarrojo cercano.

Los datos tabulados están en ``data/espectros_cromoforos.csv`` (650 a 950 nm, paso de 2 nm):
coeficientes de extinción molar decádicos de HbO2 y HHb en cm^-1/M por tetrámero y absorción
del agua y del lípido puros en cm^-1. La procedencia de cada columna está documentada en
``docs/investigacion/02_optica_de_tejidos_y_modelos.md``.

Aquí se convierten a las unidades internas: mm^-1 para la absorción y mm^-1 por mM de grupo
hemo para la hemoglobina y la mioglobina.

    mua [cm^-1] = ln(10) · eps [cm^-1/M] · C [M]        (C en tetrámeros)

Un tetrámero de hemoglobina tiene cuatro grupos hemo; la mioglobina tiene uno. Se asume que
la mioglobina tiene, por grupo hemo, el mismo espectro que la hemoglobina en este intervalo.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

import numpy as np

__all__ = [
    "DATA_DIR",
    "load_spectra",
    "heme_absorption",
    "water_absorption",
    "lipid_absorption",
    "melanosome_absorption",
    "led_spectrum",
    "band_average",
]

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_LN10 = float(np.log(10.0))


@lru_cache(maxsize=1)
def load_spectra() -> dict:
    """Devuelve los espectros tabulados como arreglos de NumPy."""
    columnas: dict = {}
    with open(DATA_DIR / "espectros_cromoforos.csv", newline="", encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            for clave, valor in fila.items():
                columnas.setdefault(clave, []).append(float(valor))
    return {clave: np.asarray(valores) for clave, valores in columnas.items()}


def _interp(wavelength_nm, columna: str) -> np.ndarray:
    tabla = load_spectra()
    wl = np.asarray(wavelength_nm, dtype=float)
    lam = tabla["lambda_nm"]
    if np.any(wl < lam[0]) or np.any(wl > lam[-1]):
        raise ValueError(f"longitud de onda fuera del intervalo tabulado ({lam[0]:.0f}-{lam[-1]:.0f} nm)")
    return np.interp(wl, lam, tabla[columna])


def heme_absorption(wavelength_nm):
    """Absorción específica por grupo hemo: (oxigenado, desoxigenado) en mm^-1 por mM de hemo."""
    factor = _LN10 / 4.0 * 1e-3 / 10.0  # por hemo, de M a mM y de cm^-1 a mm^-1
    return factor * _interp(wavelength_nm, "eps_hbo2_cm1_M1"), factor * _interp(wavelength_nm, "eps_hhb_cm1_M1")


def water_absorption(wavelength_nm) -> np.ndarray:
    """Absorción del agua pura en mm^-1."""
    return _interp(wavelength_nm, "mua_agua_cm1") / 10.0


def lipid_absorption(wavelength_nm) -> np.ndarray:
    """Absorción del lípido puro en mm^-1."""
    return _interp(wavelength_nm, "mua_lipido_cm1") / 10.0


def melanosome_absorption(wavelength_nm) -> np.ndarray:
    """Absorción del melanosoma en mm^-1: 6.6e11 · lambda^-3.33 cm^-1 (Jacques)."""
    wl = np.asarray(wavelength_nm, dtype=float)
    return 6.6e11 * wl**-3.33 / 10.0


def led_spectrum(peak_nm: float, fwhm_nm: float, n_points: int = 15):
    """Espectro de emisión gaussiano de un LED: (longitudes de onda, pesos que suman 1)."""
    if fwhm_nm <= 0:
        return np.array([float(peak_nm)]), np.array([1.0])
    sigma = fwhm_nm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    lam = np.linspace(peak_nm - 2.5 * sigma, peak_nm + 2.5 * sigma, n_points)
    pesos = np.exp(-0.5 * ((lam - peak_nm) / sigma) ** 2)
    return lam, pesos / pesos.sum()


def band_average(funcion, peak_nm: float, fwhm_nm: float) -> float:
    """Promedio de ``funcion(lambda)`` sobre el espectro de emisión del LED."""
    lam, pesos = led_spectrum(peak_nm, fwhm_nm)
    return float(np.sum(pesos * funcion(lam)))
