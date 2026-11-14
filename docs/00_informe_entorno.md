# MuscleSense Lab — Informe de preparación del entorno (Fase 1)

Fecha: 14 de noviembre de 2026
Carpeta del proyecto: `C:\Users\HP\Documents\Simulador-Sensor-Optico-Biomedico`
Estado: **Fase 1 cerrada** el 14 de noviembre de 2026 a las 03:36. Los tres entornos están verificados y las autorizaciones resueltas. La Fase 2 comenzó a continuación.

## 1. Resumen

- El entorno de Python (bibliotecas científicas, FastAPI, JupyterLab, Pytest y Monte Carlo eXtreme) está instalado y **verificado en dos entornos Linux independientes**: 26 de 26 pruebas pasan en ambos.
- En Windows el usuario ejecutó `preparar_windows.bat`: se creó `.venv`, se instalaron las bibliotecas y las extensiones de VS Code, y pasan **25 de 25 pruebas** (la número 26 solo aplica en Linux).
- Monte Carlo eXtreme funciona mediante su edición OpenCL (`pmcxcl`) y en Windows usa la GPU AMD Radeon 780M. La edición CUDA no sirve en este equipo porque la GPU no es NVIDIA.
- Playwright funciona en la nube. GitHub está vinculado y los conectores Context7 y PubMed están activos. Zotero no está disponible; PubMed lo sustituye.

## 2. Los tres entornos del proyecto

| | Entorno | Para qué sirve | Qué puede hacer Claude |
|---|---|---|---|
| A | **Windows del usuario** (Windows 11 Pro 10.0.26200, AMD Ryzen 7 PRO 7840HS de 8 núcleos y 16 hilos, 15.3 GB de RAM, Radeon 780M) | Donde vive el proyecto y donde el usuario ejecutará la aplicación | Leer y escribir archivos en Documentos. No puede ejecutar comandos ni escribir en terminales |
| B | **VM Linux local** (Ubuntu 22.04, 2 núcleos, 3.8 GB, sin GPU), con la carpeta del proyecto montada | Desarrollo diario: Python, Node, Git, pruebas | Todo, sin permisos de administrador (no hay `apt`) |
| C | **Contenedor en la nube** (Ubuntu 24.04, 2 núcleos, 7.8 GB, sin GPU) | Pruebas de extremo a extremo con navegador; segunda verificación | Todo; red limitada a registros de paquetes |

B y C se reinician en cada sesión. `scripts/preparar_linux.sh` los reconstruye en 2 a 3 minutos.

## 3. Auditoría de herramientas

| Herramienta | A. Windows | B. VM local | C. Nube |
|---|---|---|---|
| Python | 3.12.10 | 3.10.12 | 3.13.18 |
| pip | 26.3 (en `.venv`) | 26.3 (en el venv) | 26.3 (en el venv) |
| Node.js | 24.18.1 | 22.23.4 | 22.23.4 |
| npm | 11.16.0 | 10.9.9 | 10.9.9 |
| Git | 2.55.0.windows.5 | 2.34.1 | 2.43.0 |
| VS Code | 1.145.0 | no aplica | no aplica |
| GPU / OpenCL | Radeon 780M con OpenCL de AMD (controlador 32.0.22050.4002), verificado | CPU con PoCL 3.0 | CPU con PoCL 3.0 |
| SQLite | incluido en Python | 3.37.2 (incluido en Python) | 3.53.1 (incluido en Python) |

Extensiones de VS Code que ya estaban: Prettier 12.4.0, LaTeX Workshop 10.20.0, Containers 2.5.3, Live Server 5.7.10. Instaladas por el script: Python 2026.10.0 (con Pylance 2026.4.1 y debugpy 2026.6.0), Jupyter 2025.9.1, ESLint 3.0.34 y Playwright 1.1.19.
Otros programas vistos en Windows: Docker Desktop, WSL, MATLAB, MiKTeX. No se encontró Zotero ni controladores NVIDIA.

Los datos de Windows proceden de `docs/entorno/registro_windows.txt`, generado por el script el 14 de noviembre de 2026 a las 03:33.

## 4. Herramientas instaladas y versiones

Instaladas en los tres entornos dentro de un entorno virtual (`.venv` en Windows, `~/.venvs/musclesense` en B y C), con las mismas versiones fijadas en `requirements.txt`:

| Paquete | Versión | Uso |
|---|---|---|
| NumPy | 2.2.6 | Cálculo numérico |
| SciPy | 1.15.3 | Integración, ajuste, señales |
| Pandas | 2.3.3 | Datos tabulares |
| scikit-learn | 1.7.2 | Análisis de recuperación |
| Matplotlib | 3.10.9 | Figuras para documentación |
| Plotly | 7.1.0 | Gráficas interactivas |
| FastAPI | 0.162.5 | Backend |
| Uvicorn | 0.54.0 | Servidor del backend |
| httpx2 | 2.14.0 | Cliente de pruebas del backend |
| JupyterLab | 4.6.6 | Cuadernos |
| ipykernel / nbconvert | 7.3.0 / 7.17.2 | Ejecución de cuadernos |
| Pytest | 9.2.0 | Pruebas |
| pmcxcl | 0.8.1 | MCX sobre OpenCL (simulador) |
| pmcx | 0.8.1 | Utilidades de MCX en Python puro |
| pocl-binary-distribution | 3.0 | OpenCL de CPU, solo en Linux |

Las versiones no son las más recientes a propósito: es el conjunto más nuevo que funciona a la vez en Python 3.10, 3.12 y 3.13. Se comprobó con el resolvedor de pip que las quince dependencias directas tienen paquete binario para Windows con Python 3.12.

Ya presentes en la nube (no instaladas por Claude): Playwright 1.63.0, Chromium 153.0.8010.12 y `@playwright/mcp` 0.0.68.

Versiones disponibles hoy en npm para el frontend (se instalarán en la Fase 2): React 19.3.1, TypeScript 7.0.2, Vite 8.3.8, plotly.js 4.3.0, react-plotly.js 4.1.0, @playwright/test 1.65.1. Vite 8 exige Node 20.19 o superior, o 22.12 o superior; en B y C hay 22.23.4.

### Archivos creados en el proyecto

| Archivo | Contenido |
|---|---|
| `requirements.txt` | Dependencias de Python con versión fija |
| `preparar_windows.bat` | Doble clic para preparar Windows |
| `scripts/preparar_windows.ps1` | Audita, crea `.venv`, instala, añade extensiones de VS Code y ejecuta las pruebas |
| `scripts/preparar_linux.sh` | Lo mismo para los entornos Linux |
| `tests/conftest.py`, `tests/test_entorno.py` | 26 pruebas de funcionamiento del entorno |
| `.mcp.json` | Servidores MCP del proyecto: Playwright, Context7 y GitHub, sin credenciales |
| `.vscode/extensions.json` | Extensiones recomendadas |
| `.gitignore`, `.gitattributes` | Configuración de Git |

Además se inicializó un repositorio Git local (rama `main`). El primer commit (`7a53106`) contiene los archivos de la Fase 1.

## 5. Monte Carlo eXtreme (MCX)

| Edición | Requisito | Compatible aquí | Decisión |
|---|---|---|---|
| MCX (CUDA), paquete `pmcx` | GPU NVIDIA con CUDA | No: la GPU es AMD Radeon 780M | Se instala solo por sus utilidades en Python |
| MCX-CL (OpenCL), paquete `pmcxcl` | Cualquier CPU o GPU con OpenCL | Sí | **Motor elegido** |

- En Linux sin GPU se usa PoCL (OpenCL de CPU) instalado por pip, porque no hay permisos para `apt`. El cargador OpenCL no lo localiza solo; `tests/conftest.py` lo configura automáticamente. En la Fase 2 esa lógica pasará al backend.
- En Windows, MCX-CL detecta la GPU `AMD Radeon(TM) Graphics` en la plataforma AMD Accelerated Parallel Processing, y las dos simulaciones de prueba pasan en ella.
- Rendimiento medido en la VM (2 núcleos de CPU): unos 9 fotones por milisegundo en un tejido de tres capas. Un millón de fotones tarda cerca de 2 minutos y cien millones cerca de 3 horas. Con separación emisor-detector de 30 mm solo se detectaron 18 de cada 100 000 fotones. Las simulaciones grandes tendrán que correr en la GPU de Windows o apoyarse en tablas precalculadas.
- Licencia: MCX es GPL v3 o posterior. Si MuscleSense Lab se distribuye junto con MCX, conviene revisar las obligaciones de esa licencia.

### Observación para la validación de la Fase 2

En un medio sin esparcimiento (μs = 0) la fracción absorbida debe ser exactamente 1 − exp(−μa·L):

| μa (1/mm) | L (mm) | MCX-CL | Exacta | Diferencia relativa |
|---|---|---|---|---|
| 0.5 | 60 | 1.000000 | 1.000000 | 0 % |
| 0.05 | 60 | 0.950198 | 0.950213 | −0.002 % |
| 0.005 | 60 | 0.258512 | 0.259182 | −0.26 % |
| 0.005 | 100 | 0.393737 | 0.393469 | +0.07 % |

La coincidencia es buena, pero con absorción baja aparece una desviación de hasta 0.26 % que además no cambia al mover la fuente dentro del primer vóxel. La causa no está identificada. μs = 0 es un caso límite sin interés fisiológico, pero el agente de validación debe explicarlo y contrastar MCX contra teoría de difusión y referencias publicadas antes de usarlo para resultados cuantitativos.

## 6. Integraciones

| Integración | Estado | Detalle |
|---|---|---|
| Claude Code y sus herramientas | Activo | Archivos, terminal en B y C, subagentes, navegador integrado, búsqueda web, artefactos |
| Playwright | Funciona en la nube | Probado contra una página servida por FastAPI. En la VM local no hay navegador ni acceso a su descarga |
| Playwright MCP | Configurado, sin probar | En `.mcp.json`, para VS Code o Claude Code en Windows. Requiere Node 18 o superior |
| Context7 | Conectado | Conector activo y probado con una consulta. También está en `.mcp.json` |
| GitHub | Vinculado | Cuenta `santos0714` vinculada a Claude. Aún no existe un repositorio remoto del proyecto. En `.mcp.json` queda el servidor remoto oficial sin token |
| Zotero MCP | No incorporado | No está en el directorio de conectores y Zotero no está instalado en el equipo. Alternativa en uso: conector PubMed (activo y probado) y referencias verificadas por DOI o PMID |
| JupyterLab | Instalado | Un cuaderno se ejecuta correctamente con el kernel del entorno virtual |

Nota sobre GitHub: según la documentación de GitHub, el inicio de sesión OAuth con su servidor MCP remoto funciona en VS Code 1.101 o superior; Claude Code necesita un token personal. Ese token no debe escribirse en `.mcp.json`.

## 7. Pruebas de funcionamiento

| Prueba | B. VM local (Python 3.10) | C. Nube (Python 3.13) | A. Windows |
|---|---|---|---|
| Versiones instaladas = `requirements.txt` (16 comprobaciones) | Pasa | Pasa | Pasa (15; PoCL no aplica) |
| NumPy y SciPy: integral y ajuste exponencial conocidos | Pasa | Pasa | Pasa |
| Pandas y scikit-learn: regresión recupera los coeficientes | Pasa | Pasa | Pasa |
| Matplotlib genera un PNG sin pantalla | Pasa | Pasa | Pasa |
| Plotly serializa una figura | Pasa | Pasa | Pasa |
| SQLite lee y escribe | Pasa | Pasa | Pasa |
| FastAPI responde a una petición | Pasa | Pasa | Pasa |
| JupyterLab ejecuta un cuaderno | Pasa | Pasa | Pasa |
| MCX-CL: Beer-Lambert con μs = 0, tolerancia 1 % | Pasa | Pasa | Pasa |
| MCX-CL: tejido de tres capas con detector a 30 mm | Pasa | Pasa | Pasa |
| **Total `pytest tests/test_entorno.py`** | **26 de 26** | **26 de 26** | **25 de 25** |
| Playwright + Chromium contra FastAPI | Sin navegador | Pasa | Sin probar (aún no hay interfaz) |
| Git: `init`, `add` y `status` en la carpeta del proyecto | Pasa | no aplica | Git 2.55 instalado; el commit se hizo desde la VM |
| `preparar_linux.sh` de principio a fin | Pasa | no aplica | no aplica |
| `preparar_windows.ps1` | Sintaxis correcta y simulación completa con PowerShell 7.7 en Linux | no aplica | Ejecutado por el usuario: terminó sin errores |

## 8. Dependencias pendientes

1. **Repositorio remoto en GitHub**: la cuenta está vinculada, pero falta decidir nombre y visibilidad del repositorio.
2. **Frontend** (React, TypeScript, Vite, Plotly, @playwright/test): se instala al crear el frontend en la Fase 2.
3. **Navegadores de Playwright en Windows**: solo cuando existan pruebas de interfaz.

## 9. Problemas encontrados

| Problema | Resolución |
|---|---|
| Claude no puede teclear en terminales de Windows | Script de un doble clic que deja un registro legible por Claude |
| La VM local no tiene permisos de administrador | PoCL por pip y configuración automática del cargador OpenCL |
| La VM trae Python 3.10 | Versiones fijadas compatibles con 3.10 a 3.13 |
| El cliente de pruebas de FastAPI avisa que `httpx` está obsoleto | Se usa `httpx2`; la versión 2.16 exige Python 3.11, por eso se fija 2.14.0 |
| `pmcxcl` solo ofrece `run` y `gpuinfo` | Se añade `pmcx` por sus utilidades en Python puro |
| MCX en CPU es lento | Ver sección 5; se medirá la GPU en Windows |
| Desviación de 0.26 % en Beer-Lambert con μs = 0 | Sin resolver; anotada para la validación |
| `mcx.space`, la descarga de navegadores de Playwright y el Marketplace de VS Code no son accesibles desde B ni C | Documentación consultada por búsqueda web y PyPI; esas descargas ocurren en Windows |
| Los entornos B y C no persisten entre sesiones | `scripts/preparar_linux.sh` |
| `.mcp.json` no se pudo probar | Formato tomado de la documentación de VS Code y Claude Code; se validará en Windows |

Permisos concedidos en esta sesión: acceso a `Documentos` y permiso de borrado en `Documentos`. Claude solo borra dentro de la carpeta del proyecto.

## 10. Autorizaciones

| Autorización | Estado |
|---|---|
| Ejecutar `preparar_windows.bat` | Hecho por el usuario (03:33) |
| Vincular GitHub | Hecho: cuenta `santos0714` |
| Identidad de los commits | Eduardo Santos, correo institucional de CICESE |
| Conectores Context7 y PubMed | Activos |
| Acceso y permiso de borrado en Documentos | Concedidos; Claude solo borra dentro de la carpeta del proyecto |

## 11. Qué puede avanzar sin lo pendiente

| Paso de la metodología | ¿Bloqueado? |
|---|---|
| 1. Investigación científica | No. PubMed la haría más fiable |
| 2. Arquitectura | No |
| 3. Motor físico | No |
| 4. Validación matemática | No |
| 5. Simulación Monte Carlo | Parcial: en CPU con pocos fotones. Las corridas grandes necesitan la GPU de Windows |
| 6. Instrumentación virtual | No |
| 7. Interfaz | No |
| 8. Integración | No |
| 9. Pruebas automatizadas | No: Pytest en B, Playwright en C |
| 10. Documentación | No |

Sin GitHub solo se pierde el respaldo remoto. Sin el paso de Windows, el usuario no puede ejecutar la aplicación en su equipo, pero el desarrollo continúa.

## Fuentes

- [pmcx en PyPI](https://pypi.org/project/pmcx)
- [pmcxcl en PyPI](https://pypi.org/project/pmcxcl/)
- [Referencia de configuración MCP de VS Code](https://code.visualstudio.com/docs/agents/reference/mcp-configuration.md)
- [Añadir y gestionar servidores MCP en VS Code](https://code.visualstudio.com/docs/agent-customization/mcp-servers.md)
- [Documentación de MCP de Claude Code](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [Servidor MCP de GitHub: guías de instalación](https://glama.ai/mcp/servers/@github/github-mcp-server/blob/bf6467855c13d3b8f5cf72f8dfd9c86f8336b20b/docs/installation-guides/README.md)
- [Playwright MCP: instalación](https://www.mintlify.com/microsoft/playwright-mcp/installation)
- [Context7: todos los clientes](https://www.mintlify.com/upstash/context7/mcp/all-clients)
