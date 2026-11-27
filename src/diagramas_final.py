"""Mapa del proceso MC4 → Skinpass y diagrama causal del artículo final (plan, sección 6).

Se dibujan al tamaño de impresión (7.0 in de ancho, letra ≥ 7.5 pt) para atender la
observación de la Entrega I sobre la letra pequeña. Las figuras de la Entrega I
(``src/diagramas.py``) se conservan sin cambios para que los notebooks 01–06 sigan
reproduciendo esa entrega.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .visualizacion import ANCHO_DOBLE, AZUL, GRIS, NARANJA, ROJO, VERDE

# ---------------------------------------------------------------------------- mapa del proceso
ETAPAS = [
    # (nombre, línea, datos que usamos)
    ("Horno y\ndesbaste", "MC4", "Producto y dimensión\npedidos (Norma, Grado,\nespesor y ancho obj.)"),
    ("Tren acabador\nF1–F7", "MC4", "Corona y cuña de\nsalida; espesor real;\nprograma del MC4"),
    ("Mesa de\nenfriamiento\ny enrollado", "MC4", "T. de enrollado\nreal y objetivo;\ndefectos e inclusiones"),
    ("Skinpass de\nPesquería\n(SKP_PSQ)", "SKP", "Preset y bending real;\nfuerza, tensiones,\nelongación; programa\ny rodillo de trabajo"),
    ("Decapado (DEC3)\ny laminado en frío\n(DECAPADO, FRIO)", "OTRO", "Sin datos (solo la\nruta teórica); CALIENTE\nsale del Skinpass"),
]


def mapa_proceso_skp(n_mc4: int = 149_734, n_skp: int = 58_786, desfase_h: float = 125.0):
    fig, ax = plt.subplots(figsize=(ANCHO_DOBLE, 2.35), layout="none")
    fig.subplots_adjust(0.005, 0.005, 0.995, 0.995)
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.05, 3.45)
    ax.axis("off")
    w, h, y0 = 1.62, 0.95, 1.6
    xs = [0.12 + i * 2.0 for i in range(len(ETAPAS))]
    colores = {"MC4": AZUL, "SKP": NARANJA, "OTRO": GRIS}
    for i, (x, (nombre, linea, datos)) in enumerate(zip(xs, ETAPAS)):
        c = colores[linea]
        ax.add_patch(FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.03", fc="white", ec=c,
                                    lw=1.4, ls="--" if linea == "OTRO" else "-"))
        ax.text(x + w / 2, y0 + h / 2, nombre, ha="center", va="center", fontsize=8 if linea != "OTRO" else 7.3, weight="bold",
                color="black" if linea != "OTRO" else GRIS)
        ax.text(x + w / 2, y0 - 0.12, datos, ha="center", va="top", fontsize=7.5, color=c, linespacing=1.15)
        if i < len(ETAPAS) - 1:
            ax.add_patch(FancyArrowPatch((x + w + 0.04, y0 + h / 2), (xs[i + 1] - 0.04, y0 + h / 2),
                                         arrowstyle="-|>", mutation_scale=11, color="black", lw=1.1))
    # bandas de fuente de datos
    def banda(x0, x1, texto, c):
        ax.add_patch(FancyBboxPatch((x0, 2.78), x1 - x0, 0.6, boxstyle="round,pad=0.02",
                                    fc=c, ec="none", alpha=0.13))
        ax.text((x0 + x1) / 2, 3.08, texto, ha="center", va="center", fontsize=7.6, color="black",
                linespacing=1.1)
    banda(xs[0], xs[2] + w, f"Archivo MC4_PSQ 2025: 24 quincenas, {n_mc4:,} rollos (un renglón por rollo)", AZUL)
    banda(xs[3] - 0.05, xs[3] + w + 0.05, f"SKP_PSQ 2025: 12 meses,\n{n_skp:,} piezas", NARANJA)
    # llave de unión y desfase (pie de la figura)
    ax.text(5.0, 0.05, f"Unión por rollo: Material Salida (MC4) = Material Entrada (Skinpass).  "
            f"Desfase mediano MC4 → Skinpass: {desfase_h:.0f} h.", ha="center", va="bottom", fontsize=7.6, color=ROJO)
    return fig


# ---------------------------------------------------------------------------- diagrama causal
NODOS = {
    # clave: (x, y, texto, estilo)
    "periodo": (1.05, 5.05, "Periodo (mes)", "obs"),
    "pedido": (3.55, 5.05, "Pedido: producto\ny dimensión", "obs"),
    "prog": (6.2, 5.05, "Programa del Skinpass\n(rodillo de trabajo,\noperador, campaña)", "obs"),
    "preset": (8.85, 5.05, "Preset de bending\n(receta)", "obs"),
    "rodmc4": (1.05, 3.05, "Estado de rodillos\ny medidores del MC4", "no_obs"),
    "corona": (3.55, 3.05, "Corona relativa\nde salida del MC4", "expo"),
    "planeza": (6.2, 3.05, "Planeza y esfuerzos\nde entrada al Skinpass", "no_obs"),
    "bend": (8.85, 3.05, "Bending real (lazo\nautomático de planeza)\nY = real − preset", "resultado"),
    "inclus": (1.05, 1.15, "Inclusiones del MC4\n(control negativo)", "obs"),
    "temp": (3.55, 1.15, "Desv. de T. de enrollado\n(exposición secundaria)", "expo2"),
    "simul": (6.2, 1.15, "Fuerza, tensiones y\nelongación reales", "simul"),
    "etiq": (8.85, 1.15, "Dictamen, defectos,\nretenido (MC4 y SKP)", "posterior"),
}
ARISTAS = [
    # (origen, destino, tipo)  tipo: conf | expo | normal | noobs | simul
    ("periodo", "pedido", "conf"), ("periodo", "corona", "conf"), ("periodo", "prog", "normal", "arriba"),
    ("pedido", "corona", "conf"), ("pedido", "preset", "conf", "arriba"), ("pedido", "prog", "normal"),
    ("prog", "preset", "normal"), ("prog", "bend", "normal"), ("preset", "bend", "normal"),
    ("rodmc4", "corona", "normal"), ("rodmc4", "planeza", "noobs", "abajo"),
    ("corona", "planeza", "expo"), ("planeza", "bend", "expo"), ("temp", "planeza", "normal"),
    ("bend", "simul", "simul"), ("bend", "etiq", "normal"), ("inclus", "etiq", "normal", "abajo"),
]
ESTILOS = {
    "obs": dict(fc="white", ec="black", ls="-"),
    "no_obs": dict(fc="#e9e9e9", ec=GRIS, ls="--"),
    "expo": dict(fc="#dce8f5", ec=AZUL, ls="-"),
    "expo2": dict(fc="#eef3f9", ec=AZUL, ls="-"),
    "resultado": dict(fc="#fdebd3", ec=NARANJA, ls="-"),
    "posterior": dict(fc="#fff7ec", ec=NARANJA, ls=":"),
    "simul": dict(fc="#f4f4f4", ec="black", ls="-."),
}


def diagrama_causal_final():
    fig, ax = plt.subplots(figsize=(ANCHO_DOBLE, 4.25), layout="none")
    fig.subplots_adjust(0.005, 0.005, 0.995, 0.995)
    ax.set_xlim(-0.15, 10.05)
    ax.set_ylim(-0.95, 6.25)
    ax.axis("off")
    W, H = 2.12, 0.98
    caja = {}
    for k, (x, y, t, est) in NODOS.items():
        st = ESTILOS[est]
        ax.add_patch(FancyBboxPatch((x - W / 2, y - H / 2), W, H, boxstyle="round,pad=0.03",
                                    fc=st["fc"], ec=st["ec"], ls=st["ls"], lw=1.3))
        ax.text(x, y, t, ha="center", va="center", fontsize=7.7, linespacing=1.12,
                weight="bold" if est in ("expo", "resultado") else "normal")
        caja[k] = (x, y)

    def borde(a, b):
        (xa, ya), (xb, yb) = caja[a], caja[b]
        dx, dy = xb - xa, yb - ya
        fa = min(abs((W / 2 + 0.05) / dx) if dx else 9, abs((H / 2 + 0.05) / dy) if dy else 9)
        fb = min(abs((W / 2 + 0.07) / dx) if dx else 9, abs((H / 2 + 0.07) / dy) if dy else 9)
        return (xa + dx * fa, ya + dy * fa), (xb - dx * fb, yb - dy * fb)

    estilo_arista = {
        "conf": dict(color=ROJO, lw=1.6, ls="-"),
        "expo": dict(color=AZUL, lw=2.0, ls="-"),
        "normal": dict(color="black", lw=1.0, ls="-"),
        "noobs": dict(color=GRIS, lw=1.1, ls="--"),
        "simul": dict(color="black", lw=1.0, ls="-."),
    }
    for arista in ARISTAS:
        a, b, tipo = arista[:3]
        arco = arista[3] if len(arista) > 3 else None
        e = estilo_arista[tipo]
        flecha = "<|-|>" if tipo == "simul" else "-|>"
        if arco:
            (xa, ya), (xb, yb) = caja[a], caja[b]
            s = 1 if arco == "arriba" else -1
            p0 = (xa + 0.35, ya + s * (H / 2 + 0.04))
            p1 = (xb - 0.35, yb + s * (H / 2 + 0.06))
            cs = f"arc3,rad={-0.18 * s}"
        else:
            p0, p1 = borde(a, b)
            cs = "arc3,rad=0"
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=flecha, mutation_scale=10, color=e["color"],
                                     lw=e["lw"], ls=e["ls"], connectionstyle=cs))
    # leyenda: cajas (fila 1) y flechas (fila 2)
    ley = [("observado", "obs"), ("no observado", "no_obs"), ("exposición", "expo"),
           ("resultado", "resultado"), ("posterior (no explica)", "posterior"), ("simultáneo", "simul")]
    for i, (texto, est) in enumerate(ley):
        st = ESTILOS[est]
        x = -0.05 + i * 1.66 + (0.25 if i == 5 else 0)
        ax.add_patch(FancyBboxPatch((x, -0.62), 0.22, 0.2, boxstyle="round,pad=0.01", fc=st["fc"],
                                    ec=st["ec"], ls=st["ls"]))
        ax.text(x + 0.3, -0.52, texto, fontsize=7.4, va="center")
    ley2 = [("camino cerrado por el ajuste {producto, dimensión, mes}", "conf"),
            ("camino de la pregunta", "expo"), ("confusión no medida", "noobs")]
    for i, (texto, tipo) in enumerate(ley2):
        e = estilo_arista[tipo]
        x = [-0.05, 5.05, 7.45][i]
        ax.add_patch(FancyArrowPatch((x, -0.85), (x + 0.4, -0.85), arrowstyle="-|>", mutation_scale=9,
                                     color=e["color"], lw=e["lw"], ls=e["ls"]))
        ax.text(x + 0.5, -0.85, texto, fontsize=7.4, va="center")
    return fig


if __name__ == "__main__":  # python -m src.diagramas_final
    import matplotlib

    matplotlib.use("Agg")
    from .visualizacion import estilo_articulo, guardar_articulo

    estilo_articulo()
    print(guardar_articulo(mapa_proceso_skp(), "mapa_proceso"))
    print(guardar_articulo(diagrama_causal_final(), "diagrama_causal"))
