# MuscleSense Lab — Análisis de recuperación (módulo 6)

Versión 0.2 · 15 de noviembre de 2026 (0.1: 14 de noviembre; la 0.2 añade §3.3, parámetros correlacionados) · código en `backend/musclesense/recovery_analysis/`

## 1. Pregunta

¿Permiten los rasgos de una NIRS de onda continua estimar el estado de recuperación de la fuerza
del bíceps después del ejercicio? La especificación pide no suponer que reoxigenación equivale a
recuperación, así que la pregunta se divide en dos:

1. **Disociación.** ¿Cuántas veces la oxigenación ya volvió al basal mientras la fuerza no?
2. **Información añadida.** En un instante dado de la recuperación, ¿mejora la NIRS la
   predicción de la fuerza más allá de lo que el experimentador ya sabe (la dosis de ejercicio)?

La simulación solo puede contestar bajo supuestos explícitos sobre cómo la fatiga altera la
hemodinámica (acoplamientos). Por eso los acoplamientos se barren en lugar de fijarse.

## 2. Métodos

### 2.1 Cohorte virtual (`cohort.py`)

- 17 parámetros fisiológicos, 3 de tejido (grasa subcutánea, grosor de piel, melanina) y el
  protocolo varían entre sujetos.
- Cada parámetro sigue una distribución triangular (mínimo, nominal, máximo) construida con el
  intervalo y el valor nominal de `data/parametros_fisiologicos.json`. **Supuesto:** los
  intervalos publicados reúnen estudios distintos y no son distribuciones poblacionales. Por
  defecto los parámetros son independientes; §3.3 añade una estructura de correlación.
- Se descartan y se vuelven a muestrear los sujetos incoherentes: flujo y consumo de reposo
  incompatibles, o saturación vascular de reposo fuera de 0.55–0.80 (`smo2_reposo`).
- Protocolo: isométrico (50 %), dinámico (25 %) o excéntrico (25 %); intensidad triangular
  20–50–80 % MVC (el excéntrico, al 100 %); duración triangular 30–60–180 s; recuperación con
  marcas a 0, 5, 15 y 30 min.

### 2.2 Simulación (`dataset.py`)

Cada sujeto pasa por la cadena completa (tejido → difusión de N capas → sensor con ruido →
Beer-Lambert con DPF 4.16 → rasgos). Por sujeto y marca se guardan:

| Grupo | Columnas |
|---|---|
| Conocido por el experimentador | marca, intensidad, duración, tipo de contracción |
| Medido por el sensor (`nirs_`) | caída de (O₂ − desoxi) en el ejercicio, pico de desoxi, tiempo medio de reoxigenación, pico y tiempo de la hiperemia; cambios de oxi, desoxi, total y diferencia en la marca; fracción reoxigenada |
| Sensor perfecto (`verdad_`) | los mismos rasgos con los cambios reales en el músculo |
| Objetivo | capacidad de fuerza verdadera y sus componentes (rápida, lenta, daño) |

Los niveles de acoplamiento de un mismo sujeto comparten tejido, transporte de luz y semilla de
ruido: las diferencias entre niveles se deben solo a los acoplamientos.

### 2.3 Acoplamientos (`couplings.py`)

| Nivel | Acoplamiento | Respaldo |
|---|---|---|
| `ninguno` | todos en cero: la fatiga lenta y el daño no dejan huella hemodinámica | — |
| `dano_flujo_5pct`, `_9pct`, `_22pct` | daño → flujo de reposo, calibrado para que la SmO₂ de reposo suba 5, 9 y 22 % tras el excéntrico de referencia (70 contracciones máximas ≈ 210 s); c = 0.245, 0.492 y 1.915 | Ahmadi et al. 2008: +22 % agudo, +5 a +9 % durante días |
| `lenta_hiperemia_1`, `_2.5`, `_5` | la fatiga lenta reduce la hiperemia 10, 25 y 50 % por cada 10 % de pérdida lenta de fuerza | supuesto |
| `lenta_mvo2_0.5`, `_1`, `_2` | la fatiga lenta aumenta el consumo de reposo 5, 10 y 20 % por cada 10 % de pérdida lenta | supuesto |
| `combinado` | daño +9 %, hiperemia −25 %, consumo +10 % | mixto |

### 2.4 Estadística (`statistics.py`)

- **Un modelo por marca** (el tiempo queda implícito), una fila por sujeto. Con un modelo común
  a las cuatro marcas, los rasgos de sesión se repetirían en las cuatro filas de cada sujeto y la
  elección interna de la regularización (dejar uno fuera) premiaría memorizar sujetos.
- Predictores anidados: `nulo` (media de la marca), `dosis`, `nirs` (sin dosis), `dosis_nirs`,
  `dosis_oraculo`.
- Modelos: regresión ridge (rasgos estandarizados y recortados a ±3 desviaciones; la
  regularización se elige por validación interna) y árboles potenciados (`HistGradientBoosting`).
- Validación cruzada de 5 particiones sobre sujetos, idénticas para todos los conjuntos
  (comparación pareada). Métricas: R², error absoluto medio y AUC para "no recuperado"
  (fuerza < 0.95 de la previa).
- Correlación de Spearman de cada rasgo con la fuerza dentro de cada marca, cruda y parcial
  (controlando la dosis por regresión lineal).

### 2.5 Corrección del procesado detectada en este análisis

Con pocas cuentas (piel oscura y grasa delgada, SNR de 3 a 15 dB), tomar el logaritmo antes de
filtrar sesgaba la atenuación por la desigualdad de Jensen y por el recorte en 1 cuenta: un
sujeto mostraba −28 µM a los 30 min con una verdad de cero. Ahora la cadena filtra la intensidad
y después toma el logaritmo; el error cae a −8 µM, del orden del ruido
(`test_filtrar_la_intensidad_antes_del_logaritmo_reduce_el_error_con_pocas_cuentas`).

## 3. Resultados (150 sujetos, semilla 2026)

150 sujetos aceptados (42 descartes, aceptación 78 %): 86 isométricos, 28 dinámicos y
36 excéntricos. Sin fallos de simulación ni saturación del ADC. Fracción de trayectoria en el
músculo: mediana 0.26 (percentiles 5–95: 0.08–0.56). SNR mínima por sujeto: mediana 38 dB,
percentil 5 de 19 dB, mínimo 3.5 dB. Reproducible con
`python scripts/estudio_recuperacion.py --sujetos 150 --semilla 2026` (unos 15 min en 2 núcleos).

### 3.1 La reoxigenación no es recuperación

Sin acoplamientos (cambios reales en el músculo; "reoxigenado" = al menos 90 % de la caída
recuperada; "recuperado" = fuerza ≥ 0.95 de la previa):

| Marca | Reoxigenados | Recuperados | Reoxigenados sin fuerza recuperada | Fuerza media (mínima) |
|---|---|---|---|---|
| 0 min | 0 % | 0.7 % | 0 % | 0.59 (0.00) |
| 5 min | 96 % | 4.7 % | 92.7 % | 0.80 (0.28) |
| 15 min | 100 % | 24 % | 76 % | 0.85 (0.36) |
| 30 min | 100 % | 41 % | 58.7 % | 0.87 (0.41) |

A los 5 minutos casi todos los sujetos han reoxigenado y casi ninguno ha recuperado la fuerza.
Leer la reoxigenación como recuperación sería un error en 9 de cada 10 sujetos a los 5 min y en
6 de cada 10 a los 30 min. Con acoplamientos la tabla apenas cambia: la fracción reoxigenada
sube hasta 1.05 (hiperemia sostenida) y la fuerza no se mueve.

### 3.2 La NIRS casi no añade información a la dosis

R² con validación cruzada (ridge). La ganancia es R²(dosis + rasgos) − R²(dosis):

| Nivel | Marca | Dosis | NIRS sola | Dosis + NIRS | Dosis + oráculo | Ganancia NIRS | Ganancia oráculo |
|---|---|---|---|---|---|---|---|
| ninguno | 5 min | 0.897 | 0.105 | 0.898 | 0.905 | +0.001 | +0.008 |
| ninguno | 30 min | 0.908 | 0.169 | 0.909 | 0.911 | +0.001 | +0.003 |
| daño → flujo 22 % | 15 min | 0.907 | 0.795 | 0.899 | 0.927 | −0.008 | +0.020 |
| daño → flujo 22 % | 30 min | 0.908 | 0.831 | 0.909 | 0.927 | +0.001 | +0.019 |
| lenta → consumo 2 | 30 min | 0.908 | 0.218 | 0.924 | 0.938 | +0.015 | +0.030 |
| combinado | 30 min | 0.908 | 0.618 | 0.915 | 0.918 | +0.006 | +0.010 |

En los 11 niveles y las 4 marcas, la ganancia del sensor está entre −0.023 y +0.015 con ridge y
entre −0.046 y +0.021 con árboles; la del oráculo no pasa de +0.031 (ridge) y +0.055 (árboles).
Las tablas completas están en `docs/resultados/estudio_2026_150/` (`ganancia_ridge.csv`,
`ganancia_hgb.csv`, `evaluacion.csv`).

Tres observaciones:

1. **La dosis explica casi todo.** Intensidad, duración y tipo de contracción explican entre
   78 % (inmediatamente después) y 91 % (a los 30 min) de la varianza de la fuerza entre sujetos.
2. **"NIRS sola" engaña.** Con el acoplamiento de daño, la NIRS sola llega a R² = 0.83 a los
   30 min, pero porque reconoce el ejercicio excéntrico (hiperemia sostenida), algo que el
   experimentador ya sabe. Sin acoplamientos su R² a los 30 min es 0.17.
3. **El cuello de botella es fisiológico, no instrumental.** El oráculo (un sensor perfecto sin
   grasa, ruido ni errores de Beer-Lambert) gana como mucho 0.03 (ridge) o 0.055 (árboles). La pérdida por el
   instrumento (oráculo − NIRS) es del mismo orden. Mejorar el sensor no cambiaría la
   conclusión dentro de este modelo.

Las asociaciones existen, pero son pequeñas en varianza explicada: dentro de la misma dosis, la
fracción reoxigenada a los 30 min se correlaciona con la fuerza (ρ parcial = 0.51, p = 4·10⁻¹¹)
cuando la fatiga lenta eleva el consumo de reposo, y −0.26 (p = 10⁻³) a los 15 min con el
acoplamiento de daño. Como la dosis ya explica ~90 %, ρ = 0.5 sobre el residuo equivale a
unos 0.02 de R².

### 3.3 Con parámetros correlacionados: el fenotipo oxidativo

En personas, la capacidad oxidativa y la resistencia a la fatiga van juntas (más fibras lentas:
PCr más rápida, más capilares y mioglobina, menos caída de fuerza y recuperación más rápida). La
cohorte de §3.1–3.2 no lo modelaba. Ahora `CohortSpec.phenotype_correlation` añade un fenotipo
latente z (cópula gaussiana de un factor): nueve parámetros se correlacionan entre sí con
correlación r en valor absoluto y las distribuciones marginales no cambian.

| Sube con el fenotipo | Baja con el fenotipo |
|---|---|
| consumo máximo (`mvo2_max_factor`), flujo de hiperemia (`flow_peak`), mioglobina | constante de la PCr (`tau_pcr_s`), caída de fuerza de referencia y excéntrica, constantes de recuperación rápida y lenta de la fuerza, fracción lenta |

Los signos tienen respaldo (Paganini 1997; Larson-Meyer 2001: marcadores oxidativos frente a
tipo de fibra, r = 0.41–0.66; Thorstensson y Karlsson 1976; Lievens 2020), salvo el de la
fracción lenta, que es un supuesto. **La magnitud r no está medida para estos parámetros**, así
que se barre: 0, 0.25, 0.5 y 0.75. Las correlaciones publicadas entre marcadores sugieren que
0.25–0.5 es lo plausible y 0.75 un extremo. Con la misma semilla, los sujetos de dos valores de
r comparten todos los sorteos (comparación pareada).

Ganancia de R² sobre la dosis, sin acoplamientos, medias de las marcas de 5, 15 y 30 min
(ridge; 400 sujetos con sensor, 117 descartes, sin fallos):

| r | R² dosis | Fenotipo perfecto | Sensor perfecto (oráculo) | Sensor real | Sensor real + grasa conocida |
|---|---|---|---|---|---|
| 0 (600 sujetos, sin sensor) | 0.886 | 0.000 | −0.002 | — | — |
| 0.5 | 0.854 | +0.055 | +0.017 | +0.002 | +0.004 |
| 0.75 | 0.840 | +0.078 | +0.039 | +0.008 | +0.013 |

Con el acoplamiento fatiga lenta → consumo (`lenta_mvo2_1`), medias de 15 y 30 min:

| r | Sensor perfecto | Sensor real (ridge) | Sensor real (árboles) |
|---|---|---|---|
| 0 (150 sujetos) | +0.001 | +0.005 | +0.002 |
| 0.5 | +0.054 | +0.028 | +0.058 |
| 0.75 | +0.074 | +0.045 | +0.082 |

Lectura:

1. **La correlación sí da valor a la NIRS, como se sospechaba, pero con techo bajo.** La dosis
   explica menos (0.89 → 0.84) porque la varianza entre sujetos crece, y una lectura *perfecta*
   del fenotipo recuperaría como mucho 0.06–0.08 de R² (la mitad de lo que la dosis no explica).
2. **Un sensor perfecto recupera entre un tercio y la mitad de ese techo; el sensor real, una
   décima parte o menos.** Los rasgos reales del músculo se correlacionan con el fenotipo
   (ρ parcial hasta 0.68 para la amplitud de la desoxigenación con r = 0.75), pero en el sensor
   esa correlación cae a 0.25–0.29 porque la grasa escala la amplitud. Conocer el grosor de
   grasa la sube a 0.32–0.40 y apenas mejora la predicción.
3. **Cambia una conclusión de la versión 0.1.** Con parámetros independientes el límite era
   fisiológico; con parámetros correlacionados la pérdida por el instrumento (oráculo − sensor,
   0.015–0.03) es mayor que lo que el sensor aporta. Corregir la grasa y la trayectoria (DPF
   por sujeto, dos distancias) pasa a ser lo que más rendiría.
4. **El tiempo medio de reoxigenación no mide capacidad oxidativa en este modelo.** Su
   correlación con el fenotipo es positiva (+0.28 a +0.38): los sujetos oxidativos tardan *más*
   en reoxigenar, porque desoxigenan más hondo y tienen más mioglobina que rellenar, y eso pesa
   más que su PCr rápida y su mayor hiperemia. Variando un parámetro cada vez en el escenario de
   referencia: PCr de 68 a 18 s, 43 → 33 s; flujo de 5.3 a 11.1, 61 → 27 s; mioglobina de 0.2 a
   0.5 mM, 29 → 58 s; consumo máximo de ×5 a ×25, 20 → 37 s. La medida específica de capacidad
   oxidativa es la recuperación del consumo con oclusiones repetidas (Ryan 2012), que el
   protocolo admite y está desactivada.
5. **La disociación no cambia**: con r = 0.75, a los 5 min el 95 % ha reoxigenado y el 13 % ha
   recuperado la fuerza (150 sujetos).
6. **Ruido de las cifras.** Con 150 sujetos las ganancias tienen un error del orden de ±0.02
   (ridge) y ±0.05 (árboles): con r = 0, diez rasgos sin información restan hasta eso. Con 600
   sujetos, una variable de puro ruido aún "gana" +0.017 con árboles. Por eso las tablas de
   esta sección usan 400 y 600 sujetos y ridge como referencia.
   Los valores de r = 0 con cópula difieren de los de §3.2 en el segundo decimal porque los
   sorteos son otros; las conclusiones de §3.2 se mantienen.

Tablas completas: `docs/tablas/correlacion_fenotipo_ganancias.csv` (todos los tamaños, niveles y
modelos) y `docs/tablas/correlacion_fenotipo_cota_400.csv`.

## 4. Interpretación

Dentro de los supuestos del modelo:

- La reoxigenación termina en menos de 5 minutos y la fuerza tarda de decenas de minutos a días.
  Un índice de reoxigenación no sirve como indicador de recuperación funcional.
- La NIRS puede detectar el tipo de ejercicio o el daño muscular (si el acoplamiento daño → flujo
  es real), lo que tendría valor en el campo cuando la dosis no se conoce. Con la dosis conocida
  no mejora la estimación de la fuerza.
- La información que la hemodinámica contiene sobre la fuerza depende casi por completo de
  acoplamientos sin medir. La pregunta experimental que más mueve el resultado es cuánto altera
  la fatiga de baja frecuencia el consumo de O₂ y la hiperemia en reposo.
- Si la capacidad oxidativa y la resistencia a la fatiga se correlacionan (§3.3), la NIRS aporta
  algo aun sin acoplamientos, pero poco: hasta +0.01 de R² el sensor actual y +0.04 uno perfecto.
  El caso más favorable que se ha encontrado (correlación 0.75 y acoplamiento fatiga lenta →
  consumo) da +0.05 con ridge y +0.08 con árboles.

## 5. Límites y supuestos que más pesan

1. **Correlación entre parámetros sin medir.** §3.3 la barre con un solo factor latente y la
   misma correlación para los nueve parámetros. La estructura real (cuánto pesa cada parámetro,
   si hay más de un factor) no se conoce; el techo de 0.06–0.08 depende de ella.
2. **Distribuciones triangulares** sobre intervalos de literatura, no poblacionales.
3. **Modelo de fuerza** determinista dada la dosis y los parámetros; sin variabilidad de
   motivación, activación central ni error de medida de la MVC (que en la práctica es de ~5 %
   y reduciría todos los R²).
4. **Sin ruido fisiológico** (ondas de Mayer, respiración, movimiento) ni deriva del sensor: la
   NIRS simulada es más limpia que la real.
5. **Rasgos fijos**: diez rasgos definidos a mano. Las pruebas de oclusión arterial están en el
   protocolo pero desactivadas. Tras §3.3 activarlas es el paso con más rendimiento esperado:
   la constante de recuperación del consumo es la lectura directa del fenotipo que a los rasgos
   actuales les falta.
6. **Melanina homogeneizada** en toda la piel (ver ESTADO, asunto 8): sobrestima la pérdida de
   señal en piel oscura y con ella el ruido de esos sujetos.

## 6. Reproducir

```bash
python scripts/estudio_recuperacion.py --sujetos 150 --semilla 2026
python scripts/estudio_recuperacion.py --sujetos 60 --sin-optica      # solo fisiología, minutos
# §3.3 (con varios a la vez, fijar OMP_NUM_THREADS=1: los árboles se estorban entre procesos)
python scripts/estudio_recuperacion.py --sujetos 400 --correlacion 0.5 --niveles ninguno lenta_mvo2_1
python scripts/estudio_recuperacion.py --sujetos 600 --sin-optica --correlacion 0 --niveles ninguno
```

Los resultados se escriben en `resultados/` (fuera de git). La versión 0.1 citaba
`docs/resultados/estudio_2026_150/`, que `.gitignore` excluye y no llegó al repositorio; se
regenera con la primera orden.

Desde la API: `POST /api/estudios` con `{"n_subjects": 40, "optics": false}` y consultar
`GET /api/estudios/{id}` hasta que el estado sea `terminado`.
