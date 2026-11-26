"""Estilo común y guardado de figuras."""
from __future__ import annotations

import matplotlib.pyplot as plt

from .config import FIGURAS_DIR

# Paleta sobria y legible en blanco y negro (orden = prioridad)
AZUL, NARANJA, VERDE, ROJO, GRIS, MORADO = "#1f5a96", "#d9822b", "#3a8d4f", "#b8312f", "#8a8f98", "#6a4c93"


def estilo() -> None:
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 200, "font.size": 9, "axes.titlesize": 10,
        "axes.labelsize": 9, "axes.spines.top": False, "axes.spines.right": False,
        "axes.titleweight": "bold", "legend.frameon": False, "figure.constrained_layout.use": True,
    })


def guardar(fig, nombre: str):
    FIGURAS_DIR.mkdir(parents=True, exist_ok=True)
    ruta = FIGURAS_DIR / f"{nombre}.png"
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    return ruta


# ---------------------------------------------------------------- figuras del artículo final
ANCHO_DOBLE = 7.0   # pulgadas: ancho de página en dos columnas (elsarticle 5p ≈ 7.0 in)
ANCHO_SIMPLE = 3.4  # pulgadas: una columna


def estilo_articulo() -> None:
    """Estilo para figuras que se insertan a tamaño 1:1 en el artículo (letra ≥ 7.5 pt impresa)."""
    estilo()
    plt.rcParams.update({
        "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5, "legend.fontsize": 7.5, "figure.dpi": 150, "savefig.dpi": 300,
        "pdf.fonttype": 42, "figure.constrained_layout.use": False,
    })


def guardar_articulo(fig, nombre: str):
    """Guarda en outputs/figuras/articulo/ como PDF (vector, para LaTeX) y PNG (vista previa).

    No usa bbox_inches='tight' para respetar el tamaño de impresión declarado en figsize.
    """
    carpeta = FIGURAS_DIR / "articulo"
    carpeta.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(carpeta / f"{nombre}.{ext}", facecolor="white")
    return carpeta / f"{nombre}.pdf"
