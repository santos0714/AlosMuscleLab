"""Procesado de la señal NIRS: de cuentas a cambios de concentración y rasgos de recuperación.

1. Atenuación respecto al basal: dA = -ln(cuentas / media basal).
2. Beer-Lambert modificada con una trayectoria supuesta L = DPF · distancia emisor-detector.
   El resultado es la suma de hemoglobina y mioglobina, que la NIRS de onda continua no separa.
3. Filtro pasa bajas de fase cero y extracción de rasgos.

Las concentraciones se devuelven en uM de grupo hemo (para comparar con valores publicados por
tetrámero hay que dividir entre 4).
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfiltfilt

from ..optical_physics import mbll

__all__ = ["counts_to_attenuation", "estimate_concentrations", "lowpass", "extract_features"]


def counts_to_attenuation(counts: np.ndarray, t: np.ndarray, baseline_window: tuple) -> np.ndarray:
    """dA (T, n_lambda) respecto a la media de la ventana basal (t0, t1)."""
    sel = (t >= baseline_window[0]) & (t < baseline_window[1])
    referencia = counts[sel].mean(axis=0)
    return -np.log(np.clip(counts, 1.0, None) / referencia)


def lowpass(x: np.ndarray, sample_rate_hz: float, cutoff_hz: float) -> np.ndarray:
    if cutoff_hz <= 0 or cutoff_hz >= 0.5 * sample_rate_hz:
        return x
    sos = butter(4, cutoff_hz, btype="low", fs=sample_rate_hz, output="sos")
    return sosfiltfilt(sos, x, axis=0)


def estimate_concentrations(delta_a: np.ndarray, wavelengths_nm, sds_mm: float, dpf: float,
                            fwhm_nm=None) -> dict:
    """Cambios de [O2Hb+O2Mb] y [HHb+HMb] en uM de hemo, con L = dpf·sds_mm."""
    dc = mbll.solve_concentration_changes(delta_a, dpf * sds_mm, wavelengths_nm, fwhm_nm) * 1e3
    return {"d_oxy": dc[:, 0], "d_deoxy": dc[:, 1], "d_total": dc[:, 0] + dc[:, 1], "d_diff": dc[:, 0] - dc[:, 1]}


def _media(t, x, centro, medio_ancho=5.0):
    sel = (t >= centro - medio_ancho) & (t <= centro + medio_ancho)
    return float(x[sel].mean()) if sel.any() else float("nan")


def extract_features(t: np.ndarray, conc: dict, protocol) -> dict:
    """Rasgos de la señal: caída en el ejercicio, reoxigenación, hiperemia y línea base posterior."""
    te0, te1 = protocol.t_exercise_start, protocol.t_exercise_end
    diff, total = conc["d_diff"], conc["d_total"]
    ejercicio = (t >= te0) & (t < te1)
    rasgos = {
        "caida_diff_uM": float(diff[ejercicio].min()) if ejercicio.any() else float("nan"),
        "pico_deoxy_uM": float(conc["d_deoxy"][ejercicio].max()) if ejercicio.any() else float("nan"),
    }
    fin = _media(t, diff, te1 - 2.0, 2.0)
    post = t >= te1
    # tiempo medio de reoxigenación: recuperar la mitad de la caída presente al final del ejercicio
    objetivo = 0.5 * fin
    cruza = post & (diff >= objetivo) if fin < 0 else np.zeros_like(post)
    rasgos["t_medio_reox_s"] = float(t[np.argmax(cruza)] - te1) if cruza.any() else float("nan")
    ventana = (t >= te1) & (t < te1 + 300.0)
    if ventana.any():
        i = int(np.argmax(total[ventana]))
        rasgos["hiperemia_pico_total_uM"] = float(total[ventana][i])
        rasgos["hiperemia_t_pico_s"] = float(t[ventana][i] - te1)
    for nombre, tm in protocol.marks().items():
        centro = tm if nombre == "basal" else min(tm + 8.0, t[-1] - 5.0)
        for clave in ("d_oxy", "d_deoxy", "d_total", "d_diff"):
            rasgos[f"{nombre}_{clave}_uM"] = _media(t, conc[clave], centro)
    # pruebas de oclusión: pendiente de (HHb - O2Hb)/2, proporcional al consumo de O2
    for k, (a, b) in enumerate(protocol.occlusion_windows()):
        sel = (t >= a + 2.0) & (t <= b - 1.0)
        if sel.sum() > 5:
            pendiente = np.polyfit(t[sel], -0.5 * diff[sel], 1)[0]
            rasgos[f"oclusion_{k}_mvo2_uM_s"] = float(pendiente)
    return rasgos
