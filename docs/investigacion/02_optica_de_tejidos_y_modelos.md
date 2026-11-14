# 02 · Óptica de tejidos y modelos para MuscleSense Lab

Fecha: 2026-11-14. Unidades: λ en nm, longitudes en cm salvo indicación, μ en cm⁻¹. Marcas: **(V)** dato leído hoy en la fuente (tabla, página o resumen de PubMed); **(M)** dato de memoria o cita indirecta, sin comprobar. Los metadatos con PMID proceden de PubMed. Datos numéricos completos: `espectros_cromoforos.csv` y `parametros_opticos.json`.

## A. Absorción

### A.1 Procedencia de cada columna del CSV (650–950 nm, paso 2 nm, 151 filas)

| Columna | Fuente | Paso original | Tratamiento |
|---|---|---|---|
| `eps_hbo2_cm1_M1`, `eps_hhb_cm1_M1` | Compilación de Prahl con datos de Gratzer y Kollias [prahl_hb], en cm⁻¹/M por tetrámero (64 500 g/mol) | 2 nm | Sin interpolar. Las 151 filas coinciden exactamente con la copia en bruto de Homer3 [homer3] (V) |
| `mua_agua_cm1` | 667–950 nm: Kou, Labrie y Chylek [kou1993] (`kou93b.txt` de omlc.org, 226 puntos). 650–666 nm: Pope y Fry [pope1997] a través de la compilación NPSG [npsg_waterloo] | ≤ 2 nm y 5 nm | Interpolación lineal a la rejilla de 2 nm. Hay un escalón del 8 % en la costura (0.00431 a 666 nm, 0.00467 a 668 nm) |
| `mua_lipido_cm1` | van Veen et al., grasa de cerdo purificada [vanveen2004] (`fat.txt` de omlc.org, en m⁻¹) | 1 nm | Dividido entre 100; sin interpolar. Coincide con la copia NPSG en 31 longitudes de onda (V) |

Advertencia: el proxy bloquea la descarga directa de omlc.org, así que las tablas se leyeron con WebFetch (transcripción por modelo). La hemoglobina está cotejada contra un archivo en bruto; el agua de Kou solo con una segunda lectura de 7 puntos. Conviene repetir el cotejo cuando haya descarga directa.

Dispersión entre fuentes para el agua (cm⁻¹): Kou 0.0286 / 0.0219 / 0.0420 a 760 / 810 / 850 nm; Palmer y Williams (vía NPSG) 0.0268 / 0.0193 / 0.0395; Hale y Querry [hale1973] 0.0199 a 810 y 0.043 a 850. Incertidumbre razonable: ±10 %.

### A.2 Conversión

$\mu_a\,[\mathrm{cm^{-1}}] = \ln(10)\,\varepsilon\,C$, con $\varepsilon$ en cm⁻¹/M y $C$ en mol de tetrámero por litro. En masa: $\mu_a = 2.303\,\varepsilon\,x/64500$ con $x$ en g/L (150 g/L de sangre entera da $\mu_a = 0.0054\,\varepsilon$) (V, página de omlc.org). Por grupo hemo: $\varepsilon_{hemo} = \varepsilon/4$ y $C_{hemo} = 4C$ (un equivalente son 16 125 g). La copia de Homer3 escribe 66 500 g/mol; se adopta 64 500.

| λ | ε HbO₂ | ε HHb | μa sangre oxigenada | μa sangre desoxigenada | agua | lípido |
|---|---|---|---|---|---|---|
| 760 | 586 | 1548.52 | 3.14 | 8.29 | 0.0286 | 0.0128 |
| 810 | 864 | 717.08 | 4.63 | 3.84 | 0.0219 | 0.0053 |
| 850 | 1058 | 691.32 | 5.67 | 3.70 | 0.0420 | 0.0064 |

El cruce isosbéstico de esta tabla cae entre 796 y 798 nm. A 810 nm el cociente ε(HbO₂)/ε(HHb) es 1.205: el LED de 810 nm no es isosbéstico y no debe tratarse como tal.

Por capa: $\mu_a(\lambda) = \ln(10)\,[\varepsilon_{HbO_2}C_{HbO_2} + \varepsilon_{HHb}C_{HHb}] + f_w\,\mu_{a,w} + f_l\,\mu_{a,l} + \mu_{a,otros}$. Referencias para calibrar: antebrazo in vivo $\mu_a(800) = 0.23 \pm 0.04$ y pantorrilla $0.17 \pm 0.05$ cm⁻¹ [matcher1997] (V); dermis 0.33 y grasa 0.13 cm⁻¹ a 633 nm ex vivo [simpson1998] (V). El valor del antebrazo equivale a unos 116 µM de tetrámero (Hb + Mb) con 75 % de agua (cálculo propio).

### A.3 Mioglobina, melanina y citocromo

- **Mioglobina.** No se abrió ninguna tabla de Mb. El supuesto habitual es usar los espectros de la hemoglobina por grupo hemo ($\varepsilon/4$, la Mb es monomérica) y hablar de señal Hb + Mb. La diferencia espectral es pequeña: el pico desoxi cercano a 760 nm se desplaza ligeramente, y ese desplazamiento es lineal con la proporción Hb/Mb [marcinek2007] (V). La contribución de la Mb no es despreciable: 50–70 % del potencial de absorción en reposo [davis2013], y la Hb solo explicaría alrededor del 20 % de la señal en músculo humano [marcinek2007] (V). Al tener la Mb una afinidad mucho mayor por el O₂ (M), conviene modelar dos compartimentos con saturaciones distintas.
- **Melanina.** $\mu_{a,mel} = 6.6\times10^{11}\,\lambda^{-3.33}$ cm⁻¹ en el interior del melanosoma [jacques1998_skinoptics, jacques1991] (V): 168, 136 y 116 cm⁻¹ a 760, 810 y 850 nm. Epidermis: $\mu_{a,epi} = f_{mel}\,\mu_{a,mel} + (1-f_{mel})\,\mu_{a,base}$, con $\mu_{a,base} = 0.244 + 85.3\,e^{-(\lambda-154)/66.2}$ (0.25 cm⁻¹ en el NIR) y $f_{mel}$ de 1.3–6.3 % (piel clara), 11–16 % (morena) y 18–43 % (oscura) para 60 µm de epidermis (V).
- **Citocromo c oxidasa.** Su señal redox es inferior al 10 % de la de la hemoglobina (M) [wray1988, bale2016]. Con tres longitudes de onda no se puede separar: se omite.

## B. Esparcimiento, anisotropía e índice

Ley de potencia $\mu_s'(\lambda) = a\,(\lambda/500)^{-b}$ [jacques2013]. Los parámetros se leyeron del CSV que el autor publica en omlc.org (V); medias y desviaciones calculadas aquí a partir de sus filas.

| Tejido | a (cm⁻¹) | b | μs' 760 / 810 / 850 | Rango de a; rango de b | Fila |
|---|---|---|---|---|---|
| Epidermis | 68.7 | 1.161 | 42.3 / 39.2 / 37.1 | 29.7–68.7; 0.705–2.453 | 7, [salomatina2006] |
| Dermis | 45.3 | 1.292 | 26.4 / 24.3 / 22.8 | 29.7–60.1; 0.705–2.453 | 6, [salomatina2006] |
| Dermis, alternativa | 37.2 | 1.390 | 20.8 / 19.0 / 17.8 | | 3, [simpson1998] |
| Grasa subcutánea | 18.4 | 0.672 | 13.9 / 13.3 / 12.9 | 10.6–35.2; 0.385–0.988 | media de 51–56 |
| Grasa, alternativa | 13.7 | 0.385 | 11.7 / 11.4 / 11.2 | | 51, [simpson1998] |
| Músculo | 13.0 | 0.926 | 8.8 / 8.3 / 8.0 | 9.2–13.0; 0.62–2.82 | 29 |
| Músculo, alternativa | 9.8 | 2.82 | 3.0 / 2.5 / 2.2 | | 40, [alexandrakis2005] |
| Antebrazo in vivo | 11.0 − 0.0051 λ | | 7.1 / 6.9 / 6.7 | válido 760–900 nm | [matcher1997] (V) |

Medias de grupo: piel $a = 46.0 \pm 13.7$, $b = 1.42 \pm 0.52$ (8 filas); tejido graso $18.4 \pm 9.0$, $0.67 \pm 0.24$ (6); otros tejidos blandos $18.9 \pm 10.2$, $1.29 \pm 0.52$ (18). La incertidumbre real de μs' es del 30–50 %, y para el músculo las dos filas difieren en un factor 3: debe ser un parámetro configurable. Comprobación cruzada: los ajustes de Simpson dan 26.8 y 12.5 cm⁻¹ a 633 nm, y su resumen da 2.73 y 1.26 mm⁻¹ (V). La pantorrilla in vivo sigue $16.0 - 0.0089\,\lambda$ cm⁻¹ [matcher1997]. Bashkatov [bashkatov2005, bashkatov2011] y Zamora-Rojas no se pudieron abrir.

- **g.** Valor de trabajo 0.9 en las cuatro capas (M); la piel se sitúa entre 0.7 y 0.95 [jacques1998_skinoptics] (V). Con $\mu_s = \mu_s'/(1-g)$ el resultado a ρ ≥ 10 mm apenas depende de g.
- **n.** La mayoría de tejidos, músculo incluido, está entre 1.38 y 1.41 a 632.8 nm [bolin1989] (V). Propuesta: epidermis 1.43, dermis 1.40, grasa 1.44, músculo 1.40; los tres primeros son (M) (el resumen de [ding2006] no da cifras). Para validar contra difusión es más limpio usar n = 1.40 uniforme.

## C. Modelos

### C.1 Beer-Lambert modificada [delpy1988]

$OD(\lambda) = -\log_{10}(I/I_0) = \sum_i \varepsilon_i(\lambda)\,c_i\,\rho\,DPF(\lambda) + G(\lambda)$, y para cambios $\Delta OD(\lambda) = \rho\,DPF(\lambda)\sum_i \varepsilon_i(\lambda)\,\Delta c_i$. Con tres longitudes de onda y dos cromóforos: $\Delta c = (E^TE)^{-1}E^T\,[\Delta OD/(\rho\,DPF)]$ [matcher1995]. Hipótesis: G constante en el tiempo, cambio de absorción homogéneo y pequeño, DPF conocido. El DPF es el camino medio diferencial $\langle L\rangle/\rho = \partial A/\partial\mu_a/\rho$ (con $A = -\ln R$), no la atenuación total dividida por μa [sassaroli2004].

En capas [hiraoka1993]: $\Delta OD = \frac{1}{\ln 10}\sum_k \langle L_k\rangle\,\Delta\mu_{a,k}$, con $\langle L_k\rangle = \partial A/\partial\mu_{a,k}$ y $\sum_k\langle L_k\rangle = \rho\,DPF$. La sensibilidad de cada capa es $\partial OD/\partial\mu_{a,k} = \langle L_k\rangle/\ln 10$, y la MBLL homogénea subestima el cambio muscular en el factor $\langle L_{músculo}\rangle/(\rho\,DPF)$. El espesor adiposo es el principal factor de confusión [vanbeekvelt2001, yang2005].

DPF medidos a 807 nm con separaciones mayores de 4 cm [duncan1995] (V): antebrazo $4.16 \pm 18.8\,\%$ (±0.78), pantorrilla $5.51 \pm 18\,\%$, cabeza adulta $6.26 \pm 14.1\,\%$, cabeza neonatal $4.99 \pm 9\,\%$. Es aproximadamente constante por encima de 2.5 cm [vanderzee1992] y disminuye con λ, típicamente un 12 % entre 740 y 840 nm [essenpreis1993] (V). No se encontraron medidas específicas del bíceps: se calculará con el Monte Carlo. Los valores numéricos de van der Zee y Ferrari [ferrari1992] no figuran en sus resúmenes.

### C.2 Difusión estacionaria en medio semiinfinito

$\mu_t' = \mu_a + \mu_s'$, $z_0 = 1/\mu_t'$, $D = 1/(3\mu_t')$, $\mu_{eff} = \sqrt{\mu_a/D}$, $z_b = 2AD$, $r_1 = \sqrt{z_0^2+\rho^2}$, $r_2 = \sqrt{(z_0+2z_b)^2+\rho^2}$.

Reflectancia de flujo [farrell1992], en cm⁻² por fotón incidente:
$R_f(\rho) = \frac{a'}{4\pi}\left[z_0\left(\mu_{eff}+\frac{1}{r_1}\right)\frac{e^{-\mu_{eff}r_1}}{r_1^2} + (z_0+2z_b)\left(\mu_{eff}+\frac{1}{r_2}\right)\frac{e^{-\mu_{eff}r_2}}{r_2^2}\right]$, con $a' = \mu_s'/\mu_t'$.

Versión mejorada [kienle1997]: $R(\rho) = C_1\,\Phi(\rho,0) + C_2\,R_f(\rho)$, con $\Phi(\rho,0) = \frac{a'}{4\pi D}\left(\frac{e^{-\mu_{eff}r_1}}{r_1} - \frac{e^{-\mu_{eff}r_2}}{r_2}\right)$, $C_1 = \frac{1}{4\pi}\int[1-R_F(\theta)]\cos\theta\,d\Omega$ y $C_2 = \frac{3}{4\pi}\int[1-R_F(\theta)]\cos^2\theta\,d\Omega$ sobre el hemisferio de salida; para n = 1.4, $C_1 = 0.118$ y $C_2 = 0.306$ (M).

Factor de frontera $A = (1+R_{eff})/(1-R_{eff})$ [haskell1994]. Ajuste polinómico de [contini1997] para n > 1 (M): $A = 504.332889 - 2641.00214\,n + 5923.699064\,n^2 - 7376.355814\,n^3 + 5507.53041\,n^4 - 2463.357945\,n^5 + 610.956547\,n^6 - 64.8047\,n^7$. Evaluado aquí da A(1) = 0.998, A(1.33) = 2.52, A(1.40) = 2.95 y A(1.50) = 3.63, coherente con $R_{eff} = 0.493$ para n = 1.40 (M). La fórmula empírica de Groenhuis, $r_d = -1.440\,n^{-2} + 0.710\,n^{-1} + 0.668 + 0.0636\,n$ (M), da 3.25 para n = 1.40.

DPF analítico (deducción propia a partir de $R \propto (1+\mu_{eff}\rho)\,e^{-\mu_{eff}\rho}/\rho^3$; véanse [arridge1992, fantini1999]):
$DPF = \frac{\sqrt{3\mu_s'}}{2\sqrt{\mu_a}}\cdot\frac{\mu_{eff}\,\rho}{1+\mu_{eff}\,\rho}$, con $\mu_{eff}=\sqrt{3\mu_a\mu_s'}$. Con los valores in vivo del antebrazo (0.023 y 0.692 mm⁻¹, ρ = 40 mm) da 4.26, dentro de $4.16 \pm 0.78$.

Validez orientativa (M): $\mu_s'/\mu_a \gtrsim 10$ y $\rho \gg 1/\mu_t'$; con $\mu_s' \approx 7$ cm⁻¹ conviene ρ ≥ 10–15 mm. A 10 mm sobre piel y grasa la difusión homogénea es poco fiable y manda el Monte Carlo.

### C.3 Difusión en N capas [kienle1998, liemert2010]

Formulación en el dominio de Hankel, deducida aquí en forma de admitancias y equivalente a la de las referencias; debe validarse contra el caso de dos capas y contra el Monte Carlo. Capa k: espesor $d_k$, $D_k = 1/(3(\mu_{a,k}+\mu_{s,k}'))$, $\alpha_k(s) = \sqrt{s^2 + \mu_{a,k}/D_k}$. Fuente isótropa en $z_0 = 1/(\mu_{a,1}+\mu_{s,1}')$ con $z_0 < d_1$; $\Phi = 0$ en $z = -z_b$, $z_b = 2AD_1$. En cada interfaz son continuos el flujo $D\,\partial_z\Phi$ y $\Phi/n^2$.

1. Última capa semiinfinita: $Y_N = D_N\alpha_N$.
2. Recursión hacia arriba, para $k = N-1,\dots,2$, con $\tilde Y_{k+1} = Y_{k+1}\,(n_{k+1}/n_k)^2$:
   $Y_k = D_k\alpha_k\,\dfrac{D_k\alpha_k\tanh(\alpha_k d_k) + \tilde Y_{k+1}}{D_k\alpha_k + \tilde Y_{k+1}\tanh(\alpha_k d_k)}$.
3. Primera capa, con $\beta = D_1\alpha_1$ e $\tilde Y_2$:
   $\tilde\Phi_1(s,0) = \dfrac{1-e^{-2\alpha_1 z_b}}{2\beta}\,e^{-\alpha_1 z_0}\,\dfrac{(\beta+\tilde Y_2) + (\beta-\tilde Y_2)\,e^{-2\alpha_1(d_1-z_0)}}{(\beta+\tilde Y_2) + (\beta-\tilde Y_2)\,e^{-2\alpha_1(d_1+z_b)}}$.
   La forma con exponenciales decrecientes evita desbordamientos. El flujo es $\tilde R_f(s) = \beta\coth(\alpha_1 z_b)\,\tilde\Phi_1(s,0)$.
4. Inversión: $\Phi(\rho,0) = \frac{1}{2\pi}\int_0^\infty \tilde\Phi_1(s,0)\,J_0(s\rho)\,s\,ds$, e igual para $R_f$; después $R = C_1\Phi + C_2R_f$. Integrar por tramos entre ceros de $J_0(s\rho)$ con Gauss-Legendre hasta que $e^{-s z_0}$ sea despreciable.

Comprobación: con $\tilde Y_2 = \beta$ se recupera el dipolo homogéneo, $[e^{-\alpha z_0} - e^{-\alpha(z_0+2z_b)}]/(2D\alpha)$. Los caminos parciales salen de $\langle L_k\rangle = -\partial\ln R/\partial\mu_{a,k}$ por diferencias finitas. Aplicación al antebrazo con piel, grasa y músculo: [kienle1999].

### C.4 Espectroscopía resuelta espacialmente [suzuki1999, matcher1995]

Para $\rho \gg 1/\mu_{eff}$, $R \propto e^{-\mu_{eff}\rho}/\rho^2$, de modo que $\partial A_{10}/\partial\rho = \frac{1}{\ln 10}(\mu_{eff} + 2/\rho)$. Con dos detectores: $\mu_{eff}(\lambda) = \dfrac{\ln(I_1/I_2) - 2\ln(\rho_2/\rho_1)}{\rho_2-\rho_1}$. Suponiendo $\mu_s'(\lambda) = k\,(1-h\lambda)$: $k\,\mu_a(\lambda) = \dfrac{\mu_{eff}^2}{3\,(1-h\lambda)}$. Se resuelve $k\,C_{HbO_2}$ y $k\,C_{HHb}$ por mínimos cuadrados y $TSI = k\,C_{HbO_2}/(k\,C_{HbO_2}+k\,C_{HHb})$; k se cancela. De las rectas de [matcher1997], $h = 4.6\times10^{-4}$ nm⁻¹ en antebrazo y $5.6\times10^{-4}$ en pantorrilla (V). Supuestos: medio homogéneo semiinfinito, acoplamiento idéntico en ambos detectores y solo Hb como absorbente variable; el agua debe restarse y la capa adiposa sesga el índice. La forma exacta del algoritmo de Suzuki es (M).

### C.5 Monte Carlo en capas [wang1995]

- **Lanzamiento:** peso $W = 1 - R_{sp}$, con $R_{sp} = [(n_0-n_1)/(n_0+n_1)]^2$.
- **Paso:** $s = -\ln\xi/\mu_t$, y en cada interacción se deposita $\Delta W = W\mu_a/\mu_t$. Variante equivalente y apta para reponderar: $s = -\ln\xi/\mu_s$ con $W \leftarrow W\,e^{-\mu_a s}$ (es la de MCX).
- **Henyey-Greenstein:** $\cos\theta = \frac{1}{2g}\left[1+g^2-\left(\frac{1-g^2}{1-g+2g\xi}\right)^2\right]$; si $g = 0$, $\cos\theta = 2\xi-1$; $\varphi = 2\pi\xi$.
- **Interfaces:** si el paso cruza una frontera se avanza hasta ella y se guarda el resto adimensional $(s-d_b)\,\mu_t$. Fresnel no polarizado: $R(\theta_i) = \frac12\left[\frac{\sin^2(\theta_i-\theta_t)}{\sin^2(\theta_i+\theta_t)} + \frac{\tan^2(\theta_i-\theta_t)}{\tan^2(\theta_i+\theta_t)}\right]$, con $n_i\sin\theta_i = n_t\sin\theta_t$ y reflexión total por encima del ángulo crítico. Si $\xi \le R$ se refleja; si no, se refracta y el paso restante se convierte con el $\mu_t$ de la nueva capa.
- **Ruleta:** si $W < 10^{-4}$, sobrevive con probabilidad $1/m$ ($m = 10$) y peso $mW$ (M en los valores).
- **Trayectorias parciales:** acumular $L_k$ por capa en cada fotón y guardar ($w_i$, $L_{ik}$) de los detectados. Reponderación [kienle1996, alerstam2008, sassaroli1998]: $w_i' = w_i\exp[-\sum_k(\mu_{a,k}-\mu_{a,k}^0)\,L_{ik}]$, con $\mu_a^0 = 0$ en el Monte Carlo blanco; $\langle L_k\rangle = \sum_i w_i' L_{ik}/\sum_i w_i'$. Para el esparcimiento [hayakawa2001] (M): $w' = w\prod_k(\mu_{s,k}'/\mu_{s,k})^{j_k}\,e^{-(\mu_{s,k}'-\mu_{s,k})L_k}$, con $j_k$ colisiones en la capa. Vigilar $N_{eff} = (\sum w)^2/\sum w^2$.

## D. Valores de referencia

| Caso | Entradas | Referencia | MCML | Prahl 1989 |
|---|---|---|---|---|
| Losa de van de Hulst | n = 1, μa = 10, μs = 90, g = 0.75, d = 0.02 cm | Rd 0.09739; Tt 0.66096 | 0.09734 ± 0.00035; 0.66096 ± 0.00020 | 0.09711 ± 0.00033; 0.66159 ± 0.00049 |
| Giovanelli, semiinfinito | n = 1.5, μa = 10, μs = 90, g = 0 | Rd 0.2600 | 0.25907 ± 0.00170 | 0.26079 ± 0.00079 |

Leído en el manual de MCML, tablas 6.1 y 6.2 [mcml_manual] (V); las fuentes primarias [vandehulst1980, giovanelli1955, prahl1989] no se abrieron. En la losa, la transmitancia no esparcida es $e^{-2} = 0.13534$ y la difusa 0.52562.

**Pendiente en Giovanelli.** El manual llama al valor «reflectancia difusa total» y no dice que se sume la especular; sus definiciones separan Rd de Rsp. Nuestro código da 0.2192 de difusa, que con la especular (0.04) suma 0.2592, igual a los valores tabulados. Lo más probable es que 0.2600 incluya la especular, pero no se pudo confirmar en la fuente.

Otros casos: (1) absorbente puro, $A = 1 - e^{-\mu_a L}$ (0.259182 y 0.950213 para 0.005 y 0.05 mm⁻¹ en 60 mm); con Fresnel, $T = (1-R_1)(1-R_2)\,e^{-\mu_a d}/(1-R_1R_2\,e^{-2\mu_a d})$. (2) Balance $R_{sp}+R_d+A+T_t = 1$. (3) Decaimiento en profundidad con μa = 0.1, μs = 100, g = 0.9: $\mu_{eff}$ teórico 1.741 cm⁻¹; MCML ajusta 1.73 (n = 1) y 1.74 (n = 1.37) [mcml_manual] (V). (4) Fórmulas de C.2 frente al Monte Carlo a ρ ≥ 15 mm.

## E. MCX y MCX-CL [fang2009, yu2018]

Leído en el README y el código de la rama master [mcx_readme] (V):

- Vóxeles cúbicos de arista `unitinmm` (mm). Las posiciones de fuente y detectores van en **unidades de vóxel**; μa y μs van siempre en mm⁻¹, y μs es el coeficiente sin reducir.
- `issrcfrom0` vale 0 por defecto: la esquina del primer vóxel es [1,1,1]. Una fuente fuera del dominio o en un vóxel 0 se traslada al primer vóxel no nulo (`skipvoid`).
- `detpos = [x y z r]`: discos; se registra el fotón que sale del dominio dentro de alguno. Los caminos parciales guardados están en unidades de vóxel (multiplicar por `unitinmm`). Peso detectado: $w_0\exp(-\sum_i\mu_{a,i}L_i)$ (`detweight`, `meanpath`).
- `isreflect` aplica Fresnel en la frontera del dominio. El balance es `energyabs = energytot - energyesc`, sin contar la pérdida especular inicial.
- Normalización por defecto: función de Green de la tasa de fluencia, en 1/(mm² s) por fotón; la fluencia continua es la suma de las puertas por Δt, con la ventana temporal suficientemente larga.
- Capas planas alineadas con la rejilla no tienen error de escalera, pero su espesor se redondea a un número entero de vóxeles; en fronteras curvas sí lo hay [binzoni2008, yan2020].

**Prueba con μs = 0.** No hay explicación documentada. Lo que muestra el código: (a) con μs = 0 el fotón avanza de vóxel en vóxel y su peso se actualiza con `expf` en precisión simple; (b) las energías lanzada y escapada se acumulan en variables `float` de 32 bits por hilo, tanto en MCX como en MCX-CL, y solo se suman en doble precisión en el anfitrión. Sin esparcimiento todos los fotones salen con el mismo peso y el redondeo de esa suma es sistemático. Simulación propia de la acumulación en 32 bits con $w = e^{-0.3}$: sesgo relativo de +1.9·10⁻⁴, +2.8·10⁻⁴ y +1.1·10⁻³ con 2·10⁴, 6·10⁴ y 1.2·10⁵ sumas por hilo; lo observado (0.258512) equivale a +9.0·10⁻⁴. Con $w = e^{-3}$ el mismo mecanismo da un error de 0.0015–0.0017 % en la fracción absorbida, como el 0.002 % medido. Es una hipótesis: se confirma variando los fotones por hilo. El registro de cambios menciona además un sesgo de hasta 0.25 % por las semillas, que no puede actuar en una trayectoria determinista. Que el resultado no cambie al mover la fuente de z = 0 a z = 0.5 se explica si `issrcfrom0 = 0`: ambas posiciones quedan fuera del dominio y se trasladan a la misma cara.

## No verificado

g por tejido; n de epidermis, dermis y grasa; C₁ y C₂ de Kienle; polinomio de Contini y fórmula de Groenhuis (solo coherencia numérica); algoritmo exacto de Suzuki; umbral de ruleta; reponderación de esparcimiento; magnitud del citocromo; espectros propios de la mioglobina; identidad del artículo de la fila 29 (músculo); DPF de van der Zee y Ferrari; la corrección publicada de Jacques 2013; Bashkatov 2005 y 2011, Zamora-Rojas y Nilsson; DOI de Kou, Hale, Pope y Suzuki; fuentes primarias de los benchmarks y la cuestión de la especular en Giovanelli.

## Referencias

Títulos completos en `parametros_opticos.json`.

- [alerstam2008] Alerstam et al. (2008) J Biomed Opt 13:041304. doi:10.1117/1.2950319. PMID 19021312.
- [alexandrakis2005] Alexandrakis et al. (2005) Phys Med Biol 50:4225. doi:10.1088/0031-9155/50/17/021. PMID 16177541.
- [arridge1992] Arridge, Cope, Delpy (1992) Phys Med Biol 37:1531. doi:10.1088/0031-9155/37/7/005. PMID 1631197.
- [bale2016] Bale et al. (2016) J Biomed Opt 21:091307. doi:10.1117/1.JBO.21.9.091307. PMID 27170072.
- [bashkatov2005] Bashkatov et al. (2005) J Phys D 38:2543. doi:10.1088/0022-3727/38/15/004 (M).
- [bashkatov2011] Bashkatov et al. (2011) J Innov Opt Health Sci 4:9. doi:10.1142/S1793545811001319 (M).
- [binzoni2008] Binzoni et al. (2008) Comput Methods Programs Biomed 89:14. doi:10.1016/j.cmpb.2007.10.008. PMID 18045725.
- [bolin1989] Bolin et al. (1989) Appl Opt 28:2297. doi:10.1364/AO.28.002297. PMID 20555515.
- [contini1997] Contini, Martelli, Zaccanti (1997) Appl Opt 36:4587. doi:10.1364/ao.36.004587. PMID 18259254.
- [davis2013] Davis, Barstow (2013) Respir Physiol Neurobiol 186:180. doi:10.1016/j.resp.2013.01.012. PMID 23357615.
- [delpy1988] Delpy et al. (1988) Phys Med Biol 33:1433. doi:10.1088/0031-9155/33/12/008. PMID 3237772.
- [ding2006] Ding et al. (2006) Phys Med Biol 51:1479. doi:10.1088/0031-9155/51/6/008. PMID 16510957.
- [duncan1995] Duncan et al. (1995) Phys Med Biol 40:295. doi:10.1088/0031-9155/40/2/007. PMID 7708855.
- [essenpreis1993] Essenpreis et al. (1993) Appl Opt 32:418. doi:10.1364/AO.32.000418. PMID 20802707.
- [fang2009] Fang, Boas (2009) Opt Express 17:20178. doi:10.1364/OE.17.020178. PMID 19997242.
- [fantini1999] Fantini et al. (1999) Phys Med Biol 44:1543. doi:10.1088/0031-9155/44/6/308. PMID 10498522.
- [farrell1992] Farrell, Patterson, Wilson (1992) Med Phys 19:879. doi:10.1118/1.596777. PMID 1518476.
- [ferrari1992] Ferrari et al. (1992) J Photochem Photobiol B 16:141. doi:10.1016/1011-1344(92)80005-g. PMID 1474423.
- [giovanelli1955] Giovanelli (1955) Optica Acta 2:153 (M).
- [hale1973] Hale, Querry (1973) Appl Opt 12:555. doi:10.1364/AO.12.000555 (DOI sin abrir).
- [haskell1994] Haskell et al. (1994) J Opt Soc Am A 11:2727. doi:10.1364/josaa.11.002727. PMID 7931757.
- [hayakawa2001] Hayakawa et al. (2001) Opt Lett 26:1335. doi:10.1364/ol.26.001335. PMID 18049600.
- [hiraoka1993] Hiraoka et al. (1993) Phys Med Biol 38:1859. doi:10.1088/0031-9155/38/12/011. PMID 8108489.
- [homer3] BUNPC, Homer3, `GetExtinctions.m`, github.com/BUNPC/Homer3.
- [jacques1991] Jacques, McAuliffe (1991) Photochem Photobiol 53:769. doi:10.1111/j.1751-1097.1991.tb09891.x. PMID 1886936.
- [jacques1998_skinoptics] Jacques (1998) Skin Optics, omlc.org/news/jan98/skinoptics.html.
- [jacques2013] Jacques (2013) Phys Med Biol 58:R37. doi:10.1088/0031-9155/58/11/R37. PMID 23666068. Datos: omlc.org/news/dec14/Jacques_PMB2013.
- [kienle1996] Kienle, Patterson (1996) Phys Med Biol 41:2221. doi:10.1088/0031-9155/41/10/026. PMID 8912392.
- [kienle1997] Kienle, Patterson (1997) J Opt Soc Am A 14:246. doi:10.1364/josaa.14.000246. PMID 8988618.
- [kienle1998] Kienle et al. (1998) Appl Opt 37:779. doi:10.1364/ao.37.000779. PMID 18268653.
- [kienle1999] Kienle, Glanzmann (1999) Phys Med Biol 44:2689. doi:10.1088/0031-9155/44/11/301. PMID 10588278.
- [kou1993] Kou, Labrie, Chylek (1993) Appl Opt 32:3531. doi:10.1364/AO.32.003531 (DOI sin abrir).
- [liemert2010] Liemert, Kienle (2010) J Biomed Opt 15:025002. doi:10.1117/1.3368682. PMID 20459243.
- [marcinek2007] Marcinek et al. (2007) Appl Spectrosc 61:665. doi:10.1366/000370207781269819. PMID 17650380.
- [matcher1995] Matcher et al. (1995) Anal Biochem 227:54. doi:10.1006/abio.1995.1252. PMID 7668392.
- [matcher1997] Matcher, Cope, Delpy (1997) Appl Opt 36:386. doi:10.1364/ao.36.000386. PMID 18250686.
- [mcml_manual] Wang, Jacques (1992) manual de MCML, its.caltech.edu/~coil/mcr5/Mcman.pdf.
- [mcx_readme] Fang et al., github.com/fangq/mcx y github.com/fangq/mcxcl (leídos el 2026-11-14).
- [npsg_waterloo] NPSG, Universidad de Waterloo, npsg.uwaterloo.ca/data/skin.php.
- [pope1997] Pope, Fry (1997) Appl Opt 36:8710. doi:10.1364/AO.36.008710 (M).
- [prahl1989] Prahl et al. (1989) SPIE Institute Series IS 5:102 (M).
- [prahl_hb] Prahl, omlc.org/spectra/hemoglobin/summary.html.
- [salomatina2006] Salomatina et al. (2006) J Biomed Opt 11:064026. doi:10.1117/1.2398928. PMID 17212549.
- [sassaroli1998] Sassaroli et al. (1998) Appl Opt 37:7392. doi:10.1364/ao.37.007392. PMID 18301573.
- [sassaroli2004] Sassaroli, Fantini (2004) Phys Med Biol 49:N255. doi:10.1088/0031-9155/49/14/n07. PMID 15357206.
- [simpson1998] Simpson et al. (1998) Phys Med Biol 43:2465. doi:10.1088/0031-9155/43/9/003. PMID 9755939.
- [suzuki1999] Suzuki et al. (1999) Proc SPIE 3597:582. doi:10.1117/12.356862 (M).
- [vanbeekvelt2001] van Beekvelt et al. (2001) Clin Sci 101:21. doi:10.1042/cs20000247. PMID 11410110.
- [vandehulst1980] van de Hulst (1980) Multiple Light Scattering, Academic Press (M).
- [vanderzee1992] van der Zee et al. (1992) Adv Exp Med Biol 316:143. doi:10.1007/978-1-4615-3404-4_17. PMID 1288074.
- [vanveen2004] van Veen et al. (2004) OSA BIOMED; omlc.org/spectra/fat/fat.txt. Versión en revista: J Biomed Opt 10:054004, doi:10.1117/1.2085149, PMID 16292964.
- [wang1995] Wang, Jacques, Zheng (1995) Comput Methods Programs Biomed 47:131. doi:10.1016/0169-2607(95)01640-f. PMID 7587160.
- [wray1988] Wray et al. (1988) Biochim Biophys Acta 933:184. doi:10.1016/0005-2728(88)90069-2. PMID 2831976.
- [yan2020] Yan, Fang (2020) Biomed Opt Express 11:6262. doi:10.1364/BOE.409468. PMID 33282488.
- [yang2005] Yang et al. (2005) Opt Express 13:1570. doi:10.1364/opex.13.001570. PMID 16044624.
- [yu2018] Yu et al. (2018) J Biomed Opt 23:010504. doi:10.1117/1.JBO.23.1.010504. PMID 29374404.
