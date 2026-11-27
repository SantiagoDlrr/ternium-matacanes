"""Componente predictivo (plan, sección 8.E): ¿la información previa al Skinpass anticipa Y?

Un solo modelo de aprendizaje automático (``HistGradientBoostingRegressor``) contra una línea
base sencilla (media de Y por producto × dimensión en entrenamiento: lo que haría una receta por
producto), con la misma validación:

- ``GroupKFold`` (k = 5) por programa del Skinpass: ningún programa queda dividido;
- partición temporal: programas que empiezan en ene–ago (entrenamiento) contra sep–nov (prueba);
- ``KFold`` aleatorio, solo para mostrar cuánto infla el desempeño mezclar rollos de un programa.

El preset no entra (es componente de Y). Hiperparámetros: búsqueda pequeña con ``GroupKFold``
interno (k = 3) dentro de cada partición de entrenamiento. La importancia por permutación se
describe como "lo que usa el modelo para predecir", nunca como efecto (Shmueli, 2010).
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, KFold

from .config import SEMILLA

CATEGORICAS = ["producto", "dimension", "tipo"]
NUMERICAS = ["mes_num", "corona_rel_pct", "dev_te", "Espesor Objetivo", "Ancho Objetivo", "Temp Enrollado Obj"]
NOMBRES = {"producto": "Producto", "dimension": "Dimensión", "tipo": "Tipo de material", "mes_num": "Mes",
           "corona_rel_pct": "Corona relativa MC4", "dev_te": "Desv. T. enrollado",
           "Espesor Objetivo": "Espesor objetivo", "Ancho Objetivo": "Ancho objetivo",
           "Temp Enrollado Obj": "T. enrollado objetivo"}
REJILLA = [dict(learning_rate=lr, max_leaf_nodes=hojas) for lr, hojas in itertools.product([0.05, 0.1], [15, 31])]
MIN_ROLLOS_CATEGORIA = 30


def preparar(a: pd.DataFrame) -> pd.DataFrame:
    d = a.copy()
    d["mes_num"] = d["mes"].dt.month.astype(float)
    prog_ini = d.groupby("programa_skp")["fecha_skp"].transform("min")
    d["mes_prog"] = prog_ini.dt.month
    return d.reset_index(drop=True)


class Codificador:
    """Categorías a enteros, con las raras (< 30 rollos en entrenamiento) agrupadas en 'OTRO'."""

    def fit(self, d: pd.DataFrame):
        self.mapas = {}
        for c in CATEGORICAS:
            vc = d[c].value_counts()
            keep = vc[vc >= MIN_ROLLOS_CATEGORIA].index
            self.mapas[c] = {v: i for i, v in enumerate(keep)}
        return self

    def transform(self, d: pd.DataFrame) -> np.ndarray:
        cols = []
        for c in CATEGORICAS:
            mp = self.mapas[c]
            otro = len(mp)
            cols.append(d[c].map(mp).fillna(otro).to_numpy(float))
        for c in NUMERICAS:
            cols.append(d[c].to_numpy(float))
        return np.column_stack(cols)


def _modelo(params: dict) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        max_iter=300, min_samples_leaf=100, l2_regularization=1.0, random_state=SEMILLA,
        categorical_features=list(range(len(CATEGORICAS))), early_stopping=False, **params)


def _ajustar(tr: pd.DataFrame, buscar: bool = True) -> tuple[HistGradientBoostingRegressor, Codificador, dict]:
    mejor = REJILLA[0]
    if buscar:
        puntajes = []
        gkf = GroupKFold(n_splits=3)
        for params in REJILLA:
            maes = []
            for i_tr, i_va in gkf.split(tr, groups=tr["programa_skp"]):
                cod = Codificador().fit(tr.iloc[i_tr])
                mdl = _modelo(params).fit(cod.transform(tr.iloc[i_tr]), tr["y_corr"].iloc[i_tr])
                maes.append(mean_absolute_error(tr["y_corr"].iloc[i_va], mdl.predict(cod.transform(tr.iloc[i_va]))))
            puntajes.append(np.mean(maes))
        mejor = REJILLA[int(np.argmin(puntajes))]
    cod = Codificador().fit(tr)
    mdl = _modelo(mejor).fit(cod.transform(tr), tr["y_corr"])
    return mdl, cod, mejor


def linea_base(tr: pd.DataFrame, te: pd.DataFrame) -> np.ndarray:
    """Media de Y por producto × dimensión en entrenamiento; si no existe, por producto; si no, global."""
    m_pd = tr.groupby(["producto", "dimension"])["y_corr"].mean()
    m_p = tr.groupby("producto")["y_corr"].mean()
    pred = pd.Series(m_pd.reindex(pd.MultiIndex.from_frame(te[["producto", "dimension"]])).to_numpy(), index=te.index)
    pred = pred.fillna(te["producto"].map(m_p)).fillna(tr["y_corr"].mean())
    return pred.to_numpy()


def _metricas(y, p) -> dict:
    return {"MAE": mean_absolute_error(y, p), "RMSE": np.sqrt(mean_squared_error(y, p)), "R2": r2_score(y, p)}


def _particiones(d: pd.DataFrame):
    gkf = GroupKFold(n_splits=5)
    for k, (i_tr, i_te) in enumerate(gkf.split(d, groups=d["programa_skp"])):
        yield "Agrupada por programa (GroupKFold)", k + 1, i_tr, i_te
    i_tr = np.where(d["mes_prog"] <= 8)[0]
    i_te = np.where(d["mes_prog"] >= 9)[0]
    yield "Temporal (ene–ago → sep–nov)", 1, i_tr, i_te
    kf = KFold(n_splits=5, shuffle=True, random_state=SEMILLA)
    for k, (i_tr, i_te) in enumerate(kf.split(d)):
        yield "Aleatoria (KFold; mezcla programas)", k + 1, i_tr, i_te


def evaluar(a: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Desempeño por partición (modelo y línea base) e importancia por permutación (partición temporal)."""
    d = preparar(a)
    filas, imp = [], None
    for esquema, k, i_tr, i_te in _particiones(d):
        tr, te = d.iloc[i_tr], d.iloc[i_te]
        mdl, cod, params = _ajustar(tr)
        p_m = mdl.predict(cod.transform(te))
        p_b = linea_base(tr, te)
        fila = {"esquema": esquema, "particion": k, "rollos_entrenamiento": len(tr), "rollos_prueba": len(te),
                "programas_prueba": te["programa_skp"].nunique(),
                "programas_en_ambos": len(set(tr["programa_skp"]) & set(te["programa_skp"])),
                "hiperparametros": str(params)}
        for nombre, p in [("modelo", p_m), ("linea_base", p_b)]:
            for met, v in _metricas(te["y_corr"], p).items():
                fila[f"{met}_{nombre}"] = v
        filas.append(fila)
        if esquema.startswith("Temporal"):
            X_te = cod.transform(te)
            r = permutation_importance(mdl, X_te, te["y_corr"], n_repeats=5, random_state=SEMILLA,
                                       scoring="neg_mean_absolute_error")
            imp = pd.DataFrame({"variable": [NOMBRES[c] for c in CATEGORICAS + NUMERICAS],
                                "aumento_MAE_kN": r.importances_mean, "de": r.importances_std}
                               ).sort_values("aumento_MAE_kN", ascending=False)
    t = pd.DataFrame(filas)
    for met in ["MAE", "RMSE", "R2"]:
        t[f"{met}_dif"] = t[f"{met}_modelo"] - t[f"{met}_linea_base"]
    return t, imp


def resumen(t: pd.DataFrame) -> pd.DataFrame:
    g = t.groupby("esquema", sort=False)
    out = g[["MAE_modelo", "MAE_linea_base", "MAE_dif", "RMSE_modelo", "RMSE_linea_base",
             "R2_modelo", "R2_linea_base", "R2_dif"]].agg(["mean", "std"])
    out.columns = [f"{a}_{b}" for a, b in out.columns]
    out["particiones"] = g.size()
    out["particiones_donde_modelo_mejora_MAE"] = g["MAE_dif"].apply(lambda s: int((s < 0).sum()))
    return out.reset_index()
