"""Pruebas de funcionamiento del entorno (Fase 1).

No prueban la fisica de MuscleSense Lab: comprueban que cada herramienta instalada
arranca y da un resultado correcto conocido. Ejecutar desde la raiz del proyecto:

    python -m pytest tests/test_entorno.py -v
"""
import io
import math
import sqlite3
import sys
from importlib import metadata
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------- versiones
def _requisitos_fijados():
    from packaging.requirements import Requirement

    fijados = []
    for linea in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines():
        linea = linea.split("#", 1)[0].strip()
        if not linea:
            continue
        req = Requirement(linea)
        if req.marker is not None and not req.marker.evaluate():
            continue  # no aplica a esta plataforma
        version = next(iter(req.specifier)).version
        fijados.append((req.name, version))
    return fijados


def test_python_compatible():
    assert (3, 10) <= sys.version_info[:2] <= (3, 13), sys.version


@pytest.mark.parametrize("paquete,version", _requisitos_fijados())
def test_version_instalada_coincide_con_requirements(paquete, version):
    assert metadata.version(paquete) == version


# ---------------------------------------------------------------- nucleo cientifico
def test_numpy_scipy_resultados_conocidos():
    from scipy import integrate, optimize

    valor, _ = integrate.quad(lambda x: math.exp(-x), 0, np.inf)
    assert valor == pytest.approx(1.0, abs=1e-10)

    # Ajuste no lineal de una atenuacion exponencial: debe recuperar mu = 0.25
    x = np.linspace(0, 10, 50)
    (mu,), _ = optimize.curve_fit(lambda x, mu: np.exp(-mu * x), x, np.exp(-0.25 * x), p0=[1.0])
    assert mu == pytest.approx(0.25, rel=1e-6)


def test_pandas_sklearn_regresion():
    import pandas as pd
    from sklearn.linear_model import LinearRegression

    rng = np.random.default_rng(0)
    df = pd.DataFrame({"x1": rng.normal(size=200), "x2": rng.normal(size=200)})
    df["y"] = 3.0 * df["x1"] - 2.0 * df["x2"] + 0.5
    modelo = LinearRegression().fit(df[["x1", "x2"]], df["y"])
    assert modelo.coef_ == pytest.approx([3.0, -2.0], abs=1e-9)
    assert modelo.intercept_ == pytest.approx(0.5, abs=1e-9)


def test_matplotlib_genera_png_sin_pantalla():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([760, 810, 850], [1.0, 0.8, 0.9])
    memoria = io.BytesIO()
    fig.savefig(memoria, format="png")
    plt.close(fig)
    assert memoria.getvalue()[:8] == b"\x89PNG\r\n\x1a\n"


def test_plotly_serializa_figura():
    import json

    import plotly.graph_objects as go

    fig = go.Figure(go.Scatter(x=[0, 1, 2], y=[0.0, 1.0, 4.0], name="prueba"))
    datos = json.loads(fig.to_json())
    assert datos["data"][0]["y"] == [0.0, 1.0, 4.0]


# ---------------------------------------------------------------- backend y almacenamiento
def test_sqlite_lee_y_escribe():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE medicion (lambda_nm INTEGER, od REAL)")
    con.executemany("INSERT INTO medicion VALUES (?, ?)", [(760, 0.31), (810, 0.27), (850, 0.29)])
    (n, media) = con.execute("SELECT COUNT(*), AVG(od) FROM medicion").fetchone()
    con.close()
    assert n == 3 and media == pytest.approx(0.29)
    assert sqlite3.sqlite_version_info >= (3, 35)


def test_fastapi_responde():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/salud")
    def salud():
        return {"estado": "ok"}

    respuesta = TestClient(app).get("/salud")
    assert respuesta.status_code == 200 and respuesta.json() == {"estado": "ok"}


def test_jupyter_ejecuta_un_cuaderno():
    import nbformat
    from nbclient import NotebookClient

    cuaderno = nbformat.v4.new_notebook()
    cuaderno.cells.append(nbformat.v4.new_code_cell("import numpy as np\nprint(int(np.arange(5).sum()))"))
    NotebookClient(cuaderno, timeout=120, kernel_name="python3").execute()
    assert cuaderno.cells[0].outputs[0]["text"].strip() == "10"


# ---------------------------------------------------------------- Monte Carlo eXtreme (OpenCL)
@pytest.fixture(scope="module")
def pmcxcl():
    modulo = pytest.importorskip("pmcxcl")
    try:
        dispositivos = modulo.gpuinfo()
    except RuntimeError as error:
        pytest.fail(f"pmcxcl esta instalado pero no hay runtime OpenCL utilizable: {error}")
    assert dispositivos, "OpenCL no reporta ningun dispositivo"
    print("\nDispositivos OpenCL:", [d["name"] for d in dispositivos])
    return modulo


def test_mcx_beer_lambert_sin_esparcimiento(pmcxcl):
    """Medio absorbente puro (mus = 0): la fraccion absorbida debe ser 1 - exp(-mua * L)."""
    lado, mua = 60, 0.05  # mm, 1/mm
    res = pmcxcl.run(
        nphoton=200_000,
        vol=np.ones([lado, lado, lado], dtype="uint8"),
        tstart=0, tend=5e-9, tstep=5e-9,
        srcpos=[30, 30, 0], srcdir=[0, 0, 1],
        prop=[[0, 0, 1, 1], [mua, 0.0, 1.0, 1.0]],
        isreflect=0, seed=12345, gpuid=1,
    )
    fraccion = res["stat"]["energyabs"] / res["stat"]["energytot"]
    assert fraccion == pytest.approx(1 - math.exp(-mua * lado), rel=1e-2)


def test_mcx_tejido_tres_capas_con_detector(pmcxcl):
    """Losa piel/grasa/musculo con un detector a 30 mm: prueba funcional, no validacion fisica."""
    vol = np.zeros([80, 60, 40], dtype="uint8")
    vol[:, :, 0:2], vol[:, :, 2:6], vol[:, :, 6:] = 1, 2, 3
    prop = np.array([[0, 0, 1, 1], [0.02, 15.0, 0.9, 1.40], [0.005, 10.0, 0.9, 1.44], [0.02, 7.0, 0.9, 1.37]])
    cfg = dict(
        nphoton=50_000, vol=vol, prop=prop,
        tstart=0, tend=5e-9, tstep=5e-9,
        srcpos=[25, 30, 0], srcdir=[0, 0, 1],
        detpos=[[55, 30, 0, 3.0]], issavedet=1, isreflect=1,
        seed=2026, gpuid=1, unitinmm=1.0,
    )
    res = pmcxcl.mcxlab(cfg)  # mcxlab recibe un diccionario, no argumentos sueltos
    estad = res["stat"]
    assert 0 < estad["energyabs"] < estad["energytot"]
    assert np.isfinite(res["flux"]).all() and res["flux"].max() > 0
    trayectos = res["detp"]["ppath"]
    assert trayectos.ndim == 2 and trayectos.shape[1] == 3 and trayectos.shape[0] > 0
    pesos = pmcxcl.detweight(res["detp"], prop)
    assert ((pesos > 0) & (pesos <= 1)).all()
