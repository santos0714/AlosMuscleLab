"""Envoltura de MCX-CL (Monte Carlo eXtreme sobre OpenCL) para tejido en capas planas.

MCX trabaja con un volumen de vóxeles y detectores esféricos, no con capas analíticas ni
anillos. Esta envoltura:

1. Construye un volumen de capas con vóxeles cúbicos de ``voxel_mm``; los grosores se
   redondean a un número entero de vóxeles (el grosor efectivo queda en ``layers``).
2. Coloca un anillo de ``n_detectors`` detectores de radio ``detector_radius_mm`` a la
   distancia emisor-detector, centrados en la superficie.
3. Simula "en blanco" (absorción nula) y guarda la trayectoria parcial de cada fotón detectado
   por medio, de modo que la absorción se aplica después: w = exp(-sum_j mua_j·L_j).

El resultado es una ``DetectorPathLibrary``, compatible con ``PathLibrary`` del Monte Carlo
propio pero normalizada por el área de los detectores en lugar de la de un anillo.

Supuestos y límites:

* Ventana temporal ``tend_ns``: los fotones con trayectoria total mayor que c/n·tend se pierden.
  Con 5 ns y n = 1.4 el corte es ~1070 mm; con mua >= 0.005 1/mm su peso sería < e^-5.
* Fuente puntual con incidencia normal; se aplica la reflexión especular de Fresnel al entrar,
  igual que en el Monte Carlo propio (MCX lanza los fotones ya dentro del medio).
* ``use_similarity`` (por defecto) simula con g = 0 y mus = mus', como el motor propio en la
  cadena; es casi 10 veces más rápido y válido lejos de la fuente.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

import numpy as np

from .diffusion import LayerOptics
from .montecarlo import PathLibrary, disk_acceptance
from .opencl import configure_cpu_opencl

__all__ = ["DetectorPathLibrary", "run_layered_mcx", "mcx_available", "disk_acceptance"]

_C_MM_NS = 299.792458  # mm/ns


def mcx_available() -> bool:
    """True si pmcxcl se puede importar y OpenCL reporta al menos un dispositivo."""
    configure_cpu_opencl()
    try:
        import pmcxcl
        return bool(pmcxcl.gpuinfo())
    except (ImportError, RuntimeError, OSError):
        return False


@dataclass
class DetectorPathLibrary(PathLibrary):
    """Biblioteca de trayectorias de fotones capturados por un anillo de detectores de disco."""

    detector_rho_mm: float = 0.0
    detector_radius_mm: float = 0.0
    n_detectors: int = 0
    voxel_mm: float = 0.0
    outside_fraction: float = 0.0  # fotones detectados fuera del disco nominal (descartados; debe ser ~0)

    @property
    def detector_area_mm2(self) -> float:
        return self.n_detectors * np.pi * self.detector_radius_mm**2

    def _check_rho(self, rho: float) -> None:
        if abs(rho - self.detector_rho_mm) > 1e-6:
            raise ValueError(f"los detectores están a {self.detector_rho_mm} mm, no a {rho} mm")

    def reflectance(self, mua, rho: float, half_width: float | None = None, min_cos: float = 0.0):
        """R(rho) [1/mm^2] promediada sobre los discos detectores. ``half_width`` se ignora."""
        self._check_rho(rho)
        sel = self.exit_side == 0
        if min_cos > 0.0:
            sel &= self.exit_cos >= min_cos
        w = self.weights(mua)[sel]
        total = w.sum()
        r = (1.0 - self.specular_reflectance) * total / (self.n_launched * self.detector_area_mm2)
        rel_err = float(np.sqrt((w**2).sum()) / total) if total > 0 else np.inf
        return float(r), int(sel.sum()), rel_err

    def mean_partial_pathlengths(self, mua, rho: float, half_width: float | None = None,
                                 min_cos: float = 0.0) -> np.ndarray:
        self._check_rho(rho)
        sel = self.exit_side == 0
        if min_cos > 0.0:
            sel &= self.exit_cos >= min_cos
        w = self.weights(mua)[sel]
        if w.sum() <= 0:
            return np.full(self.n_layers, np.nan)
        return (w[:, None] * self.ppath_mm[sel]).sum(axis=0) / w.sum()


def run_layered_mcx(layers: Sequence[LayerOptics], n_photons: int, rho_mm: float, seed: int = 1234,
                    voxel_mm: float = 0.25, detector_radius_mm: float = 1.0, n_detectors: int | None = None,
                    lateral_margin_mm: float = 25.0, depth_mm: float | None = None, tend_ns: float = 5.0,
                    use_similarity: bool = True, n_out: float = 1.0, gpuid: int = 1,
                    max_detected: int = 5_000_000) -> DetectorPathLibrary:
    """Simula con MCX-CL un medio de capas (la última semiinfinita) y devuelve la biblioteca."""
    configure_cpu_opencl()
    import pmcxcl

    capas = list(layers)
    if len(capas) < 1:
        raise ValueError("hace falta al menos una capa")
    if any(not np.isfinite(c.thickness_mm) for c in capas[:-1]):
        raise ValueError("solo la última capa puede ser semiinfinita")
    if len({c.n for c in capas}) != 1:
        raise ValueError("esta envoltura supone el mismo índice de refracción en todas las capas")
    if n_detectors is None:
        n_detectors = max(4, min(32, int(np.pi * rho_mm / (1.5 * detector_radius_mm))))
    if 2.0 * np.pi * rho_mm < n_detectors * 2.0 * detector_radius_mm:
        raise ValueError("los detectores se solapan: reduce su número o su radio")

    # --- volumen ---------------------------------------------------------------------------
    gruesos = [int(round(c.thickness_mm / voxel_mm)) for c in capas[:-1]]
    if any(g < 1 for g in gruesos):
        raise ValueError(f"una capa es más delgada que un vóxel de {voxel_mm} mm")
    profundidad = depth_mm or max(40.0, sum(gruesos) * voxel_mm + 30.0)
    nz = int(np.ceil(profundidad / voxel_mm))
    lado = 2.0 * (rho_mm + detector_radius_mm + lateral_margin_mm)
    nxy = int(np.ceil(lado / voxel_mm))
    vol = np.full((nxy, nxy, nz), len(capas), dtype=np.uint8)
    z = 0
    for i, g in enumerate(gruesos):
        vol[:, :, z:z + g] = i + 1
        z += g
    efectivas = tuple(replace(c, thickness_mm=g * voxel_mm) for c, g in zip(capas[:-1], gruesos)) + (capas[-1],)

    # --- propiedades: [mua, mus, g, n] por medio; el medio 0 es el exterior ------------------
    prop = [[0.0, 0.0, 1.0, n_out]]
    for c in capas:
        mus, g = (c.musp, 0.0) if use_similarity else (c.musp / (1.0 - c.g), c.g)
        prop.append([0.0, mus, g, c.n])
    prop = np.array(prop, dtype=np.float32)

    centro = nxy * voxel_mm / 2.0
    ang = 2.0 * np.pi * np.arange(n_detectors) / n_detectors
    detpos = [[(centro + rho_mm * np.cos(a)) / voxel_mm, (centro + rho_mm * np.sin(a)) / voxel_mm, 0.0,
               detector_radius_mm / voxel_mm] for a in ang]
    cfg = dict(nphoton=int(n_photons), vol=vol, prop=prop, tstart=0.0, tend=tend_ns * 1e-9, tstep=tend_ns * 1e-9,
               srcpos=[centro / voxel_mm, centro / voxel_mm, 0.0], srcdir=[0.0, 0.0, 1.0], detpos=detpos,
               issavedet=1, savedetflag="dpx", isreflect=1, seed=int(seed), gpuid=gpuid, unitinmm=voxel_mm,
               maxdetphoton=int(max_detected), isnormalized=1,
               issrcfrom0=1)  # coordenadas desde 0 en fuente, detectores y salidas (por defecto, fuente y
    # detectores empiezan en 1 al estilo de MATLAB y las salidas en 0: un vóxel de desfase)
    res = pmcxcl.mcxlab(cfg)
    detp = res.get("detp")
    if not isinstance(detp, dict) or "ppath" not in detp:
        ppath = np.zeros((0, len(capas)), dtype=np.float64)
        posiciones = np.zeros((0, 3), dtype=np.float64)
        detid = np.zeros(0, dtype=int)
    else:
        ppath = np.asarray(detp["ppath"], dtype=np.float64).reshape(-1, len(capas)) * voxel_mm  # vóxeles -> mm
        posiciones = np.asarray(detp["p"], dtype=np.float64).reshape(-1, 3) * voxel_mm
        detid = np.asarray(detp["detid"]).reshape(-1).astype(int)
    if ppath.shape[0] >= max_detected:
        raise RuntimeError("se llenó el búfer de fotones detectados; sube max_detected")
    # salvaguarda: solo cuentan los fotones que salen dentro del disco nominal (con issrcfrom0=1
    # deben ser todos), para que la normalización por su área sea exacta
    centros = np.array([[d[0] * voxel_mm, d[1] * voxel_mm] for d in detpos])
    dentro = np.hypot(*(posiciones[:, :2] - centros[np.clip(detid - 1, 0, n_detectors - 1)]).T) <= detector_radius_mm
    fuera = float(1.0 - dentro.mean()) if dentro.size else 0.0
    ppath, posiciones = ppath[dentro], posiciones[dentro]
    # comprobación de unidades: ningún fotón puede recorrer más de lo que permite la ventana
    limite = _C_MM_NS / capas[0].n * tend_ns
    if ppath.size and ppath.sum(axis=1).max() > 1.01 * limite:
        raise RuntimeError("trayectorias mayores que la ventana temporal: revisa las unidades de ppath")
    rho_salida = np.hypot(posiciones[:, 0] - centro, posiciones[:, 1] - centro)
    r_spec = float(((n_out - capas[0].n) / (n_out + capas[0].n)) ** 2)
    return DetectorPathLibrary(
        ppath_mm=ppath.astype(np.float32), exit_rho_mm=rho_salida.astype(np.float32),
        exit_cos=np.ones(ppath.shape[0], dtype=np.float32), exit_side=np.zeros(ppath.shape[0], dtype=np.int8),
        n_launched=int(n_photons), specular_reflectance=r_spec, mua_floor=np.zeros(len(capas)),
        truncated_fraction=float("nan"), seed=int(seed), layers=efectivas,
        detector_rho_mm=float(rho_mm), detector_radius_mm=float(detector_radius_mm), n_detectors=int(n_detectors),
        voxel_mm=float(voxel_mm), outside_fraction=fuera,
    )
