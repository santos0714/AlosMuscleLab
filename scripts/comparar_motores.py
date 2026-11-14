"""Compara los tres motores de transporte en el tejido de referencia, por grosor de grasa.

Para cada grosor de grasa y longitud de onda calcula, a la distancia emisor-detector del
sensor, la reflectancia y la fracción de trayectoria en el músculo con:

* difusión de N capas (motor por defecto de la interfaz),
* Monte Carlo propio (NumPy, CPU),
* MCX-CL (OpenCL; en Windows usa la GPU), si está disponible.

Los grosores se redondean al vóxel de MCX para que los tres motores vean la misma geometría.
Uso (desde la raíz del proyecto):

    python scripts/comparar_motores.py                       # 1e6 fotones por caso
    python scripts/comparar_motores.py --fotones 5000000 --grasa 1.5 3 5 9

En la CPU de la nube MCX-CL va a ~5 fotones/ms; con la Radeon 780M debería ir cientos de veces
más rápido. Escribe resultados/comparacion_motores.csv y un resumen en Markdown.
"""
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import replace
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from musclesense.optical_physics.diffusion import layered_partial_pathlengths, layered_reflectance  # noqa: E402
from musclesense.optical_physics.mcx_engine import mcx_available, run_layered_mcx  # noqa: E402
from musclesense.optical_physics.montecarlo import run_layered_monte_carlo  # noqa: E402
from musclesense.sensor_designer.device import SensorDesign  # noqa: E402
from musclesense.tissue_simulator.model import TissueModel  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grasa", type=float, nargs="+", default=[1.5, 3.0, 5.0, 9.0])
    ap.add_argument("--fotones", type=int, default=1_000_000)
    ap.add_argument("--radio-detector", type=float, default=2.0)
    ap.add_argument("--voxel", type=float, default=0.25)
    ap.add_argument("--sin-mcx", action="store_true")
    args = ap.parse_args(argv)

    sensor = SensorDesign()
    rho = sensor.sds_mm
    usar_mcx = not args.sin_mcx and mcx_available()
    filas = []
    for att in args.grasa:
        att_v = round(att / args.voxel) * args.voxel
        tejido = TissueModel.default(att_mm=att_v)
        tejido = replace(tejido, skin=replace(tejido.skin, thickness_mm=round(tejido.skin.thickness_mm / args.voxel) * args.voxel))
        for lam in sensor.wavelengths:
            capas = tejido.optics(lam)
            mua = [c.mua for c in capas]
            blancas = [replace(c, mua=0.0) for c in capas]
            fila = {"grasa_mm": att_v, "lambda_nm": lam}
            r = layered_reflectance(rho, capas)
            l = layered_partial_pathlengths(rho, capas)
            fila.update(R_difusion=r, fmus_difusion=l[2] / l.sum())
            t = time.time()
            mc = run_layered_monte_carlo(blancas, args.fotones, seed=7, mua_floor=[0.9 * m for m in mua],
                                         use_similarity=True,
                                         store_rho_range=(rho - args.radio_detector, rho + args.radio_detector))
            r_mc, n_mc, e_mc = mc.disk_reflectance(mua, rho, args.radio_detector)
            l_mc = mc.disk_partial_pathlengths(mua, rho, args.radio_detector)
            fila.update(R_mc=r_mc, err_mc=e_mc, n_mc=n_mc, fmus_mc=l_mc[2] / l_mc.sum(), s_mc=time.time() - t)
            if usar_mcx:
                t = time.time()
                mx = run_layered_mcx(blancas, args.fotones, rho, seed=8, voxel_mm=args.voxel,
                                     detector_radius_mm=args.radio_detector)
                r_x, n_x, e_x = mx.reflectance(mua, rho)
                l_x = mx.mean_partial_pathlengths(mua, rho)
                fila.update(R_mcx=r_x, err_mcx=e_x, n_mcx=n_x, fmus_mcx=l_x[2] / l_x.sum(), s_mcx=time.time() - t)
            filas.append(fila)
            print({k: (round(v, 5) if isinstance(v, float) else v) for k, v in fila.items()}, flush=True)

    df = pd.DataFrame(filas)
    df["dif_vs_mc"] = df["R_difusion"] / df["R_mc"] - 1.0
    if "R_mcx" in df:
        df["mcx_vs_mc"] = df["R_mcx"] / df["R_mc"] - 1.0
    salida = RAIZ / "resultados"
    salida.mkdir(exist_ok=True)
    df.to_csv(salida / "comparacion_motores.csv", index=False)
    print(df.to_string())
    return df


if __name__ == "__main__":
    main()
