# MuscleSense Lab

Plataforma científica de simulación óptica (NIRS) para estudiar la recuperación muscular del bíceps braquial después del ejercicio.

**Estado:** Fase 1 (preparación del entorno) terminada. Fase 2 (desarrollo) sin iniciar.
Informe completo: [docs/00_informe_entorno.md](docs/00_informe_entorno.md).

## Preparar el entorno

### Windows

Doble clic en `preparar_windows.bat`, o desde PowerShell en esta carpeta:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\preparar_windows.ps1
```

El script audita el equipo, crea `.venv`, instala `requirements.txt`, añade las extensiones de VS Code que falten y ejecuta las pruebas. El resultado queda en `docs\entorno\registro_windows.txt`.

Opciones: `-SoloAuditar` (no instala nada) y `-SinExtensiones` (no toca VS Code).

### Linux o WSL

```bash
bash scripts/preparar_linux.sh
```

## Comprobar el entorno

```bash
python -m pytest tests/test_entorno.py -v
```

## Estructura actual

| Ruta | Contenido |
|---|---|
| `requirements.txt` | Dependencias de Python con versión fija |
| `scripts/` | Preparación del entorno |
| `tests/` | Pruebas de funcionamiento del entorno |
| `docs/` | Informes y documentación |
| `.mcp.json` | Servidores MCP del proyecto (Playwright, Context7, GitHub) |
