"""Análisis del artículo (plan, secciones 7–8.D y 9–11): soporte, resultado principal,
heterogeneidad, validación y robustez. Las figuras están en ``src/figuras_articulo.py``.

Convenciones:
- ``a`` es la población analítica (paso 4) y ``a5`` la de la asociación (paso 5), ambas de
  ``skinpass.analitica``.
- Toda estimación reporta rollos **y** programas del Skinpass.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import inferencia as inf
from .config import TABLAS_DIR

NIVELES = ["tipo", "producto", "dimension", "programa_skp"]
NIVELES_ALT = ["tipo", "programa_skp", "producto", "dimension"]
NOMBRE_NIVEL = {"tipo": "Tipo de material", "producto": "Producto", "dimension": "Dimensión",
                "programa_skp": "Programa del Skinpass", "dia_skp": "Día del Skinpass",
                "semana_skp": "Semana del Skinpass", "rodillo_trabajo": "Rodillo de trabajo"}
EXPOS = ["corona_rel_pct", "dev_te"]
FE = "celda"            # producto × dimensión × mes
CLUSTER = "programa_skp"


# ============================================================================ cifras para el texto
def guardar_cifras(d: dict) -> None:
    """Agrega cifras a ``outputs/tablas/cifras.json`` (se convierten en macros LaTeX)."""
    ruta = TABLAS_DIR / "cifras.json"
    actual = json.loads(ruta.read_text()) if ruta.exists() else {}
    actual.update({k: str(v) for k, v in d.items()})
    ruta.write_text(json.dumps(dict(sorted(actual.items())), ensure_ascii=False, indent=1))


def fmt(x: float, nd: int = 1) -> str:
    """Número con separador de miles y signo menos tipográfico (para LaTeX)."""
    x = float(x)
    if round(x, nd) == 0:
        x = 0.0  # evita "−0.0"
    s = f"{x:,.{nd}f}"
    return s.replace("-", "−")


# ============================================================================ soporte (sección 7)
def soporte_por_producto(a: pd.DataFrame, a5: pd.DataFrame) -> pd.DataFrame:
    g = a.groupby("producto")
    t = pd.DataFrame({
        "tipo": g["tipo"].agg(lambda s: s.mode().iat[0]),
        "rollos": g.size(),
        "programas_skp": g["programa_skp"].nunique(),
        "meses": g["mes_str"].nunique(),
        "pct_preset_cero": 100 * g["preset_cero"].mean(),
    })
    c = a5.groupby(["producto", FE])
    cel = pd.DataFrame({"n": c.size(), "sd": c["corona_rel_pct"].std(), "rango": c["corona_rel_pct"].agg(lambda s: s.max() - s.min())})
    cel = cel.reset_index()
    t["celdas_ge5"] = cel[cel["n"] >= 5].groupby("producto").size()
    t["rollos_en_celdas_ge2"] = cel[cel["n"] >= 2].groupby("producto")["n"].sum()
    pesos = cel[cel["n"] >= 2]
    t["sd_corona_dentro_celda"] = pesos.groupby("producto").apply(lambda d: np.average(d["sd"], weights=d["n"]))
    t["rango_corona_dentro_celda_mediano"] = pesos.groupby("producto")["rango"].median()
    t = t.fillna({"celdas_ge5": 0, "rollos_en_celdas_ge2": 0})
    t["con_soporte"] = (t["rollos_en_celdas_ge2"] > 0) & (t["sd_corona_dentro_celda"].fillna(0) > 0)
    return t.sort_values("rollos", ascending=False)


def soporte_resumen(a: pd.DataFrame, a5: pd.DataFrame, sop: pd.DataFrame) -> pd.DataFrame:
    """Tabla de soporte del artículo: por tipo de material y total."""
    filas = []
    for tipo, sub in list(a.groupby("tipo")) + [("Total", a)]:
        s5 = a5[a5["tipo"].eq(tipo)] if tipo != "Total" else a5
        c = s5.groupby(FE)["corona_rel_pct"]
        n = c.size()
        sd = c.std()
        sp = sop[sop["tipo"].eq(tipo)] if tipo != "Total" else sop
        filas.append({
            "Tipo": tipo, "Rollos": len(sub), "Programas SKP": sub["programa_skp"].nunique(),
            "Productos": sub["producto"].nunique(),
            "Productos con ≥300 rollos": int((sp["rollos"] >= 300).sum()),
            "Celdas p×d×m": sub[FE].nunique(),
            "% rollos en celdas ≥5": 100 * sub[FE].map(sub[FE].value_counts()).ge(5).mean(),
            "DE corona rel. dentro de celda (pp)": float(np.average(sd[n >= 2], weights=n[n >= 2])),
            "% preset = 0": 100 * sub["preset_cero"].mean(),
        })
    return pd.DataFrame(filas)


# ============================================================================ resultado principal
def descomposiciones(a: pd.DataFrame, n_perm: int = 100, n_boot: int = 200) -> dict[str, pd.DataFrame]:
    out = {
        "principal": inf.exceso_sobre_azar(a, "y_corr", NIVELES, n_perm=n_perm, n_boot=n_boot),
        "orden_programa_primero": inf.exceso_sobre_azar(a, "y_corr", NIVELES_ALT, n_perm=n_perm, n_boot=n_boot),
    }
    return out


def asociacion(a5: pd.DataFrame, y: str = "y_corr", xs: list[str] | None = None, fe: str = FE,
               cluster: str = CLUSTER) -> pd.DataFrame:
    return inf.fe_ols(a5, y, xs or EXPOS, fe, cluster)


def indicadores_secundarios(a5: pd.DataFrame) -> pd.DataFrame:
    """Misma especificación con cada indicador secundario como resultado (plan, sección 4)."""
    d = a5.copy()
    d["def_inspector_pp"] = 100 * d["def_inspector_skp"].astype(float)
    d["retenido_pp"] = 100 * d["retenido_skp"].astype(float)
    filas = []
    specs = [
        ("bend_real", "Bending real (kN)", d),
        ("def_inspector_pp", "Defecto de inspector en el Skinpass (pp)", d),
        ("retenido_pp", "RETENIDO en el Skinpass (pp)", d),
        ("elongacion", "Elongación lograda, modo Elongación (%)", d[d["modo_molino"].eq("Elongación")]),
        ("bend_preset", "Preset de bending (kN; comprobación de S3)", d),
    ]
    for y, nombre, sub in specs:
        r = inf.fe_ols(sub, y, EXPOS, FE, CLUSTER)
        r.insert(0, "resultado", nombre)
        filas.append(r)
    return pd.concat(filas, ignore_index=True)


def pendientes_por_producto(a5: pd.DataFrame, min_rollos: int = 300) -> pd.DataFrame:
    """Pendiente de corona → Y dentro de cada producto (FE dimensión × mes; errores por programa)."""
    d = a5.copy()
    d["celda_dm"] = d["dimension"] + " | " + d["mes_str"]
    n = d.groupby("producto").size()
    filas = []
    for prod in n[n >= min_rollos].index:
        sub = d[d["producto"].eq(prod)]
        try:
            r = inf.fe_ols(sub, "y_corr", EXPOS, "celda_dm", CLUSTER).iloc[0]
        except np.linalg.LinAlgError:
            continue
        filas.append({"producto": prod, "tipo": sub["tipo"].mode().iat[0], "coef": r["coef"], "se": r["se"],
                      "ic_inf": r["ic_inf"], "ic_sup": r["ic_sup"], "p": r["p"], "rollos": int(r["rollos"]),
                      "programas": int(r["grupos_cluster"]), "rollos_producto": int(n[prod])})
    t = pd.DataFrame(filas)
    t = pd.concat([t, inf.bh(t["p"])], axis=1)
    return t.sort_values("coef").reset_index(drop=True)


# ============================================================================ validación y robustez
def control_negativo(a5: pd.DataFrame) -> pd.DataFrame:
    d = a5.copy()
    d["inclusiones"] = d["def_inclus"].astype(float)
    r = inf.fe_ols(d, "y_corr", ["inclusiones"], FE, CLUSTER)
    r2 = inf.fe_ols(d, "y_corr", ["inclusiones", *EXPOS], FE, CLUSTER)
    r.insert(0, "modelo", "Y ~ inclusiones + FE")
    r2.insert(0, "modelo", "Y ~ inclusiones + corona + desv. T. enrollado + FE")
    return pd.concat([r, r2], ignore_index=True)


def _resumen_descomp(t: pd.DataFrame, nivel_grupo: str) -> dict:
    t = t.set_index("nivel")
    return {"exceso_producto": t.loc["producto", "exceso"], "exceso_grupo": t.loc[nivel_grupo, "exceso"],
            "programa_mayor_que_producto": bool(t.loc[nivel_grupo, "exceso"] > t.loc["producto", "exceso"])}


def variante(m: pd.DataFrame, nombre: str, alternativa: str, base_paso: str = "paso4",
             preparar=None, cov_extra: list[str] | None = None, grupo: str = "programa_skp",
             y: str = "y_corr", n_perm: int = 20) -> dict:
    """Recalcula las dos salidas de V3 (pendiente de corona y orden grupo vs producto) para una variante."""
    from .skinpass import analitica

    a = analitica(m, base_paso)
    if preparar is not None:
        a = preparar(a)
    a = a.dropna(subset=[y])
    a5 = a.dropna(subset=["corona_rel_pct"])
    r = inf.fe_ols(a5, y, ["corona_rel_pct", "dev_te", *(cov_extra or [])], FE, grupo).iloc[0]
    t = inf.exceso_sobre_azar(a, y, ["tipo", "producto", "dimension", grupo], grupo_boot=None, n_perm=n_perm, n_boot=0)
    out = {"robustez": nombre, "alternativa": alternativa, "coef": r["coef"], "ic_inf": r["ic_inf"],
           "ic_sup": r["ic_sup"], "p": r["p"], "rollos": int(r["rollos"]), "grupos": int(r["grupos_cluster"]),
           "rollos_descomp": len(a)}
    out.update(_resumen_descomp(t, grupo))
    return out
