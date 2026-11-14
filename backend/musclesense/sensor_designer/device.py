"""Instrumento virtual: emisores LED, fotodiodo, amplificador de transimpedancia, ADC y
microcontrolador, con componentes del catálogo ``data/componentes.json``.

Cadena de señal por LED y por trama:

    potencia emitida · acoplamiento · R(rho) [1/mm^2] · área del fotodiodo  -> potencia detectada
    potencia detectada · responsividad                                      -> fotocorriente
    fotocorriente · Rf                                                      -> tensión
    tensión / LSB                                                           -> cuentas

Ruido referido a la entrada, integrado en el ancho de banda B = 1/(2·t_encendido):
shot 2q·I·B, térmico de Rf 4kT·B/Rf, corriente del amplificador in²·B y tensión del
amplificador en²·(1/Rf² + (2·pi·C)²·B²/3)·B. Con resta de luz ambiente se suma el ruido de la
ranura oscura. La cuantización añade LSB²/12.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from functools import lru_cache

import numpy as np

from ..optical_physics.spectra import DATA_DIR

__all__ = ["LedSpec", "PhotodiodeSpec", "TiaSpec", "AdcSpec", "McuSpec", "SensorDesign", "load_catalog"]

_Q = 1.602176634e-19
_KT = 1.380649e-23 * 300.0


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    with open(DATA_DIR / "componentes.json", encoding="utf-8") as archivo:
        return json.load(archivo)


def _buscar(grupo: str, numero_parte: str) -> dict:
    for item in load_catalog().get(grupo, []):
        if str(item.get("numero_parte", "")).startswith(numero_parte):
            return item
    return {}


def _num(item: dict, clave: str, defecto: float) -> float:
    valor = item.get(clave)
    return float(valor) if isinstance(valor, (int, float)) else float(defecto)


@dataclass(frozen=True)
class LedSpec:
    part: str
    peak_nm: float
    fwhm_nm: float
    radiant_power_mW: float
    coupling_efficiency: float = 0.5  # (supuesto) fracción de la potencia que entra en el tejido

    @classmethod
    def from_catalog(cls, numero_parte: str, peak_nm: float, fwhm_nm: float, power_mW: float) -> "LedSpec":
        item = _buscar("leds", numero_parte)
        return cls(numero_parte, _num(item, "lambda_pico_nm", peak_nm), _num(item, "fwhm_nm", fwhm_nm),
                   _num(item, "potencia_radiante_mW", power_mW))


@dataclass(frozen=True)
class PhotodiodeSpec:
    part: str = "BPW34"
    area_mm2: float = 7.5
    responsivity_A_W: tuple = ((760.0, 0.50), (810.0, 0.55), (850.0, 0.60))
    dark_current_nA: float = 2.0
    capacitance_pF: float = 70.0
    collection_efficiency: float = 1.0  # (supuesto) fracción de la luz saliente que acepta

    def responsivity(self, wavelength_nm):
        lam, resp = np.array(self.responsivity_A_W).T
        return np.interp(wavelength_nm, lam, resp)


@dataclass(frozen=True)
class TiaSpec:
    part: str = "OPA380"
    rf_ohm: float = 1.0e6
    cf_pF: float = 10.0
    en_nV_rtHz: float = 67.0
    in_fA_rtHz: float = 10.0
    cin_pF: float = 3.0

    @property
    def bandwidth_hz(self) -> float:
        return 1.0 / (2.0 * np.pi * self.rf_ohm * self.cf_pF * 1e-12)


@dataclass(frozen=True)
class AdcSpec:
    part: str = "ADS1220"
    bits: int = 24
    vref_V: float = 2.048

    @property
    def lsb_V(self) -> float:
        return self.vref_V / 2**self.bits


@dataclass(frozen=True)
class McuSpec:
    """Microcontrolador virtual: secuencia los LED, promedia y resta la luz ambiente."""

    part: str = "nRF52840"
    frame_rate_hz: float = 10.0
    led_on_time_ms: float = 5.0
    ambient_subtraction: bool = True


@dataclass(frozen=True)
class SensorDesign:
    leds: tuple = field(default_factory=lambda: (
        LedSpec.from_catalog("LED760-01AU", 760.0, 30.0, 19.0),
        LedSpec.from_catalog("LED810-01AU", 810.0, 35.0, 22.0),
        LedSpec.from_catalog("VSMY2850G", 850.0, 30.0, 55.0),
    ))
    photodiode: PhotodiodeSpec = field(default_factory=PhotodiodeSpec)
    tia: TiaSpec = field(default_factory=TiaSpec)
    adc: AdcSpec = field(default_factory=AdcSpec)
    mcu: McuSpec = field(default_factory=McuSpec)
    sds_mm: float = 30.0  # distancia emisor-detector
    ambient_photocurrent_nA: float = 5.0

    def __post_init__(self):
        if not 5.0 <= self.sds_mm <= 60.0:
            raise ValueError("la distancia emisor-detector debe estar entre 5 y 60 mm")
        if (len(self.leds) + 1) * self.mcu.led_on_time_ms * 1e-3 > 1.0 / self.mcu.frame_rate_hz:
            raise ValueError("los tiempos de encendido no caben en una trama a esa frecuencia")

    @property
    def wavelengths(self) -> tuple:
        return tuple(led.peak_nm for led in self.leds)

    def photocurrent(self, reflectance_per_mm2, led_index: int, responsivity: float | None = None):
        """Fotocorriente de señal [A] para una reflectancia R(rho) [1/mm^2]."""
        led = self.leds[led_index]
        resp = self.photodiode.responsivity(led.peak_nm) if responsivity is None else responsivity
        potencia = led.radiant_power_mW * 1e-3 * led.coupling_efficiency
        return potencia * np.asarray(reflectance_per_mm2) * self.photodiode.area_mm2 * self.photodiode.collection_efficiency * resp

    def noise_current_rms(self, i_signal):
        """Ruido rms referido a la entrada [A] de una muestra (ya con la resta de ambiente)."""
        tia, pd = self.tia, self.photodiode
        b = 1.0 / (2.0 * self.mcu.led_on_time_ms * 1e-3)
        c_total = (pd.capacitance_pF + tia.cin_pF + tia.cf_pF) * 1e-12
        i_fondo = (pd.dark_current_nA + self.ambient_photocurrent_nA) * 1e-9
        fijo = (4.0 * _KT / tia.rf_ohm + (tia.in_fA_rtHz * 1e-15) ** 2
                + (tia.en_nV_rtHz * 1e-9) ** 2 * (1.0 / tia.rf_ohm**2 + (2.0 * np.pi * c_total) ** 2 * b**2 / 3.0)) * b
        var = 2.0 * _Q * (np.asarray(i_signal) + i_fondo) * b + fijo
        if self.mcu.ambient_subtraction:
            var = var + 2.0 * _Q * i_fondo * b + fijo
        lsb_i = self.adc.lsb_V / tia.rf_ohm
        return np.sqrt(var + lsb_i**2 / 12.0 * (2.0 if self.mcu.ambient_subtraction else 1.0))

    def acquire(self, i_signal, rng: np.random.Generator | None = None) -> dict:
        """Convierte la fotocorriente de señal (T,) en cuentas del ADC, con ruido si se da rng."""
        i_signal = np.asarray(i_signal, dtype=float)
        ruido = self.noise_current_rms(i_signal)
        i_medida = i_signal + (rng.normal(0.0, 1.0, i_signal.shape) * ruido if rng is not None else 0.0)
        i_fondo = (self.photodiode.dark_current_nA + self.ambient_photocurrent_nA) * 1e-9
        saturado = (i_signal + i_fondo) * self.tia.rf_ohm > self.adc.vref_V
        cuentas = np.round(i_medida * self.tia.rf_ohm / self.adc.lsb_V)
        snr = 20.0 * np.log10(np.maximum(i_signal, 1e-30) / ruido)
        return {"counts": cuentas, "snr_db": snr, "saturated": saturado, "noise_rms_A": ruido}

    def with_sds(self, sds_mm: float) -> "SensorDesign":
        return replace(self, sds_mm=sds_mm)
