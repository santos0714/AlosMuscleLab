# Fisiología muscular y NIRS para MuscleSense Lab (bíceps braquial)

Dossier del Biomedical Agent. Las claves entre corchetes remiten a la lista final y a `parametros_fisiologicos.json`. Los metadatos y resúmenes se consultaron en PubMed; cada referencia lleva su DOI. **(nv)** significa *no verificado*: valor de memoria o derivado por mí, no leído en la fuente. Cuando el dato no es de flexores del codo se indica el músculo.

## A. Composición y geometría

| Magnitud | Nominal (rango) | Contexto | Fuente |
|---|---|---|---|
| Piel (epidermis + dermis) | 2.0 mm (1.5–2.6) | Brazo 2.2 mm; deltoides 2.02; muslo 1.55; sin dato específico de la cara anterior | [gibney2010] [laurent2007] |
| ATT sobre el bíceps | 3.0 ± 0.3 mm (1.5–9) | Ecografía, 8 hombres jóvenes; el rango viene del antebrazo de 78 sanos (1.4–8.9 mm) | [muthalib2016] [vanbeekvelt2001_att] |
| Efecto de sexo y adiposidad | +5.1 mm en mujeres; +4 mm por cada 10 kg/m² | Grasa subcutánea del brazo en adultos con diabetes (media 10.8 mm) | [gibney2010] |
| Grosor del bíceps | 20 mm (12–35) (nv) | Normativos por sexo y edad sin cifras en el resumen | [arts2010] |
| Hb en sangre | 15 g/dL (12–17.5) (nv) | 2.33 mM de tetrámero, 9.3 mM de hemo | [beutler2006] |
| Fracción de sangre en músculo | 0.03 (0.015–0.05) (nv) | Reposo | [davis2013] |
| tHb tisular (solo Hb) | ~70 µM de tetrámero (nv) | Derivado: 0.03 × 2.33 mM | — |
| total-[Hb+Mb] por FD-NIRS | 372–620 µM a ATT = 0 | Cuatro músculos en reposo; bíceps en contracción 225–264 µM de hemo | [craig2017] [sears2024] |
| SaO2 | > 0.97 | Normoxia | [millet2012] |
| SvO2 muscular en reposo | 0.70 (0.55–0.80) (nv) | — | — |
| SmO2/TSI en reposo | 0.68 (0.55–0.80) (nv) | Depende del equipo y del ATT | [niemeijer2017] |
| Mioglobina | 4.7 mg/g = 0.28 mmol/kg | Músculo de la pierna, n = 31, sin diferencia por sexo | [moller1981] |
| P50 y n de Hb | 26.9 mmHg; n ≈ 2.7 | S = 1/(23400/(PO2³ + 150·PO2) + 1) | [severinghaus1979] |
| P50 de Mb | 2.39 mmHg (37 °C, pH 7.0); 3.2 en 1H-MRS | Hill n = 1 | [schenkman1997] [richardson1995] |
| SMbO2 en reposo | 0.91 (PO2 intracelular 34 ± 6 mmHg) | 1H-MRS a 4 T, cuádriceps | [richardson2006] |
| SMbO2 en ejercicio intenso | 0.49 (0.40–0.55) | Desde el 50 % del VO2máx; PO2 3.1 mmHg | [richardson1995] [mole1999] |
| Agua: piel / grasa / músculo | 0.65 / 0.21 / 0.74 (nv) | Fracción de masa | [woodard1986] |
| Lípido: grasa / músculo | 0.74 / 0.04 (nv) | Fracción de masa | [woodard1986] |
| Sangre en dermis | 0.2 % promedio; 2–5 % en el plexo | Nota técnica web | [jacques1998] |
| Sangre en grasa | 0.5 % (nv) | Supuesto de modelado | — |
| Melanosomas en epidermis | 1.3–6.3 % clara; 11–16 % media; 18–43 % oscura | Asignación a fototipos I–II, III–IV, V–VI: supuesto | [jacques1998] |

Notas. (1) La convención habitual es ATT = pliegue/2 (nv), que incluye la piel. (2) Ex vivo, la grasa absorbe cerca de la mitad que la dermis (633 nm: 0.013 frente a 0.033 mm⁻¹) [simpson1998]. (3) La desaturación de Mb aparece en los primeros 20 s de ejercicio y se mantiene constante hasta el máximo [richardson1995]. (4) No encontré ATT bicipital verificado en mujeres ni por nivel de adiposidad.

## B. Contribución de hemoglobina y mioglobina a la señal

| Estudio | Método | Fracción atribuida a Mb |
|---|---|---|
| [seiyama1988] | Extremidad de rata perfundida | < 10 % (Mb + citocromos) |
| [mancini1994] | 1H-MRS en antebrazo | Señal "principalmente Hb": con 80 ± 7 % de desoxigenación NIRS solo un sujeto mostró desoxi-Mb |
| [lai2009] | Modelo de transporte de O2 | Hb y Mb comparables |
| [davis2013] | Cálculo químico-morfométrico | 50–70 % en reposo; ~70 % del cambio reposo→pico |
| [marcinek2007] | Desplazamiento del pico de 760 nm | ~80 % en humano (Hb ≈ 20 %); en ratón Hb ≈ 80 % |
| [tran1999] [bendahan2017] | 1H-MRS + NIRS simultáneos | Predominio de Mb |

**A favor de Hb:** la absorción 760–800 nm sigue a la saturación venosa (r = 0.92) y responde a vasodilatadores y vasoconstrictores [mancini1994]; con P50 de 2.4 mmHg la Mb apenas se desatura mientras la PO2 capilar supere ~20 mmHg. **A favor de Mb:** la 1H-MRS moderna muestra ~50 % de desaturación de Mb ya a intensidad moderada; la cinética de desoxi-Mb coincide con la de NIRS [tran1999]; y por contenido de hemo ambas reservas son similares: 0.28 mmol/kg de Mb frente a 0.03 × 9.3 mM ≈ 0.28 mM de hemo-Hb (nv, depende de la fracción de sangre). Además, el aumento de tHb en ejercicio (hasta 30 %) se explica por el hematocrito microvascular [davis2013].

**Por qué un equipo CW de 2–3 longitudes de onda no las separa.** Los espectros de Hb y Mb son casi idénticos en el infrarrojo cercano; la única diferencia aprovechable es un desplazamiento pequeño del pico desoxi cerca de 760 nm, que exige espectro continuo [marcinek2007]. Con tres LED hay cuatro incógnitas (HbO2, HHb, MbO2, Mb) más el camino óptico. El equipo solo puede informar oxi- y desoxi-[Hb+Mb]; las revisiones lo mantienen como cuestión abierta [ferrari2011] [jones2016] [barstow2019]. En el simulador conviene modelar ambos compartimentos y tratar la fracción de Mb (0.1–0.8) como parámetro incierto.

## C. Dinámica durante y después del ejercicio

| Magnitud | Valor | Músculo y condición | Fuente |
|---|---|---|---|
| mVO2 en reposo | 0.11 ± 0.04 mL O2/min/100 g (≈ 0.8 µM O2/s); 4.6 ± 1.3 µmol/100 mL/min | Antebrazo | [vanbeekvelt2001_att] [deblasi1994] |
| mVO2 en reposo (relativo) | 0.52–0.77 %/s | Vasto lateral | [brizendine2013] |
| mVO2 frente a intensidad | 0.036, 0.054, 0.062 y 0.067 mM ATP/s a 10, 20, 30 y 40 % MVC | Handgrip dinámico; la relación satura | [hamaoka1996] |
| mVO2 máximo local | ×5 (isométrico sostenido); ×25 al final de 10 s de MVC | Flexores de los dedos | [vanbeekvelt2001_perf] [kime2003] |
| Flujo en reposo | 1.28 ± 0.82 y 1.9 ± 0.8 mL/min/100 mL | Antebrazo | [vanbeekvelt2001_att] [deblasi1994] |
| Flujo tras ejercicio | 8.2 ± 2.9 mL/min/100 mL; ×3 tras 10 s de MVC | Antebrazo | [deblasi1994] [kime2003] |
| Oclusión por presión intramuscular | 50–64 % MVC | Flexión de codo, rodilla y tobillo | [sadamoto1983] |
| Flujo suficiente | < 10 % MVC sostenido | Rodilla, mano y bíceps | [sjogaard1988] [blangsted2005] |
| Retraso y τ de desoxigenación | 6–13 s y 7–10 s | Vasto lateral, ciclismo | [delorey2003] [grassi2003] |
| Reoxigenación | τ 27.6–29.4 s (t½ ≈ 19–20 s); t½ 13.8 s tras oclusión; 10–80 s en remeros | Pantorrilla, cuádriceps | [mccully1994] [walsh2001] [chance1992] |
| Tasa de reoxigenación | 0.53–12.47 %/s tras 10 s de MVC | Flexores de los dedos | [kime2003] |
| Sobreimpulso de tHb y duración | ~10 % y 1–3 min (nv) | Fenómeno descrito, magnitud no hallada | [bopp2011] |
| τ de recuperación del mVO2 | 31.5 ± 8.9 s; 18.4 s (atletas) frente a 32.4 s (inactivos); ~38 s en muñeca | Gastrocnemio, vasto lateral, flexores de muñeca | [ryan2013_xval] [brizendine2013] [southern2015] |
| τ de PCr | 31.5 ± 8.5 s; 36.0 s submáximo y 68.3 s con pH < 6.8; 17.8–38.3 s | Pantorrilla, dedos | [ryan2013_xval] [mccully1994] [kime2003] |
| Consumo elevado posejercicio | Deuda de 0.55 L O2/kg de músculo en 60 min; PCr al 40 % y 85 % a los 3 y 10 min | Cuádriceps, ejercicio exhaustivo | [bangsbo1990] |

Durante la contracción isométrica del bíceps al 10 % MVC la presión intramuscular se cuadruplica desde 12.2 mmHg y la oxigenación cae 6.9 % para volver al nivel de reposo en 1 min [blangsted2005]; en contracciones máximas el total-[hemo] disminuye en cada contracción [sears2024]. Por encima del umbral de oclusión la desaturación es casi lineal y su pendiente equivale al mVO2. La forma de la restricción entre 10 y 50 % MVC es un supuesto.

La τ del mVO2 (protocolo de oclusiones repetidas) coincide con la de PCr (r = 0.88–0.95) [ryan2013_xval] y con la respirometría en fibras (r = 0.61–0.74) [ryan2014]; exige corregir el volumen sanguíneo y la calibración isquémica elimina el efecto del ATT [ryan2012]. Es un índice de capacidad oxidativa, no de recuperación funcional. No hallé τ de mVO2 en bíceps.

## D. Recuperación del rendimiento frente a reoxigenación

| Componente | Curso temporal | Fuente |
|---|---|---|
| Rápida: central y metabólica | Fatiga central ~2 min; periférica ligada a reperfusión 3–5 min; fuerza y Pi ~5 min tras 2 min de MVC; torque al 101.8 % a los 300 s tras 30 s de MVC | [carroll2017] [baker1993] [ufland2012] |
| Lenta: acoplamiento excitación-contracción | Fatiga más allá de 15 min tras ejercicio largo; eficiencia neuromuscular sin recuperar a los 60 min; horas a baja frecuencia | [baker1993] [miller1987] [edwards1977] |
| Flexores del codo, 43 min al 15 % MVC | MVC al 58.6 ± 14.5 %; vuelve solo a ~85 %; el twitch no se recupera | [sogaard2006] |
| Daño excéntrico de flexores del codo | −57 % inmediato; 67 % de recuperación a las 132 h; ~10 días; 33–47 días en casos extremos | [sayers2001] [clarkson1992] |
| pH y Pi | pH de 7.1 a 6.4, recuperado en < 20 min; Pi en ~5 min | [miller1987] [baker1993] |
| W′ | 37, 65 y 86 % a los 2, 6 y 15 min; t½ 234 ± 32 s (VO2: 74 s; lactato: 1366 s) | [ferguson2010] [skiba2012] |

Las constantes del modelo (τ rápida ~90 s, τ lenta ~1 h, fracción lenta ~0.3, τ de pH ~400 s) son ajustes míos a estas observaciones (nv).

**Evidencia de disociación**

- Bíceps, 10 min al 10 % MVC: la oxigenación vuelve al reposo en 1 min mientras los signos EMG y mecanomiográficos de fatiga persisten 30 min [blangsted2005].
- La resaturación tiene la misma τ tras ejercicio submáximo y máximo (27.6 y 29.4 s) aunque la τ de PCr pasa de 36 a 68 s [mccully1994].
- Tras 10 s de MVC, reoxigenar más rápido corresponde a *menor* capacidad oxidativa (r² = 0.939 con la τ de PCr) [kime2003].
- La oxigenación explica ~10 % de la varianza del torque recuperado (r = 0.32) [ufland2012]; la perfusión es necesaria (88.6 % con oclusión frente a 101.8 %; sin recuperación en isquemia [gandevia1996]) pero no suficiente.
- La fatiga lenta no depende de fosfatos ni de pH [edwards1977] [miller1987] [allen2008].

**Variables NIRS que sí cambian con daño**

- Bíceps tras 70 contracciones excéntricas: saturación de reposo +22 % aguda y +5 a +9 % durante 6 días; cinéticas de desaturación y resaturación reducidas 6 días; flujo y VO2 elevados solo el primer día [ahmadi2008].
- La caída de TOI durante tareas máximas disminuye 1–4 días, en paralelo a la pérdida de torque; al 30 % MVC no cambia [muthalib2010_ecc] [muthalib2011_rbe].
- Cuádriceps a las 48 h: tiempo medio de respuesta de [HHb] de 14 ± 3 a 19 ± 3 s [davies2008].
- Resultados negativos: sin cambios de [HHb] ni TSI a las 48 h, aunque la dilatación mediada por flujo local baja de 6.75 a 4.01 % [caldwell2016]; sin cambios en tiempos medios de desaturación ni resaturación [walsh2001].

## E. Metodología NIRS muscular

**Efecto del ATT.** El mVO2 aparente cae con el ATT (r = −0.70); los diez sujetos más delgados duplican a los diez con más grasa [vanbeekvelt2001_att]. In vitro, con 14 mm de grasa la sangre al 100 % se lee 74 % y al 0 % se lee 68 % [niemeijer2017]. El total-[Hb+Mb] pierde 26–54 µM por milímetro según el músculo [craig2017]. Moxy y PortaMon coinciden con ATT < 7 mm y difieren 14.7 % por encima de 10 mm [mcmanus2018]. El ATT altera amplitudes (r = 0.86–0.89) pero no constantes de tiempo [bopp2011]. Correcciones propuestas: calibración fisiológica con isquemia [ryan2012], factores por músculo [craig2017], excluir sitios con ATT superior al 60 % de la separación [feldmann2019] y varias distancias o métodos resueltos en tiempo [hamaoka2011]; ver también [homma1996].

**DPF.** Antebrazo adulto a 807 nm: 4.16 ± 18.8 %; pantorrilla 5.51; constante para separaciones mayores de 2.5 cm; varía con la longitud de onda y el sexo [duncan1995] [vanderzee1992].

**Revisiones.** Cuestiones abiertas: capa de grasa, mioglobina, cambios de esparcimiento y perfusión cutánea [ferrari2011] [jones2016]; la variable interpretable es la extracción fraccional de O2 [grassi2016]; buenas prácticas de reproducibilidad [barstow2019]; uso en deporte y precauciones del método de oclusiones [perrey2018] [adami2018].

| Equipo | Longitudes de onda | Distancias | Muestreo | Fuente |
|---|---|---|---|---|
| PortaMon | 760 y 850 nm | 30, 35 y 40 mm | 0.1–10 Hz; CW + SRS | [artinis_portamon] |
| Moxy | Cuatro (680–800 nm, nv) | 12.5 y 25 mm | 0.5 Hz; Monte Carlo por capas | [feldmann2019] [crum2017] |
| Humon Beta | (nv) | 12, 18 y 24 mm | (nv) | [farzam2018] |
| NIRO-200 | 775, 810 y 850 nm (nv) | 40 mm | 6 Hz en bíceps; SRS | [muthalib2016] |
| Oxymon MkIII | (nv) | (nv) | (nv) | — |

Los LED de 760, 810 y 850 nm de MuscleSense reproducen la combinación clásica: desoxi dominante, casi isosbéstico (~800 nm [mancini1994]) y oxi dominante.

## Implicaciones para el modelo

**Variables de estado recomendadas**

1. Demanda metabólica (PCr): primer orden, τ ≈ 30 s, enlentecida por el pH [meyer1988] [mccully1994]. De ella sale el mVO2: 0.8 µM O2/s en reposo, ×5 a ×25 en ejercicio.
2. Flujo: 1.3–1.9 mL/min/100 mL en reposo, multiplicado por un factor de compresión que vale 1 hasta 10 % MVC y 0 entre 50 y 64 % MVC.
3. Volumen sanguíneo (tHb): cae en la contracción y rebota después.
4. Reservas de O2: saturación microvascular de Hb (Severinghaus) y de Mb (P50 2.39–3.2 mmHg), con fracción de Mb incierta.
5. pH: variable lenta (minutos).
6. Rendimiento: fatiga rápida, fatiga lenta y daño, cada una con su escala (minutos, horas, días).

**Acoplamientos con respaldo cuantitativo**

- Intensidad → mVO2 y restricción de flujo → desaturación.
- τ de mVO2 ≈ τ de PCr; acidosis → τ de PCr de 36 a 68 s.
- Perfusión → recuperación rápida de la fuerza (88.6 frente a 101.8 % a los 300 s).
- Daño excéntrico → saturación de reposo +5 a +9 % durante 6 días y menor desaturación en contracciones máximas, esta última mediada por la pérdida de fuerza.
- Daño → respuesta de [HHb] ~5 s más lenta a las 48 h (cuádriceps, hallazgo no universal).

**Supuestos (sin respaldo directo)**

- Forma del factor de compresión entre 10 y 50 % MVC.
- Magnitud y duración del sobreimpulso hiperémico.
- τ de pH, τ y fracción de las componentes de la fuerza.
- Valores de bíceps tomados de antebrazo, pantorrilla o cuádriceps.
- Cualquier efecto de la fatiga lenta sobre flujo, mVO2 o SmO2: no hallé evidencia; por defecto debe ser nulo.

**Disociación.** El simulador debe poder generar casos en que SmO2 vuelve a la línea base en 1–3 min mientras la MVC sigue al 85 % o menos durante 30 min o más, y casos con daño en que SmO2 de reposo sube aunque la fuerza esté deprimida. Un estimador de recuperación basado solo en la reoxigenación fallaría en ambos; los candidatos con algún respaldo son la saturación basal, la amplitud de desaturación en una contracción estandarizada, la τ del mVO2 y la respuesta hiperémica, siempre validados contra la fuerza.

## Referencias

Títulos completos y estado de verificación en `parametros_fisiologicos.json`.

- [adami2018] Adami A et al. (2018). J Appl Physiol 124(1):245-248. https://doi.org/10.1152/japplphysiol.00445.2017. PMID 28684592.
- [ahmadi2008] Ahmadi S et al. (2008). Appl Physiol Nutr Metab 33(4):743-52. https://doi.org/10.1139/h08-048. PMID 18641718.
- [allen2008] Allen DG et al. (2008). Physiol Rev 88(1):287-332. https://doi.org/10.1152/physrev.00015.2007. PMID 18195089.
- [artinis_portamon] Artinis Medical Systems (2012). Documento del fabricante. sin DOI. sin PMID.
- [arts2010] Arts IM et al. (2010). Muscle Nerve 41(1):32-41. https://doi.org/10.1002/mus.21458. PMID 19722256.
- [baker1993] Baker AJ et al. (1993). J Appl Physiol 74(5):2294-300. https://doi.org/10.1152/jappl.1993.74.5.2294. PMID 8335559.
- [bangsbo1990] Bangsbo J et al. (1990). J Physiol 422:539-59. https://doi.org/10.1113/jphysiol.1990.sp018000. PMID 2352192.
- [barstow2019] Barstow TJ (2019). J Appl Physiol 126(5):1360-1376. https://doi.org/10.1152/japplphysiol.00166.2018. PMID 30844336.
- [bendahan2017] Bendahan D et al. (2017). Am J Physiol Regul Integr Comp Physiol 313(6):R740-R753. https://doi.org/10.1152/ajpregu.00203.2017. PMID 28877871.
- [beutler2006] Beutler E et al. (2006). Blood 107(5):1747-50. https://doi.org/10.1182/blood-2005-07-3046. PMID 16189263.
- [blangsted2005] Blangsted AK et al. (2005). Acta Physiol Scand 183(4):379-88. https://doi.org/10.1111/j.1365-201X.2005.01411.x. PMID 15799774.
- [bopp2011] Bopp CM et al. (2011). Eur J Appl Physiol 111(11):2753-61. https://doi.org/10.1007/s00421-011-1898-z. PMID 21409404.
- [brizendine2013] Brizendine JT et al. (2013). Med Sci Sports Exerc 45(5):869-75. https://doi.org/10.1249/MSS.0b013e31827e0eb6. PMID 23247709.
- [caldwell2016] Caldwell JT et al. (2016). Physiol Rep 4(22):e13032. https://doi.org/10.14814/phy2.13032. PMID 27884955.
- [carroll2017] Carroll TJ et al. (2017). J Appl Physiol 122(5):1068-1076. https://doi.org/10.1152/japplphysiol.00775.2016. PMID 27932676.
- [chance1992] Chance B et al. (1992). Am J Physiol 262(3 Pt 1):C766-75. https://doi.org/10.1152/ajpcell.1992.262.3.C766. PMID 1312785.
- [clarkson1992] Clarkson PM et al. (1992). Med Sci Sports Exerc 24(5):512-20. sin DOI. PMID 1569847.
- [craig2017] Craig JC et al. (2017). J Appl Physiol 123(6):1571-1578. https://doi.org/10.1152/japplphysiol.00207.2017. PMID 28935822.
- [crum2017] Crum EM et al. (2017). Eur J Sport Sci 17(8):1037-1043. https://doi.org/10.1080/17461391.2017.1330899. PMID 28557670.
- [davies2008] Davies RC et al. (2008). J Appl Physiol 105(5):1413-21. https://doi.org/10.1152/japplphysiol.90743.2008. PMID 18703757.
- [davis2013] Davis ML et al. (2013). Respir Physiol Neurobiol 186(2):180-7. https://doi.org/10.1016/j.resp.2013.01.012. PMID 23357615.
- [deblasi1994] De Blasi RA et al. (1994). J Appl Physiol 76(3):1388-93. https://doi.org/10.1152/jappl.1994.76.3.1388. PMID 8005887.
- [delorey2003] DeLorey DS et al. (2003). J Appl Physiol 95(1):113-20. https://doi.org/10.1152/japplphysiol.00956.2002. PMID 12679363.
- [duncan1995] Duncan A et al. (1995). Phys Med Biol 40(2):295-304. https://doi.org/10.1088/0031-9155/40/2/007. PMID 7708855.
- [edwards1977] Edwards RH et al. (1977). J Physiol 272(3):769-78. https://doi.org/10.1113/jphysiol.1977.sp012072. PMID 592214.
- [farzam2018] Farzam P et al. (2018). Physiol Rep 6(7):e13664. https://doi.org/10.14814/phy2.13664. PMID 29611324.
- [feldmann2019] Feldmann A et al. (2019). J Biomed Opt 24(11):115001. https://doi.org/10.1117/1.JBO.24.11.115001. PMID 31741352.
- [ferguson2010] Ferguson C et al. (2010). J Appl Physiol 108(4):866-74. https://doi.org/10.1152/japplphysiol.91425.2008. PMID 20093659.
- [ferrari2011] Ferrari M et al. (2011). Philos Trans A Math Phys Eng Sci 369(1955):4577-90. https://doi.org/10.1098/rsta.2011.0230. PMID 22006907.
- [gandevia1996] Gandevia SC et al. (1996). J Physiol 490(Pt 2):529-36. https://doi.org/10.1113/jphysiol.1996.sp021164. PMID 8821149.
- [gibney2010] Gibney MA et al. (2010). Curr Med Res Opin 26(6):1519-30. https://doi.org/10.1185/03007995.2010.481203. PMID 20429833.
- [grassi2003] Grassi B et al. (2003). J Appl Physiol 95(1):149-58. https://doi.org/10.1152/japplphysiol.00695.2002. PMID 12611769.
- [grassi2016] Grassi B et al. (2016). J Biomed Opt 21(9):091313. https://doi.org/10.1117/1.JBO.21.9.091313. PMID 27443955.
- [hamaoka1996] Hamaoka T et al. (1996). J Appl Physiol 81(3):1410-7. https://doi.org/10.1152/jappl.1996.81.3.1410. PMID 8889781.
- [hamaoka2011] Hamaoka T et al. (2011). Philos Trans A Math Phys Eng Sci 369(1955):4591-604. https://doi.org/10.1098/rsta.2011.0298. PMID 22006908.
- [homma1996] Homma S et al. (1996). J Biomed Opt 1(4):418-24. https://doi.org/10.1117/12.252417. PMID 23014785.
- [jacques1998] Jacques SL (1998). Oregon Medical Laser Center News (nota tecnica web, omlc.org/news/jan98/skinoptics.html). sin DOI. sin PMID.
- [jones2016] Jones S et al. (2016). Artery Res 16:25-33. https://doi.org/10.1016/j.artres.2016.09.001. PMID 27942271.
- [kime2003] Kime R et al. (2003). Eur J Appl Physiol 89(1):34-41. https://doi.org/10.1007/s00421-002-0757-3. PMID 12627303.
- [lai2009] Lai N et al. (2009). J Appl Physiol 106(6):1858-74. https://doi.org/10.1152/japplphysiol.91102.2008. PMID 19342438.
- [laurent2007] Laurent A et al. (2007). Vaccine 25(34):6423-30. https://doi.org/10.1016/j.vaccine.2007.05.046. PMID 17640778.
- [mancini1994] Mancini DM et al. (1994). J Appl Physiol 77(6):2740-7. https://doi.org/10.1152/jappl.1994.77.6.2740. PMID 7896615.
- [marcinek2007] Marcinek DJ et al. (2007). Appl Spectrosc 61(6):665-9. https://doi.org/10.1366/000370207781269819. PMID 17650380.
- [mccully1994] McCully KK et al. (1994). J Appl Physiol 77(1):5-10. https://doi.org/10.1152/jappl.1994.77.1.5. PMID 7961273.
- [mcmanus2018] McManus CJ et al. (2018). J Biomed Opt 23(1):015007. https://doi.org/10.1117/1.JBO.23.1.015007. PMID 29368457.
- [meyer1988] Meyer RA (1988). Am J Physiol 254(4 Pt 1):C548-53. https://doi.org/10.1152/ajpcell.1988.254.4.C548. PMID 3354652.
- [miller1987] Miller RG et al. (1987). Muscle Nerve 10(9):810-21. https://doi.org/10.1002/mus.880100906. PMID 3683452.
- [millet2012] Millet GY et al. (2012). J Appl Physiol 112(8):1335-44. https://doi.org/10.1152/japplphysiol.00804.2011. PMID 22323647.
- [mole1999] Mole PA et al. (1999). Am J Physiol 277(1):R173-80. https://doi.org/10.1152/ajpregu.1999.277.1.R173. PMID 10409271.
- [moller1981] Moller P et al. (1981). Scand J Clin Lab Invest 41(5):479-82. https://doi.org/10.3109/00365518109090486. PMID 7313529.
- [muthalib2010_ecc] Muthalib M et al. (2010). J Appl Physiol 109(3):710-20. https://doi.org/10.1152/japplphysiol.01297.2009. PMID 20595540.
- [muthalib2011_rbe] Muthalib M et al. (2011). J Appl Physiol 110(5):1390-9. https://doi.org/10.1152/japplphysiol.00191.2010. PMID 21330620.
- [muthalib2016] Muthalib M et al. (2016). Eur J Transl Myol 26(2):6058. https://doi.org/10.4081/ejtm.2016.6058. PMID 27478574.
- [niemeijer2017] Niemeijer VM et al. (2017). Physiol Meas 38(3):539-554. https://doi.org/10.1088/1361-6579/aa5dd5. PMID 28151429.
- [perrey2018] Perrey S et al. (2018). Sports Med 48(3):597-616. https://doi.org/10.1007/s40279-017-0820-1. PMID 29177977.
- [richardson1995] Richardson RS et al. (1995). J Clin Invest 96(4):1916-26. https://doi.org/10.1172/JCI118237. PMID 7560083.
- [richardson2006] Richardson RS et al. (2006). J Physiol 571(Pt 2):415-24. https://doi.org/10.1113/jphysiol.2005.102327. PMID 16396926.
- [ryan2012] Ryan TE et al. (2012). J Appl Physiol 113(2):175-83. https://doi.org/10.1152/japplphysiol.00319.2012. PMID 22582211.
- [ryan2013_xval] Ryan TE et al. (2013). J Appl Physiol 115(12):1757-66. https://doi.org/10.1152/japplphysiol.00835.2013. PMID 24136110.
- [ryan2014] Ryan TE et al. (2014). J Physiol 592(15):3231-41. https://doi.org/10.1113/jphysiol.2014.274456. PMID 24951618.
- [sadamoto1983] Sadamoto T et al. (1983). Eur J Appl Physiol Occup Physiol 51(3):395-408. https://doi.org/10.1007/BF00429076. PMID 6685038.
- [sayers2001] Sayers SP et al. (2001). Eur J Appl Physiol 84(1-2):122-6. https://doi.org/10.1007/s004210000346. PMID 11394240.
- [schenkman1997] Schenkman KA et al. (1997). J Appl Physiol 82(1):86-92. https://doi.org/10.1152/jappl.1997.82.1.86. PMID 9029202.
- [sears2024] Sears KN et al. (2024). Eur J Appl Physiol 125(2):353-364. https://doi.org/10.1007/s00421-024-05605-0. PMID 39251444.
- [seiyama1988] Seiyama A et al. (1988). J Biochem 103(3):419-24. https://doi.org/10.1093/oxfordjournals.jbchem.a122285. PMID 3391996.
- [severinghaus1979] Severinghaus JW (1979). J Appl Physiol Respir Environ Exerc Physiol 46(3):599-602. https://doi.org/10.1152/jappl.1979.46.3.599. PMID 35496.
- [simpson1998] Simpson CR et al. (1998). Phys Med Biol 43(9):2465-78. https://doi.org/10.1088/0031-9155/43/9/003. PMID 9755939.
- [sjogaard1988] Sjogaard G et al. (1988). Eur J Appl Physiol Occup Physiol 57(3):327-35. https://doi.org/10.1007/BF00635992. PMID 3371342.
- [skiba2012] Skiba PF et al. (2012). Med Sci Sports Exerc 44(8):1526-32. https://doi.org/10.1249/MSS.0b013e3182517a80. PMID 22382171.
- [sogaard2006] Sogaard K et al. (2006). J Physiol 573(Pt 2):511-23. https://doi.org/10.1113/jphysiol.2005.103598. PMID 16556656.
- [southern2015] Southern WM et al. (2015). Physiol Rep 3(4):e12353. https://doi.org/10.14814/phy2.12353. PMID 25855248.
- [tran1999] Tran TK et al. (1999). Am J Physiol 276(6):R1682-90. https://doi.org/10.1152/ajpregu.1999.276.6.R1682. PMID 10362748.
- [ufland2012] Ufland P et al. (2012). Clin Physiol Funct Imaging 32(5):380-7. https://doi.org/10.1111/j.1475-097X.2012.01141.x. PMID 22856345.
- [vanbeekvelt2001_att] van Beekvelt MC et al. (2001). Clin Sci (Lond) 101(1):21-8. https://doi.org/10.1042/cs20000247. PMID 11410110.
- [vanbeekvelt2001_perf] Van Beekvelt MC et al. (2001). J Appl Physiol 90(2):511-9. https://doi.org/10.1152/jappl.2001.90.2.511. PMID 11160049.
- [vanderzee1992] van der Zee P et al. (1992). Adv Exp Med Biol 316:143-53. https://doi.org/10.1007/978-1-4615-3404-4_17. PMID 1288074.
- [walsh2001] Walsh B et al. (2001). Med Sci Sports Exerc 33(3):436-41. https://doi.org/10.1097/00005768-200103000-00016. PMID 11252071.
- [woodard1986] Woodard HQ et al. (1986). Br J Radiol 59(708):1209-18. https://doi.org/10.1259/0007-1285-59-708-1209. PMID 3801800.
