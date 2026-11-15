"""Mapa del proceso (Componente 1) y diagrama causal preliminar (Componente 4).

Se dibujan con matplotlib para que el repo sea autocontenido y reproducible.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .visualizacion import AZUL, GRIS, NARANJA, ROJO, VERDE

TIPO_COLOR = {"C": AZUL, "M": VERDE, "E": NARANJA, "X": "#555555", "N": "#9a9a9a"}
TIPO_NOMBRE = {
    "C": "consigna / especificación", "M": "medición", "E": "etiqueta derivada (regla o inspección)",
    "X": "contexto / identificador", "N": "no observado o 100 % vacío",
}

ETAPAS = [
    ("Planchón\n(acería / proveedor)", [
        ("Colada, Grado Planchón", "X"), ("Espesor/Ancho/Largo\nEntrada Real", "M"),
        ("INCLUSIONES, ESCAMAS\n(origen PROVEEDOR)", "E")]),
    ("Horno de\nrecalentamiento (H1/H2)", [
        ("Horno (alterna 93 %)", "X"), ("Tiempo Estancia", "M"), ("Temp. Descarga Salida", "M"),
        ("MARCA DE PATIN,\nTEMP. MIN SALIDA HORNO", "E")]),
    ("Descascarado y\ndesbaste R1–R2 + SSP", [
        ("SSP Utilizado", "C"), ("Canteo R1, R2, SSP", "M"), ("TEMPERATURA DESBASTE", "E")]),
    ("Barra de\ntransferencia", [
        ("Espesor Barra", "C"), ("% Uso Cubierta Térmica", "C"), ("Long. barra, tiempo R2→F1", "M"),
        ("INCUMPL. ESP. BARRA", "E")]),
    ("Tren acabador\nF1–F7 + loopers", [
        ("Programa, Secuencia", "X"), ("Cambio Rodillo Trabajo (?)", "X"), ("Temp. F1–F7", "M"),
        ("Tensión y tiempo looper 1–6", "M"), ("Sprays (patrón perdido)", "N"),
        ("Temp Acabado Obj/Mín/Máx", "C"), ("Temp Acabado Real", "M"),
        ("Espesor, Ancho, Corona,\nAcuñamiento, Taper", "M"),
        ("ESPESOR ±, ANCHO ±, MAL PERFIL,\nTEMP. ACABADO, ÓX. RODILLOS", "E"),
        ("Bending / control de perfil", "N")]),
    ("Mesa de\nenfriamiento", [
        ("PRAM → Temp Enrollado\nObj/Mín/Máx", "C"), ("Estrategia de enfriamiento", "N")]),
    ("Enrollado\n(E1/E2)", [
        ("Enrollador (alterna 97 %)", "X"), ("Temp Enrollado Real", "M"), ("Diam Salida, Peso", "M"),
        ("TEMP. ENROLLADO, MAL\nENROLLADO, ÓXIDO POR TEMP.", "E")]),
    ("Inspección\ny dictamen", [
        ("Defecto (1–5): causa, ubicación,\nintensidad, registro automático", "E"),
        ("Dictamen, Resolución,\nCalidad Sugerida", "E"), ("Envío a Inspección, Usuario", "X")]),
    ("Decapado\n(solo DECAPADO-SKP)", [
        ("Espesor Final (meta del producto)", "C"), ("Sin datos del proceso", "N")]),
    ("Skinpass\nPesquería", [
        ("% Elongación Mín/Máx,\nEspesor Mín/Máx SKP (vacías)", "N"),
        ("Bending, fuerza, tensión,\nvelocidad", "N"), ("Planeza, rugosidad,\npropiedades", "N")]),
]


def mapa_proceso():
    fig, ax = plt.subplots(figsize=(17, 6.6))
    ax.set_xlim(0, 10.2)
    ax.set_ylim(1.05, 8.45)
    ax.axis("off")
    # Banda de especificación
    ax.add_patch(FancyBboxPatch((0.05, 7.55), 10.05, 0.8, boxstyle="round,pad=0.02", fc="#eaf1f8", ec=AZUL))
    ax.text(5.07, 7.95,
            "Especificación y orden (fijadas antes de laminar): Norma · Grado · Subnorma · Cliente · Orden · PRO · PRAM · "
            "Uso General · Forma Final · Ruta Teórica · objetivos y tolerancias de espesor, ancho, peso y temperatura",
            ha="center", va="center", fontsize=8.5, color=AZUL, wrap=True)
    w = 0.9
    for i, (nombre, variables) in enumerate(ETAPAS):
        x = 0.1 + i * 1.01
        no_obs = i >= 8
        ax.add_patch(FancyBboxPatch((x, 6.25), w, 0.95, boxstyle="round,pad=0.02",
                                    fc="#f2f2f2" if no_obs else "white", ec=GRIS if no_obs else "black",
                                    ls="--" if no_obs else "-", lw=1.2))
        ax.text(x + w / 2, 6.72, nombre, ha="center", va="center", fontsize=7.6, weight="bold",
                color=GRIS if no_obs else "black")
        ax.annotate("", xy=(x + w / 2, 7.2), xytext=(x + w / 2, 7.53),
                    arrowprops=dict(arrowstyle="->", color=AZUL, lw=0.8))
        if i < len(ETAPAS) - 1:
            ax.annotate("", xy=(x + w + 0.11, 6.72), xytext=(x + w, 6.72),
                        arrowprops=dict(arrowstyle="->", color="black", lw=1))
        y = 5.95
        for texto, tipo in variables:
            n_lin = texto.count("\n") + 1
            ax.text(x + 0.02, y, texto, ha="left", va="top", fontsize=6.4, color=TIPO_COLOR[tipo],
                    style="italic" if tipo == "N" else "normal")
            y -= 0.27 * n_lin + 0.12
    ax.axvline(0.1 + 8 * 1.01 - 0.05, ymin=0.06, ymax=0.8, color=ROJO, ls=":", lw=1.2)
    ax.text(0.1 + 8 * 1.01 - 0.08, 1.6, "fin de lo observado\n(archivos MC4_PSQ)", ha="right", va="bottom",
            fontsize=7, color=ROJO)
    for k, (t, nombre) in enumerate(TIPO_NOMBRE.items()):
        ax.text(0.15 + k * 2.0, 1.15, "■ " + nombre, color=TIPO_COLOR[t], fontsize=7.5)
    return fig


NODOS = {
    # clave: (x, y, texto, tipo)  tipo: obs | no_obs | resultado | posterior | cuasi
    "spec": (1.0, 7.0, "Especificación y orden\n(Norma–Grado, cliente,\nespesor y ancho objetivo)", "obs"),
    "prog": (3.7, 8.6, "Programación\n(programa y posición\ndel rollo)", "obs"),
    "rod": (6.6, 8.6, "Estado de rodillos de trabajo\n(desgaste, corona térmica,\nrectificado)", "no_obs"),
    "mat": (1.0, 3.6, "Material de entrada\n(colada, química,\nplanchón)", "parcial"),
    "cons": (3.7, 5.6, "Consignas MC4\n(PRAM → T. objetivo\ny tolerancias)", "obs"),
    "ctrl": (6.6, 6.4, "Control de perfil\n(bending, ajustes\ndel operador)", "no_obs"),
    "cond": (6.6, 3.6, "Condiciones medidas\n(T. F1–F7, T. acabado,\nloopers)", "obs"),
    "perfil": (9.4, 5.6, "Condición de llegada\n(corona y cuña relativas,\nT. enrollado vs. tolerancia)", "resultado"),
    "etiq": (9.4, 8.6, "Etiquetas derivadas\n(MAL PERFIL, Dictamen)", "posterior"),
    "falta": (12.2, 8.6, "Dato faltante\n(corona no registrada)", "obs"),
    "plan": (9.4, 3.0, "Planeza y esfuerzos\nresiduales de entrada\nal Skinpass", "no_obs"),
    "skp": (9.4, 0.9, "Configuración y calidad\ndel Skinpass (receta\npor tipo de material)", "no_obs"),
    "eq": (3.7, 2.0, "Horno y enrollador\n(alternancia ≈ 50/50)", "cuasi"),
}
ARISTAS = [
    ("spec", "prog", "conf"), ("spec", "cons", ""), ("spec", "perfil", "conf"), ("spec", "mat", ""),
    ("prog", "rod", "conf"), ("rod", "perfil", "conf"), ("rod", "ctrl", ""), ("ctrl", "perfil", ""),
    ("mat", "cond", ""), ("mat", "perfil", ""), ("cons", "cond", ""), ("cons", "perfil", ""),
    ("cond", "perfil", ""), ("eq", "cond", ""), ("perfil", "etiq", ""), ("falta", "etiq", ""),
    ("perfil", "plan", "?"), ("plan", "skp", "?"),
]


def diagrama_causal():
    fig, ax = plt.subplots(figsize=(13, 8.4))
    ax.set_xlim(-0.4, 13.5)
    ax.set_ylim(-0.2, 9.6)
    ax.axis("off")
    estilos = {
        "obs": dict(fc="white", ec="black", ls="-"),
        "parcial": dict(fc="#f7f7f7", ec="black", ls="-."),
        "no_obs": dict(fc="#e6e6e6", ec=GRIS, ls="--"),
        "resultado": dict(fc="#fdebd3", ec=NARANJA, ls="-"),
        "posterior": dict(fc="#fff7ec", ec=NARANJA, ls=":"),
        "cuasi": dict(fc="#e8f3ea", ec=VERDE, ls="-"),
    }
    caja = {}
    for k, (x, y, t, tipo) in NODOS.items():
        st = estilos[tipo]
        ancho, alto = 2.35, 1.05
        ax.add_patch(FancyBboxPatch((x - ancho / 2, y - alto / 2), ancho, alto, boxstyle="round,pad=0.04",
                                    fc=st["fc"], ec=st["ec"], ls=st["ls"], lw=1.4))
        ax.text(x, y, t, ha="center", va="center", fontsize=8)
        caja[k] = (x, y, ancho, alto)

    def borde(a, b):
        (xa, ya, wa, ha), (xb, yb, wb, hb) = caja[a], caja[b]
        dx, dy = xb - xa, yb - ya
        fa = min(abs((wa / 2 + 0.05) / dx) if dx else 9, abs((ha / 2 + 0.05) / dy) if dy else 9)
        fb = min(abs((wb / 2 + 0.08) / dx) if dx else 9, abs((hb / 2 + 0.08) / dy) if dy else 9)
        return (xa + dx * fa, ya + dy * fa), (xb - dx * fb, yb - dy * fb)

    for a, b, tipo in ARISTAS:
        p0, p1 = borde(a, b)
        color = ROJO if tipo == "conf" else ("#9a9a9a" if tipo == "?" else "black")
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=12, color=color,
                                     lw=1.6 if tipo == "conf" else 1.1, ls="--" if tipo == "?" else "-",
                                     connectionstyle="arc3,rad=0.0"))
    ley = [("observado", "obs"), ("parcialmente observado", "parcial"), ("no observado", "no_obs"),
           ("resultado de la pregunta", "resultado"), ("posterior al resultado (no explica)", "posterior"),
           ("fuente de variación casi aleatoria", "cuasi")]
    for i, (t, tipo) in enumerate(ley):
        st = estilos[tipo]
        ax.add_patch(FancyBboxPatch((-0.3 + i * 2.15, -0.15), 0.3, 0.25, boxstyle="round,pad=0.01",
                                    fc=st["fc"], ec=st["ec"], ls=st["ls"]))
        ax.text(0.08 + i * 2.15, -0.03, t, fontsize=7.5, va="center")
    ax.text(-0.3, 9.45, "Rojo: caminos de confusión (especificación → programa → rodillos → condición, y "
            "especificación → condición). Gris discontinuo: relación hipotética que no podemos estimar con MC4.",
            fontsize=8, color=ROJO)
    return fig


if __name__ == "__main__":  # python -m src.diagramas
    import matplotlib

    matplotlib.use("Agg")
    from .visualizacion import estilo, guardar

    estilo()
    print(guardar(mapa_proceso(), "mapa_proceso"))
    print(guardar(diagrama_causal(), "diagrama_causal"))
