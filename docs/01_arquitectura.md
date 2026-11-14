# MuscleSense Lab — Arquitectura del sistema

Versión 0.1 · 14 de noviembre de 2026

## 1. Propósito y alcance

MuscleSense Lab simula de extremo a extremo una medición NIRS de onda continua sobre el bíceps braquial: tejido → luz → electrónica → señal → estimación → análisis de recuperación. Como toda la cadena es sintética, se conoce la "verdad" fisiológica y se puede medir cuánto de ella recupera el instrumento.

Lo que una simulación puede y no puede concluir:

- **Puede** responder preguntas de identificabilidad: bajo supuestos explícitos sobre cómo la fatiga altera la hemodinámica, ¿un sensor realista distingue estados de recuperación a pesar del ruido, la grasa subcutánea, la mioglobina y los errores del modelo de Beer-Lambert?
- **No puede** demostrar que esos supuestos se cumplen en personas. Cada acoplamiento entre fatiga y hemodinámica se declara como "respaldado por literatura" o "supuesto", con su intensidad ajustable, incluida la intensidad cero.

## 2. Estructura del repositorio

```
backend/
  musclesense/
    constants.py            unidades y constantes físicas
    data/                   espectros, parámetros de tejido, catálogo de componentes
    optical_physics/        1. Optical Physics
      spectra.py            espectros de cromóforos, promedio sobre el espectro del LED
      mbll.py               Beer-Lambert modificada, directa e inversa
      diffusion.py          difusión: semiinfinito y N capas
      montecarlo.py         Monte Carlo en capas, biblioteca de trayectorias
      mcx_engine.py         envoltura de MCX-CL (opcional)
    tissue_simulator/       2. Tissue Simulator
    sensor_designer/        3. Sensor Designer
    exercise_protocol/      4. Exercise Protocol
    signal_processing/      5. Signal Processing
    recovery_analysis/      6. Recovery Analysis
    pipeline.py             escenario, etapas, caché y propagación de cambios
    api/                    FastAPI y SQLite
  tests/                    Pytest
frontend/                   React, TypeScript, Vite, Plotly
e2e/                        Playwright
docs/                       investigación, modelos, validación, diseño instrumental
```

Los identificadores del código van en inglés, igual que los nombres de módulo pedidos. Comentarios, documentación e interfaz van en español. El código es compatible con Python 3.10 a 3.13.

## 3. Convención de unidades

| Magnitud | Unidad interna |
|---|---|
| Longitud, grosor, distancia emisor-detector | mm |
| μa, μs, μs' | mm⁻¹ |
| Longitud de onda | nm |
| Concentración de cromóforo en tejido | mM (por grupo hemo para Hb y Mb) |
| Tiempo | s |
| Potencia óptica, corriente, tensión | W, A, V |
| Atenuación | logaritmo natural: A = −ln(I/I₀) |

Los espectros publicados (ε decádico en cm⁻¹/M por tetrámero) se convierten una sola vez al cargar: μa [mm⁻¹] = ln(10) · ε · C[M] / 10. La densidad óptica en base 10 solo se usa para mostrar resultados.

## 4. Flujo de datos y propagación de parámetros

Un `Scenario` inmutable reúne cuatro bloques de parámetros: sujeto (geometría, composición y fisiología), sensor, protocolo y ajustes de simulación. El cálculo es una cadena de etapas; cada etapa declara de qué parámetros depende y se guarda en caché con una huella (hash) de esos parámetros.

| # | Etapa | Depende de | Costo |
|---|---|---|---|
| 1 | Propiedades ópticas por capa y longitud de onda | composición del tejido, longitudes de onda | bajo |
| 2 | Transporte de fotones: reflectancia y trayectorias parciales | esparcimiento, índices, grosores, distancia y tamaño del detector | **alto** |
| 3 | Fisiología en el tiempo | fisiología del sujeto, protocolo | bajo |
| 4 | Absorción por capa en el tiempo | 1 y 3 | bajo |
| 5 | Potencia óptica detectada en el tiempo | 2, 4 y emisores | bajo |
| 6 | Señal eléctrica con ruido y cuantización | 5 y electrónica | bajo |
| 7 | Estimación de ΔO₂Hb, ΔHHb, tHb y saturación | 6 y ajustes del procesado | bajo |
| 8 | Rasgos de recuperación y comparación con la verdad | 7 y 3 | bajo |

La etapa 2 no depende de la absorción: se simula el recorrido de los fotones una vez y la absorción se aplica después ponderando cada fotón detectado con exp(−Σⱼ μaⱼ·Lᵢⱼ). Así, cambiar la intensidad del ejercicio o la potencia del LED no repite el transporte, y cambiar el grosor de grasa sí. `Pipeline.run()` devuelve qué etapas se recalcularon, y hay pruebas que lo comprueban.

## 5. Motores de transporte de fotones

| Motor | Uso | Validez |
|---|---|---|
| Difusión semiinfinita analítica | Referencia y pruebas | Medio homogéneo, ρ ≫ 1/μs' |
| Difusión de N capas (transformada de Hankel) | Interfaz interactiva; respuesta inmediata | ρ ≳ 10 mm, capas no demasiado finas |
| Monte Carlo propio en capas (NumPy) | Referencia portable; contraste independiente de MCX | General; costo de segundos a minutos |
| MCX-CL (`pmcxcl`) | Corridas grandes en GPU | General; discretización en vóxeles |

Los cuatro producen la misma estructura: reflectancia por unidad de área en el detector y trayectoria parcial media por capa. Los dos Monte Carlo producen además una `PathLibrary` con las trayectorias de cada fotón detectado.

La validación se apoya en que son independientes entre sí: difusión de N capas con capas idénticas frente a la fórmula semiinfinita, Monte Carlo propio frente a las tablas de MCML, Monte Carlo propio frente a MCX-CL, y difusión frente a Monte Carlo donde la difusión es válida.

## 6. Módulos

### 6.1 Optical Physics
- `spectra`: carga de espectros tabulados, interpolación y promedio sobre el espectro de emisión del LED.
- `mbll`: problema directo (ΔA a partir de Δc y trayectorias) e inverso (mínimos cuadrados con 2 o 3 longitudes de onda), con número de condición de la matriz de extinción.
- `diffusion`, `montecarlo`, `mcx_engine`: los motores del apartado 5.

### 6.2 Tissue Simulator
- `Layer`: grosor, fracciones de sangre, agua, lípido y melanina, mioglobina, saturaciones, ley de esparcimiento, g y n.
- `TissueModel`: piel, grasa y músculo; calcula μa(λ) y μs'(λ) por capa; perfiles de sujeto predefinidos.

### 6.3 Sensor Designer
- Catálogo de componentes reales (`data/componentes.json`).
- `SensorDesign`: emisores, fotodiodo, amplificador de transimpedancia, ADC, microcontrolador virtual (secuencia de encendido, promediado, resta de luz ambiente), distancia emisor-detector.
- Cadena de señal: potencia detectada → fotocorriente → tensión → cuentas, con ruido shot, térmico, del amplificador y de cuantización.

### 6.4 Exercise Protocol
- Modelo dinámico (ecuaciones diferenciales) con variables separadas para oxigenación y para capacidad de fuerza: flujo, volumen sanguíneo, saturación microvascular, saturación de mioglobina, consumo de O₂, fosfocreatina, y componentes rápida y lenta de la fatiga.
- `ProtocolSpec`: basal, ejercicio (intensidad, duración, tipo de contracción) y recuperación con marcas a 0, 5, 15 y 30 minutos.

### 6.5 Signal Processing
- Cuentas → atenuación → concentraciones con Beer-Lambert modificada (DPF supuesto por el usuario).
- Filtrado, índice de saturación, y rasgos: caída durante el ejercicio, tiempo medio de reoxigenación, sobreimpulso hiperémico, línea base posterior.

### 6.6 Recovery Analysis
- Compara los rasgos NIRS con la capacidad de fuerza "verdadera" del modelo.
- Cohortes virtuales con variabilidad entre sujetos; correlación, regresión y validación cruzada.
- Análisis de sensibilidad sobre los acoplamientos supuestos entre fatiga y hemodinámica.

## 7. Backend, almacenamiento e interfaz

- FastAPI expone el catálogo, los perfiles, la ejecución de escenarios y el historial.
- SQLite guarda escenarios, resultados resumidos y la caché de transporte.
- La interfaz tiene una vista por módulo; cada vista edita su bloque del escenario y muestra qué etapas se recalcularon.

## 8. Reproducibilidad

- Toda simulación estocástica recibe una semilla explícita.
- Cada resultado guarda el escenario completo, la huella de cada etapa y las versiones del software.
- Los parámetros con origen bibliográfico viven en archivos de datos con su referencia y una marca `verificado`.

## 9. Agentes

| Agente | Responsabilidad |
|---|---|
| Biomedical | Fisiología, parámetros y referencias |
| Physics | Óptica de tejidos, modelos y valores de referencia |
| Hardware | Componentes comerciales, lista de materiales, seguridad |
| Simulation | Motores de transporte |
| Data Science | Procesado de señal y análisis de recuperación |
| Software | API, base de datos, interfaz, pruebas |
| Validation | Revisión crítica independiente de todo lo anterior |
