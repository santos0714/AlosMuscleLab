"""Modelo de tejido en tres capas: piel, tejido adiposo subcutáneo y músculo.

Cada capa calcula su absorción a partir de su composición,

    mua = sangre·Hb·[S·a_oxi + (1-S)·a_desoxi] + Mb·[Smb·a_oxi + (1-Smb)·a_desoxi]
          + agua·mua_agua + lípido·mua_lípido + melanosomas·mua_melanosoma + base,

y su esparcimiento reducido con la ley de potencia mus' = a·(lambda/500 nm)^(-b).
Los valores por defecto salen de ``data/parametros_opticos.json`` (Jacques 2013) y de
``data/parametros_fisiologicos.json``. Unidades: mm, mm^-1, mM de grupo hemo.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np

from ..exercise_protocol.model import PhysiologyParams, _rest_state, load_physiology_reference
from ..optical_physics import spectra
from ..optical_physics.diffusion import LayerOptics

__all__ = ["TissueLayer", "TissueModel", "PROFILES", "load_optical_reference", "skin_baseline_absorption"]

EPIDERMIS_MM = 0.06  # grosor de epidermis usado por Jacques para la fracción de melanosomas


@lru_cache(maxsize=1)
def load_optical_reference() -> dict:
    with open(spectra.DATA_DIR / "parametros_opticos.json", encoding="utf-8") as archivo:
        return json.load(archivo)


def _fis(clave: str) -> float:
    return float(load_physiology_reference()[clave]["valor_nominal"])


def skin_baseline_absorption(wavelength_nm):
    """Absorción de la piel sin sangre ni melanina (Jacques), en mm^-1."""
    wl = np.asarray(wavelength_nm, dtype=float)
    return (0.244 + 85.3 * np.exp(-(wl - 154.0) / 66.2)) / 10.0


@dataclass(frozen=True)
class TissueLayer:
    name: str
    thickness_mm: float
    scatter_a_mm: float  # mus' a 500 nm, en mm^-1
    scatter_b: float
    g: float = 0.9
    n: float = 1.4
    blood_volume_fraction: float = 0.0
    blood_so2: float = 0.7
    hb_heme_mM: float = 9.302
    myoglobin_mM: float = 0.0
    smbo2: float = 1.0
    water_fraction: float = 0.0
    lipid_fraction: float = 0.0
    melanosome_fraction: float = 0.0
    skin_baseline: bool = False

    def static_absorption(self, wavelength_nm):
        """Absorción que no depende de la sangre ni de la mioglobina, en mm^-1."""
        wl = np.asarray(wavelength_nm, dtype=float)
        mua = self.water_fraction * spectra.water_absorption(wl) + self.lipid_fraction * spectra.lipid_absorption(wl)
        mua = mua + self.melanosome_fraction * spectra.melanosome_absorption(wl)
        if self.skin_baseline:
            mua = mua + (1.0 - self.melanosome_fraction) * skin_baseline_absorption(wl)
        return mua

    def heme_absorption(self, wavelength_nm, blood_volume_fraction=None, blood_so2=None, smbo2=None):
        """Absorción de hemoglobina y mioglobina; acepta series temporales en los tres argumentos."""
        oxi, desoxi = spectra.heme_absorption(wavelength_nm)
        v = self.blood_volume_fraction if blood_volume_fraction is None else blood_volume_fraction
        s = self.blood_so2 if blood_so2 is None else blood_so2
        sm = self.smbo2 if smbo2 is None else smbo2
        sangre = v * self.hb_heme_mM * (s * oxi + (1.0 - s) * desoxi)
        mio = self.myoglobin_mM * (sm * oxi + (1.0 - sm) * desoxi)
        return sangre + mio

    def mua(self, wavelength_nm):
        return self.static_absorption(wavelength_nm) + self.heme_absorption(wavelength_nm)

    def musp(self, wavelength_nm):
        return self.scatter_a_mm * (np.asarray(wavelength_nm, dtype=float) / 500.0) ** (-self.scatter_b)

    def optics(self, wavelength_nm: float, semi_infinite: bool = False) -> LayerOptics:
        grosor = np.inf if semi_infinite else self.thickness_mm
        return LayerOptics(grosor, float(self.mua(wavelength_nm)), float(self.musp(wavelength_nm)), self.n, self.g)


@dataclass(frozen=True)
class TissueModel:
    skin: TissueLayer
    fat: TissueLayer
    muscle: TissueLayer

    @property
    def layers(self) -> tuple:
        return (self.skin, self.fat, self.muscle)

    def optics(self, wavelength_nm: float) -> list:
        """Propiedades ópticas por capa; el músculo se trata como semiinfinito."""
        return [self.skin.optics(wavelength_nm), self.fat.optics(wavelength_nm),
                self.muscle.optics(wavelength_nm, semi_infinite=True)]

    @classmethod
    def default(cls, att_mm: float | None = None, skin_mm: float | None = None,
                melanosome_epidermis: float | None = None,
                physiology: PhysiologyParams | None = None) -> "TissueModel":
        """Tejido de referencia; la composición del músculo se toma de la fisiología del sujeto."""
        p = physiology or PhysiologyParams()
        esp = load_optical_reference()["esparcimiento"]
        skin_mm = _fis("piel_grosor_mm") if skin_mm is None else skin_mm
        att_mm = _fis("att_biceps_mm") if att_mm is None else att_mm
        f_mel = _fis("melanina_epidermis") if melanosome_epidermis is None else melanosome_epidermis
        sc_rest, _, _ = _rest_state(p)
        smo2_rest = p.arterial_volume_fraction * p.sao2 + (1.0 - p.arterial_volume_fraction) * sc_rest

        def capa(nombre, clave, grosor, **extra):
            e = esp[clave]
            return TissueLayer(nombre, grosor, e["a_cm1"] / 10.0, e["b"], e["g"], e["n"], hb_heme_mM=p.hb_heme_mM, **extra)

        piel = capa("piel", "dermis", skin_mm, blood_volume_fraction=_fis("fraccion_sangre_dermis"),
                    water_fraction=_fis("agua_piel"), melanosome_fraction=f_mel * EPIDERMIS_MM / skin_mm,
                    skin_baseline=True)
        grasa = capa("grasa", "grasa", att_mm, blood_volume_fraction=_fis("fraccion_sangre_grasa"),
                     water_fraction=_fis("agua_grasa"), lipid_fraction=_fis("lipido_grasa"))
        musculo = capa("musculo", "musculo", _fis("musculo_grosor_mm"), blood_volume_fraction=p.blood_volume_fraction,
                       blood_so2=smo2_rest, myoglobin_mM=p.myoglobin_mM, smbo2=p.smbo2_rest,
                       water_fraction=_fis("agua_musculo"), lipid_fraction=_fis("lipido_musculo"))
        return cls(piel, grasa, musculo)

    def with_att(self, att_mm: float) -> "TissueModel":
        return replace(self, fat=replace(self.fat, thickness_mm=att_mm))


# Perfiles de sujeto: grosor de grasa sobre el bíceps y fracción de melanosomas de la epidermis
PROFILES = {
    "referencia": {"att_mm": 3.0, "melanosome_epidermis": 0.04},
    "delgado": {"att_mm": 1.5, "melanosome_epidermis": 0.04},
    "adiposidad_media": {"att_mm": 5.0, "melanosome_epidermis": 0.04},
    "adiposidad_alta": {"att_mm": 9.0, "melanosome_epidermis": 0.04},
    "piel_oscura": {"att_mm": 3.0, "melanosome_epidermis": 0.30},
}
