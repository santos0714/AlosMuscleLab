# 03 Instrumentación y componentes (BORRADOR PARCIAL, en curso)

> Avance parcial guardado el 2026-11-14. Este archivo se reemplaza por el dossier final.

## Datos ya verificados en hoja de datos (con URL)

### LED
- Vishay VSMY2850G / VSMY2850RG (850 nm): pico 850 (840-870) nm a 100 mA; FWHM 30 nm; 55 mW tip. a 100 mA (tp 20 ms); IF máx 100 mA cc; IFM 200 mA (tp/T 0.5, 100 us); IFSM 1 A (100 us); VF 1.6 tip./1.9 máx a 100 mA; +-10 grados; 0.25 nm/K; -0.12 %/K; -1.5 mV/K; SMD 2.3x2.3x2.8 mm. Doc 83398 Rev 1.7 21-mar-2025. https://media.onlinecomponents.com/productfiles/mf-vis/vis-vsmy2850rg-56814234.pdf
- OSRAM SFH 4780S (810 nm centroide, pico 820): 600 mW a 1 A (10 ms); FWHM 30 nm; IF máx 500 mA; pulso 2 A (<=200 us); VF 3.3 V a 0.5 A (chip apilado); +-10 grados; 0.3 nm/K; -0.3 %/K; 3.5x3.5x2.4 mm. Hoja en versión borrador 2015. https://nonprod.docs.rs-online.com/a4f4/0900766b813dd148.pdf
- Luminus SST-10-IRD-B90H-V810 / B130H: pico 815 tip. (bin 800-830), centroide 810; FWHM 30; 615 mW a 350 mA; VF 3.0; IF máx 1.5 A cc, 5 A pulso; +0.3 nm/C; -0.2 %/C. https://download.luminus.com/datasheets/Luminus_SST-10-IRD-BxxH_810_Datasheet.pdf
- Roithner LED760-series (LED760-01AU ...; epoxi 3/4/5 mm): 760 nm tip.; 19 mW tip. a 50 mA; VF 1.8/2.2; FWHM 30 nm; IF máx 100 mA; IFP 500 mA; PD 200 mW. https://dtsheet.com/doc/1336610/led760-series
- Roithner SMB1N-760D: 760 (750-770) nm; 400 mW a 800 mA; FWHM 26; VF 2.0/2.5; IF 800 mA; IFP 2 A (1 %, 10 us). https://dtsheet.com/doc/1336171/smb1n-760d
- Marktech MTMD7885N24 (770/810/850 en TO-18): 3.1/3.0/2.7 mW a 20 mA; VF 1.6/1.55/1.4; FWHM 35/30/35; IF máx 50/100/100 mA; pulso 0.5/1/1 A (10 us, 10 ms). https://specs.marktechopto.com/pdf/optrans/MTMD7885N24.pdf
- Marktech MTMD7885T38 (770/810/850 x2 en TO-5): mismas potencias; FWHM 25/35/35. https://specs.marktechopto.com/pdf/optrans/MTMD7885T38.pdf

### Fotodetectores
- Hamamatsu S1223 / S1223-01: 6.6 / 13 mm2; 0.52 A/W a 780; 0.54 a 830; 0.6 a 960 (pico); Id 0.1/0.2 nA tip. (10 máx) a 20 V; Ct 10/20 pF a 20 V; NEP 9.4e-15 / 1.3e-14; TO-5. KPIN1050E02. https://www.farnell.com/datasheets/3171157.pdf
- TI OPT101: 2.29x2.29 mm (5.2 mm2); 0.45 A/W a 650 nm; 1 Mohm interno; 14 kHz; ruido 300 uVrms (0.1 Hz-20 kHz); offset 7.5 mV; Iq 120 uA; 2.7-36 V. https://www.ti.com/product/OPT101

## Avance parcial 2 (más datos verificados)
- Roithner LED810-xxAU (epoxi): 810 nm tip.; 22 mW tip. (17 mín) a 50 mA; VF 1.7/1.9; FWHM 35 nm; IF 100 mA; IFP 500 mA; PD 170 mW. https://pdf.jiepei.com/led810-02au-33102841.html
- OSRAM SFH 4250 (850 nm, Power TOPLED): 40 mW a 100 mA; FWHM 35; VF 1.5/1.8; IF 100 mA; IFSM 1.5 A (100 us); +-60 grados; +0.2 nm/K; -0.5 %/K; -0.7 mV/K. Hoja 2007 preliminar. https://www.komponenten.es.aau.dk/fileadmin/komponenten/Data_Sheet/SMD_Data/Dioder/SFH4250.pdf
- Vishay BPW34: 7.5 mm2; Id 2 nA tip./30 máx (10 V); C 70 pF (0 V), 25 pF tip. (3 V); pico 900 nm; 600-1050 nm; 50 uA a 1 mW/cm2 950 nm (=> 0.67 A/W nominal a 950); NEP 4e-14 (10 V, 950 nm); +-65 grados. Doc 81521. https://www.farnell.com/datasheets/463636.pdf
- OPA380 (SBOS291G): Ib 3 pA tip./50 máx; en 67 nV/rtHz a 10 kHz, 5.8 a >1 MHz; in 10 fA/rtHz a 10 kHz; GBW 90 MHz; Cdif 1.1 pF, Ccm 3 pF; Vos 4/25 uV; 2.7-5.5 V; Iq 7.5 mA. https://www.ti.com/lit/gpn/opa380
- ADA4530-1 (Rev D): Ib <1 fA tip./20 fA máx; en 14 nV/rtHz a 10 kHz; in 0.07 fA/rtHz; GBW 2 MHz; Cin 8 pF; 4.5-16 V; Iq 0.9 mA; SOIC-8. https://www.analog.com/media/en/technical-documentation/data-sheets/ADA4530-1.pdf
- LTC6268: Ib 3 fA; en 4.3 nV/rtHz a 1 MHz; in 5.5 fA/rtHz a 100 kHz; GBW 500 MHz; Cin 0.45 pF; 3.1-5.25 V; Iq 16.5 mA; 5.09 USD (1ku). https://www.analog.com/en/products/ltc6268.html
- AFE4404: 3 LED, 50 mA (100 mA con ILED_2X), DAC 6 bits; Rf 10k-2M; ADC 22 bits; 100 dB; offset DAC +-7 uA; PRF 10-1000 Hz; I2C; DSBGA 2.6x1.6 mm. https://ti.com/lit/gpn/AFE4404
- ADPD4100/4101: 8 drivers LED, 1.5-200 mA (400 mA total), 8 entradas, TIA 12.5k-200k, ADC 14 bits, SNR 100 dB (100 Hz, 80 pulsos), rechazo ambiente 60 dB (cc-1 kHz), 0.004 Hz-9 kHz, SPI/I2C, WLCSP 3.11x2.14. https://www-cce.cldnet.analog.com/media/en/technical-documentation/data-sheets/adpd4100-4101.pdf
- MAX86141: 2 canales, 3 drivers LED hasta 124 mA (8 bits), ADC 19 bits, >90 dB, ALC 100 uA / >70 dB a 120 Hz, <50 pA rms, 8-4096 sps, SPI, WLP 2.048x1.848. https://www.farnell.com/datasheets/2580845.pdf
- nRF52840: BLE 5, SAADC 12 bits SAR 200 ksps 8 canales; TX 0 dBm 4.8 mA; RX 4.6 mA; 1.7-5.5 V. https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/keyfeatures_html5.html
- PortaMon: 760/850 nm, 3 LED x 2 lambdas, 30/35/40 mm, 0.1-10 Hz, 88 g. https://www.ntnu.edu/documents/221360533/1261844786/PortaMon+Leaflet+-+ver1205.pdf/2192e225-05b4-4f4b-95e6-6adc667570cf
- Moxy: 680/720/760/800 nm, 1 emisor, 2 detectores a 12.5 y 25 mm, 2 Hz. (JBO 23(1) 015007)
- ICNIRP 2013: piel H = 2.0e4 t^0.25 J/m2 (t<=10 s, <3000 nm); >10 s sin límite numérico (estrés térmico). Córnea/cristalino 780-3000: 1.8e4 t^-0.75 W/m2 (t<1000 s), 100 W/m2 (t>=1000 s), ponderación 0.3 en 780-1000 nm. https://www.icnirp.org/cms/upload/publications/ICNIRPVisible_Infrared2013.pdf
- TI SBOA122 (X. Ramus, nov 2009): GBP = 2 pi RF CS f3dB^2; polo 1/(2 pi RF CF); ruido eq. 13.
