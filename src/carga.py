"""Carga de los 24 archivos MC4_PSQ originales, sin ediciones manuales.

``load_all()`` concatena los 24 archivos quincenales (~150 mil renglones × 280 columnas).
La primera lectura toma ~1–2 minutos; después se usa un caché parquet local en
``outputs/cache/`` (ignorado por git) para que los notebooks corran rápido.
El caché es una copia fiel del Excel: ninguna limpieza ocurre aquí.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .config import CACHE_DIR, DATA_DIR, FILE_GLOB, SHEET_NAME

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}
_NOMBRE = re.compile(r"MC4_PSQ (\w+) (\d+) a (\d+) (\d{4})\.xlsx$", re.IGNORECASE)


def list_files(data_dir: Path = DATA_DIR) -> list[Path]:
    """Archivos quincenales ordenados cronológicamente según su nombre."""
    files = list(Path(data_dir).glob(FILE_GLOB))
    if not files:
        raise FileNotFoundError(
            f"No encontré archivos {FILE_GLOB!r} en {data_dir}. "
            "Copia los 24 xlsx a data/ o define TERNIUM_DATA_DIR (ver README)."
        )
    return sorted(files, key=lambda f: file_period(f)[0])


def file_period(path: Path) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Periodo (inicio, fin) que declara el nombre del archivo."""
    m = _NOMBRE.search(Path(path).name)
    if not m:
        raise ValueError(f"Nombre de archivo inesperado: {path}")
    mes, d0, d1, anio = m.group(1).lower(), int(m.group(2)), int(m.group(3)), int(m.group(4))
    inicio = pd.Timestamp(anio, MESES[mes], d0)
    fin = pd.Timestamp(anio, MESES[mes], d1) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    return inicio, fin


def read_file(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=SHEET_NAME, engine="calamine")
    df.columns = [str(c).strip() for c in df.columns]
    inicio, _ = file_period(path)
    meta = pd.DataFrame({"archivo": Path(path).name, "quincena": inicio}, index=df.index)
    return pd.concat([meta, df], axis=1)


def load_all(usar_cache: bool = True) -> pd.DataFrame:
    """Concatena los 24 archivos originales (con caché parquet opcional)."""
    cache = CACHE_DIR / "mc4_crudo.parquet"
    if usar_cache and cache.exists():
        return pd.read_parquet(cache)
    frames = [read_file(f) for f in list_files()]
    df = pd.concat(frames, ignore_index=True)
    for c in df.columns:
        if c.startswith("Fecha") and df[c].dtype == object:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    if usar_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        # parquet exige tipos homogéneos: las columnas mixtas se guardan como texto
        out = df.copy()
        for c in out.columns:
            if out[c].dtype == object:
                out[c] = out[c].astype("string")
        out.to_parquet(cache)
    return df


def defect_slots(df: pd.DataFrame, max_slots: int = 5) -> pd.DataFrame:
    """Pasa los bloques de defectos (1)…(5) a formato largo: un renglón por defecto registrado."""
    partes = []
    for i in range(1, max_slots + 1):
        cols = [c for c in df.columns if c.endswith(f"({i})")]
        if not cols:
            continue
        sub = df[["Material Salida", "Fecha Inicio", *cols]].copy()
        sub.columns = ["Material Salida", "Fecha Inicio", *[c.replace(f" ({i})", "") for c in cols]]
        sub["slot"] = i
        partes.append(sub[sub["Defecto"].notna() | sub["Codigo defecto"].notna()])
    return pd.concat(partes, ignore_index=True)
