# MuscleSense Lab

Plataforma científica de simulación óptica (NIRS) para estudiar la recuperación muscular del bíceps braquial después del ejercicio.

**Estado actual y siguientes pasos:** [docs/ESTADO.md](docs/ESTADO.md).

| Documento | Contenido |
|---|---|
| [docs/ESTADO.md](docs/ESTADO.md) | Qué está hecho, qué falta y cómo retomar |
| [docs/01_arquitectura.md](docs/01_arquitectura.md) | Módulos, unidades, flujo de datos |
| [docs/02_analisis_recuperacion.md](docs/02_analisis_recuperacion.md) | ¿La NIRS estima la recuperación de la fuerza? Métodos y resultados |
| [docs/investigacion/](docs/investigacion/) | Dossieres y datos con referencias |
| [docs/00_informe_entorno.md](docs/00_informe_entorno.md) | Preparación del entorno (Fase 1) |
| [docs/especificacion_musclesense_lab.md](docs/especificacion_musclesense_lab.md) | Especificación original |

## Preparar el entorno

Windows: doble clic en `preparar_windows.bat`. Linux o WSL: `bash scripts/preparar_linux.sh`.

## Probar

```bash
python -m pytest tests backend/tests -q
```

## Uso mínimo

```python
from musclesense.pipeline import Pipeline, Scenario
resultado = Pipeline().run(Scenario())
```

Ejecutar con `backend` en `PYTHONPATH` (pytest ya lo hace mediante `pytest.ini`).

## Interfaz

```bash
cd frontend
npm install
npm run build                                   # compila la interfaz en frontend/dist
cd ../backend
uvicorn musclesense.api.app:app                 # interfaz en http://127.0.0.1:8000
```

En desarrollo: `uvicorn musclesense.api.app:app --reload` en `backend/` y `npm run dev` en
`frontend/` (http://localhost:5173, con `/api` reenviado a uvicorn).

Pruebas de la interfaz (Playwright): `npx playwright install chromium` una vez y después
`npm run build && npm run test:e2e` en `frontend/`. Arrancan su propia API con una base temporal.

## API

```bash
cd backend
uvicorn musclesense.api.app:app --reload        # documentación en http://127.0.0.1:8000/docs
```

Rutas principales: `POST /api/escenarios/ejecutar`, `GET /api/historial`, `GET /api/perfiles`,
`GET /api/parametros`, `GET /api/catalogo`, `POST /api/estudios`. La base SQLite queda en
`resultados/musclesense.sqlite` (o en `MUSCLESENSE_DB`).

## Estudios

```bash
python scripts/estudio_recuperacion.py --sujetos 150 --semilla 2026   # cohorte virtual y barrido
python scripts/comparar_motores.py                                    # difusión, Monte Carlo y MCX-CL
```
