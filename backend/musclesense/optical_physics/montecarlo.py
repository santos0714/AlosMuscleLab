"""Monte Carlo de transporte de fotones en capas planas (referencia propia, en NumPy).

Es un Monte Carlo "blanco": los fotones se propagan sin absorción y se guarda, para cada fotón
que sale del tejido, su trayectoria dentro de cada capa. La absorción se aplica después con la
ley de Beer-Lambert a lo largo de la trayectoria,

    w_i = exp(-sum_j mua_j · L_ij),

lo que permite recalcular la señal para cualquier absorción sin repetir la simulación.

El algoritmo de propagación es el de MCML (Wang, Jacques y Zheng 1995): paso libre exponencial,
función de fase de Henyey-Greenstein y reflexión o refracción de Fresnel en cada interfaz.

Unidades: mm y 1/mm. El haz entra en (0, 0, 0) con dirección +z (incidencia normal).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from .diffusion import LayerOptics

__all__ = ["PathLibrary", "run_layered_monte_carlo", "disk_acceptance"]


def disk_acceptance(exit_rho_mm, rho_mm: float, radius_mm: float) -> np.ndarray:
    """Fracción de la circunferencia de radio ``exit_rho`` que cae dentro de un disco de radio
    ``radius_mm`` centrado a ``rho_mm`` de la fuente (simetría azimutal).

    Permite estimar con el Monte Carlo propio lo mismo que mide un detector de disco de MCX.
    """
    r = np.asarray(exit_rho_mm, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        c = (r**2 + rho_mm**2 - radius_mm**2) / (2.0 * r * rho_mm)
    ang = np.arccos(np.clip(c, -1.0, 1.0))
    return np.where(np.abs(r - rho_mm) < radius_mm, ang / np.pi, 0.0)


@dataclass
class PathLibrary:
    """Fotones que salieron del medio, con su trayectoria parcial por capa."""

    ppath_mm: np.ndarray  # (n, n_capas)
    exit_rho_mm: np.ndarray  # (n,) distancia radial del punto de salida
    exit_cos: np.ndarray  # (n,) coseno del ángulo de salida respecto a la normal, ya fuera
    exit_side: np.ndarray  # (n,) 0 = cara superior (reflectancia), 1 = cara inferior
    n_launched: int
    specular_reflectance: float
    mua_floor: np.ndarray  # (n_capas,) absorción mínima para la que la biblioteca es válida
    truncated_fraction: float  # fotones abandonados por atenuación garantizada
    seed: int
    layers: tuple = field(default_factory=tuple)

    @property
    def n_layers(self) -> int:
        return self.ppath_mm.shape[1]

    def _check(self, mua) -> np.ndarray:
        mua = np.asarray(mua, dtype=float)
        if mua.shape != (self.n_layers,):
            raise ValueError(f"se esperaban {self.n_layers} coeficientes de absorción")
        if np.any(mua < self.mua_floor - 1e-12):
            raise ValueError(
                "absorción por debajo del mínimo con el que se generó la biblioteca "
                f"(mua={mua}, mínimo={self.mua_floor}); hay que regenerarla"
            )
        return mua

    def weights(self, mua) -> np.ndarray:
        """Peso de supervivencia de cada fotón guardado para la absorción dada."""
        return np.exp(-self.ppath_mm @ self._check(mua))

    def total_reflectance(self, mua) -> float:
        """Reflectancia difusa total (fracción de la luz incidente)."""
        w = self.weights(mua)
        return float((1.0 - self.specular_reflectance) * w[self.exit_side == 0].sum() / self.n_launched)

    def total_transmittance(self, mua) -> float:
        """Transmitancia total, incluida la no esparcida."""
        w = self.weights(mua)
        return float((1.0 - self.specular_reflectance) * w[self.exit_side == 1].sum() / self.n_launched)

    def _annulus(self, rho: float, half_width: float) -> np.ndarray:
        lo, hi = max(rho - half_width, 0.0), rho + half_width
        return (self.exit_side == 0) & (self.exit_rho_mm >= lo) & (self.exit_rho_mm < hi)

    def reflectance(self, mua, rho: float, half_width: float = 1.0, min_cos: float = 0.0):
        """Reflectancia R(rho) [1/mm^2] en un anillo de radio rho ± half_width.

        Devuelve (R, n_detectados, error_estándar_relativo). min_cos limita el ángulo de
        aceptación del detector (0 = acepta todo el hemisferio).
        """
        sel = self._annulus(rho, half_width)
        if min_cos > 0.0:
            sel &= self.exit_cos >= min_cos
        w = self.weights(mua)[sel]
        lo, hi = max(rho - half_width, 0.0), rho + half_width
        area = np.pi * (hi**2 - lo**2)
        total = w.sum()
        r = (1.0 - self.specular_reflectance) * total / (self.n_launched * area)
        rel_err = float(np.sqrt((w**2).sum()) / total) if total > 0 else np.inf
        return float(r), int(sel.sum()), rel_err

    def mean_partial_pathlengths(self, mua, rho: float, half_width: float = 1.0,
                                 min_cos: float = 0.0) -> np.ndarray:
        """Trayectoria parcial media por capa [mm] de los fotones detectados, ponderada."""
        sel = self._annulus(rho, half_width)
        if min_cos > 0.0:
            sel &= self.exit_cos >= min_cos
        w = self.weights(mua)[sel]
        if w.sum() <= 0:
            return np.full(self.n_layers, np.nan)
        return (w[:, None] * self.ppath_mm[sel]).sum(axis=0) / w.sum()


    def disk_reflectance(self, mua, rho: float, radius: float):
        """R [1/mm^2] promediada sobre un disco de radio ``radius`` centrado a ``rho`` de la fuente.

        Es lo que mide un detector de disco (p. ej. los de MCX); por simetría azimutal cada fotón
        cuenta con la fracción de su circunferencia de salida que cae dentro del disco.
        Devuelve (R, n_fotones_que_contribuyen, error_estándar_relativo).
        """
        sel = self.exit_side == 0
        f = disk_acceptance(self.exit_rho_mm[sel], rho, radius)
        w = self.weights(mua)[sel] * f
        total = w.sum()
        r = (1.0 - self.specular_reflectance) * total / (self.n_launched * np.pi * radius**2)
        rel_err = float(np.sqrt((w**2).sum()) / total) if total > 0 else np.inf
        return float(r), int((f > 0).sum()), rel_err

    def disk_partial_pathlengths(self, mua, rho: float, radius: float) -> np.ndarray:
        """Trayectoria parcial media por capa de los fotones que llegarían a un disco detector."""
        sel = self.exit_side == 0
        w = self.weights(mua)[sel] * disk_acceptance(self.exit_rho_mm[sel], rho, radius)
        if w.sum() <= 0:
            return np.full(self.n_layers, np.nan)
        return (w[:, None] * self.ppath_mm[sel]).sum(axis=0) / w.sum()


def _fresnel(cos_i: np.ndarray, n1: np.ndarray, n2: np.ndarray):
    """Reflectancia de Fresnel no polarizada y coseno del ángulo transmitido."""
    sin_t2 = (n1 / n2) ** 2 * (1.0 - cos_i**2)
    total = sin_t2 >= 1.0
    cos_t = np.sqrt(np.clip(1.0 - sin_t2, 0.0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = ((n1 * cos_i - n2 * cos_t) / (n1 * cos_i + n2 * cos_t)) ** 2
        rp = ((n1 * cos_t - n2 * cos_i) / (n1 * cos_t + n2 * cos_i)) ** 2
    r = np.where(total, 1.0, 0.5 * (rs + rp))
    r = np.where(n1 == n2, 0.0, np.nan_to_num(r, nan=1.0))
    return r, cos_t


def _scatter(ux, uy, uz, g, rng):
    """Nueva dirección tras un esparcimiento de Henyey-Greenstein."""
    k = ux.size
    xi = rng.random(k)
    g_safe = np.where(g == 0.0, 1.0, g)
    cos_t = np.where(
        g == 0.0,
        2.0 * xi - 1.0,
        (1.0 + g_safe**2 - ((1.0 - g_safe**2) / (1.0 - g_safe + 2.0 * g_safe * xi)) ** 2) / (2.0 * g_safe),
    )
    cos_t = np.clip(cos_t, -1.0, 1.0)
    sin_t = np.sqrt(1.0 - cos_t**2)
    phi = 2.0 * np.pi * rng.random(k)
    cp, sp = np.cos(phi), np.sin(phi)
    near = np.abs(uz) > 0.99999
    temp = np.sqrt(np.clip(1.0 - uz**2, 1e-30, None))
    nux = sin_t * (ux * uz * cp - uy * sp) / temp + ux * cos_t
    nuy = sin_t * (uy * uz * cp + ux * sp) / temp + uy * cos_t
    nuz = -sin_t * cp * temp + uz * cos_t
    nux = np.where(near, sin_t * cp, nux)
    nuy = np.where(near, sin_t * sp, nuy)
    nuz = np.where(near, np.sign(uz) * cos_t, nuz)
    norm = np.sqrt(nux**2 + nuy**2 + nuz**2)
    return nux / norm, nuy / norm, nuz / norm


def run_layered_monte_carlo(
    layers: Sequence[LayerOptics],
    n_photons: int,
    *,
    seed: int,
    n_out_top: float = 1.0,
    n_out_bottom: float = 1.0,
    mua_floor: Sequence[float] | None = None,
    weight_threshold: float = 1e-4,
    store_rho_range: tuple[float, float] = (0.0, np.inf),
    use_similarity: bool = False,
    batch_size: int = 200_000,
    max_path_mm: float = 2.0e4,
) -> PathLibrary:
    """Simula n_photons fotones y devuelve la biblioteca de trayectorias de los que salen.

    mua_floor: absorción mínima por capa para la que se usará la biblioteca. Un fotón se
      abandona cuando exp(-sum_j mua_floor_j·L_j) < weight_threshold, porque su contribución
      ya es despreciable para cualquier absorción mayor. Por defecto, la mitad de la absorción
      declarada en cada capa.
    use_similarity: sustituye (mus, g) por (musp, 0). Es unas 1/(1-g) veces más rápido y es
      una buena aproximación lejos de la fuente; no usar para validar contra MCML.
    store_rho_range: solo se guardan las salidas por la cara superior dentro de este intervalo
      radial; las salidas por la cara inferior se guardan siempre.
    """
    layers = list(layers)
    nl = len(layers)
    thickness = np.array([layer.thickness_mm for layer in layers], dtype=float)
    bounds = np.concatenate(([0.0], np.cumsum(thickness)))
    if use_similarity:
        mus = np.array([layer.musp for layer in layers], dtype=float)
        g = np.zeros(nl)
    else:
        mus = np.array([layer.mus for layer in layers], dtype=float)
        g = np.array([layer.g for layer in layers], dtype=float)
    n_idx = np.array([layer.n for layer in layers], dtype=float)
    floor = (
        0.5 * np.array([layer.mua for layer in layers], dtype=float)
        if mua_floor is None
        else np.asarray(mua_floor, dtype=float)
    )
    if floor.shape != (nl,):
        raise ValueError("mua_floor debe tener un valor por capa")
    att_max = -np.log(weight_threshold)
    rho_lo, rho_hi = store_rho_range
    r_spec = float(((n_out_top - n_idx[0]) / (n_out_top + n_idx[0])) ** 2)

    rng = np.random.default_rng(seed)
    out_pp, out_rho, out_cos, out_side = [], [], [], []
    truncated = 0
    remaining = int(n_photons)
    while remaining > 0:
        m = min(batch_size, remaining)
        remaining -= m
        x = np.zeros(m)
        y = np.zeros(m)
        z = np.zeros(m)
        ux = np.zeros(m)
        uy = np.zeros(m)
        uz = np.ones(m)
        lay = np.zeros(m, dtype=np.int64)
        sleft = np.zeros(m)
        att = np.zeros(m)
        total = np.zeros(m)
        pp = np.zeros((m, nl))
        while m > 0:
            need = sleft <= 0.0
            k = int(need.sum())
            if k:
                sleft[need] = -np.log(1.0 - rng.random(k))
            mu = mus[lay]
            with np.errstate(divide="ignore", invalid="ignore"):
                step = np.where(mu > 0.0, sleft / np.where(mu > 0.0, mu, 1.0), np.inf)
                z_lo = bounds[lay]
                z_hi = bounds[lay + 1]
                db = np.where(uz > 0.0, (z_hi - z) / uz, np.where(uz < 0.0, (z_lo - z) / uz, np.inf))
            db = np.maximum(db, 0.0)
            hit = db <= step
            d = np.where(hit, db, step)
            x += ux * d
            y += uy * d
            z += uz * d
            pp[np.arange(m), lay] += d
            att += floor[lay] * d
            total += d
            sleft = np.where(hit, sleft - d * mu, 0.0)
            dead = np.zeros(m, dtype=bool)

            sc = np.flatnonzero(~hit)
            if sc.size:
                ux[sc], uy[sc], uz[sc] = _scatter(ux[sc], uy[sc], uz[sc], g[lay[sc]], rng)

            hb = np.flatnonzero(hit)
            if hb.size:
                down = uz[hb] > 0.0
                z[hb] = np.where(down, z_hi[hb], z_lo[hb])  # sin deriva numérica
                nxt = lay[hb] + np.where(down, 1, -1)
                n1 = n_idx[lay[hb]]
                n2 = np.where(nxt < 0, n_out_top, np.where(nxt >= nl, n_out_bottom, n_idx[np.clip(nxt, 0, nl - 1)]))
                cos_i = np.abs(uz[hb])
                refl_prob, cos_t = _fresnel(cos_i, n1, n2)
                reflect = rng.random(hb.size) < refl_prob
                rf = hb[reflect]
                uz[rf] = -uz[rf]
                tr = ~reflect
                ht = hb[tr]
                if ht.size:
                    nxt_t = nxt[tr]
                    ratio = n1[tr] / n2[tr]
                    cos_tt = cos_t[tr]
                    leaving = (nxt_t < 0) | (nxt_t >= nl)
                    inner = ht[~leaving]
                    if inner.size:
                        ux[inner] *= ratio[~leaving]
                        uy[inner] *= ratio[~leaving]
                        uz[inner] = np.sign(uz[inner]) * cos_tt[~leaving]
                        lay[inner] = nxt_t[~leaving]
                    gone = ht[leaving]
                    if gone.size:
                        side = (nxt_t[leaving] >= nl).astype(np.int8)
                        rho = np.hypot(x[gone], y[gone])
                        keep = (side == 1) | ((rho >= rho_lo) & (rho < rho_hi))
                        if keep.any():
                            out_pp.append(pp[gone[keep]].astype(np.float32))
                            out_rho.append(rho[keep].astype(np.float32))
                            out_cos.append(cos_tt[leaving][keep].astype(np.float32))
                            out_side.append(side[keep])
                        dead[gone] = True

            lost = (~dead) & ((att > att_max) | (total > max_path_mm))
            truncated += int(lost.sum())
            dead |= lost
            if dead.any():
                alive = ~dead
                x, y, z, ux, uy, uz = x[alive], y[alive], z[alive], ux[alive], uy[alive], uz[alive]
                lay, sleft, att, total, pp = lay[alive], sleft[alive], att[alive], total[alive], pp[alive]
                m = int(alive.sum())

    if out_pp:
        ppath = np.concatenate(out_pp)
        exit_rho = np.concatenate(out_rho)
        exit_cos = np.concatenate(out_cos)
        exit_side = np.concatenate(out_side)
    else:
        ppath = np.zeros((0, nl), dtype=np.float32)
        exit_rho = np.zeros(0, dtype=np.float32)
        exit_cos = np.zeros(0, dtype=np.float32)
        exit_side = np.zeros(0, dtype=np.int8)
    return PathLibrary(
        ppath_mm=ppath,
        exit_rho_mm=exit_rho,
        exit_cos=exit_cos,
        exit_side=exit_side,
        n_launched=int(n_photons),
        specular_reflectance=r_spec,
        mua_floor=floor,
        truncated_fraction=truncated / float(n_photons),
        seed=int(seed),
        layers=tuple(layers),
    )
