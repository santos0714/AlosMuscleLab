# MuscleSense Lab — Estado del proyecto

Actualizado: 14 de noviembre de 2026, 14:20 (hora de Tijuana).
Este archivo es el punto de partida para continuar el trabajo en una sesión nueva.

## Dónde estamos

| Paso de la metodología | Estado |
|---|---|
| Fase 1. Preparación del entorno | Terminada y verificada en Windows, VM local y nube (`docs/00_informe_entorno.md`) |
| 1. Investigación científica | Terminada: tres dossieres y cuatro archivos de datos en `docs/investigacion/` |
| 2. Arquitectura | Terminada: `docs/01_arquitectura.md` |
| 3. Motor físico | Terminado: espectros, Beer-Lambert modificada, difusión semiinfinita y de N capas |
| 4. Validación matemática | Hecha para el motor físico (ver "Validación") |
| 5. Monte Carlo | Motor propio terminado y validado. **Falta** la envoltura de MCX-CL |
| 6. Instrumentación virtual | Modelo del sensor terminado. **Falta** el documento de diseño instrumental |
| Modelo fisiológico y protocolo | Terminado (primera versión calibrada con la literatura) |
| Procesado de señal | Terminado (primera versión) |
| Cadena completa con caché | Terminada: `musclesense/pipeline.py` |
| Análisis de recuperación (módulo 6) | **Falta** |
| 7. Interfaz (React, TypeScript, Plotly) | **Falta** |
| 8. Integración (FastAPI, SQLite) | **Falta** |
| 9. Pruebas automatizadas | 61 pruebas de Pytest del backend. **Faltan** las de API y Playwright |
| 10. Documentación científica | **Faltan** modelos matemáticos, informe de validación y lista de materiales final |
| Validation Agent | **Falta**: revisión crítica independiente de todo lo anterior |

## Código existente (`backend/musclesense/`)

| Módulo | Archivo | Contenido |
|---|---|---|
| Optical Physics | `optical_physics/spectra.py` | Espectros tabulados, conversión de unidades, espectro del LED |
| | `optical_physics/mbll.py` | Beer-Lambert modificada directa e inversa |
| | `optical_physics/diffusion.py` | Fresnel, frontera extrapolada, semiinfinito, N capas (Hankel), trayectorias parciales |
| | `optical_physics/montecarlo.py` | Monte Carlo en capas con biblioteca de trayectorias reponderable |
| Tissue Simulator | `tissue_simulator/model.py` | Capas piel, grasa y músculo; composición a μa y μs'; perfiles de sujeto |
| Sensor Designer | `sensor_designer/device.py` | LED, fotodiodo, TIA, ADC, MCU; fotocorriente, ruido y cuentas |
| Exercise Protocol | `exercise_protocol/model.py` | Ecuaciones diferenciales de O2, flujo, volumen, PCr y fatiga; protocolo y marcas |
| Signal Processing | `signal_processing/processing.py` | Atenuación, concentraciones, filtro y rasgos |
| Cadena | `pipeline.py` | `Scenario`, `Pipeline.run()`, huellas por etapa y lista de etapas recalculadas |

Datos en `backend/musclesense/data/`: `espectros_cromoforos.csv`, `parametros_opticos.json`, `parametros_fisiologicos.json`, `componentes.json`. Son copia de los de `docs/investigacion/`; al cambiarlos hay que mantener ambas copias iguales o dejar una sola.

## Validación ya hecha

| Comprobación | Resultado |
|---|---|
| Coeficientes de frontera para n = 1.4 | R_eff = 0.493, A = 2.95, C1 = 0.118, C2 = 0.306, iguales a los publicados |
| N capas con capas idénticas frente a la fórmula semiinfinita | Coinciden a 1e-8 |
| Monte Carlo, losa de van de Hulst | Rd = 0.0972 y Tt = 0.6613 frente a 0.09739 y 0.66096 |
| Monte Carlo, semiinfinito isótropo con índice igualado | 0.4153 frente a 0.41495 (solución exacta con la función H de Chandrasekhar) |
| Monte Carlo, caso de Giovanelli (n = 1.5) | Difusa 0.2192 + especular 0.04 = 0.2592 frente a 0.2600 |
| Monte Carlo frente a difusión, medio homogéneo | Reflectancia: +11 % a 10 mm, de 0 a 4 % entre 15 y 30 mm. Trayectoria media: dentro del 5 % |
| Reponderación de la biblioteca | Reproduce la solución exacta con otra absorción |
| Modelo fisiológico | Reposo estacionario; tiempo medio de reoxigenación vascular de 13 a 27 s (publicado: 10 a 55 s); 15 % MVC durante 43 min deja la fuerza en 0.59 y en 0.85 a los 30 min (publicado: 0.586 y cerca de 0.85) |
| Propagación de parámetros | Cambiar el amplificador o el ejercicio no repite el transporte; cambiar la grasa o la distancia sí |

## Primeros resultados de la cadena completa

Escenario de referencia (50 % MVC isométrico, 60 s, distancia de 30 mm, motor de difusión):

| Grasa subcutánea | Fracción de trayectoria en el músculo | Estimado / real (ΔHHb) | Fotocorriente a 850 nm | SNR a 760 nm |
|---|---|---|---|---|
| 1.5 mm | 0.62 | 0.78 | 1.0 nA | 44 dB |
| 3.0 mm | 0.41 | 0.58 | 1.7 nA | 48 dB |
| 5.0 mm | 0.21 | 0.33 | 3.7 nA | 53 dB |
| 9.0 mm | 0.05 | 0.10 | 12.6 nA | 62 dB |

Con Beer-Lambert y el DPF de antebrazo (4.16), el sensor subestima el cambio real en el músculo, y la subestimación crece con la grasa. El tiempo medio de reoxigenación que ve la NIRS (unos 40 s) es mayor que el vascular (unos 17 s) porque la mioglobina se resatura después.

## Asuntos científicos abiertos

1. **Supuestos del modelo fisiológico.** Los parámetros marcados `(supuesto)` en `exercise_protocol/model.py` no vienen de una medida: reclutamiento difusivo, hiperemia reactiva, constantes de tiempo de flujo y volumen, carga de referencia de la fatiga. Están calibrados para reproducir anclas publicadas.
2. **Acoplamientos entre fatiga y hemodinámica.** Por defecto valen cero. Solo uno tiene respaldo cuantitativo: tras ejercicio excéntrico la saturación de reposo del bíceps sube 22 % de forma aguda y de 5 a 9 % durante días. El módulo de análisis de recuperación debe barrer su intensidad.
3. **Parámetros sin verificar.** 20 de 59 parámetros fisiológicos están marcados `"verificado": false` con su origen en la nota.
4. **MCX-CL.** Desviación de 0.26 % en Beer-Lambert con μs = 0 y absorción baja, sin explicar. No se ha comparado aún MCX-CL con el Monte Carlo propio en tejido de tres capas.
5. **Difusión con capas finas.** La difusión de N capas es el motor por defecto de la interfaz; frente al Monte Carlo propio la fracción de trayectoria en el músculo difiere menos de 0.15, pero falta cuantificarlo por grosor de grasa.
6. **Índices de refracción.** La difusión de N capas supone el mismo índice en todas las capas.
7. **Dossier de óptica.** `02_optica_de_tejidos_y_modelos.md` se escribió justo antes de un corte por límite de uso: revisar que esté completo.

## Qué sigue, en orden

1. `recovery_analysis/`: cohortes virtuales, relación entre rasgos NIRS y capacidad de fuerza, barrido de acoplamientos, validación cruzada con scikit-learn.
2. `optical_physics/mcx_engine.py`: envoltura de `pmcxcl` que devuelva una `PathLibrary`, y prueba cruzada con el Monte Carlo propio.
3. `api/`: FastAPI con SQLite (catálogo, perfiles, ejecutar escenario, historial).
4. `frontend/`: seis vistas, una por módulo, con Plotly.
5. Pruebas de API y Playwright.
6. Validation Agent y documentos finales: modelos matemáticos, informe de validación, diseño instrumental y lista de materiales.

## Cómo retomar

En Linux (VM local o nube):

```bash
bash scripts/preparar_linux.sh
source ~/.venvs/musclesense/bin/activate
python -m pytest backend/tests -q          # 61 pruebas, alrededor de 1 minuto
```

En Windows: `.venv\Scripts\python -m pytest backend\tests -q`.

Ejemplo mínimo:

```python
from musclesense.pipeline import Pipeline, Scenario
resultado = Pipeline().run(Scenario())
print(resultado.features["estimado"], resultado.muscle_path_fraction)
```

## Decisiones pendientes del usuario

- Crear el repositorio remoto en GitHub (cuenta `santos0714`): nombre y si es público o privado.
