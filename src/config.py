"""Configuración local del proyecto.

Cada integrante apunta a su copia de los datos sin tocar este archivo, definiendo la
variable de entorno TERNIUM_DATA_DIR:

    export TERNIUM_DATA_DIR="/ruta/a/los/archivos/MC4_PSQ"

Si no se define, se usa la carpeta ``data/`` del repositorio (ignorada por git: los
datos de Ternium están bajo acuerdo de confidencialidad y nunca se versionan).
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("TERNIUM_DATA_DIR", REPO_ROOT / "data")).resolve()
OUTPUTS_DIR = REPO_ROOT / "outputs"
FIGURAS_DIR = OUTPUTS_DIR / "figuras"
TABLAS_DIR = OUTPUTS_DIR / "tablas"
CACHE_DIR = OUTPUTS_DIR / "cache"  # parquet intermedio (también ignorado por git)

# Patrón de los archivos quincenales entregados por Ternium
FILE_GLOB = "MC4_PSQ *.xlsx"
SHEET_NAME = "ResumenProduccion"

SEMILLA = 20251115  # semilla fija para permutaciones y cualquier muestreo
