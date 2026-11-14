# 03 Instrumentación y componentes de MuscleSense Lab

Fecha de consulta: 2026-11-14. Los datos completos, con una URL por componente, están en `componentes.json` (mismos identificadores).

## 0. Alcance y convenciones

- Los parámetros salen de hojas de datos del fabricante o de páginas de distribuidores leídas en esta sesión con un extractor de texto. Las curvas (responsividad espectral, deriva térmica) no se pudieron leer: lo que depende de ellas está marcado como estimado.
- Precios para 1 pieza en USD. **[D]** = visto ese día en la página de un distribuidor. **[E]** = estimación sin consultar. Los precios vistos en EUR, GBP o CAD se convirtieron con tipos aproximados (1.17, 1.335 y 0.72), lo que añade un ±5 %.
- "No confirmado" en el estado significa que no se vio una página vigente del fabricante o distribuidor, no que la pieza esté obsoleta.

## A. Emisores

| Parte | λ pico (nm) | FWHM (nm) | Potencia (mW) a I (mA) | I máx cc / pulso (mA) | VF (V) | Semiángulo | Deriva (nm/K) | Encapsulado | Precio |
|---|---|---|---|---|---|---|---|---|---|
| Roithner LED760-01AU | 760 | 30 | 19 a 50 | 100 / 500 | 1.8 | s/d | solo curva | epoxi 5 mm | 5 [E] |
| Roithner SMB1N-760D | 760 ±10 | 26 | 400 a 800 | 800 / 2000 | 2.0 | ±65° | solo curva | SMD potencia | 20 [E] |
| Marktech MTE1077N1-R | 770 | s/d | s/d | 50 / s/d | 1.55 | ±12° | s/d | radial | 3.54 [D] |
| Roithner LED810-01AU | 810 | 35 | 22 a 50 | 100 / 500 | 1.7 | s/d | s/d | epoxi radial | 5 [E] |
| Marktech MTE2081S-OH5 | 810 | s/d | s/d | 100 / s/d | 1.55 | ±7° | s/d | radial 5 mm | 5.87 [D] |
| OSRAM SFH 4780S | 820 (centroide 810) | 30 | 600 a 1000 | 500 / 2000 | 3.3 | ±10° | 0.3 | SMD 3.5×3.5 | 4 [E] |
| Luminus SST-10-IRD-B90H-V810 | 815 (800–830) | 30 | 615 a 350 | 1500 / 5000 | 3.0 | ±45° | 0.3 | SMD cerámico | 5 [E] |
| Vishay VSMY2850G | 850 (840–870) | 30 | 55 a 100 | 100 / 1000 | 1.6 | ±10° | 0.25 | SMD 2.3×2.3 | 1.17 [D] |
| OSRAM SFH 4250 | 850 | 35 | 40 a 100 | 100 / 1500 | 1.5 | ±60° | 0.2 | Power TOPLED | 1 [E] |
| Marktech MTMD7885N24 (3 chips) | 770 / 810 / 850 | 35 / 30 / 35 | 3.1 / 3.0 / 2.7 a 20 | 50 / 100 / 100 cc | 1.6 / 1.55 / 1.4 | s/d | s/d | TO-18 con domo | 37.26 [D] |

Lectura para el modelo del instrumento:

- **Espectro.** FWHM entre 26 y 35 nm en las tres bandas. Una gaussiana con σ = FWHM/2.355 (11 a 15 nm) es una primera aproximación; los LED de AlGaAs tienen una cola asimétrica que las hojas no cuantifican.
- **Potencia.** Pendientes de 0.38 mW/mA (760 nm), 0.44 mW/mA (810 nm) y 0.55 mW/mA (850 nm). A 20 mA resultan unos 8, 9 y 11 mW si se supone linealidad, que es una hipótesis: las hojas solo dan un punto.
- **Tolerancia de λ.** Solo tres hojas la acotan (±10 nm, 840–870 nm y el intervalo 800–830 nm). Propongo ±10 nm como incertidumbre de fabricación.
- **Deriva.** De 0.2 a 0.3 nm/K en las piezas de 810 y 850 nm. Para 760 nm no hay coeficiente numérico: usar 0.25 nm/K como supuesto. Ninguna hoja da la deriva con la corriente; conviene modelarla como autocalentamiento (sección G).
- **Un solo encapsulado.** El MTMD7885N24 es la única opción de tres chips con hoja de datos y precio vistos, pero emite a 770 nm, no a 760 nm, y había 1 pieza en existencia. La familia SMT de Ushio (Epitex) admite hasta tres chips de 350 µm en 3.5 × 2.8 mm; no encontré un número de parte 760/810/850 y la página anuncia la descontinuación de parte de la familia con última orden el 30-06-2026.
- Los LED de potencia (SMB1N, SFH 4780S, SST-10) existen y cubren 760 y 810 nm, pero están muy sobredimensionados: se usarían a menos del 5 % de su corriente nominal.

## B. Fotodetectores

| Parte | Tipo | Área (mm²) | R a 760 / 810 / 850 (A/W) | I oscuridad (nA) | C (pF) | NEP (W/√Hz) | Precio |
|---|---|---|---|---|---|---|---|
| Vishay BPW34 | PIN | 7.5 | 0.50 / 0.55 / 0.60 (est.) | 2 (30 máx) a 10 V | 70 a 0 V; 25 a 3 V | 4×10⁻¹⁴ | 1.37 [D] |
| Hamamatsu S1223 | PIN | 6.6 | 0.51 / 0.53 / 0.55 (interp.) | 0.1 (10 máx) a 20 V | 10 a 20 V | 9.4×10⁻¹⁵ | 15 [E] |
| Hamamatsu S1223-01 | PIN | 13 | 0.51 / 0.53 / 0.55 (interp.) | 0.2 a 20 V | 20 a 20 V | 1.3×10⁻¹⁴ | 18.85 [D] |
| TI OPT101P | PIN + TIA | 5.2 | 0.53 / 0.57 / 0.60 (est.) | 0.0025 | 1200 (interna) | solo gráfica | 11.17 [D] |

- La responsividad del S1223 está tabulada a 660, 780, 830 y 960 nm (0.45, 0.52, 0.54 y 0.60 A/W); los valores de la tabla son interpolación lineal. Para el BPW34 solo hay un punto (0.67 A/W equivalentes a 950 nm) y para el OPT101 otro (0.45 A/W a 650 nm): sus columnas son estimaciones con ±10 %.
- OPT101: ganancia interna de 10⁶ V/A, 14 kHz de ancho de banda, 300 µVrms de ruido de salida (0.1 Hz a 20 kHz) y 7.5 mV de offset en oscuridad. Con resistencia externa de 10 MΩ el ancho de banda baja a 1.8 kHz. Es la vía más simple, pero la ganancia fija limita el intervalo de 10 a 45 mm.
- La capacitancia del BPW34 sin polarizar (70 pF) penaliza el ruido; con 3 V de polarización inversa baja a 25 pF a cambio de corriente de oscuridad.

## C. Amplificador de transimpedancia discreto

| Parte | Ib (pA) | en (nV/√Hz) | in (fA/√Hz) | GBW (MHz) | Cin (pF) | Alimentación (V) | Iq (mA) | Precio |
|---|---|---|---|---|---|---|---|---|
| TI OPA380 | 3 (50 máx) | 67 a 10 kHz; 5.8 sobre 1 MHz | 10 | 90 | 4.1 | 2.7–5.5 | 7.5 | 9.01 [D] |
| ADI ADA4530-1 | 0.001 (0.02 máx) | 14 a 10 kHz | 0.07 | 2 | 8 | 4.5–16 | 0.9 | 22 [E] |
| ADI LTC6268 | 0.003 | 4.3 a 1 MHz | 5.5 | 500 | 0.45 | 3.1–5.25 | 16.5 | 9.5 [E] |

**Fórmulas de diseño.** Con Rf y Cf en la realimentación y Cin = C del fotodiodo + C de entrada del amplificador:

1. Ganancia: Vout = Ipd · Rf.
2. Polo de realimentación: fp = 1 / (2π · Rf · Cf).
3. Respuesta máximamente plana (Butterworth, Q = 0.707): Cf ≈ √(Cin / (π · Rf · GBW)).
4. Ancho de banda resultante: f₋₃dB = √(GBW / (2π · Rf · Cin)).
5. Estabilidad: Cf igual o mayor que el valor de (3); un Cf mayor da más margen de fase y menos ancho de banda, que queda fijado por (2).
6. Ganancia de ruido: 1 + Rf/Rsh en baja frecuencia y 1 + Cin/Cf en alta frecuencia.
7. Densidad de ruido de corriente referida a la entrada: iₙ² = 2q(Ipd + Id) + 4kT/Rf + in² + (en/Rf)² + (en · 2π · f · Cin)². Promediado en una banda de 0 a F, el último término vale (en · 2π · Cin · F)²/3.

Origen: la relación (4) está en la nota de aplicación SBOA122 de TI como GBP = 2π·Rf·Cs·f² (ecuación 12), junto con el polo, el cero y los términos de ruido (ecuación 13); la ganancia de ruido y el ruido de disparo, en la hoja del ADA4530-1 (ecuaciones 21 a 28). La forma cerrada (3) la escribo de memoria: la extracción del texto estaba dañada y conviene cotejarla con el PDF.

**Ejemplo (BPW34 sin polarizar + OPA380, Rf = 1 MΩ).** Cin = 74 pF. La condición (3) da Cf mínimo de 0.5 pF y (4) da 440 kHz, muy por encima de lo necesario. Con Cf = 10 pF el polo queda en 15.9 kHz. Ruido: térmico de Rf, 0.13 pA/√Hz; de disparo, 0.18 pA/√Hz con 100 nA y 0.06 con 10 nA; corriente del amplificador, 0.01; término en·Cin, 0.03 pA/√Hz a 1 kHz y 0.31 a 10 kHz. Conclusión: limitar la banda a pocos kHz o polarizar el fotodiodo; el piso térmico equivale a un NEP de 0.22 pW/√Hz a 850 nm, y con Rf = 10 MΩ baja a 0.07 pW/√Hz.

## D. Front-end analógico integrado

| Parte | Canales LED / I máx | Entradas | TIA | ADC | Rango dinámico | Luz ambiente | Muestreo (Hz) | Interfaz | Precio |
|---|---|---|---|---|---|---|---|---|---|
| TI AFE4404 | 3 / 100 mA (6 bits) | 1 | 10 kΩ–2 MΩ | 22 bits | 100 dB | DAC de ±7 µA y fase de ambiente | 10–1000 | I²C | 6 [E] |
| ADI ADPD4100 / 4101 | 8 / 200 mA | 8 (2 canales simultáneos) | 12.5–200 kΩ | 14 bits con integración | 100 dB (80 pulsos) | 60 dB, cc a 1 kHz | 0.004–9000 | SPI / I²C | 10 [E] |
| ADI MAX86141 | 3 / 124 mA (8 bits) | 2 simultáneas | integrador de carga | 19 bits | más de 90 dB | más de 70 dB a 120 Hz | 8–4096 | SPI | 10 [E] |

- El AFE4404 tiene justo tres canales de LED y consume menos de 0.7 mA, pero admite un solo fotodiodo y opera de −20 a 70 °C.
- El ADPD4101 es el más flexible para varias distancias (ocho entradas, 12 ranuras de tiempo).
- Los tres vienen en encapsulados de bolas con paso de 0.4 a 0.5 mm: para un prototipo manual hace falta una placa de evaluación o ensamblaje externo. Para el AFE4404 solo se vio un anuncio "desde 2.84 USD" sin cantidad.

## E. Microcontrolador y resto del sistema

| Parte | ADC interno | Radio | Consumo | Placa y precio |
|---|---|---|---|---|
| Nordic nRF52840 | SAR de 12 bits, 200 ksps, 8 canales | BLE 5 | 4.8 mA en transmisión a 0 dBm; 1.5 µA en reposo | Seeed XIAO nRF52840, 11.10 [D] |
| Espressif ESP32-C3 | 2 SAR de 12 bits, 100 ksps; INL ±12 LSB | BLE 5 | 17–28 mA en modem-sleep; 5 µA en deep-sleep | DevKitM-1 o XIAO ESP32C3, 8 [E] |
| Nordic nRF52832 | SAR de 12 bits (de memoria) | BLE 5 | sin verificar | 15 [E] |
| ST STM32WB55 | SAR de 12 bits (de memoria) | BLE 5 | sin verificar | P-NUCLEO-WB55, 45 [E] |

- **Elección:** nRF52840 en placa XIAO (21 × 17.5 mm), que ya incluye cargador de litio BQ25101 y antena. El ESP32-C3 es más barato pero consume un orden de magnitud más y su ADC es poco lineal.
- **ADC externo.** Con 12 bits internos el paso de cuantización no cubre el rango dinámico entre 10 y 45 mm. ADS1220: 24 bits, sigma-delta, 2 kSPS, 4 entradas multiplexadas, 2.3–5.5 V, 9.26 USD [D], sin existencias en Digi-Key el día de la consulta (reposición anunciada para marzo de 2027). Alternativas no verificadas: ADS1115 (16 bits, 860 SPS, I²C) y ADS131M04 (24 bits, 4 canales simultáneos).
- **Fuente de corriente para LED.** Un sumidero por canal con amplificador operacional, MOSFET y resistencia de medida, con consigna de un DAC de 12 bits; 5 a 50 mA en pulsos de 1 a 2 ms. Propuesta genérica, sin números de parte verificados.
- **Alimentación.** Celda LiPo de unos 400 mAh, cargador de la placa y un regulador lineal de bajo ruido de 3.3 V para la parte analógica. El OPA380 (7.5 mA por canal) domina el consumo.
- **Mecánica y óptica.** PCB rígida de 2 capas para el primer prototipo (la flexible cuesta de 3 a 5 veces más); carcasa impresa en material negro opaco; barrera de espuma o silicona negra entre emisores y detectores, con los componentes ópticos en contacto con la piel para evitar el acoplamiento directo. El rechazo de luz ambiente se confía a una ranura oscura por ciclo; el filtro pasa-largo es opcional y no tiene número de parte verificado.

## Arquitectura recomendada (discreta)

```
LiPo 3.7 V -> cargador BQ25101 (placa XIAO) -> 3.3 V digital
                                            -> regulador de bajo ruido -> 3.3 V analógico

nRF52840 --I2C--> DAC --> 3 sumideros de corriente --> LED 760 | LED 810 | LED 850
   |  (temporizador: ranuras 760, 810, 850 y oscuridad)        (LED760-01AU, LED810-01AU, VSMY2850G)
   |                                                                    |
   |                                              tejido (bíceps), 10 a 45 mm
   |                                                                    v
   |<--SPI-- ADS1220 (24 bits) <-- paso bajo RC <-- 2 x OPA380 <-- 2 x BPW34 (corta y larga)
   |                                                 Rf conmutable 1 / 10 MΩ, Cf 10 pF
   +--BLE 5--> PC o teléfono (10 a 50 Hz por longitud de onda)
```

Parámetros para el simulador: 8 a 11 mW por LED a 20 mA, FWHM de 30 a 35 nm, 0.50 a 0.60 A/W, piso de 0.13 pA/√Hz con 1 MΩ, polo del TIA en 15.9 kHz y cuantización de 24 bits (un ADC multiplexado obliga a esperar el asentamiento en cada ranura).

## Arquitectura alternativa integrada

```
LiPo -> regulador de 1.8 V (AVDD/DVDD) y 3.3 V (LED, E/S)
nRF52840 --I2C--> ADPD4101 --> drivers internos --> LED 760 | 810 | 850
                      ^--- entradas IN1..IN4 <--- 2 x BPW34 (corta y larga)
            (TIA 12.5 a 200 kΩ, integración de pulsos, rechazo de ambiente de 60 dB)
nRF52840 --BLE 5--> PC o teléfono
```

Ahorra el TIA, el ADC y la fuente de corriente (unos 32 USD de la lista) y reduce el consumo, a cambio de un encapsulado difícil de soldar, ganancia máxima de 200 kΩ (compensada con integración de muchos pulsos) y un modelo de ruido menos transparente. Variante más simple: AFE4404 con un solo fotodiodo.

## Lista de materiales (1 unidad, arquitectura discreta)

| Concepto | Parte | Cant. | Unitario (USD) | Subtotal | Origen |
|---|---|---|---|---|---|
| LED de 760 nm | Roithner LED760-01AU | 1 | 5.00 | 5.00 | [E] |
| LED de 810 nm | Roithner LED810-01AU | 1 | 5.00 | 5.00 | [E] |
| LED de 850 nm | Vishay VSMY2850G | 1 | 1.17 | 1.17 | [D] Digi-Key, 1.63 CAD |
| Fotodiodo PIN | Vishay BPW34 | 2 | 1.37 | 2.74 | [D] Digi-Key, USD |
| TIA | TI OPA380AIDGKT | 2 | 9.01 | 18.02 | [D] Digi-Key, 12.52 CAD |
| ADC de 24 bits | TI ADS1220IPWR | 1 | 9.26 | 9.26 | [D] Digi-Key, USD |
| Placa MCU con BLE | Seeed XIAO nRF52840 | 1 | 11.10 | 11.10 | [D] Kiwi Electronics, 9.49 EUR |
| Fuente de corriente de LED | genérica | 1 | 5.00 | 5.00 | [E] |
| Regulador de bajo ruido | genérico de 3.3 V | 1 | 1.00 | 1.00 | [E] |
| Batería LiPo de 400 mAh | genérica | 1 | 7.00 | 7.00 | [E] |
| PCB rígida de 2 capas | a pedido | 1 | 15.00 | 15.00 | [E] |
| Carcasa 3D y barrera óptica | propia | 1 | 5.00 | 5.00 | [E] |
| Pasivos, conectores, correa | varios | 1 | 8.00 | 8.00 | [E] |
| **Total nominal** | | | | **93.29** | |

De ese total, 42.29 USD (45 %) son precios vistos en distribuidor y 51.00 USD son estimaciones. **Rango: 65 a 160 USD.** El extremo alto supone el emisor de tres chips MTMD7885N24, fotodiodos S1223-01, PCB flexible y gastos de envío e importación a México. No incluye herramientas ni mano de obra.

## F. Equipos y proyectos de referencia

| Equipo | λ (nm) | Distancias (mm) | Muestreo (Hz) | Verificado |
|---|---|---|---|---|
| Artinis PortaMon | 760, 850 | 30, 35, 40 | 0.1–10 | sí (folleto del fabricante, versión antigua) |
| Moxy Monitor | 680, 720, 760, 800 | 12.5, 25 | 2 | sí (artículo comparativo en J. Biomed. Opt.) |
| Artinis PortaLite | 760, 850 | 30, 35, 40 | 50 | no (de memoria) |
| Train.Red FYER / PLUS | no publicado | no publicado | 10 / 100 | no (reseña de terceros) |
| Humon Hex | sin datos | sin datos | sin datos | no; descontinuado en 2020 |
| Hamamatsu NIRO-200NX | 735, 810, 850 | sin datos | sin datos | no (de memoria) |
| ninjaNIRS (hardware abierto) | 730, 850 | variable | sin datos | sí |

El PortaMon usa tres emisores de dos longitudes de onda y un fotodiodo; el Moxy, un emisor y dos detectores: son las dos geometrías que el simulador debería poder reproducir. El ninjaNIRS integra LED, fotodiodo, TIA y ADC en cada optodo y declara un NEP menor de 500 fW/√Hz y casi 140 dB de rango dinámico, una cota útil para juzgar el diseño discreto. Ningún fabricante consultado publica la potencia óptica. Existe un proyecto openNIRS en SourceForge que no se revisó.

## G. Seguridad óptica y térmica

- **Límite para la piel (ICNIRP 2013, ecuación 22; IEC 62471 adopta el mismo criterio).** Lesión térmica, longitudes de onda menores de 3000 nm: H = 2.0×10⁴ · t^0.25 J/m² para t ≤ 10 s. Para exposiciones más largas la guía no da un valor numérico y remite al estrés térmico.
- **Cálculo orientativo.** A 10 s el límite es 35 566 J/m², equivalente a 3557 W/m² (356 mW/cm²) de irradiancia media. Tres LED de 10 mW de pico con ciclo del 25 % suman 7.5 mW medios; sobre una mancha de 3 mm de diámetro son 1061 W/m², un 30 % de ese valor, y sobre 5 mm, 382 W/m².
- **Ojo, con el sensor sin colocar.** El límite para córnea y cristalino (780–3000 nm, peso 0.3 por debajo de 1000 nm) es de 100 W/m² para más de 1000 s. Un VSMY2850G a 100 mA (125 mW/sr) produce 3.1 W/m² a 200 mm, 0.94 W/m² ponderados.
- **Calentamiento.** A 20 mA y 25 % de ciclo cada LED disipa unos 8 mW; con 250 K/W la unión sube unos 2 K y la emisión se desplaza unos 0.5 nm. A 100 mA en continuo serían 160 mW, unos 40 K y 10 nm: operar en pulsos, por debajo de 50 mA.
- **Sin verificar:** el texto de IEC 62471 (norma de pago), el límite de 43 °C de contacto de IEC 60601-1, el área de promediado sobre la piel y el estudio de Bozkurt y Onaral (2004) sobre calentamiento por conducción.

## Pendientes de verificación

1. Precios y disponibilidad de los LED de Roithner (hojas de 2010 y 2014 leídas en copias de terceros) y ángulo de emisión de los sufijos -01AU.
2. Potencia y FWHM de los Marktech MTE1077N1-R y MTE2081S-OH5.
3. Responsividad a 760, 810 y 850 nm de BPW34 y OPT101 (estimada) y del S1223 (interpolada).
4. Número de parte y vigencia de un emisor Ushio de 760/810/850 nm.
5. Especificaciones de nRF52832, STM32WB55, ADS1115 y ADS131M04, y los precios marcados [E].
6. Forma exacta de la expresión de Cf en SBOA122 y en la hoja del OPA380.
7. Datos de PortaLite, Train.Red, Humon Hex y NIRO-200NX.

## Fuentes

- Roithner LED760: https://dtsheet.com/doc/1336610/led760-series
- Roithner SMB1N-760D: https://dtsheet.com/doc/1336171/smb1n-760d
- Roithner LED810: https://pdf.jiepei.com/led810-02au-33102841.html
- Marktech MTMD7885N24: https://specs.marktechopto.com/pdf/optrans/MTMD7885N24.pdf
- Marktech MTMD7885T38: https://specs.marktechopto.com/pdf/optrans/MTMD7885T38.pdf
- Marktech, catálogo multi-longitud de onda: https://marktechopto.com/marktech-emitters/multi-wavelength-emitters/
- Digi-Key MTMD7885N24: https://www.digikey.de/en/products/detail/marktech-optoelectronics/MTMD7885N24/4746372
- Digi-Key MTE1077N1-R: https://www.digikey.com/en/products/detail/MTE1077N1-R/1125-1081-ND/3516637
- Digi-Key MTE2081S-OH5: https://www.digikey.it/en/products/detail/marktech-optoelectronics/MTE2081S-OH5/24765598
- OSRAM SFH 4780S: https://nonprod.docs.rs-online.com/a4f4/0900766b813dd148.pdf
- OSRAM SFH 4250: https://www.komponenten.es.aau.dk/fileadmin/komponenten/Data_Sheet/SMD_Data/Dioder/SFH4250.pdf
- Luminus SST-10-IRD 810: https://download.luminus.com/datasheets/Luminus_SST-10-IRD-BxxH_810_Datasheet.pdf
- Vishay VSMY2850G: https://media.onlinecomponents.com/productfiles/mf-vis/vis-vsmy2850rg-56814234.pdf
- Digi-Key VSMY2850G: https://www.digikey.ca/en/products/detail/vishay-semiconductor-opto-division/VSMY2850G/2615290
- Ushio, familia SMT: https://www.ushio.eu/smt-family/
- Vishay BPW34: https://www.farnell.com/datasheets/463636.pdf
- Digi-Key BPW34: https://www.digikey.com.mx/en/products/detail/BPW34/751-1015-ND/1681149
- Hamamatsu S1223: https://www.farnell.com/datasheets/3171157.pdf
- Farnell S1223-01: https://export.farnell.com/hamamatsu/s1223-01/photo-diode-200pa-2-pin/dp/4228551
- TI OPT101: https://www.ti.com/product/OPT101
- OPT101, hoja de datos (copia): https://people.ece.cornell.edu/land/courses/ece4760/FinalProjects/s2006/ajk28/ajk28/OPT101datasheet.pdf
- Digi-Key OPT101P: https://www.digikey.com.mx/en/products/detail/OPT101P/296-23090-5-ND/251177
- TI OPA380: https://www.ti.com/lit/gpn/opa380
- Digi-Key OPA380AIDGKT: https://www.digikey.ca/en/products/detail/texas-instruments/OPA380AIDGKT/639561
- ADI ADA4530-1: https://www.analog.com/media/en/technical-documentation/data-sheets/ADA4530-1.pdf
- ADI LTC6268: https://www.analog.com/en/products/ltc6268.html
- TI SBOA122: https://www.ti.com/lit/sboa122
- TI AFE4404: https://ti.com/lit/gpn/AFE4404
- LCSC AFE4404YZPT: https://www.lcsc.com/product-detail/C465775.html
- ADI ADPD4100/4101: https://www-cce.cldnet.analog.com/media/en/technical-documentation/data-sheets/adpd4100-4101.pdf
- MAX86140/MAX86141: https://www.farnell.com/datasheets/2580845.pdf
- Nordic nRF52840: https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/keyfeatures_html5.html
- Kiwi Electronics, XIAO nRF52840: https://www.kiwi-electronics.com/en/seeed-studio-xiao-nrf52840-11041
- Espressif ESP32-C3 (copia v1.2): https://www.scs.stanford.edu/~zyedidia/docs/pcb/esp32_c3_datasheet.pdf
- Digi-Key ADS1220IPWR: https://www.digikey.com/en/products/detail/texas-instruments/ADS1220IPWR/4307638
- Artinis PortaMon, folleto: https://www.ntnu.edu/documents/221360533/1261844786/PortaMon+Leaflet+-+ver1205.pdf/2192e225-05b4-4f4b-95e6-6adc667570cf
- Comparación MOXY y PortaMon, J. Biomed. Opt. 23(1), 015007: https://journals.spiedigitallibrary.org/journals/journal-of-biomedical-optics/volume-23/issue-01/015007/Performance-comparison-of-the-MOXY-and-PortaMon-near-infrared-spectroscopy/10.1117/1.JBO.23.1.015007.full
- Reseña de sensores de oxígeno muscular: https://the5krunner.com/muscle-oxygen-sensors/
- Train.Red, Proc. SPIE 12375, 123750A: https://electronicimaging.spiedigitallibrary.org/conference-proceedings-of-spie/12375/123750A/Assessing-stability-and-accuracy-of-a-novel-commercial-wearable-near/10.1117/12.2657434.full
- ninjaNIRS (von Lühmann et al., 2020): https://sites.bu.edu/nil/files/2020/04/AlexanderOSA.pdf
- openNIRS: https://sourceforge.net/p/opennirs/
- ICNIRP 2013: https://www.icnirp.org/cms/upload/publications/ICNIRPVisible_Infrared2013.pdf
