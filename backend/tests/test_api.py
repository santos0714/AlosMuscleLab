"""API: ejecución de escenarios, propagación de cambios, caché persistente, perfiles y estudios."""
import time

import pytest
from fastapi.testclient import TestClient

from musclesense.api.app import create_app


@pytest.fixture(scope="module")
def ruta_db(tmp_path_factory):
    return tmp_path_factory.mktemp("api") / "prueba.sqlite"


@pytest.fixture(scope="module")
def cliente(ruta_db):
    with TestClient(create_app(ruta_db, static_dir="/no/existe")) as c:
        yield c


def test_salud_parametros_y_catalogo(cliente):
    salud = cliente.get("/api/salud").json()
    assert salud["estado"] == "ok" and "numpy" in salud["versiones"]
    p = cliente.get("/api/parametros").json()
    campos = {f["campo"]: f for f in p["fisiologia"]}
    assert campos["coupling_damage_flow"]["supuesto"] is True
    assert campos["myoglobin_mM"]["supuesto"] is False and campos["myoglobin_mM"]["rango"]
    assert p["protocolo"]["exercise_s"] > 0 and "referencia" in p["perfiles"]
    cat = cliente.get("/api/catalogo").json()
    assert cat["leds"] and cat["bom_recomendada"]


def test_ejecutar_propagar_y_consultar_historial(cliente):
    r = cliente.post("/api/escenarios/ejecutar", json={"name": "referencia", "output_rate_hz": 0.5})
    assert r.status_code == 200
    assert "NaN" not in r.text and "Infinity" not in r.text  # JSON estricto
    j = r.json()
    assert j["recalculadas"][0] == "optics" and "transport" in j["recalculadas"]
    serie = j["series"]
    assert len(serie["t_s"]) == len(serie["fisiologia"]["fuerza"]) == len(serie["estimado_uM"]["d_oxy"])
    assert serie["t_s"][1] - serie["t_s"][0] == pytest.approx(2.0)
    assert set(j["resumen"]["fuerza_en_marcas"]) == {"basal", "rec_0min", "rec_5min", "rec_15min", "rec_30min"}
    assert not j["resumen"]["saturado"]

    r2 = cliente.post("/api/escenarios/ejecutar", json={"sensor": {"tia_rf_ohm": 1e7, "tia_cf_pF": 1.0}})
    assert r2.json()["recalculadas"] == ["electronics", "processing", "features"]
    r3 = cliente.post("/api/escenarios/ejecutar", json={"protocol": {"intensity_pct_mvc": 30}, "save": False})
    assert r3.json()["id"] is None and "transport" not in r3.json()["recalculadas"]

    historial = cliente.get("/api/historial").json()
    assert [h["id"] for h in historial][:2] == [r2.json()["id"], j["id"]]
    detalle = cliente.get(f"/api/historial/{j['id']}").json()
    assert detalle["nombre"] == "referencia" and detalle["escenario"]["tissue"]["profile"] == "referencia"
    assert cliente.delete(f"/api/historial/{r2.json()['id']}").status_code == 204
    assert cliente.get(f"/api/historial/{r2.json()['id']}").status_code == 404


def test_el_transporte_se_reutiliza_desde_sqlite(cliente, ruta_db):
    cliente.post("/api/escenarios/ejecutar", json={"save": False})  # garantiza la entrada en la caché
    assert cliente.get("/api/salud").json()["cache"]["transport"]["entradas"] >= 1
    with TestClient(create_app(ruta_db, static_dir="/no/existe")) as nuevo:  # otra instancia, caché en memoria vacía
        rec = nuevo.post("/api/escenarios/ejecutar", json={"save": False}).json()["recalculadas"]
    assert "optics" in rec and "transport" not in rec


@pytest.mark.parametrize("cuerpo", [
    {"physiology": {"inventado": 1.0}},
    {"protocol": {"contraction": "saltar"}},
    {"protocol": {"recovery_s": 9000}},
    {"tissue": {"profile": "no_existe"}},
    {"sensor": {"sds_mm": 100}},
    {"sensor": {"led_power_mW": [10, 10]}},
    {"settings": {"engine": "magia"}},
    {"campo_extra": 1},
])
def test_peticiones_invalidas_dan_422(cliente, cuerpo):
    assert cliente.post("/api/escenarios/ejecutar", json=cuerpo).status_code == 422


def test_perfiles_guardados(cliente):
    assert cliente.post("/api/perfiles", json={"name": "referencia", "att_mm": 4.0}).status_code == 409
    r = cliente.post("/api/perfiles", json={"name": "atleta", "att_mm": 2.2, "melanosome_epidermis": 0.1})
    assert r.status_code == 201
    nombres = {p["nombre"]: p["tipo"] for p in cliente.get("/api/perfiles").json()}
    assert nombres["atleta"] == "guardado" and nombres["delgado"] == "predefinido"
    j = cliente.post("/api/escenarios/ejecutar", json={"tissue": {"profile": "atleta"}, "save": False}).json()
    assert j["resumen"]["tejido"]["grasa"]["grosor_mm"] == pytest.approx(2.2)
    assert cliente.delete("/api/perfiles/atleta").status_code == 204
    assert cliente.delete("/api/perfiles/atleta").status_code == 404


def test_estudio_en_segundo_plano(cliente):
    assert cliente.post("/api/estudios", json={"n_subjects": 4, "levels": ["no_existe"]}).status_code == 422
    niveles = {n["nombre"] for n in cliente.get("/api/estudios/niveles").json()}
    assert {"ninguno", "dano_flujo_22pct", "combinado"} <= niveles
    r = cliente.post("/api/estudios", json={"n_subjects": 6, "seed": 1, "levels": ["ninguno", "dano_flujo_22pct"]})
    assert r.status_code == 202
    sid = r.json()["id"]
    limite = time.time() + 120
    while time.time() < limite:
        e = cliente.get(f"/api/estudios/{sid}").json()
        if e["estado"] in ("terminado", "error"):
            break
        time.sleep(0.5)
    assert e["estado"] == "terminado", e.get("error")
    res = e["resultado"]
    assert res["sujetos"] == 6 and res["fallos"] == []
    assert {g["nivel"] for g in res["ganancia"]} == {"ninguno", "dano_flujo_22pct"}
    assert len(res["puntos"]) == 6 * 2 * 4
    assert any(d["marca"] == "rec_30min" for d in res["disociacion"])
    assert cliente.get("/api/estudios").json()[0]["id"] == sid
