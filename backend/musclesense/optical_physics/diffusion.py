"""Teoría de difusión estacionaria para medios turbios.

Contiene:
  * Reflectancia de Fresnel y los coeficientes de frontera que se derivan de ella.
  * Medio semiinfinito homogéneo con frontera extrapolada (Farrell, Patterson y Wilson 1992;
    Kienle y Patterson 1997).
  * Medio de N capas planas resuelto en el dominio de Hankel (Kienle et al. 1998), con
    recursión de admitancias para las capas inferiores.

Unidades: longitudes en mm, coeficientes en 1/mm. La reflectancia R(rho) se da en 1/mm^2 por
fotón incidente (potencia detectada por unidad de área y por unidad de potencia emitida).

Supuestos de la solución de N capas: mismo índice de refracción en todas las capas, fuente
isótropa puntual a profundidad z0 = 1/(mua + musp) dentro de la primera capa y última capa
semiinfinita.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

import numpy as np
from scipy import special

__all__ = [
    "LayerOptics",
    "fresnel_reflectance",
    "effective_reflection_coefficient",
    "boundary_factor_A",
    "detection_coefficients",
    "semi_infinite_fluence_and_flux",
    "semi_infinite_reflectance",
    "semi_infinite_mean_pathlength",
    "layered_reflectance",
    "layered_partial_pathlengths",
]


@dataclass(frozen=True)
class LayerOptics:
    """Propiedades ópticas de una capa plana a una longitud de onda."""

    thickness_mm: float  # usar np.inf en la última capa
    mua: float  # 1/mm
    musp: float  # 1/mm, coeficiente de esparcimiento reducido
    n: float = 1.4
    g: float = 0.9  # solo lo usa Monte Carlo

    @property
    def mus(self) -> float:
        """Coeficiente de esparcimiento (no reducido)."""
        return self.musp / (1.0 - self.g) if self.g < 1.0 else self.musp


# --------------------------------------------------------------------------- Fresnel y frontera
def fresnel_reflectance(cos_i, n_in: float, n_out: float):
    """Reflectancia de Fresnel para luz no polarizada que incide desde n_in hacia n_out."""
    cos_i = np.clip(np.asarray(cos_i, dtype=float), 0.0, 1.0)
    if n_in == n_out:
        return np.zeros_like(cos_i)
    sin_t2 = (n_in / n_out) ** 2 * (1.0 - cos_i**2)
    total = sin_t2 >= 1.0
    cos_t = np.sqrt(np.clip(1.0 - sin_t2, 0.0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = ((n_in * cos_i - n_out * cos_t) / (n_in * cos_i + n_out * cos_t)) ** 2
        rp = ((n_in * cos_t - n_out * cos_i) / (n_in * cos_t + n_out * cos_i)) ** 2
    r = 0.5 * (rs + rp)
    return np.where(total, 1.0, np.nan_to_num(r, nan=1.0))


@lru_cache(maxsize=64)
def _fresnel_moments(n_rel: float) -> tuple[float, float]:
    """Momentos angulares de la reflectancia interna (Haskell et al. 1994)."""
    nodes, weights = np.polynomial.legendre.leggauss(400)
    theta = 0.25 * np.pi * (nodes + 1.0)
    w = 0.25 * np.pi * weights
    r = fresnel_reflectance(np.cos(theta), n_rel, 1.0)
    r_phi = float(np.sum(w * 2.0 * np.sin(theta) * np.cos(theta) * r))
    r_j = float(np.sum(w * 3.0 * np.sin(theta) * np.cos(theta) ** 2 * r))
    return r_phi, r_j


def effective_reflection_coefficient(n_rel: float) -> float:
    """Coeficiente de reflexión efectivo R_eff de la frontera tejido-exterior."""
    if n_rel == 1.0:
        return 0.0
    r_phi, r_j = _fresnel_moments(float(n_rel))
    return (r_phi + r_j) / (2.0 - r_phi + r_j)


def boundary_factor_A(n_rel: float) -> float:
    """Factor A = (1 + R_eff)/(1 - R_eff); la frontera extrapolada está en z_b = 2·A·D."""
    r_eff = effective_reflection_coefficient(n_rel)
    return (1.0 + r_eff) / (1.0 - r_eff)


@lru_cache(maxsize=64)
def detection_coefficients(n_rel: float) -> tuple[float, float]:
    """Coeficientes C1 y C2 de R = C1·Phi + C2·J (Kienle y Patterson 1997).

    Integran la transmisión de Fresnel sobre el hemisferio de salida; para n = 1.4 valen
    aproximadamente 0.118 y 0.306.
    """
    nodes, weights = np.polynomial.legendre.leggauss(400)
    theta = 0.25 * np.pi * (nodes + 1.0)
    w = 0.25 * np.pi * weights
    t = 1.0 - fresnel_reflectance(np.cos(theta), float(n_rel), 1.0)
    c1 = float(np.sum(w * 0.5 * t * np.cos(theta) * np.sin(theta)))
    c2 = float(np.sum(w * 1.5 * t * np.cos(theta) ** 2 * np.sin(theta)))
    return c1, c2


# --------------------------------------------------------------------------- semiinfinito
def semi_infinite_fluence_and_flux(rho, mua: float, musp: float, n_rel: float = 1.4):
    """Fluencia Phi(rho, z=0) [1/mm^2] y flujo saliente J(rho) [1/mm^2] en la superficie.

    Fuente isótropa unitaria en z0 = 1/(mua+musp) y su imagen negativa respecto a la frontera
    extrapolada. No incluye el factor de albedo a' de Farrell.
    """
    rho = np.asarray(rho, dtype=float)
    mut = mua + musp
    d_coef = 1.0 / (3.0 * mut)
    mueff = np.sqrt(mua / d_coef)
    z0 = 1.0 / mut
    zb = 2.0 * boundary_factor_A(n_rel) * d_coef
    r1 = np.sqrt(z0**2 + rho**2)
    r2 = np.sqrt((z0 + 2.0 * zb) ** 2 + rho**2)
    phi = (np.exp(-mueff * r1) / r1 - np.exp(-mueff * r2) / r2) / (4.0 * np.pi * d_coef)
    flux = (
        z0 * (mueff + 1.0 / r1) * np.exp(-mueff * r1) / r1**2
        + (z0 + 2.0 * zb) * (mueff + 1.0 / r2) * np.exp(-mueff * r2) / r2**2
    ) / (4.0 * np.pi)
    return phi, flux


def _combine(phi, flux, n_rel: float, model: str, albedo: float):
    if model == "flux":
        return flux
    if model == "farrell":
        return albedo * flux
    if model == "kienle":
        c1, c2 = detection_coefficients(n_rel)
        return c1 * phi + c2 * flux
    raise ValueError(f"modelo de reflectancia desconocido: {model!r}")


def semi_infinite_reflectance(rho, mua: float, musp: float, n_rel: float = 1.4, model: str = "kienle"):
    """Reflectancia difusa R(rho) [1/mm^2] de un medio semiinfinito homogéneo.

    model:
      "flux"    flujo de Fick en la superficie para una fuente unitaria.
      "farrell" flujo multiplicado por el albedo de transporte (Farrell et al. 1992).
      "kienle"  combinación C1·Phi + C2·J (Kienle y Patterson 1997); es la más exacta.
    """
    phi, flux = semi_infinite_fluence_and_flux(rho, mua, musp, n_rel)
    return _combine(phi, flux, n_rel, model, musp / (mua + musp))


def semi_infinite_mean_pathlength(rho: float, mua: float, musp: float, n_rel: float = 1.4,
                                  model: str = "kienle") -> float:
    """Trayectoria media <L> = -d ln R / d mua [mm] por diferencia centrada."""
    h = 1e-4 * mua + 1e-9
    r_plus = semi_infinite_reflectance(rho, mua + h, musp, n_rel, model)
    r_minus = semi_infinite_reflectance(rho, mua - h, musp, n_rel, model)
    return float(-(np.log(r_plus) - np.log(r_minus)) / (2.0 * h))


# --------------------------------------------------------------------------- N capas
def _layered_surface_spectrum(s: np.ndarray, layers: Sequence[LayerOptics], n_rel: float):
    """Fluencia y flujo en z = 0 en el dominio de Hankel para cada frecuencia espacial s."""
    first = layers[0]
    d1_coef = 1.0 / (3.0 * (first.mua + first.musp))
    z0 = 1.0 / (first.mua + first.musp)
    if z0 >= first.thickness_mm:
        raise ValueError(
            "La fuente isótropa equivalente (z0 = %.3f mm) cae fuera de la primera capa "
            "(%.3f mm): la solución de N capas no es aplicable." % (z0, first.thickness_mm)
        )
    zb = 2.0 * boundary_factor_A(n_rel) * d1_coef
    alpha1 = np.sqrt(first.mua / d1_coef + s**2)

    # Admitancia gamma = -D·Phi'/Phi vista desde el fondo de la primera capa.
    last = layers[-1]
    d_last = 1.0 / (3.0 * (last.mua + last.musp))
    gamma = d_last * np.sqrt(last.mua / d_last + s**2)
    if len(layers) == 1:
        gamma = d1_coef * alpha1
    for layer in reversed(layers[1:-1]):
        d_k = 1.0 / (3.0 * (layer.mua + layer.musp))
        a_k = np.sqrt(layer.mua / d_k + s**2)
        t_k = np.tanh(a_k * layer.thickness_mm)
        gamma = d_k * a_k * (gamma + d_k * a_k * t_k) / (d_k * a_k + gamma * t_k)

    if len(layers) == 1 or not np.isfinite(first.thickness_mm):
        # primera capa semiinfinita: beta = 1
        p_s = np.ones_like(s)
        q_s = np.ones_like(s)
    else:
        h = first.thickness_mm - z0
        beta = gamma / (d1_coef * alpha1)
        e2 = np.exp(-2.0 * alpha1 * h)
        p_s = 0.5 * (1.0 + e2) + 0.5 * beta * (1.0 - e2)  # P·exp(-alpha·h)
        q_s = 0.5 * (1.0 - e2) + 0.5 * beta * (1.0 + e2)  # Q·exp(-alpha·h)
    e_src = np.exp(-2.0 * alpha1 * (z0 + zb))
    c_s = 0.5 * (1.0 + e_src)  # cosh escalado
    s_s = 0.5 * (1.0 - e_src)  # sinh escalado
    amp = p_s / (d1_coef * alpha1 * (c_s * p_s + s_s * q_s))
    e_a = np.exp(-alpha1 * z0)
    e_b = np.exp(-alpha1 * (z0 + 2.0 * zb))
    phi0 = amp * 0.5 * (e_a - e_b)
    flux0 = d1_coef * alpha1 * amp * 0.5 * (e_a + e_b)
    return phi0, flux0, z0


def _hankel_nodes(rho: float, z0: float, order: int = 12):
    """Nodos y pesos de Gauss-Legendre entre ceros consecutivos de J0(s·rho)."""
    s_max = 36.0 / z0
    n_zeros = int(np.ceil(s_max * rho / np.pi)) + 2
    edges = np.concatenate(([0.0], special.jn_zeros(0, n_zeros) / rho))
    x, w = np.polynomial.legendre.leggauss(order)
    half = 0.5 * (edges[1:] - edges[:-1])
    mid = 0.5 * (edges[1:] + edges[:-1])
    nodes = (mid[:, None] + half[:, None] * x[None, :]).ravel()
    weights = (half[:, None] * w[None, :]).ravel()
    return nodes, weights


def layered_reflectance(rho, layers: Sequence[LayerOptics], n_out: float = 1.0, model: str = "kienle"):
    """Reflectancia difusa R(rho) [1/mm^2] de un medio de N capas planas.

    La última capa se trata como semiinfinita aunque tenga grosor finito declarado.
    """
    layers = list(layers)
    n_rel = layers[0].n / n_out
    scalar = np.ndim(rho) == 0
    out = []
    albedo = layers[0].musp / (layers[0].mua + layers[0].musp)
    for r in np.atleast_1d(np.asarray(rho, dtype=float)):
        z0 = 1.0 / (layers[0].mua + layers[0].musp)
        s, w = _hankel_nodes(float(r), z0)
        phi0, flux0, _ = _layered_surface_spectrum(s, layers, n_rel)
        kernel = w * s * special.j0(s * r) / (2.0 * np.pi)
        phi = float(np.sum(kernel * phi0))
        flux = float(np.sum(kernel * flux0))
        out.append(_combine(phi, flux, n_rel, model, albedo))
    return out[0] if scalar else np.array(out)


def layered_partial_pathlengths(rho: float, layers: Sequence[LayerOptics], n_out: float = 1.0,
                                model: str = "kienle") -> np.ndarray:
    """Trayectoria parcial media por capa, <L_j> = -d ln R / d mua_j [mm]."""
    layers = list(layers)
    result = np.zeros(len(layers))
    for j, layer in enumerate(layers):
        h = 1e-4 * layer.mua + 1e-9

        def _with(mua: float) -> float:
            mod = list(layers)
            mod[j] = LayerOptics(layer.thickness_mm, mua, layer.musp, layer.n, layer.g)
            return float(layered_reflectance(rho, mod, n_out, model))

        result[j] = -(np.log(_with(layer.mua + h)) - np.log(_with(layer.mua - h))) / (2.0 * h)
    return result
