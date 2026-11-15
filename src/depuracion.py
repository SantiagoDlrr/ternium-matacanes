"""Reglas de depuración declaradas ANTES de estimar cualquier efecto.

Principios:
- No se elimina ningún rollo. Un valor imposible o centinela se convierte en NaN en una
  columna *derivada* (sufijo ``_l`` o nombre nuevo) y se marca con una bandera
  ``flag_<regla>``. La columna original queda intacta para auditar.
- Cada regla tiene un motivo físico u operativo, no un motivo de "mejorar" un resultado.
- ``bitacora`` reporta cuántos rollos toca cada regla y si la regla se relaciona con el
  resultado (P(RETENIDO) con y sin bandera), como pide la guía.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Misma norma escrita de dos formas en los datos
VARIANTES_NORMA = {"TSG 3101G": "TSG3101G", "MS50002": "MS 50002"}

# (id, columna, descripción de la condición, acción, motivo)
REGLAS = [
    ("L1", "Corona Salida", "≤ 0 µm o > 1000 µm", "NaN en corona_um",
     "La corona de banda caliente es positiva y del orden de decenas a cientos de µm; ±8,700 µm es imposible."),
    ("L2", "Acuñamiento Salida", "|valor| > 500 µm", "NaN en cuna_um",
     "Misma lógica que L1; la cuña típica es de decenas de µm."),
    ("L3", "Temperatura Descarga Salida", "≤ 0 °C", "NaN en temp_descarga_l",
     "Centinela: un planchón no sale del horno a 0 °C."),
    ("L4", "Temp Enrollado Real", "≤ 0 °C", "NaN en temp_enrollado_real_l",
     "Centinela de medición faltante del pirómetro."),
    ("L5", "% Uso Modelo", "< 0 %", "NaN en uso_modelo_l",
     "Un porcentaje de uso no puede ser negativo (mínimo observado ≈ −100,000)."),
    ("L6", "Peso Báscula", "= 0 kg", "NaN en peso_bascula_l",
     "0 indica rollo no pesado en báscula, no peso cero."),
    ("L7", "Tiempo Estancia", "> 1000 min", "solo bandera",
     "Estancias de días sugieren paros de horno; son reales pero atípicas: se marcan, no se borran."),
    ("L8", "Defecto (i), Norma, Uso General", "variantes de captura", "texto normalizado",
     "Mayúsculas, espacios y punto final crean categorías duplicadas."),
    ("L9", "topSpyOn*/botSpyOn*", "patrón de bits convertido a número", "columna excluida",
     "La conversión a número de ~15 dígitos perdió el patrón original; no es recuperable."),
    ("L10", "Columnas vacías o constantes", "100 % NaN o un solo valor", "columna excluida",
     "No aportan variación; se documentan en el diccionario."),
]

COLUMNAS_SPRAYS = ["topSpyOnH", "botSpyOnH", "topSpyOnM", "botSpyOnM", "topSpyOnT", "botSpyOnT"]


def tabla_reglas() -> pd.DataFrame:
    return pd.DataFrame(REGLAS, columns=["id", "columna", "condición", "acción", "motivo"])


def normalizar_texto(s: pd.Series) -> pd.Series:
    """Mayúsculas, sin espacios extra y sin punto final."""
    return (s.astype("string").str.upper().str.strip()
            .str.replace(r"\s+", " ", regex=True).str.rstrip(".").str.strip())


def aplicar_reglas(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas depuradas (``*_l``, ``corona_um``, ``cuna_um``) y banderas ``flag_L*``."""
    out = df.copy()
    cr, cu = out["Corona Salida"], out["Acuñamiento Salida"]
    out["flag_L1"] = (cr <= 0) | (cr > 1000)
    out["flag_L2"] = cu.abs() > 500
    perfil_ok = ~(out["flag_L1"] | out["flag_L2"])
    out["corona_um"] = cr.where(perfil_ok)
    out["cuna_um"] = cu.where(perfil_ok)
    out["flag_L3"] = out["Temperatura Descarga Salida"] <= 0
    out["temp_descarga_l"] = out["Temperatura Descarga Salida"].mask(out["flag_L3"])
    out["flag_L4"] = out["Temp Enrollado Real"] <= 0
    out["temp_enrollado_real_l"] = out["Temp Enrollado Real"].mask(out["flag_L4"])
    out["flag_L5"] = out["% Uso Modelo"] < 0
    out["uso_modelo_l"] = out["% Uso Modelo"].mask(out["flag_L5"])
    out["flag_L6"] = out["Peso Báscula"] == 0
    out["peso_bascula_l"] = out["Peso Báscula"].mask(out["flag_L6"])
    out["flag_L7"] = out["Tiempo Estancia"] > 1000
    out["norma_l"] = normalizar_texto(out["Norma"]).replace(VARIANTES_NORMA)
    out["uso_general_l"] = normalizar_texto(out["Uso General"])
    for i in range(1, 6):
        col = f"Defecto ({i})"
        if col in out:
            out[col] = normalizar_texto(out[col])
    return out


def bitacora(df: pd.DataFrame) -> pd.DataFrame:
    """Cuántos rollos toca cada regla y si la bandera se asocia con el dictamen."""
    ret = df["Dictamen"].eq("RETENIDO")
    filas = []
    for rid in ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]:
        f = df[f"flag_{rid}"].fillna(False).astype(bool)
        filas.append({
            "regla": rid,
            "rollos marcados": int(f.sum()),
            "% de rollos": 100 * f.mean(),
            "P(RETENIDO | marcado)": ret[f].mean() if f.any() else np.nan,
            "P(RETENIDO | no marcado)": ret[~f].mean(),
        })
    return pd.DataFrame(filas)


def columnas_sin_variacion(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    vacias = [c for c in df.columns if df[c].isna().all()]
    constantes = [c for c in df.columns if c not in vacias and df[c].nunique(dropna=True) == 1]
    return vacias, constantes
