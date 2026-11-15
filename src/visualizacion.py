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
