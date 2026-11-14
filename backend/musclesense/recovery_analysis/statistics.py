"""¿Aporta la NIRS información sobre la recuperación de la fuerza?

La comparación central no es "rasgo NIRS contra fuerza", porque ambos dependen del tiempo
desde el ejercicio y la correlación saldría alta aunque la NIRS no aportara nada. La pregunta
es si, **en un instante dado de la recuperación**, la NIRS mejora la predicción de la fuerza más
allá de lo que el experimentador ya sabe: la dosis de ejercicio. Por eso se ajusta un modelo
por marca (0, 5, 15 y 30 min; el tiempo queda implícito) y se comparan predictores anidados:

    nulo            solo la media de la marca
    dosis           intensidad, duración y tipo de contracción
    nirs            rasgos NIRS estimados por el sensor (sin dosis)
    dosis_nirs      dosis + rasgos NIRS estimados
    dosis_oraculo   dosis + los mismos rasgos calculados con los cambios reales en el músculo

La diferencia dosis_nirs - dosis es lo que aporta el sensor; oráculo - dosis_nirs es lo que se
pierde por el instrumento (grasa, ruido, Beer-Lambert, mioglobina); oráculo - dosis es la cota
de lo que la hemodinámica muscular contiene sobre la fuerza bajo los supuestos del modelo.

Un modelo por marca deja una sola fila por sujeto, de modo que la validación cruzada (KFold
sobre sujetos) y la elección interna de la regularización (dejar uno fuera) operan sobre
observaciones independientes. Un modelo común a las cuatro marcas repetiría los rasgos de sesión
en las cuatro filas de cada sujeto y la regularización interna premiaría memorizar sujetos.
El alcance 'global' concatena las predicciones de las cuatro marcas; su R² lo domina el tiempo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, RidgeCV
from sklearn.metrics import mean_absolute_error, r2_score, roc_auc_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from .dataset import RECOVERY_MARKS, feature_columns

__all__ = ["FEATURE_SETS", "RECOVERED_THRESHOLD", "make_model", "evaluate", "feature_associations",
           "dissociation_table", "nirs_gain"]

RECOVERED_THRESHOLD = 0.95  # fuerza >= 95 % de la previa: dentro de la variabilidad día a día de la MVC
_DOSIS = ["intensidad_pct_mvc", "duracion_s", "es_dinamico", "es_excentrico"]

FEATURE_SETS = {
    "nulo": [],
    "dosis": _DOSIS,
    "nirs": feature_columns("nirs"),
    "dosis_nirs": _DOSIS + feature_columns("nirs"),
    "dosis_oraculo": _DOSIS + feature_columns("verdad"),
}


def make_model(kind: str, seed: int = 0):
    """Modelo de regresión: 'ridge' (lineal, regularizado) o 'hgb' (árboles potenciados).

    En 'ridge' los rasgos estandarizados se recortan a ±3 desviaciones: varios rasgos tienen
    colas largas o casi no varían (en el oráculo sin acoplamientos, diferencias de 1e-7 uM), y
    sin recorte un solo sujeto extremo domina el ajuste.
    """
    if kind == "ridge":
        return make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(),
                             FunctionTransformer(np.clip, kw_args={"a_min": -3.0, "a_max": 3.0}),
                             RidgeCV(alphas=np.logspace(-3, 3, 13)))
    if kind == "hgb":
        return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, min_samples_leaf=10,
                                             l2_regularization=1.0, random_state=seed)
    raise ValueError(f"modelo desconocido: {kind!r}")


def _metricas(y: np.ndarray, pred: np.ndarray, umbral: float) -> dict:
    no_recuperado = y < umbral
    auc = roc_auc_score(no_recuperado, -pred) if 0 < no_recuperado.sum() < y.size else np.nan
    return {
        "r2": r2_score(y, pred) if y.size > 1 and np.var(y) > 0 else np.nan,
        "mae": mean_absolute_error(y, pred),
        "rmse": float(np.sqrt(np.mean((y - pred) ** 2))),
        "auc_no_recuperado": auc,
        "n": int(y.size),
    }


def evaluate(df: pd.DataFrame, feature_sets: dict | None = None, models=("ridge", "hgb"), n_splits: int = 5,
             threshold: float = RECOVERED_THRESHOLD, seed: int = 0) -> pd.DataFrame:
    """Predicción de la capacidad de fuerza con un modelo por marca y validación cruzada.

    Devuelve una fila por nivel de acoplamiento, conjunto de predictores, modelo y alcance
    ('global' o cada marca). Las predicciones se recortan a [0, 1]. Las particiones son las
    mismas para todos los conjuntos y modelos (comparación pareada).
    """
    conjuntos = feature_sets or FEATURE_SETS
    filas = []
    for nivel, datos in df.groupby("nivel", sort=False):
        datos = datos.reset_index(drop=True)
        marcas = [m for m in RECOVERY_MARKS if (datos["marca"] == m).any()]
        n_sujetos = datos.groupby("marca").size().min()
        k = min(n_splits, int(n_sujetos))
        if k < 2:
            raise ValueError("hacen falta al menos dos sujetos para la validación cruzada")
        cv = KFold(n_splits=k, shuffle=True, random_state=seed)
        for nombre, columnas in conjuntos.items():
            if any(c not in datos for c in columnas):
                continue  # p. ej. rasgos nirs_* en una cohorte simulada sin óptica
            tipos = models if columnas else ("media",)
            for tipo in tipos:
                y_todo, pred_todo = [], []
                for marca in marcas:
                    d = datos[datos["marca"] == marca].sort_values("sujeto")
                    y = d["fuerza"].to_numpy()
                    if columnas:
                        X, modelo = d[columnas].to_numpy(dtype=float), make_model(tipo, seed)
                    else:
                        X, modelo = np.zeros((len(d), 1)), DummyRegressor()
                    pred = np.clip(cross_val_predict(modelo, X, y, cv=cv), 0.0, 1.0)
                    filas.append({"nivel": nivel, "conjunto": nombre, "modelo": tipo, "alcance": marca,
                                  **_metricas(y, pred, threshold)})
                    y_todo.append(y)
                    pred_todo.append(pred)
                filas.append({"nivel": nivel, "conjunto": nombre, "modelo": tipo, "alcance": "global",
                              **_metricas(np.concatenate(y_todo), np.concatenate(pred_todo), threshold)})
    return pd.DataFrame(filas)


def nirs_gain(evaluation: pd.DataFrame, model: str = "ridge") -> pd.DataFrame:
    """R² por conjunto y ganancias del sensor y del oráculo sobre la dosis, por nivel y alcance."""
    ev = evaluation[evaluation["modelo"].isin([model, "media"])]
    tabla = ev.pivot_table(index=["nivel", "alcance"], columns="conjunto", values="r2", sort=False)
    salida = pd.DataFrame(index=tabla.index)
    for conjunto in FEATURE_SETS:
        if conjunto in tabla:
            salida[f"r2_{conjunto}"] = tabla[conjunto]
    if {"dosis", "dosis_nirs"} <= set(tabla):
        salida["ganancia_nirs"] = tabla["dosis_nirs"] - tabla["dosis"]
    if {"dosis", "dosis_oraculo"} <= set(tabla):
        salida["ganancia_oraculo"] = tabla["dosis_oraculo"] - tabla["dosis"]
        if "ganancia_nirs" in salida:
            salida["perdida_instrumento"] = salida["ganancia_oraculo"] - salida["ganancia_nirs"]
    return salida.reset_index()


def _residuo(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    return y - LinearRegression().fit(X, y).predict(X)


def feature_associations(df: pd.DataFrame, prefixes=("nirs", "verdad")) -> pd.DataFrame:
    """Correlación de Spearman de cada rasgo con la fuerza, dentro de cada marca.

    ``rho_parcial`` controla la dosis de ejercicio: correlación de rangos entre los residuos de
    rasgo ~ dosis y fuerza ~ dosis (regresión lineal dentro de la marca).
    """
    filas = []
    for (nivel, marca), datos in df.groupby(["nivel", "marca"], sort=False):
        dosis = datos[_DOSIS].to_numpy(dtype=float)
        fuerza = datos["fuerza"].to_numpy()
        for prefijo in prefixes:
            for col in feature_columns(prefijo):
                if col not in datos:
                    continue
                x = datos[col].to_numpy(dtype=float)
                ok = np.isfinite(x)
                fila = {"nivel": nivel, "marca": marca, "rasgo": col, "n": int(ok.sum()),
                        "rho": np.nan, "p": np.nan, "rho_parcial": np.nan, "p_parcial": np.nan}
                if ok.sum() >= 5 and np.ptp(x[ok]) > 0 and np.ptp(fuerza[ok]) > 0:
                    fila["rho"], fila["p"] = stats.spearmanr(x[ok], fuerza[ok])
                    rx, rf = _residuo(x[ok], dosis[ok]), _residuo(fuerza[ok], dosis[ok])
                    if np.ptp(rx) > 1e-12 and np.ptp(rf) > 1e-12:
                        fila["rho_parcial"], fila["p_parcial"] = stats.spearmanr(rx, rf)
                filas.append(fila)
    return pd.DataFrame(filas)


def dissociation_table(df: pd.DataFrame, reox_threshold: float = 0.9, force_threshold: float = RECOVERED_THRESHOLD,
                       prefix: str = "verdad") -> pd.DataFrame:
    """Reoxigenación frente a recuperación de la fuerza en cada marca.

    ``reox_sin_fuerza`` es la fracción de sujetos que ya recuperaron al menos ``reox_threshold``
    de la caída de oxigenación pero aún no la fuerza: los casos en que leer la reoxigenación
    como recuperación sería un error.
    """
    col = f"{prefix}_reox_frac"
    filas = []
    for (nivel, marca), d in df.groupby(["nivel", "marca"], sort=False):
        reox = d[col] >= reox_threshold
        recup = d["fuerza"] >= force_threshold
        filas.append({
            "nivel": nivel, "marca": marca, "n": len(d),
            "reox_frac_media": d[col].mean(), "fuerza_media": d["fuerza"].mean(),
            "fuerza_min": d["fuerza"].min(),
            "reoxigenados": reox.mean(), "recuperados": recup.mean(),
            "reox_sin_fuerza": (reox & ~recup).mean(),
        })
    return pd.DataFrame(filas)
