"""Estudio de recuperación: cohorte virtual, barrido de acoplamientos y tablas de resultados.

Uso (desde la raíz del proyecto, con el entorno activado):

    python scripts/estudio_recuperacion.py --sujetos 150 --semilla 2026
    python scripts/estudio_recuperacion.py --sujetos 40 --sin-optica      # solo fisiología, rápido

Escribe en resultados/estudio_<semilla>_<n>/ los datos por sujeto y marca (CSV), la evaluación,
las ganancias, la tabla de disociación, las asociaciones por rasgo y un resumen en Markdown.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import sklearn  # noqa: E402

from musclesense.recovery_analysis import (  # noqa: E402
    FEATURE_SETS, CohortSpec, default_levels, dissociation_table, evaluate, feature_associations, generate_cohort, nirs_gain,
    simulate_cohort,
)


def _tabla_md(df: pd.DataFrame, decimales: int = 3) -> str:
    df = df.copy()
    for c in df.select_dtypes("number"):
        df[c] = df[c].map(lambda v: "" if pd.isna(v) else f"{v:.{decimales}f}")
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    filas = ["| " + " | ".join(map(str, r)) + " |" for r in df.to_numpy()]
    return "\n".join([cab, sep, *filas])


def _cota_fenotipo(datos: pd.DataFrame, optica: bool) -> pd.DataFrame:
    """R² (ridge) de conjuntos que acotan lo que la NIRS puede sacar del fenotipo oxidativo.

    ``dosis_fenotipo`` usa el fenotipo latente verdadero: es lo máximo que daría una lectura
    perfecta del fenotipo. ``dosis_grasa`` y ``dosis_grasa_nirs`` añaden el grosor de grasa
    (medible con un plicómetro), que escala la amplitud de los rasgos del sensor.
    """
    dosis = FEATURE_SETS["dosis"]
    conjuntos = {"dosis": dosis, "dosis_fenotipo": dosis + ["fenotipo"], "dosis_oraculo": FEATURE_SETS["dosis_oraculo"]}
    if optica:
        conjuntos.update({"dosis_nirs": FEATURE_SETS["dosis_nirs"], "dosis_grasa": dosis + ["tejido_att_mm"],
                          "dosis_grasa_nirs": dosis + ["tejido_att_mm"] + FEATURE_SETS["nirs"]})
    ev = evaluate(datos, feature_sets=conjuntos, models=("ridge",))
    tabla = ev.pivot_table(index=["nivel", "alcance"], columns="conjunto", values="r2", sort=False)
    tabla = tabla[[c for c in conjuntos if c in tabla]].add_prefix("r2_")
    tabla["ganancia_fenotipo"] = tabla["r2_dosis_fenotipo"] - tabla["r2_dosis"]
    tabla["ganancia_oraculo"] = tabla["r2_dosis_oraculo"] - tabla["r2_dosis"]
    if optica:
        tabla["ganancia_nirs"] = tabla["r2_dosis_nirs"] - tabla["r2_dosis"]
        tabla["ganancia_nirs_con_grasa"] = tabla["r2_dosis_grasa_nirs"] - tabla["r2_dosis_grasa"]
    return tabla.reset_index()


def main(argv=None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sujetos", type=int, default=150)
    ap.add_argument("--semilla", type=int, default=2026)
    ap.add_argument("--sin-optica", action="store_true", help="solo fisiología (sin rasgos NIRS estimados)")
    ap.add_argument("--niveles", nargs="*", help="nombres de niveles a simular (por defecto, todos)")
    ap.add_argument("--correlacion", type=float, default=None,
                    help="correlación entre parámetros ligados al fenotipo oxidativo (cópula); "
                         "sin indicar, muestreo independiente original")
    ap.add_argument("--salida", type=Path, default=RAIZ / "resultados")
    args = ap.parse_args(argv)

    inicio = time.time()
    cohorte = generate_cohort(CohortSpec(n_subjects=args.sujetos, seed=args.semilla,
                                         phenotype_correlation=args.correlacion))
    niveles = default_levels()
    if args.niveles:
        niveles = [n for n in niveles if n.name in set(args.niveles)]
    print(f"{len(cohorte)} sujetos ({cohorte.rejected} descartes), {len(niveles)} niveles", flush=True)

    def progreso(i, n):
        if i % max(n // 10, 1) == 0 or i == n:
            print(f"  {i}/{n} sujetos  ({time.time() - inicio:.0f} s)", flush=True)

    datos = simulate_cohort(cohorte, niveles, optics=not args.sin_optica, progress=progreso)
    sufijo = ("_sin_optica" if args.sin_optica else "") + ("" if args.correlacion is None else f"_r{args.correlacion:g}")
    carpeta = args.salida / f"estudio_{args.semilla}_{args.sujetos}{sufijo}"
    carpeta.mkdir(parents=True, exist_ok=True)
    datos.to_csv(carpeta / "datos.csv", index=False)
    print(f"simulación guardada ({time.time() - inicio:.0f} s); evaluando modelos", flush=True)
    evaluacion = evaluate(datos)
    ganancia_ridge, ganancia_hgb = nirs_gain(evaluacion, "ridge"), nirs_gain(evaluacion, "hgb")
    prefijo = "verdad" if args.sin_optica else "nirs"
    disociacion = dissociation_table(datos, prefix="verdad")
    asociaciones = feature_associations(datos)

    evaluacion.to_csv(carpeta / "evaluacion.csv", index=False)
    cota = None
    if args.correlacion is not None:
        cota = _cota_fenotipo(datos, optica=not args.sin_optica)
        cota.to_csv(carpeta / "cota_fenotipo.csv", index=False)
    ganancia_ridge.to_csv(carpeta / "ganancia_ridge.csv", index=False)
    ganancia_hgb.to_csv(carpeta / "ganancia_hgb.csv", index=False)
    disociacion.to_csv(carpeta / "disociacion.csv", index=False)
    asociaciones.to_csv(carpeta / "asociaciones.csv", index=False)
    meta = {
        "sujetos": len(cohorte), "descartes": cohorte.rejected, "semilla": args.semilla,
        "correlacion_fenotipo": args.correlacion, "optica": not args.sin_optica,
        "niveles": {n.name: {"valores": n.values, "descripcion": n.description} for n in niveles},
        "fallos": datos.attrs.get("fallos", []), "segundos": round(time.time() - inicio, 1),
        "versiones": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
                      "scikit-learn": sklearn.__version__},
    }
    (carpeta / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    cols = ["nivel", "alcance", "r2_dosis", f"r2_dosis_{'oraculo' if args.sin_optica else 'nirs'}",
            "r2_dosis_oraculo", "ganancia_nirs", "ganancia_oraculo", "perdida_instrumento"]
    cols = list(dict.fromkeys(cols))  # sin óptica, la columna del oráculo aparecería dos veces
    resumen = [
        f"# Estudio de recuperación — {len(cohorte)} sujetos, semilla {args.semilla}",
        "",
        f"Descartes por incoherencia fisiológica: {cohorte.rejected}. Fallos de simulación: {len(meta['fallos'])}. "
        f"Tiempo: {meta['segundos']} s. Rasgos del sensor: {prefijo}.",
        "",
        "## Niveles de acoplamiento",
        "",
        _tabla_md(pd.DataFrame([{"nivel": n.name, "descripcion": n.description} for n in niveles])),
        "",
        "## R² con validación cruzada (ridge, un modelo por marca)",
        "",
        _tabla_md(ganancia_ridge[[c for c in cols if c in ganancia_ridge]]),
        "",
        "## R² con validación cruzada (árboles potenciados)",
        "",
        _tabla_md(ganancia_hgb[[c for c in cols if c in ganancia_hgb]]),
        "",
        "## Reoxigenación frente a recuperación de la fuerza (cambios reales en el músculo)",
        "",
        _tabla_md(disociacion),
        "",
    ]
    if cota is not None:
        resumen += [f"## Cota del fenotipo oxidativo (correlación {args.correlacion:g}, ridge)", "",
                    _tabla_md(cota[[c for c in cota if c == "nivel" or c == "alcance" or c.startswith("ganancia")]]), ""]
    (carpeta / "resumen.md").write_text("\n".join(resumen), encoding="utf-8")
    print(f"Resultados en {carpeta}")
    return carpeta


if __name__ == "__main__":
    main()
