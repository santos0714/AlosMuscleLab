"""API de MuscleSense Lab (FastAPI).

Arranque en desarrollo, desde ``backend/``:

    uvicorn musclesense.api.app:app --reload

La base de datos se guarda en ``MUSCLESENSE_DB`` (por defecto ``resultados/musclesense.sqlite``
en la raíz del proyecto). Si existe ``frontend/dist`` se sirve como sitio estático en ``/``.
"""
from __future__ import annotations

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from ..optical_physics.spectra import DATA_DIR
from ..pipeline import Pipeline
from ..recovery_analysis import (
    CohortSpec, default_levels, dissociation_table, evaluate, generate_cohort, nirs_gain, simulate_cohort,
)
from ..tissue_simulator.model import PROFILES
from . import service
from .database import Database, TransportStore

__all__ = ["create_app", "app"]

RAIZ = Path(__file__).resolve().parents[3]


# -- esquemas de entrada --------------------------------------------------------------------------
class TissueIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile: str | None = "referencia"
    att_mm: float | None = Field(None, ge=0.5, le=30.0)
    skin_mm: float | None = Field(None, ge=0.5, le=5.0)
    melanosome_epidermis: float | None = Field(None, ge=0.0, le=0.6)


class SensorIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sds_mm: float | None = Field(None, ge=5.0, le=60.0)
    tia_rf_ohm: float | None = Field(None, gt=0.0)
    tia_cf_pF: float | None = Field(None, gt=0.0)
    adc_bits: int | None = Field(None, ge=8, le=32)
    led_power_mW: list[float] | None = None
    ambient_photocurrent_nA: float | None = Field(None, ge=0.0)


class ScenarioIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(None, max_length=120)
    physiology: dict[str, float] = Field(default_factory=dict)
    protocol: dict[str, float | str] = Field(default_factory=dict)
    tissue: TissueIn = Field(default_factory=TissueIn)
    sensor: SensorIn = Field(default_factory=SensorIn)
    settings: dict[str, float | int | bool | str] = Field(default_factory=dict)
    output_rate_hz: float = Field(1.0, gt=0.0, le=10.0)
    save: bool = True


class ProfileIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=60)
    att_mm: float = Field(..., ge=0.5, le=30.0)
    skin_mm: float | None = Field(None, ge=0.5, le=5.0)
    melanosome_epidermis: float = Field(0.04, ge=0.0, le=0.6)


class StudyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    n_subjects: int = Field(40, ge=4, le=300)
    seed: int = 2026
    levels: list[str] | None = None
    optics: bool = False
    models: list[Literal["ridge", "hgb"]] = Field(default_factory=lambda: ["ridge"])


# -- aplicación -----------------------------------------------------------------------------------
def create_app(db_path: str | Path | None = None, static_dir: str | Path | None = None) -> FastAPI:
    ruta_db = db_path or os.environ.get("MUSCLESENSE_DB") or RAIZ / "resultados" / "musclesense.sqlite"
    db = Database(ruta_db)
    tuberia = Pipeline(max_entries=256, store=TransportStore(db))
    candado = threading.Lock()  # la caché de la cadena no es segura entre hilos
    ejecutor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="estudio")

    app = FastAPI(title="MuscleSense Lab", version=service.versions()["musclesense"],
                  description="Simulación de un sensor NIRS de onda continua sobre el bíceps braquial.")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                       allow_methods=["*"], allow_headers=["*"])
    app.state.db, app.state.pipeline, app.state.executor = db, tuberia, ejecutor

    def perfiles_guardados() -> dict:
        return {p["nombre"]: p["datos"] for p in db.list_profiles()}

    @app.get("/api/salud")
    def salud():
        return {"estado": "ok", "versiones": service.versions(), "cache": db.cache_stats()}

    @app.get("/api/parametros")
    def parametros():
        return service.parameter_catalog()

    @app.get("/api/catalogo")
    def catalogo():
        with open(DATA_DIR / "componentes.json", encoding="utf-8") as archivo:
            return json.load(archivo)

    @app.get("/api/perfiles")
    def perfiles():
        predefinidos = [{"nombre": k, "datos": v, "tipo": "predefinido"} for k, v in PROFILES.items()]
        guardados = [{"nombre": p["nombre"], "datos": p["datos"], "tipo": "guardado"} for p in db.list_profiles()]
        return predefinidos + guardados

    @app.post("/api/perfiles", status_code=201)
    def guardar_perfil(perfil: ProfileIn):
        if perfil.name in PROFILES:
            raise HTTPException(409, f"{perfil.name!r} es un perfil predefinido")
        datos = perfil.model_dump(exclude={"name"}, exclude_none=True)
        return {"id": db.save_profile(perfil.name, datos), "nombre": perfil.name, "datos": datos}

    @app.delete("/api/perfiles/{nombre}", status_code=204)
    def borrar_perfil(nombre: str):
        if not db.delete_profile(nombre):
            raise HTTPException(404, "perfil no encontrado")

    @app.post("/api/escenarios/ejecutar")
    def ejecutar(peticion: ScenarioIn):
        cuerpo = peticion.model_dump()
        try:
            escenario = service.build_scenario(cuerpo, perfiles_guardados())
        except service.ScenarioError as error:
            raise HTTPException(422, str(error)) from error
        inicio = time.perf_counter()
        try:
            with candado:
                res = tuberia.run(escenario)
        except ValueError as error:  # p. ej. absorción fuera del intervalo tabulado
            raise HTTPException(422, f"simulación: {error}") from error
        segundos = time.perf_counter() - inicio
        resumen = service.summarize(res, escenario)
        guardar = {k: v for k, v in cuerpo.items() if k not in ("save", "output_rate_hz")}
        run_id = db.save_run(peticion.name, guardar, res.fingerprints, res.recomputed, resumen, segundos,
                             service.versions()) if peticion.save else None
        return {"id": run_id, "recalculadas": res.recomputed, "huellas": res.fingerprints,
                "segundos": round(segundos, 3), "resumen": resumen, "series": service.series(res, peticion.output_rate_hz)}

    @app.get("/api/historial")
    def historial(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
        return db.list_runs(limit, offset)

    @app.get("/api/historial/{run_id}")
    def detalle(run_id: int):
        run = db.get_run(run_id)
        if run is None:
            raise HTTPException(404, "ejecución no encontrada")
        return run

    @app.delete("/api/historial/{run_id}", status_code=204)
    def borrar_ejecucion(run_id: int):
        if not db.delete_run(run_id):
            raise HTTPException(404, "ejecución no encontrada")

    # -- estudios de recuperación (en segundo plano) --------------------------------------------
    def _correr_estudio(study_id: int, p: StudyIn):
        try:
            db.update_study(study_id, estado="en_curso")
            niveles = default_levels()
            if p.levels:
                niveles = [n for n in niveles if n.name in set(p.levels)]
            cohorte = generate_cohort(CohortSpec(n_subjects=p.n_subjects, seed=p.seed))
            datos = simulate_cohort(cohorte, niveles, optics=p.optics,
                                    progress=lambda i, n: db.update_study(study_id, progreso=0.9 * i / n))
            ev = evaluate(datos, models=tuple(p.models))
            puntos = datos[["sujeto", "nivel", "marca", "contraccion", "fuerza", "verdad_reox_frac"]
                           + (["nirs_reox_frac"] if "nirs_reox_frac" in datos else [])]
            resultado = service.clean_json({
                "sujetos": len(cohorte), "descartes": cohorte.rejected, "fallos": datos.attrs.get("fallos", []),
                "niveles": [{"nombre": n.name, "descripcion": n.description, "valores": n.values} for n in niveles],
                "ganancia": nirs_gain(ev, p.models[0]).to_dict(orient="records"),
                "evaluacion": ev.to_dict(orient="records"),
                "disociacion": dissociation_table(datos).to_dict(orient="records"),
                "puntos": puntos.to_dict(orient="records"),
            })
            db.update_study(study_id, estado="terminado", progreso=1.0, resultado=resultado)
        except Exception as error:  # se informa al cliente en lugar de perderse en el hilo
            db.update_study(study_id, estado="error", error=f"{type(error).__name__}: {error}")

    @app.post("/api/estudios", status_code=202)
    def crear_estudio(p: StudyIn):
        validos = {n.name for n in default_levels()}
        if p.levels and set(p.levels) - validos:
            raise HTTPException(422, f"niveles desconocidos: {sorted(set(p.levels) - validos)}")
        study_id = db.create_study(p.model_dump())
        ejecutor.submit(_correr_estudio, study_id, p)
        return {"id": study_id, "estado": "en_cola"}

    @app.get("/api/estudios")
    def estudios():
        return db.list_studies()

    @app.get("/api/estudios/niveles")
    def niveles():
        return [{"nombre": n.name, "descripcion": n.description, "valores": n.values} for n in default_levels()]

    @app.get("/api/estudios/{study_id}")
    def estudio(study_id: int):
        e = db.get_study(study_id)
        if e is None:
            raise HTTPException(404, "estudio no encontrado")
        return e

    sitio = Path(static_dir) if static_dir else RAIZ / "frontend" / "dist"
    if sitio.is_dir():
        app.mount("/", StaticFiles(directory=sitio, html=True), name="sitio")
    return app


def __getattr__(nombre):
    # ``app`` se crea al pedirla (uvicorn musclesense.api.app:app), no al importar el módulo
    if nombre == "app":
        global app
        app = create_app()
        return app
    raise AttributeError(nombre)
