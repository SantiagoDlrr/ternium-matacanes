"""Figuras y tablas de Resultados del artículo (máximo seis en total; guía, Parte 1).

Cada figura se dibuja al tamaño de impresión (``ANCHO_DOBLE`` o ``ANCHO_SIMPLE``), con
unidades en los ejes, intervalos visibles y n (rollos y programas) en el título del panel.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .config import TABLAS_DIR
from .visualizacion import ANCHO_DOBLE, ANCHO_SIMPLE, AZUL, GRIS, NARANJA, ROJO, VERDE

NOMBRE = {"tipo": "Tipo de material", "producto": "Producto", "dimension": "Dimensión",
          "programa_skp": "Programa del Skinpass", "dia_skp": "Día del Skinpass",
          "semana_skp": "Semana del Skinpass", "rodillo_trabajo": "Rodillo de trabajo"}


def _miles(n: int) -> str:
    return f"{n:,}"


# ============================================================================ R1 descomposición
def _panel_descomp(ax, t: pd.DataFrame, titulo: str):
    t = t.reset_index(drop=True)
    y = np.arange(len(t))[::-1]
    obs, nula, exc = 100 * t["fraccion_observada"], 100 * t["media_nula"], 100 * t["exceso"]
    lo, hi = 100 * t["exceso_ic_inf"], 100 * t["exceso_ic_sup"]
    ax.barh(y, nula, color="#d9d9d9", height=0.62, label="azar (permutación)")
    ax.barh(y, exc, left=nula, color=AZUL, height=0.62, label="exceso sobre el azar")
    ax.errorbar(nula + exc, y, xerr=[exc - lo, hi - exc], fmt="none", ecolor="black", elinewidth=0.9, capsize=2.5)
    for yi, o, nl, e, h in zip(y, obs, nula, exc, hi):
        ax.text(max(o, nl + h) + 1.2, yi, f"{e:.1f} (observado {o:.1f})", va="center", fontsize=7.4)
    ax.set_yticks(y, [NOMBRE.get(n, n) for n in t["nivel"]])
    ax.set_xlabel("% de la suma de cuadrados de Y")
    ax.set_xlim(0, 100 * t["fraccion_observada"].max() + 52)
    ax.set_title(titulo, loc="left")


def fig_descomposicion(t_principal: pd.DataFrame, t_alt: pd.DataFrame, n_rollos: int, n_prog: int):
    fig, axs = plt.subplots(1, 2, figsize=(ANCHO_DOBLE, 2.5), layout="constrained")
    _panel_descomp(axs[0], t_principal, "(a) Orden del plan")
    _panel_descomp(axs[1], t_alt, "(b) Programa primero")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper right", bbox_to_anchor=(0.995, 0.995), fontsize=7, handlelength=1.2, frameon=False)
    fig.suptitle(f"n = {_miles(n_rollos)} rollos, {n_prog} programas del Skinpass. Barra azul: exceso sobre el azar con IC 95 %\n"
                 "(mitades de programas); el rótulo da el exceso y, entre paréntesis, la fracción observada (en %).",
                 fontsize=7.4, x=0.01, ha="left")
    return fig


# ============================================================================ R2 corona → Y
def fig_corona(curva_y: pd.DataFrame, curva_preset: pd.DataFrame, est_y: pd.Series, est_p: pd.Series):
    fig, axs = plt.subplots(1, 2, figsize=(ANCHO_DOBLE, 2.45), sharex=True, layout="constrained")
    for ax, cv, est, color, titulo, ylab in [
        (axs[0], curva_y, est_y, AZUL, "(a) Corrección de bending Y = real − preset", "Y dentro de celda (kN)"),
        (axs[1], curva_preset, est_p, GRIS, "(b) Preset de bending (comprobación S3)", "Preset dentro de celda (kN)"),
    ]:
        ax.axhline(0, color="black", lw=0.6)
        ax.errorbar(cv["x_media"], cv["y_media"], yerr=[cv["y_media"] - cv["ic_inf"], cv["ic_sup"] - cv["y_media"]],
                    fmt="o", color=color, ms=4, capsize=2, elinewidth=0.9, label="media por decil (IC 95 %)")
        xs = np.linspace(cv["x_media"].min(), cv["x_media"].max(), 50)
        ax.plot(xs, est["coef"] * xs, color=ROJO if est["p"] < 0.05 else GRIS, lw=1.3,
                label=f"pendiente {est['coef']:.1f} kN/pp [{est['ic_inf']:.1f}, {est['ic_sup']:.1f}]".replace("-", "−"))
        ax.set_xlabel("Corona relativa dentro de su celda (pp del espesor)")
        ax.set_ylabel(ylab)
        ax.set_title(f"{titulo}\nn = {int(est['rollos']):,} rollos, {int(est['grupos_cluster'])} programas", loc="left")
        ax.legend(loc="upper right", fontsize=7, handlelength=1.4)
    lim = max(abs(np.r_[curva_y["ic_inf"], curva_y["ic_sup"], curva_preset["ic_inf"], curva_preset["ic_sup"]]).max() * 1.6, 15)
    for ax in axs:
        ax.set_ylim(-lim, lim)
    return fig


# ============================================================================ R3 por producto
def fig_productos(t: pd.DataFrame, est_global: pd.Series):
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    t = t.sort_values("coef").reset_index(drop=True)
    alto = 1.0 + 0.112 * len(t)
    fig, ax = plt.subplots(figsize=(ANCHO_SIMPLE, alto), layout="none")
    fig.subplots_adjust(left=0.53, right=0.97, top=1 - 0.42 / alto, bottom=0.62 / alto)
    y = np.arange(len(t))
    col = np.where(t["rechaza_bh"], ROJO, np.where(t["tipo"].eq("CALIENTE"), NARANJA, AZUL))
    ax.axvline(0, color="black", lw=0.6)
    ax.axvspan(est_global["ic_inf"], est_global["ic_sup"], color=GRIS, alpha=0.3, lw=0)
    ax.axvline(est_global["coef"], color=GRIS, lw=1, ls="--")
    for yi, r, c in zip(y, t.itertuples(), col):
        ax.plot([r.ic_inf, r.ic_sup], [yi, yi], color=c, lw=1)
        ax.plot(r.coef, yi, "o", color=c, ms=3)
    etiquetas = [f"{' '.join(p.replace('CLASE ', 'CL. ').split())[:28]} ({n:,})" for p, n in zip(t["producto"], t["rollos"])]
    ax.set_yticks(y, etiquetas, fontsize=6.3)
    ax.tick_params(axis="y", length=2, pad=1.5)
    ax.set_ylim(-0.8, len(t) - 0.2)
    ax.set_xlabel("Pendiente (kN por pp de corona)", fontsize=7.5)
    lim = np.nanquantile(np.abs(np.r_[t["ic_inf"], t["ic_sup"]]), 0.95) * 1.1
    ax.set_xlim(-lim, lim)
    fig.text(0.02, 1 - 0.08 / alto, f"{len(t)} productos con ≥ 300 rollos (n = {t['rollos'].sum():,} rollos);\n"
             "producto (rollos en la estimación); IC 95 % agrupado por programa", fontsize=7, va="top")
    h = [Line2D([], [], color=NARANJA, marker="o", ms=3, lw=1, label="CALIENTE"),
         Line2D([], [], color=AZUL, marker="o", ms=3, lw=1, label="DECAPADO"),
         Patch(color=GRIS, alpha=0.4, label="global (IC 95 %)")]
    if t["rechaza_bh"].any():
        h.append(Line2D([], [], color=ROJO, marker="o", ms=3, lw=1, label="FDR < 5 %"))
    fig.legend(handles=h, loc="lower center", ncol=len(h), fontsize=6.6, handlelength=1.2,
               columnspacing=0.8, bbox_to_anchor=(0.5, 0.0), frameon=False)
    return fig


# ============================================================================ R4 validación
def fig_validacion(mv: pd.DataFrame, nc: pd.DataFrame, est: pd.Series):
    """(a) pendiente de corona en cada alternativa; (b) exceso del grupo vs producto; (c) control negativo."""
    fig = plt.figure(figsize=(ANCHO_DOBLE, 3.35), layout="constrained")
    gs = fig.add_gridspec(1, 3, width_ratios=[1.55, 1.0, 0.95])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharey=ax1)
    ax3 = fig.add_subplot(gs[2])
    mv = mv.reset_index(drop=True)
    y = np.arange(len(mv))[::-1]
    base = mv.iloc[0]
    ax1.axvline(0, color="black", lw=0.6)
    ax1.axvspan(base["ic_inf"], base["ic_sup"], color=GRIS, alpha=0.25, lw=0)
    for yi, r in zip(y, mv.itertuples()):
        c = AZUL if r.ic_sup < 0 else GRIS
        ax1.plot([r.ic_inf, r.ic_sup], [yi, yi], color=c, lw=1.1)
        ax1.plot(r.coef, yi, "o", color=c, ms=3.5)
    ax1.set_yticks(y, mv["etiqueta"], fontsize=6.9)
    ax1.set_xlabel("Pendiente (kN por pp de corona)")
    ax1.set_title("(a) V2–V4: pendiente e IC 95 %", loc="left")
    for yi, r in zip(y, mv.itertuples()):
        ax2.plot([100 * r.exceso_producto, 100 * r.exceso_grupo], [yi, yi], color="#cccccc", lw=1, zorder=1)
        ax2.plot(100 * r.exceso_producto, yi, "s", color=NARANJA, ms=3.5, zorder=2)
        ax2.plot(100 * r.exceso_grupo, yi, "o", color=AZUL, ms=3.5, zorder=2)
    ax2.set_xlabel("Exceso sobre el azar (%)")
    ax2.set_xlim(0, 42)
    ax2.set_title("(b) Grupo vs. producto", loc="left")
    ax2.tick_params(axis="y", labelleft=False)
    from matplotlib.lines import Line2D
    ax2.legend(handles=[Line2D([], [], color=AZUL, marker="o", ls="", ms=3.5, label="grupo"),
                        Line2D([], [], color=NARANJA, marker="s", ls="", ms=3.5, label="producto")],
               loc="lower right", fontsize=6.6, handletextpad=0.3, borderaxespad=0.3)
    filas = [("Corona +1 DE\ndentro de celda", est["efecto_por_sd"], est["efecto_por_sd_ic_inf"], est["efecto_por_sd_ic_sup"], AZUL)]
    for _, r in nc.iterrows():
        et = "Inclusiones\n(sí vs. no)" if "corona" not in r["modelo"] else "Inclusiones,\najustando corona"
        filas.append((et, r["coef"], r["ic_inf"], r["ic_sup"], GRIS))
    yy = np.arange(len(filas))[::-1]
    ax3.axvline(0, color="black", lw=0.6)
    for yi, (et, c0, lo, hi, col) in zip(yy, filas):
        ax3.plot([lo, hi], [yi, yi], color=col, lw=1.2)
        ax3.plot(c0, yi, "o", color=col, ms=4)
    ax3.set_yticks(yy, [f[0] for f in filas], fontsize=6.9)
    ax3.set_ylim(-0.6, len(filas) - 0.4)
    ax3.set_xlabel("Cambio en Y (kN)")
    ax3.set_title("(c) V1: inclusiones", loc="left")
    fig.suptitle(f"Base: n = {int(base['rollos']):,} rollos, {int(base['grupos'])} programas. (a) Franja gris: IC 95 % de la base; azul: IC que excluye 0.\n"
                 "(b) Grupo = programa, rodillo, día o semana, según el renglón. (c) Control negativo (inclusiones, n = "
                 f"{int(nc['rollos'].iloc[0]):,} rollos)\nfrente al efecto de +1 DE de corona dentro de celda.", fontsize=7.2, x=0.01, ha="left")
    return fig


# ============================================================================ R5 predicción
ESQ_CORTO = {"Agrupada por programa (GroupKFold)": "Agrupada\npor programa",
             "Temporal (ene–ago → sep–nov)": "Temporal\nene–ago → sep–nov",
             "Aleatoria (KFold; mezcla programas)": "Aleatoria\n(mezcla programas)"}


def fig_prediccion(t: pd.DataFrame, n_rollos: int, n_prog: int):
    fig, axs = plt.subplots(2, 1, figsize=(ANCHO_SIMPLE, 3.6), layout="constrained", sharex=True)
    esquemas = list(dict.fromkeys(t["esquema"]))
    xs = np.arange(len(esquemas))
    for ax, met, ylab in [(axs[0], "MAE", "MAE fuera de muestra (kN)"), (axs[1], "R2", "R² fuera de muestra")]:
        for i, esq in enumerate(esquemas):
            s = t[t["esquema"].eq(esq)]
            for dx, col, nombre, mk in [(-0.13, NARANJA, "linea_base", "s"), (0.13, AZUL, "modelo", "o")]:
                v = s[f"{met}_{nombre}"]
                ax.plot(np.full(len(v), i + dx), v, mk, color=col, ms=3.2, alpha=0.75)
                ax.plot([i + dx - 0.08, i + dx + 0.08], [v.mean(), v.mean()], color=col, lw=1.8)
        ax.set_ylabel(ylab)
    from matplotlib.lines import Line2D
    axs[0].legend(handles=[Line2D([], [], color=NARANJA, marker="s", ls="", ms=3.5, label="línea base (media producto × dimensión)"),
                           Line2D([], [], color=AZUL, marker="o", ls="", ms=3.5, label="gradient boosting")],
                  fontsize=6.6, loc="lower center", borderaxespad=0.2)
    axs[0].set_title(f"n = {n_rollos:,} rollos, {n_prog} programas\npuntos: particiones; raya: media", loc="left", fontsize=7.2)
    vmin = t[["MAE_modelo", "MAE_linea_base"]].min().min()
    vmax = t[["MAE_modelo", "MAE_linea_base"]].max().max()
    axs[0].set_ylim(vmin - 0.45 * (vmax - vmin), vmax + 0.06 * (vmax - vmin))  # espacio para la leyenda
    axs[1].set_xticks(xs, [ESQ_CORTO.get(e, e) for e in esquemas], fontsize=7)
    axs[1].axhline(0, color="black", lw=0.6)
    return fig


# ============================================================================ tablas LaTeX
def tabla_latex(df: pd.DataFrame, ruta, columnas: dict[str, str], formatos: dict[str, str],
                alineacion: str | None = None) -> None:
    """Escribe el cuerpo de una tabla booktabs (sin entorno table) para \\input en el artículo."""
    cols = list(columnas)
    al = alineacion or ("l" + "r" * (len(cols) - 1))
    lineas = [f"\\begin{{tabular}}{{{al}}}", "\\toprule",
              " & ".join(columnas[c] for c in cols) + r" \\", "\\midrule"]
    for _, r in df.iterrows():
        celdas = []
        for c in cols:
            v = r[c]
            f = formatos.get(c, "{}")
            celdas.append(f.format(v) if not (isinstance(v, float) and np.isnan(v)) else "--")
        lineas.append(" & ".join(celdas).replace("%", r"\%").replace("_", r"\_") + r" \\")
    lineas += ["\\bottomrule", "\\end{tabular}"]
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(lineas) + "\n")
