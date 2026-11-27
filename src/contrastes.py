"""Tabla completa de contrastes examinados (plan, sección 11) → ``outputs/tablas/contrastes_completos.csv``.

Reúne, desde las salidas de los notebooks 08–10, todo lo que se estimó (no solo lo que aparece
en el cuerpo del artículo), con estimación, intervalo, unidades, valor p y valor q de
Benjamini–Hochberg donde corresponde.
"""
from __future__ import annotations

import pandas as pd

from .config import TABLAS_DIR

COLS = ["familia", "contraste", "resultado", "estimacion", "ic_inf", "ic_sup", "unidades", "p", "q_bh",
        "rollos", "grupos", "nota"]


def _leer(nombre: str) -> pd.DataFrame:
    return pd.read_csv(TABLAS_DIR / nombre)


def consolidar() -> pd.DataFrame:
    filas = []
    add = lambda **k: filas.append({c: k.get(c) for c in COLS})

    for nombre, fam in [("descomposicion_principal.csv", "8.B descomposición (orden del plan)"),
                        ("descomposicion_orden_programa_primero.csv", "8.B descomposición (programa primero)")]:
        for _, r in _leer(nombre).iterrows():
            add(familia=fam, contraste=f"exceso sobre el azar: {r['nivel']}", resultado="Y",
                estimacion=100 * r["exceso"], ic_inf=100 * r["exceso_ic_inf"], ic_sup=100 * r["exceso_ic_sup"],
                unidades="% de la SC de Y", rollos=r["rollos"], grupos=r["grupos_en_el_nivel"],
                nota=f"observado {100 * r['fraccion_observada']:.1f} %, nulo {100 * r['media_nula']:.1f} %")
    v4 = _leer("descomposicion_v4_periodo.csv")
    for _, r in v4[v4["nivel"].eq(v4["grupo"])].iterrows():
        add(familia="V4 programa vs. periodo", contraste=f"exceso sobre el azar: {r['nivel']}", resultado="Y",
            estimacion=100 * r["exceso"], ic_inf=100 * r["exceso_ic_inf"], ic_sup=100 * r["exceso_ic_sup"],
            unidades="% de la SC de Y", rollos=r["rollos"], grupos=r["grupos_en_el_nivel"])
    for _, r in _leer("asociacion_principal.csv").iterrows():
        add(familia="8.C asociación principal", contraste=f"pendiente de {r['variable']}", resultado="Y",
            estimacion=r["coef"], ic_inf=r["ic_inf"], ic_sup=r["ic_sup"], unidades="kN por unidad", p=r["p"],
            rollos=r["rollos"], grupos=r["grupos_cluster"], nota=f"R² parcial {r['r2_parcial']:.5f}")
    for _, r in _leer("indicadores_secundarios.csv").iterrows():
        add(familia="Indicadores secundarios", contraste=f"pendiente de {r['variable']}", resultado=r["resultado"],
            estimacion=r["coef"], ic_inf=r["ic_inf"], ic_sup=r["ic_sup"], unidades="por unidad de la exposición",
            p=r["p"], rollos=r["rollos"], grupos=r["grupos_cluster"])
    for _, r in _leer("pendientes_por_producto.csv").iterrows():
        add(familia="8.D heterogeneidad por producto", contraste=f"pendiente de corona en {r['producto']}",
            resultado="Y", estimacion=r["coef"], ic_inf=r["ic_inf"], ic_sup=r["ic_sup"], unidades="kN por pp",
            p=r["p"], q_bh=r["q_bh"], rollos=r["rollos"], grupos=r["programas"], nota=r["tipo"])
    nc = _leer("control_negativo.csv")
    for _, r in nc[nc["variable"].eq("inclusiones")].iterrows():
        add(familia="V1 control negativo", contraste=f"{r['variable']} ({r['modelo']})", resultado="Y",
            estimacion=r["coef"], ic_inf=r["ic_inf"], ic_sup=r["ic_sup"], unidades="kN", p=r["p"],
            rollos=r["rollos"], grupos=r["grupos_cluster"])
    for _, r in _leer("robustez_multiverso.csv").iterrows():
        add(familia="V3 robustez: pendiente de corona", contraste=f"{r['robustez']}: {r['alternativa']} — pendiente de corona", resultado="Y",
            estimacion=r["coef"], ic_inf=r["ic_inf"], ic_sup=r["ic_sup"], unidades="kN por pp", p=r["p"],
            rollos=r["rollos"], grupos=r["grupos"])
        add(familia="V3 robustez: exceso del grupo − producto", contraste=f"{r['robustez']}: {r['alternativa']} — exceso grupo − producto", resultado="Y",
            estimacion=100 * (r["exceso_grupo"] - r["exceso_producto"]), unidades="puntos de % de la SC",
            rollos=r["rollos_descomp"], nota=f"grupo {100 * r['exceso_grupo']:.1f} %, producto {100 * r['exceso_producto']:.1f} %")
    ch = pd.read_csv(TABLAS_DIR / "sensibilidad_cinelli_hazlett.csv", index_col=0).iloc[:, 0]
    add(familia="10 confusión no medida", contraste="valor de robustez RV (q = 1) de la pendiente de corona", resultado="Y",
        estimacion=100 * ch["RV_q1"], unidades="% de varianza residual",
        nota=f"referencia producto: R² parcial con corona {100 * ch['r2_D_ref']:.1f} %, con Y {100 * ch['r2_Y_ref']:.1f} %; "
             f"un confusor {ch['k_que_anula']:.3f} veces tan fuerte como el producto la anula")
    pr = _leer("prediccion_resumen.csv")
    for _, r in pr.iterrows():
        add(familia="8.E predictivo", contraste=f"{r['esquema']}: MAE modelo − línea base", resultado="Y",
            estimacion=r["MAE_dif_mean"], unidades="kN (media entre particiones)",
            nota=f"DE entre particiones {r['MAE_dif_std']:.2f}; mejora en {r['particiones_donde_modelo_mejora_MAE']} de {r['particiones']}")
        add(familia="8.E predictivo", contraste=f"{r['esquema']}: R² modelo − línea base", resultado="Y",
            estimacion=r["R2_dif_mean"], unidades="R²", nota=f"DE entre particiones {r['R2_dif_std']:.3f}")
    ef_ruta = TABLAS_DIR / "experimento_efecto_recentrado.csv"
    if ef_ruta.exists():
        ef = pd.read_csv(ef_ruta)
        for col, nombre in [("global", "recentrado global"), ("por_tipo", "recentrado por tipo de material"),
                            ("por_producto_dimension", "recentrado por producto × dimensión")]:
            dif = ef["receta_vigente"] - ef[col]
            add(familia="12 experimento: tamaño del efecto", contraste=f"|Y| con receta vigente − |Y| con {nombre}",
                resultado="|Y|", estimacion=dif.mean(), unidades="kN (media de 5 particiones agrupadas)",
                nota=f"DE entre particiones {dif.std():.2f}")
        dif = ef["global"] - ef["por_producto_dimension"]
        add(familia="12 experimento: tamaño del efecto", contraste="lo que agrega diferenciar por producto al recentrado global",
            resultado="|Y|", estimacion=dif.mean(), unidades="kN (media de 5 particiones agrupadas)",
            nota=f"DE entre particiones {dif.std():.2f}")
    t = pd.DataFrame(filas, columns=COLS)
    t.insert(0, "id", range(1, len(t) + 1))
    t.to_csv(TABLAS_DIR / "contrastes_completos.csv", index=False)
    tabla_resumen(t)
    return t


def tabla_resumen(t: pd.DataFrame) -> None:
    """Resumen por familia para el Anexo C (cada renglón de la tabla completa está en el CSV)."""
    filas = []
    for fam, g in t.groupby("familia", sort=False):
        con_ic = g.dropna(subset=["ic_inf", "ic_sup"])
        excl = int(((con_ic["ic_sup"] < 0) | (con_ic["ic_inf"] > 0)).sum()) if len(con_ic) else None
        qmin = g["q_bh"].min() if g["q_bh"].notna().any() else None
        filas.append((fam, len(g), g["estimacion"].min(), g["estimacion"].max(),
                      f"{excl} de {len(con_ic)}" if excl is not None else "--",
                      f"{qmin:.2f}" if qmin is not None else "--", str(g["unidades"].iloc[0])))
    lineas = [r"\begin{tabular}{L{4.6cm}rrrlrL{4.2cm}}", r"\toprule",
              r"Familia & $n$ & Mín. & Máx. & IC excluye 0 & $q_{\min}$ & Unidades \\", r"\midrule"]
    for fam, n, lo, hi, ex, q, u in filas:
        esc = lambda s: s.replace("%", r"\%").replace("_", r"\_").replace("|", r"$|$")
        num = lambda v: f"{v:,.2f}".replace("-", "−")
        lineas.append(f"{esc(fam)} & {n} & {num(lo)} & {num(hi)} & {ex} & {q} & {esc(u)} \\\\")
    lineas += [r"\bottomrule", r"\end{tabular}"]
    (TABLAS_DIR / "tabla_contrastes_resumen.tex").write_text("\n".join(lineas) + "\n")
