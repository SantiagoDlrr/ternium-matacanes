"""Skinpass de Pesquería (SKP_PSQ 2025): lectura, agregación por rollo del MC4 y unión.

Plan de análisis, secciones 2–4. Orden de operaciones (siempre el mismo):

1. ``load_skp``: lee los 12 archivos mensuales originales (hoja ``ResumenProduccion``),
   sin ediciones manuales; caché parquet en ``outputs/cache/`` (ignorado por git).
2. ``piezas``: variables por pieza (corrección de bending, banderas de defecto) y llave
   ``Material Entrada`` = ``Material Salida`` del MC4.
3. ``agregar_por_rollo``: un renglón por rollo del MC4. Variables numéricas: promedio
   ponderado por el peso de cada pieza; banderas: "alguna pieza"; fecha, programa,
   rodillo y modo: los de la primera pieza.
4. ``unir``: une con la tabla del MC4 (``poblacion.preparar``) y marca los pasos de la
   población (``tabla_poblacion``).

Ningún registro se borra en silencio: los que no ligan se cuentan (``registros_sin_liga``).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from .config import CACHE_DIR, SHEET_NAME, SKP_DIR, SKP_GLOB
from .depuracion import VARIANTES_NORMA, normalizar_texto

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}
_NOMBRE = re.compile(r"SKP_PSQ (\w+) (\d{4})\.xlsx$", re.IGNORECASE)

# Columnas del Skinpass que usa el análisis (nombres tal como vienen en los archivos)
BEND_REAL = "Bending Prom. Real [kN]"
BEND_PRESET = "Preset Bending"
NUMERICAS = {
    "bend_real": BEND_REAL,
    "bend_preset": BEND_PRESET,
    "fuerza_real": "Fuerza Real Prom.  [kN]",
    "tension_back_real": "Back Tensión Real Prom. [kN]",
    "tension_front_real": "Front Tensión Real Prom. [kN]",
    "elongacion": "Elongación",
}

# Fecha de corte por censura de fin de año (plan, sección 3, paso 3)
CORTE_CENSURA = pd.Timestamp("2025-12-01")


# ----------------------------------------------------------------------------- lectura
def list_files(skp_dir: Path = SKP_DIR) -> list[Path]:
    files = list(Path(skp_dir).glob(SKP_GLOB))
    if not files:
        raise FileNotFoundError(
            f"No encontré archivos {SKP_GLOB!r} en {skp_dir}. "
            "Copia los 12 xlsx del Skinpass a ResumenProduccionSKP/ o define TERNIUM_SKP_DIR (ver README)."
        )
    return sorted(files, key=file_month)


def file_month(path: Path) -> pd.Timestamp:
    m = _NOMBRE.search(Path(path).name)
    if not m:
        raise ValueError(f"Nombre de archivo inesperado: {path}")
    return pd.Timestamp(int(m.group(2)), MESES[m.group(1).lower()], 1)


def read_file(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=SHEET_NAME, engine="calamine")
    df.columns = [str(c).strip() for c in df.columns]
    meta = pd.DataFrame({"archivo_skp": Path(path).name, "mes_archivo_skp": file_month(path)}, index=df.index)
    return pd.concat([meta, df], axis=1)


def load_skp(usar_cache: bool = True) -> pd.DataFrame:
    """Concatena los 12 archivos mensuales originales del Skinpass (con caché parquet)."""
    cache = CACHE_DIR / "skp_crudo.parquet"
    if usar_cache and cache.exists():
        return pd.read_parquet(cache)
    df = pd.concat([read_file(f) for f in list_files()], ignore_index=True)
    if usar_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        out = df.copy()
        for c in out.columns:
            if out[c].dtype == object:
                out[c] = out[c].astype("string")
        out.to_parquet(cache)
    return df


# ----------------------------------------------------------------------------- por pieza
def piezas(s: pd.DataFrame, ids_mc4: pd.Series) -> pd.DataFrame:
    """Variables por pieza del Skinpass y bandera de liga con el MC4."""
    out = pd.DataFrame(index=s.index)
    out["material_entrada"] = s["Material Entrada"].astype("string")
    out["material_salida_skp"] = s["Material Salida"].astype("string")
    out["fecha_skp"] = pd.to_datetime(s["Fecha Inicio"])
    out["programa_skp"] = s["Programa"].astype("string")
    out["rodillo_trabajo"] = s["Rodillo de Trabajo"].astype("string")
    out["modo_molino"] = s["Modo Molino"].astype("string")
    out["peso_pieza"] = pd.to_numeric(s["Peso"], errors="coerce")
    out["norma_skp"] = normalizar_texto(s["Norma"]).replace(VARIANTES_NORMA)
    out["grado_skp"] = s["Grado"].astype("string")
    out["dictamen_skp"] = s["Dictamen"].astype("string")
    for nuevo, col in NUMERICAS.items():
        out[nuevo] = pd.to_numeric(s[col], errors="coerce")
    # Resultado principal por pieza: lo que el lazo ajustó más allá de la receta (plan, sección 4)
    out["y_corr"] = out["bend_real"] - out["bend_preset"]
    out["preset_cero"] = out["bend_preset"].eq(0)

    # Banderas de defecto por pieza (cinco bloques de defecto en el archivo)
    insp = np.zeros(len(s), dtype=bool)
    auto = np.zeros(len(s), dtype=bool)
    forma = np.zeros(len(s), dtype=bool)
    defectos_forma = {"FUERA DE PLANEZA", "ONDULACIÓN", "TABLEADO", "DOBLEZ PAÑUELO", "ARRUGAS", "COLA DE PESCADO"}
    for i in range(1, 6):
        ra = pd.to_numeric(s.get(f"Registro Automatico ({i})"), errors="coerce")
        lo = s.get(f"Linea Origen ({i})")
        de = normalizar_texto(s.get(f"Defecto ({i})"))
        en_skp = (lo == "SKP_PSQ").fillna(False).to_numpy(dtype=bool)
        insp |= (ra.eq(0).to_numpy(dtype=bool) & en_skp)
        auto |= (ra.eq(1).to_numpy(dtype=bool) & en_skp)
        forma |= (de.isin(defectos_forma).fillna(False).to_numpy(dtype=bool) & en_skp)
    out["def_inspector_skp"] = insp      # registrado por inspector, con origen en el Skinpass
    out["def_auto_skp"] = auto           # regla automática del Skinpass (no se usa como resultado)
    out["def_forma_skp"] = forma         # defectos de forma/planeza (descriptivo)
    out["retenido_skp"] = out["dictamen_skp"].eq("RETENIDO").fillna(False)

    out["liga_mc4"] = out["material_entrada"].isin(set(ids_mc4.astype("string")))
    out["entrada_es_pieza_skp"] = out["material_entrada"].str.contains("PS", na=False)
    return out


def registros_sin_liga(pz: pd.DataFrame) -> pd.DataFrame:
    """Cuenta de registros del Skinpass que no ligan con un rollo MC4 2025, por motivo."""
    sl = pz[~pz["liga_mc4"]]
    motivo = np.where(sl["entrada_es_pieza_skp"], "reproceso de una pieza ya pasada (…PS…)",
                      np.where(sl["fecha_skp"] < pd.Timestamp("2025-01-15"),
                               "probable rollo laminado en dic-2024 (registro de la 1.ª quincena de enero)", "otro identificador sin liga"))
    t = pd.Series(motivo).value_counts().rename_axis("motivo").reset_index(name="registros")
    tot = pd.DataFrame({"motivo": ["total sin liga", "total de registros", "registros que ligan"],
                        "registros": [len(sl), len(pz), int(pz["liga_mc4"].sum())]})
    return pd.concat([t, tot], ignore_index=True)


# ----------------------------------------------------------------------------- por rollo
def _ponderado(g: pd.DataFrame, col: str) -> float:
    v, w = g[col].to_numpy(float), g["peso_pieza"].to_numpy(float)
    ok = ~np.isnan(v) & ~np.isnan(w) & (w > 0)
    if not ok.any():
        return np.nan
    return float(np.average(v[ok], weights=w[ok]))


def agregar_por_rollo(pz: pd.DataFrame) -> pd.DataFrame:
    """Un renglón por rollo del MC4 que pasó por el Skinpass (solo registros que ligan)."""
    x = pz[pz["liga_mc4"]].sort_values(["material_entrada", "fecha_skp"], kind="stable").copy()
    w = x["peso_pieza"].where(x["peso_pieza"] > 0)
    gkey = x["material_entrada"]

    out = x.groupby(gkey, sort=False).agg(
        fecha_skp=("fecha_skp", "first"),
        programa_skp=("programa_skp", "first"),
        rodillo_trabajo=("rodillo_trabajo", "first"),
        modo_molino=("modo_molino", "first"),
        n_piezas=("material_salida_skp", "size"),
        n_programas_skp=("programa_skp", "nunique"),
        peso_skp=("peso_pieza", "sum"),
        def_inspector_skp=("def_inspector_skp", "any"),
        def_auto_skp=("def_auto_skp", "any"),
        def_forma_skp=("def_forma_skp", "any"),
        retenido_skp=("retenido_skp", "any"),
        preset_cero=("preset_cero", "any"),
        y_primera=("y_corr", "first"),
        bend_real_primera=("bend_real", "first"),
    )
    # Promedios ponderados por peso de pieza (vectorizado: suma(w·v)/suma(w) sobre valores válidos)
    for col in list(NUMERICAS) + ["y_corr"]:
        v = x[col]
        ok = v.notna() & w.notna()
        num = (v.where(ok) * w.where(ok)).groupby(gkey, sort=False).sum(min_count=1)
        den = w.where(ok).groupby(gkey, sort=False).sum(min_count=1)
        out[col] = num / den
    out["preset_max"] = x.groupby(gkey, sort=False)["bend_preset"].max()
    out["dividido"] = out["n_piezas"] > 1
    out.index.name = "Material Salida"
    return out.reset_index()


# ----------------------------------------------------------------------------- unión
def unir(df_mc4: pd.DataFrame, rollo_skp: pd.DataFrame, bend_real_max: float) -> pd.DataFrame:
    """Une MC4 (un renglón por rollo) con el Skinpass agregado y marca los pasos de población."""
    m = df_mc4.merge(rollo_skp, on="Material Salida", how="left", validate="one_to_one")
    # banderas del Skinpass: tras la unión izquierda quedan como object con NaN; se vuelven bool
    for c in ["def_inspector_skp", "def_auto_skp", "def_forma_skp", "retenido_skp", "preset_cero", "dividido"]:
        m[c] = m[c].astype("boolean").fillna(False).astype(bool)
    m["en_skp"] = m["fecha_skp"].notna()
    m["ruta_skp_psq"] = m["Ruta Teórica"].str.contains("SKP_PSQ", na=False)
    m["forma_final_skp"] = m["Forma Final"].str.endswith("SKP", na=False)
    m["grupo_forma"] = np.where(m["forma_final_skp"], m["Forma Final"], "Otras")
    m["desfase_h"] = (m["fecha_skp"] - m["Fecha Fin"]).dt.total_seconds() / 3600
    m["preset_alto"] = m["preset_max"] > bend_real_max   # R8
    m["cuna_abs_rel_pct"] = m["cuna_rel_pct"].abs()        # R7

    # Pasos de la población (plan, sección 3)
    m["paso1"] = m["ruta_skp_psq"]
    m["paso2"] = m["paso1"] & m["en_skp"]
    m["paso3"] = m["paso2"] & (m["Fecha Inicio"] < CORTE_CENSURA)
    m["paso4"] = m["paso3"] & m["y_corr"].notna() & m["bend_real"].notna()
    m["paso5"] = m["paso4"] & m["corona_rel_pct"].notna()
    # Mes del programa del Skinpass (para la partición temporal sin dividir programas)
    m["mes_skp"] = m["fecha_skp"].dt.to_period("M").dt.to_timestamp()
    return m


PASOS = [
    ("0", "Rollos MC4 2025", None),
    ("1", "Ruta Teórica contiene SKP_PSQ (cualquier forma final)", "paso1"),
    ("2", "Tiene registro en el Skinpass 2025", "paso2"),
    ("3", "Fecha Inicio MC4 < 2025-12-01 (censura de fin de año)", "paso3"),
    ("4", "Con bending real y preset (resultado Y definido)", "paso4"),
    ("5", "Además con corona relativa válida (asociación 8.C)", "paso5"),
]


def tabla_poblacion(m: pd.DataFrame) -> pd.DataFrame:
    filas, prev = [], None
    for paso, criterio, col in PASOS:
        mask = pd.Series(True, index=m.index) if col is None else m[col]
        n = int(mask.sum())
        prog = m.loc[mask, "programa_skp"].nunique() if col and col != "paso1" else np.nan
        filas.append({"paso": paso, "criterio": criterio, "rollos": n,
                      "excluidos en el paso": (prev - n) if prev is not None else np.nan,
                      "programas del Skinpass": prog})
        prev = n
    return pd.DataFrame(filas)


def comparar_exclusion(m: pd.DataFrame) -> pd.DataFrame:
    """Incluidos vs excluidos en cada paso: producto, espesor, corona relativa (Fenómeno 6)."""
    filas = []
    for (paso, criterio, col), (_, _, col_prev) in zip(PASOS[2:], PASOS[1:-1]):
        base = m[m[col_prev]]
        inc = base[col]
        for nombre, sub in [("incluidos", base[inc]), ("excluidos", base[~inc])]:
            filas.append({
                "paso": paso, "grupo": nombre, "rollos": len(sub),
                "espesor objetivo mediano (mm)": sub["Espesor Objetivo"].median(),
                "ancho objetivo mediano (mm)": sub["Ancho Objetivo"].median(),
                "corona relativa mediana (%)": sub["corona_rel_pct"].median(),
                "% DECAPADO": 100 * sub["tipo_material"].eq("DECAPADO").mean(),
                "% FRIO": 100 * sub["tipo_material"].eq("FRIO").mean(),
                "% RETENIDO en MC4": 100 * sub["Dictamen"].eq("RETENIDO").mean(),
                "Y mediana (kN)": sub["y_corr"].median(),
                "productos distintos": sub["norma_grado"].nunique(),
            })
    return pd.DataFrame(filas)


def construir(usar_cache: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Atajo para los notebooks 08–10: (unión completa, piezas, rollos del Skinpass)."""
    from .poblacion import preparar

    df, _ = preparar(usar_cache)
    s = load_skp(usar_cache)
    pz = piezas(s, df["Material Salida"])
    rs = agregar_por_rollo(pz)
    m = unir(df, rs, bend_real_max=float(pz["bend_real"].max()))
    return m, pz, rs


def analitica(m: pd.DataFrame, paso: str = "paso4") -> pd.DataFrame:
    """Población analítica (paso 4 por defecto) con las llaves que usan los análisis."""
    a = m[m[paso]].copy()
    a["producto"] = a["norma_grado"].astype("string").fillna("¿sin producto?")
    a["tipo"] = a["tipo_material"].astype("string").fillna("¿sin tipo?")
    a["dimension"] = a["dim"].astype("string").fillna("¿sin dimensión?")
    a["mes_str"] = a["mes"].dt.strftime("%Y-%m")
    a["celda"] = a["producto"] + " | " + a["dimension"] + " | " + a["mes_str"]
    a["dia_skp"] = a["fecha_skp"].dt.strftime("%Y-%m-%d")
    a["semana_skp"] = a["fecha_skp"].dt.strftime("%G-W%V")
    return a
