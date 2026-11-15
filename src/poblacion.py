"""Variables derivadas, población de estudio y preparación común de los notebooks.

Uso:
    from src.poblacion import preparar, poblacion
    df, d = preparar()   # df: un renglón por rollo; d: un renglón por defecto registrado
    p = poblacion(df)    # población de estudio: forma final *-SKP con SKP_PSQ en la ruta

Orden de operaciones (siempre el mismo, sin pasos manuales):
1. ``carga.load_all``: lee los 24 archivos originales desde ``TERNIUM_DATA_DIR``.
2. ``add_features``: llaves de producto y banderas de población.
3. ``depuracion.aplicar_reglas``: depuración declarada (no elimina rollos).
4. Banderas de defecto por rollo y variables derivadas.
"""
from __future__ import annotations

import pandas as pd

from .calidad import banderas_defecto
from .carga import defect_slots, load_all
from .depuracion import VARIANTES_NORMA, aplicar_reglas

# Columnas que deberían describir el Skinpass y que vienen 100 % vacías
COLUMNAS_SKP = [
    "Línea Adelantada SKP", "% Elongación Mínimo", "% Elongación Máximo",
    "Espesor Mínimo SKP", "Espesor Máximo SKP",
]

CORTES_ANCHO = [0, 1000, 1200, 1400, 1600, 2500]
ETIQUETAS_ANCHO = ["≤1000", "1000–1200", "1200–1400", "1400–1600", ">1600"]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega banderas y llaves de producto candidatas (no modifica el original)."""
    out = df.copy()
    ruta_skp = out["Ruta Teórica"].str.contains("SKP", na=False)
    out["ruta_skp"] = ruta_skp
    # Población principal del reto: ruta con Skinpass y forma final *-SKP
    out["poblacion_skp"] = ruta_skp & out["Forma Final"].str.endswith("SKP", na=False)
    out["planta_skp"] = out["Ruta Teórica"].str.extract(r"(SKP\d?_[A-Z]+)", expand=False)
    out["tipo_material"] = out["Forma Final"].str.split("-").str[2]  # CALIENTE / DECAPADO / FRIO
    norma = out["Norma"].astype("string").str.strip().replace(VARIANTES_NORMA)
    out["norma_grado"] = norma + " | " + out["Grado"].astype("string").fillna("¿sin grado?")
    out["rango_espesor"] = pd.cut(
        out["Espesor Objetivo"], [0, 1.5, 2, 2.5, 3, 4, 6, 30],
        labels=["≤1.5", "1.5–2", "2–2.5", "2.5–3", "3–4", "4–6", ">6"],
    )
    out["mes"] = out["Fecha Inicio"].dt.to_period("M").dt.to_timestamp()
    return out


def preparar(usar_cache: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = aplicar_reglas(add_features(load_all(usar_cache)))
    df = df.sort_values("Fecha Inicio", kind="stable").reset_index(drop=True)
    d = defect_slots(df)
    df = pd.concat([df, banderas_defecto(df, d)], axis=1)

    # Población de estudio: forma final *-SKP con Skinpass de Pesquería en la ruta teórica
    df["pob_psq"] = df["poblacion_skp"] & df["planta_skp"].eq("SKP_PSQ")

    # Perfil transversal relativo al espesor (corona y cuña en µm; espesor en mm)
    df["corona_rel_pct"] = df["corona_um"] / (df["Espesor"] * 1000) * 100
    df["cuna_rel_pct"] = df["cuna_um"] / (df["Espesor"] * 1000) * 100

    # Seguimiento de consignas (medición − objetivo)
    df["dev_te"] = df["temp_enrollado_real_l"] - df["Temp Enrollado Obj"]
    df["dev_ta"] = df["Temp Acabado Real"] - df["Temp Acabado Obj"]

    # Posición dentro del programa de laminación (orden cronológico)
    df["pos_programa"] = df.groupby("Programa").cumcount() + 1
    df["n_programa"] = df.groupby("Programa")["Material Salida"].transform("size")

    # Estratos dimensionales definidos por la especificación (antes de laminar)
    df["ancho_bin"] = pd.cut(df["Ancho Objetivo"], CORTES_ANCHO, labels=ETIQUETAS_ANCHO)
    df["celda"] = df["norma_grado"] + " | " + df["rango_espesor"].astype(str)
    df["dim"] = df["rango_espesor"].astype(str) + " | " + df["ancho_bin"].astype(str)

    # Anonimización: usuarios y clientes no se muestran por nombre en salidas
    for col, pref in [("Usuario", "U"), ("Cliente", "C")]:
        orden = df[col].value_counts().index
        df[col.lower() + "_anon"] = df[col].map({v: f"{pref}{i + 1}" for i, v in enumerate(orden)})
    return df, d


def poblacion(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["pob_psq"]].copy()


def tabla_jerarquia(p: pd.DataFrame) -> pd.DataFrame:
    """Jerarquía de producto con conteos (Componente 1)."""
    niveles = {
        "Tipo de material": ["tipo_material"],
        "Familia (Norma) dentro de tipo": ["tipo_material", "norma_l"],
        "Producto (Norma | Grado) dentro de tipo": ["tipo_material", "norma_grado"],
        "Producto × rango de espesor": ["tipo_material", "norma_grado", "rango_espesor"],
        "Producto × espesor × ancho": ["tipo_material", "norma_grado", "rango_espesor", "ancho_bin"],
        "Orden (pedido)": ["Orden"],
    }
    filas = []
    for nombre, claves in niveles.items():
        g = p.groupby(claves, observed=True)
        n = g.size()
        filas.append({
            "nivel": nombre, "grupos": len(n), "mediana de rollos": n.median(),
            "grupos ≥100 rollos": int((n >= 100).sum()),
            "% de rollos en grupos ≥100": round(100 * n[n >= 100].sum() / n.sum(), 1),
            "mediana de programas": g["Programa"].nunique().median(),
        })
    return pd.DataFrame(filas)
