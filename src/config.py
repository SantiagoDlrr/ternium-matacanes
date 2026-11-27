"""Configuración local del proyecto.

Cada integrante apunta a su copia de los datos sin tocar este archivo, definiendo la
variable de entorno TERNIUM_DATA_DIR:

    export TERNIUM_DATA_DIR="/ruta/a/los/archivos/MC4_PSQ"

y TERNIUM_SKP_DIR para los 12 archivos mensuales del Skinpass (SKP_PSQ 2025).
Si no se definen, se usa ``data/`` (MC4) y ``ResumenProduccionSKP/`` dentro del repositorio
o, si no existen, las carpetas hermanas ``../data_molino_prev`` y ``../ResumenProduccionSKP``.
Todas están ignoradas por git: los datos de Ternium están bajo acuerdo de confidencialidad
y nunca se versionan.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _carpeta(var: str, candidatas: list[Path]) -> Path:
    """Ruta de datos: variable de entorno si existe; si no, la primera carpeta candidata que exista."""
    if os.environ.get(var):
        return Path(os.environ[var]).resolve()
    for c in candidatas:
        if c.exists():
            return c.resolve()
    return candidatas[0].resolve()


# MC4: 24 archivos quincenales. SKP: 12 archivos mensuales del Skinpass de Pesquería 2025.
DATA_DIR = _carpeta("TERNIUM_DATA_DIR", [REPO_ROOT / "data", REPO_ROOT.parent / "data_molino_prev"])
SKP_DIR = _carpeta("TERNIUM_SKP_DIR", [REPO_ROOT / "ResumenProduccionSKP", REPO_ROOT.parent / "ResumenProduccionSKP"])
OUTPUTS_DIR = REPO_ROOT / "outputs"
FIGURAS_DIR = OUTPUTS_DIR / "figuras"
TABLAS_DIR = OUTPUTS_DIR / "tablas"
CACHE_DIR = OUTPUTS_DIR / "cache"  # parquet intermedio (también ignorado por git)

# Patrón de los archivos quincenales entregados por Ternium
FILE_GLOB = "MC4_PSQ *.xlsx"
SKP_GLOB = "SKP_PSQ *.xlsx"
SHEET_NAME = "ResumenProduccion"

SEMILLA = 20251115  # semilla fija para permutaciones y cualquier muestreo
