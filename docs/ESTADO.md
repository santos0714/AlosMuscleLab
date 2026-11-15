# MuscleSense Lab — Estado del proyecto

Actualizado: 14 de noviembre de 2026, 20:05 (hora de Tijuana).
Este archivo es el punto de partida para continuar el trabajo en una sesión nueva.

Repositorio: **santos0714/AlosMuscleLab** (https://github.com/santos0714/AlosMuscleLab). Carpeta local:
`C:\Users\HP\Documents\Simulador-Sensor-Optico-Biomedico` (rama `main`, remoto `origin`).

## Dónde estamos

| Paso de la metodología | Estado |
|---|---|
| Fase 1. Preparación del entorno | Terminada y verificada en Windows, VM local y nube (`docs/00_informe_entorno.md`) |
| 1. Investigación científica | Terminada: tres dossieres y cuatro archivos de datos en `docs/investigacion/` |
| 2. Arquitectura | Terminada: `docs/01_arquitectura.md` |
| 3. Motor físico | Terminado: espectros, Beer-Lambert modificada, difusión semiinfinita y de N capas |
| 4. Validación matemática | Hecha para el motor físico (ver "Validación") |
| 5. Monte Carlo | Motor propio y envoltura de MCX-CL terminados; MCX-CL validado contra el propio en tres capas |
| 6. Instrumentación virtual | Modelo del sensor terminado. **Falta** el documento de diseño instrumental |
| Modelo fisiológico y protocolo | Terminado (primera versión calibrada con la literatura) |
| Procesado de señal | Terminado; corregido el orden filtro → logaritmo |
| Cadena completa con caché | Terminada: `musclesense/pipeline.py`, con caché acotada y persistente |
| Análisis de recuperación (módulo 6) | **Terminado**: `recovery_analysis/` y `docs/02_analisis_recuperacion.md` |
| 7. Interfaz (React, TypeScript, Plotly) | **Terminada (primera versión)**: `frontend/`, servida por la API |
| 8. Integración (FastAPI, SQLite) | **Terminada la API**: `musclesense/api/` |
| 9. Pruebas automatizadas | 116 de Pytest (entorno, backend, API, MCX-CL) y 5 de Playwright sobre la interfaz |
| 10. Documentación científica | Hecho el análisis de recuperación. **Faltan** modelos matemáticos, informe de validación y lista de materiales final |
| Validation Agent | **Falta**: revisión crítica independiente de todo lo anterior |

## Código existente (`backend/musclesense/`)

| Módulo | Archivo | Contenido |
|---|---|---|
| Optical Physics | `optical_physics/spectra.py` | Espectros tabulados, conversión de unidades, espectro del LED |
| | `optical_physics/mbll.py` | Beer-Lambert modificada directa e inversa |
| | `optical_physics/diffusion.py` | Fresnel, frontera extrapolada, semiinfinito, N capas (Hankel), trayectorias parciales |
| | `optical_physics/montecarlo.py` | Monte Carlo en capas con biblioteca reponderable; estimadores de anillo y de disco |
| | `optical_physics/mcx_engine.py` | MCX-CL en vóxeles, anillo de detectores, `DetectorPathLibrary` reponderable |
| | `optical_physics/opencl.py` | Configura PoCL (OpenCL de CPU) en Linux sin GPU |
| Tissue Simulator | `tissue_simulator/model.py` | Capas piel, grasa y músculo; composición a μa y μs'; perfiles de sujeto |
| Sensor Designer | `sensor_designer/device.py` | LED, fotodiodo, TIA, ADC, MCU; fotocorriente, ruido y cuentas |
| Exercise Protocol | `exercise_protocol/model.py` | Ecuaciones diferenciales de O2, flujo, volumen, PCr y fatiga; protocolo y marcas |
| Signal Processing | `signal_processing/processing.py` | Atenuación, concentraciones, filtro y rasgos |
| Recovery Analysis | `recovery_analysis/cohort.py` | Cohortes virtuales (triangulares sobre intervalos publicados, descarte de incoherentes) |
| | `recovery_analysis/dataset.py` | Simulación de la cohorte por nivel de acoplamiento; tabla sujeto × marca |
| | `recovery_analysis/couplings.py` | Calibración daño → flujo con Ahmadi 2008; niveles del barrido |
| | `recovery_analysis/statistics.py` | Modelos por marca, validación cruzada, ganancia NIRS/oráculo, disociación, asociaciones |
| Cadena | `pipeline.py` | `Scenario`, `Pipeline.run()`, motores `diffusion`, `montecarlo` y `mcx` |
| API | `api/app.py`, `api/service.py`, `api/database.py` | FastAPI y SQLite: escenarios, historial, perfiles, catálogo, parámetros, estudios en segundo plano, caché de transporte |

Interfaz (`frontend/`, React 19 + TypeScript + Vite + Plotly): corte del brazo a escala con el
recorrido de la luz por capa, cadena de 8 etapas que marca cuáles se recalcularon, y vistas de
señal, fisiología, luz y tejido, sensor (con lista de materiales), recuperación (estudios de
cohorte en segundo plano) e historial. Colores de datos validados con el validador de paletas
(capas y señales, todos los pares). La API sirve `frontend/dist` en `/` si existe.

Scripts: `scripts/estudio_recuperacion.py` (estudio completo) y `scripts/comparar_motores.py`
(difusión, Monte Carlo propio y MCX-CL por grosor de grasa; pensado para la GPU de Windows).

Datos en `backend/musclesense/data/`: copia de los de `docs/investigacion/`; al cambiarlos hay
que mantener ambas copias iguales o dejar una sola.

## Validación ya hecha

| Comprobación | Resultado |
|---|---|
| Coeficientes de frontera para n = 1.4 | R_eff = 0.493, A = 2.95, C1 = 0.118, C2 = 0.306, iguales a los publicados |
| N capas con capas idénticas frente a la fórmula semiinfinita | Coinciden a 1e-8 |
| Monte Carlo, losa de van de Hulst | Rd = 0.0972 y Tt = 0.6613 frente a 0.09739 y 0.66096 |
| Monte Carlo, semiinfinito isótropo con índice igualado | 0.4153 frente a 0.41495 (función H de Chandrasekhar) |
| Monte Carlo, caso de Giovanelli (n = 1.5) | Difusa 0.2192 + especular 0.04 = 0.2592 frente a 0.2600 |
| Monte Carlo frente a difusión, medio homogéneo | Reflectancia: +11 % a 10 mm, de 0 a 4 % entre 15 y 30 mm. Trayectoria media: dentro del 5 % |
| Reponderación de la biblioteca | Reproduce la solución exacta con otra absorción |
| **MCX-CL frente al Monte Carlo propio, tres capas** | Reflectancia en disco a 10 mm y trayectorias parciales por capa coinciden (dentro de 4σ y 6 %) con dos juegos de absorción |
| Modelo fisiológico | Reposo estacionario; reoxigenación vascular 13–27 s (publicado 10–55 s); 15 % MVC 43 min → fuerza 0.59 y 0.85 a los 30 min (publicado 0.586 y ~0.85) |
| Calibración daño → flujo | Acoplamientos 0.245, 0.492 y 1.915 reproducen +5, +9 y +22 % de SmO2 de reposo tras excéntrico (Ahmadi 2008) |
| Propagación de parámetros | Cambiar el amplificador o el ejercicio no repite el transporte; cambiar la grasa o la distancia sí |
| Caché persistente | Una instancia nueva de la API lee el transporte de SQLite y no lo recalcula |
| Concurrencia | LSODA (SciPy) no admite dos integraciones a la vez; un candado global las serializa. Sin él, 5 de 5 ejecuciones con 6 hilos fallaban |
| Interfaz | Playwright: carga y vistas sin errores de consola; cambiar el amplificador recalcula solo electrónica, procesado y rasgos; cambiar la grasa repite el transporte y no la fisiología; historial; estudio pequeño |

## Resultados científicos

**Cadena completa, escenario de referencia** (50 % MVC isométrico 60 s, 30 mm, difusión): con
Beer-Lambert y DPF de antebrazo (4.16) el sensor subestima el cambio real en el músculo, más
cuanto más grasa (estimado/real de 0.78 con 1.5 mm de grasa a 0.10 con 9 mm).

**Análisis de recuperación** (150 sujetos, 11 niveles de acoplamiento; `docs/02_analisis_recuperacion.md`):

- **La reoxigenación no es recuperación.** A los 5 min el 96 % de los sujetos ha reoxigenado y
  solo el 4.7 % ha recuperado la fuerza (≥ 95 %); a los 30 min, el 59 % sigue reoxigenado sin
  fuerza recuperada.
- **La NIRS casi no añade información a la dosis.** Intensidad, duración y tipo de contracción
  explican 78–91 % de la varianza de la fuerza dentro de cada marca; la NIRS añade entre −0.02
  y +0.02 de R² y un sensor perfecto como mucho +0.03 (ridge) o +0.055 (árboles).
- **"NIRS sola" engaña:** llega a R² = 0.83 con el acoplamiento de daño porque reconoce el
  ejercicio excéntrico, que el experimentador ya conoce.
- El límite es fisiológico, no instrumental, **bajo el supuesto de parámetros independientes**
  (asunto abierto 9).

## Asuntos científicos abiertos

1. **Supuestos del modelo fisiológico.** Los parámetros marcados `(supuesto)` en `exercise_protocol/model.py` no vienen de una medida; están calibrados para reproducir anclas publicadas. La API los expone con `"supuesto": true`.
2. **Acoplamientos fatiga → hemodinámica.** Barridos en el análisis de recuperación. Solo daño → flujo tiene respaldo cuantitativo; los de fatiga lenta son supuestos.
3. **Parámetros sin verificar.** 20 de 59 parámetros fisiológicos están marcados `"verificado": false`.
4. **MCX-CL.** Validado contra el Monte Carlo propio a 10 mm con detectores de disco. Falta la comparación a 30 mm en el tejido real por grosor de grasa (`scripts/comparar_motores.py`, mejor en la GPU de Windows: en la CPU de la nube va a ~6 fotones/ms). La desviación de 0.26 % en Beer-Lambert con μs = 0 de la prueba de entorno sigue sin explicar.
5. **Difusión con capas finas.** Cuantificar por grosor de grasa frente a Monte Carlo y MCX (mismo script).
6. **Índices de refracción.** La difusión de N capas y la envoltura de MCX suponen el mismo índice en todas las capas.
7. **Dossier de óptica.** `02_optica_de_tejidos_y_modelos.md` se escribió justo antes de un corte por límite de uso: revisar que esté completo.
8. **Melanina homogeneizada.** El modelo reparte la melanina de la epidermis (60 µm) en toda la piel (~2 mm) y los fotones recorren 17–31 mm dentro de esa capa: la piel oscura atenúa ×19 a 760 nm (fotocorriente de 0.53 a 0.028 nA), probablemente de más. Plan: Monte Carlo de cuatro capas con epidermis separada frente al modelo homogeneizado, y corregir el modelo si difieren.
9. **Correlaciones entre parámetros.** La cohorte muestrea cada parámetro de forma independiente; en personas la capacidad oxidativa se correlaciona con la resistencia a la fatiga. Es el supuesto que más probablemente subestima el valor de la NIRS. Siguiente paso: añadir una estructura de correlación y repetir el barrido.

## Qué sigue, en orden

El usuario prefiere hacer con Claude Fable los puntos 1 a 4 (revisión científica y validación).

1. Correlaciones entre parámetros en la cohorte (asunto 9) y repetición del estudio de recuperación.
2. Monte Carlo con epidermis separada frente a la melanina homogeneizada (asunto 8).
3. Comparación de motores por grosor de grasa en la GPU de Windows (asuntos 4 y 5): `scripts/comparar_motores.py`.
4. Validation Agent y documentos finales: modelos matemáticos, informe de validación, diseño instrumental y lista de materiales.
5. Interfaz, segunda versión: modo oscuro (paleta validada aparte), comparar dos simulaciones del historial, exportar series en CSV.

## Cómo retomar

En Linux (VM local o nube):

```bash
bash scripts/preparar_linux.sh
source ~/.venvs/musclesense/bin/activate
python -m pytest -q                       # 116 pruebas, unos 3 minutos (MCX-CL en CPU es lo lento)
python -m pytest -q -m "not slow"         # sin MCX-CL
```

En Windows: `.venv\Scripts\python -m pytest -q`.

```python
from musclesense.pipeline import Pipeline, Scenario
resultado = Pipeline().run(Scenario())
print(resultado.features["estimado"], resultado.muscle_path_fraction)
```

Interfaz: `cd frontend && npm install && npm run build`, luego `cd ../backend && uvicorn musclesense.api.app:app`
y abrir http://127.0.0.1:8000. Pruebas de la interfaz: `npm run test:e2e` en `frontend/` (variables `PYTHON`
y `CHROME_PATH` opcionales; ver `frontend/playwright.config.ts`).

## Notas de sincronización

- El código está en GitHub: `santos0714/AlosMuscleLab`, rama `main`. La app de GitHub de Claude
  quedó autorizada el 14 de noviembre de 2026, así que una sesión nueva clona el repositorio,
  trabaja y sube con `git push` sin pasar por el equipo del usuario.
- El contenedor de la nube no persiste entre sesiones: lo que no se sube a GitHub se pierde.
- La carpeta local de Windows se pone al día con `git pull` (o, desde una sesión de Claude con
  el equipo conectado, con un paquete de git `*.bundle`, que git ignora).
