"""Almacenamiento en SQLite: perfiles, historial de ejecuciones, estudios y caché de transporte.

Se usa ``sqlite3`` de la biblioteca estándar. Cada operación abre su propia conexión, de modo
que el objeto se puede compartir entre hilos (FastAPI atiende las peticiones en un grupo de
hilos y los estudios largos corren en otro).
"""
from __future__ import annotations

import json
import pickle
import sqlite3
import threading
import zlib
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["Database", "TransportStore"]

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS perfiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    datos TEXT NOT NULL,
    creado TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ejecuciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    creado TEXT NOT NULL,
    escenario TEXT NOT NULL,
    huellas TEXT NOT NULL,
    recalculadas TEXT NOT NULL,
    resumen TEXT NOT NULL,
    segundos REAL NOT NULL,
    versiones TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS estudios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creado TEXT NOT NULL,
    estado TEXT NOT NULL,
    progreso REAL NOT NULL DEFAULT 0,
    parametros TEXT NOT NULL,
    resultado TEXT,
    error TEXT
);
CREATE TABLE IF NOT EXISTS cache_etapas (
    etapa TEXT NOT NULL,
    huella TEXT NOT NULL,
    datos BLOB NOT NULL,
    creado TEXT NOT NULL,
    PRIMARY KEY (etapa, huella)
);
"""


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._conexion() as c:
            c.executescript(_ESQUEMA)

    @contextmanager
    def _conexion(self):
        conexion = sqlite3.connect(self.path, timeout=30.0)
        conexion.row_factory = sqlite3.Row
        try:
            with conexion:
                yield conexion
        finally:
            conexion.close()

    # -- perfiles ----------------------------------------------------------------------------
    def save_profile(self, nombre: str, datos: dict) -> int:
        with self._lock, self._conexion() as c:
            cur = c.execute("INSERT INTO perfiles (nombre, datos, creado) VALUES (?, ?, ?) "
                            "ON CONFLICT(nombre) DO UPDATE SET datos = excluded.datos",
                            (nombre, json.dumps(datos), _ahora()))
            fila = c.execute("SELECT id FROM perfiles WHERE nombre = ?", (nombre,)).fetchone()
            return int(fila["id"] if fila else cur.lastrowid)

    def list_profiles(self) -> list:
        with self._conexion() as c:
            filas = c.execute("SELECT id, nombre, datos, creado FROM perfiles ORDER BY nombre").fetchall()
        return [{"id": f["id"], "nombre": f["nombre"], "datos": json.loads(f["datos"]), "creado": f["creado"]}
                for f in filas]

    def delete_profile(self, nombre: str) -> bool:
        with self._lock, self._conexion() as c:
            return c.execute("DELETE FROM perfiles WHERE nombre = ?", (nombre,)).rowcount > 0

    # -- ejecuciones -------------------------------------------------------------------------
    def save_run(self, nombre, escenario: dict, huellas: dict, recalculadas: list, resumen: dict,
                 segundos: float, versiones: dict) -> int:
        with self._lock, self._conexion() as c:
            cur = c.execute(
                "INSERT INTO ejecuciones (nombre, creado, escenario, huellas, recalculadas, resumen, segundos, versiones)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (nombre, _ahora(), json.dumps(escenario), json.dumps(huellas), json.dumps(recalculadas),
                 json.dumps(resumen), segundos, json.dumps(versiones)))
            return int(cur.lastrowid)

    def list_runs(self, limit: int = 50, offset: int = 0) -> list:
        with self._conexion() as c:
            filas = c.execute("SELECT id, nombre, creado, recalculadas, resumen, segundos FROM ejecuciones "
                              "ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        return [{"id": f["id"], "nombre": f["nombre"], "creado": f["creado"],
                 "recalculadas": json.loads(f["recalculadas"]), "resumen": json.loads(f["resumen"]),
                 "segundos": f["segundos"]} for f in filas]

    def get_run(self, run_id: int) -> dict | None:
        with self._conexion() as c:
            f = c.execute("SELECT * FROM ejecuciones WHERE id = ?", (run_id,)).fetchone()
        if f is None:
            return None
        salida = dict(f)
        for clave in ("escenario", "huellas", "recalculadas", "resumen", "versiones"):
            salida[clave] = json.loads(salida[clave])
        return salida

    def delete_run(self, run_id: int) -> bool:
        with self._lock, self._conexion() as c:
            return c.execute("DELETE FROM ejecuciones WHERE id = ?", (run_id,)).rowcount > 0

    # -- estudios ----------------------------------------------------------------------------
    def create_study(self, parametros: dict) -> int:
        with self._lock, self._conexion() as c:
            cur = c.execute("INSERT INTO estudios (creado, estado, parametros) VALUES (?, 'en_cola', ?)",
                            (_ahora(), json.dumps(parametros)))
            return int(cur.lastrowid)

    def update_study(self, study_id: int, **campos) -> None:
        permitidos = {"estado", "progreso", "resultado", "error"}
        if set(campos) - permitidos:
            raise ValueError(f"campos no permitidos: {set(campos) - permitidos}")
        if "resultado" in campos and campos["resultado"] is not None:
            campos["resultado"] = json.dumps(campos["resultado"])
        asignaciones = ", ".join(f"{k} = ?" for k in campos)
        with self._lock, self._conexion() as c:
            c.execute(f"UPDATE estudios SET {asignaciones} WHERE id = ?", (*campos.values(), study_id))

    def get_study(self, study_id: int) -> dict | None:
        with self._conexion() as c:
            f = c.execute("SELECT * FROM estudios WHERE id = ?", (study_id,)).fetchone()
        if f is None:
            return None
        salida = dict(f)
        salida["parametros"] = json.loads(salida["parametros"])
        salida["resultado"] = json.loads(salida["resultado"]) if salida["resultado"] else None
        return salida

    def list_studies(self, limit: int = 50) -> list:
        with self._conexion() as c:
            filas = c.execute("SELECT id, creado, estado, progreso, parametros, error FROM estudios "
                              "ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{**dict(f), "parametros": json.loads(f["parametros"])} for f in filas]

    # -- caché de etapas ---------------------------------------------------------------------
    def cache_get(self, etapa: str, huella: str):
        with self._conexion() as c:
            f = c.execute("SELECT datos FROM cache_etapas WHERE etapa = ? AND huella = ?", (etapa, huella)).fetchone()
        return pickle.loads(zlib.decompress(f["datos"])) if f else None  # datos escritos por esta misma aplicación

    def cache_put(self, etapa: str, huella: str, valor) -> None:
        blob = zlib.compress(pickle.dumps(valor, protocol=pickle.HIGHEST_PROTOCOL))
        with self._lock, self._conexion() as c:
            c.execute("INSERT OR REPLACE INTO cache_etapas (etapa, huella, datos, creado) VALUES (?, ?, ?, ?)",
                      (etapa, huella, blob, _ahora()))

    def cache_stats(self) -> dict:
        with self._conexion() as c:
            filas = c.execute("SELECT etapa, COUNT(*) AS n, SUM(LENGTH(datos)) AS bytes FROM cache_etapas "
                              "GROUP BY etapa").fetchall()
        return {f["etapa"]: {"entradas": f["n"], "bytes": f["bytes"]} for f in filas}


class TransportStore:
    """Adaptador entre ``Pipeline`` y la tabla de caché de la base de datos."""

    def __init__(self, db: Database):
        self.db = db

    def get(self, etapa: str, huella: str):
        return self.db.cache_get(etapa, huella)

    def put(self, etapa: str, huella: str, valor) -> None:
        self.db.cache_put(etapa, huella, valor)
