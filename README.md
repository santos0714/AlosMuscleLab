# MuscleSense Lab

Plataforma científica de simulación óptica (NIRS) para estudiar la recuperación muscular del bíceps braquial después del ejercicio.

**Estado actual y siguientes pasos:** [docs/ESTADO.md](docs/ESTADO.md).

| Documento | Contenido |
|---|---|
| [docs/ESTADO.md](docs/ESTADO.md) | Qué está hecho, qué falta y cómo retomar |
| [docs/01_arquitectura.md](docs/01_arquitectura.md) | Módulos, unidades, flujo de datos |
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
