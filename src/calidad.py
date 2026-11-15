"""Etiquetas de calidad: familias de defecto, banderas por rollo y reglas de tolerancia (Fenómeno 1)."""
from __future__ import annotations

import pandas as pd

# Familia por origen probable. Es una clasificación nuestra (por nombre, causa registrada y
# línea de origen), pendiente de validar con Ternium.
FAMILIAS = {
    "dimensional (regla vs. tolerancia)": [
        "ESPESOR (+/-)", "ANCHO (+/-)", "PESO (+)", "PESO (-)", "CAMBIO DE ESPESOR",
        "FUERA DE ESPESOR OPERATIVO", "INCUMPLIMIENTO ESP. BARRA TRANSF",
    ],
    "térmico (regla vs. tolerancia)": [
        "TEMPERATURA DE ENROLLADO (-)", "TEMPERATURA DE ENROLLADO (+/-)", "TEMPERATURA DE ENROLLADO (+)",
        "TEMPERATURA DE ACABADO (+/-)", "TEMPERATURA DE ACABADO (-)", "TEMPERATURA DESBASTE",
        "INCUMPLIMIENTO TEMP. MIN SALIDA HORNO", "INCUMPLIMIENTO DE TEMPERATURA INTERMEDIA", "FRANJA FRIA",
        "TEMPERATURA DE ACABADO (+)", "INCUMPLIMIENTO DE TIEMPO AIRE",
    ],
    "forma y perfil": [
        "MAL PERFIL", "INCUMPLIMIENTO DE PERFIL", "DOBLEZ PAÑUELO", "ONDULACIÓN", "COLEADO",
        "COLA DE PESCADO", "TELESCOPIADO", "DOBLEZ TRANSVERSAL", "ARRUGAS", "TABLEADO",
    ],
    "superficie: óxido": [
        "OXIDO POR TEMPERATURA", "ÓXIDO ROJO", "ÓXIDO DE RODILLOS", "ÓXIDO PRIMARIO", "CHISPAS DE ÓXIDO",
        "ÓXIDO SIN DESCASCARADO", "ÓXIDO DE LAMINADO",
    ],
    "superficie: marcas": [
        "MARCAS", "MARCA DE PATIN", "RAYAS", "SOMBRAS", "PLASTAS", "MANCHAS NEGRAS CAL",
    ],
    "aguas arriba (acería / planchón)": ["INCLUSIONES", "ESCAMAS", "GRIETA"],
    "manejo y empaque": ["EMPAQUE", "MAL ENROLLADO", "PUNTA RASGADA", "ORILLA DEFECTUOSA", "TENSIÓN DE ENROLLADO"],
    "sistema o dato": [
        "FALLA DE EQUIPO", "ERROR EN ESPECIFICACIONES", "DIFERENCIA ENTRE MEDIDORES", "SIN EVALUACIÓN T-EXPERT",
    ],
}
DEFECTO_A_FAMILIA = {d: f for f, ds in FAMILIAS.items() for d in ds}
# Nombre de columna corto para cada familia
SLUG_FAMILIA = {
    "dimensional (regla vs. tolerancia)": "fam_dimensional",
    "térmico (regla vs. tolerancia)": "fam_termico",
    "forma y perfil": "fam_forma",
    "superficie: óxido": "fam_oxido",
    "superficie: marcas": "fam_marcas",
    "aguas arriba (acería / planchón)": "fam_aguas_arriba",
    "manejo y empaque": "fam_manejo",
    "sistema o dato": "fam_sistema",
}

# Banderas por rollo que usan los notebooks: nombre corto -> nombre del defecto (normalizado)
BANDERAS = {
    "def_espesor": "ESPESOR (+/-)",
    "def_ancho": "ANCHO (+/-)",
    "def_peso_mas": "PESO (+)",
    "def_peso_menos": "PESO (-)",
    "def_te_menos": "TEMPERATURA DE ENROLLADO (-)",
    "def_te_pm": "TEMPERATURA DE ENROLLADO (+/-)",
    "def_ta_pm": "TEMPERATURA DE ACABADO (+/-)",
    "def_mal_perfil": "MAL PERFIL",
    "def_doblez": "DOBLEZ PAÑUELO",
    "def_ox_temp": "OXIDO POR TEMPERATURA",
    "def_ox_rojo": "ÓXIDO ROJO",
    "def_ox_rod": "ÓXIDO DE RODILLOS",
    "def_patin": "MARCA DE PATIN",
    "def_inclus": "INCLUSIONES",
}


def familia(defecto: pd.Series) -> pd.Series:
    return defecto.map(DEFECTO_A_FAMILIA).fillna("otro / sin clasificar")


def banderas_defecto(df: pd.DataFrame, d: pd.DataFrame) -> pd.DataFrame:
    """Una columna booleana por defecto de interés y por familia (``fam_*``)."""
    out = pd.DataFrame(index=df.index)
    ids = df["Material Salida"]
    for corto, nombre in BANDERAS.items():
        out[corto] = ids.isin(d.loc[d["Defecto"] == nombre, "Material Salida"])
    fam = familia(d["Defecto"])
    for f, slug in SLUG_FAMILIA.items():
        out[slug] = ids.isin(d.loc[fam == f, "Material Salida"])
    out["def_cualquiera"] = ids.isin(d["Material Salida"])
    return out


def reglas_tolerancia(df: pd.DataFrame) -> dict[str, tuple[str, pd.Series]]:
    """Reglas que podrían generar cada defecto automático usando SOLO el resumen por rollo.

    Devuelve {bandera: (descripción de la regla, serie booleana)}.
    """
    t = df
    return {
        "def_espesor": ("espesor promedio fuera de [mín, máx]",
                        (t["Espesor"] < t["Espesor Mínimo"]) | (t["Espesor"] > t["Espesor Máximo"])),
        "def_ancho": ("ancho promedio fuera de [mín, máx]",
                      (t["Ancho"] < t["Ancho Mínimo"]) | (t["Ancho"] > t["Ancho Máximo"])),
        "def_te_menos": ("temp. enrollado real < mínimo",
                         t["temp_enrollado_real_l"] < t["Temp Enrollado Min"]),
        "def_te_pm": ("temp. enrollado real fuera de [mín, máx]",
                      (t["temp_enrollado_real_l"] < t["Temp Enrollado Min"]) | (t["temp_enrollado_real_l"] > t["Temp Enrollado Max"])),
        "def_ta_pm": ("temp. acabado real fuera de [mín, máx]",
                      (t["Temp Acabado Real"] < t["Temp Acabado Min"]) | (t["Temp Acabado Real"] > t["Temp Acabado Max"])),
        "def_peso_mas": ("peso > máximo", t["Peso"] > t["Peso Máximo"]),
        "def_peso_menos": ("peso < mínimo", t["Peso"] < t["Peso Mínimo"]),
        "def_mal_perfil": ("corona sin dato", t["Corona Salida"].isna()),
    }


def concordancia_regla(y: pd.Series, regla: pd.Series) -> dict[str, float]:
    """Qué tanto reproduce una regla a la etiqueta."""
    r = regla.fillna(False).astype(bool)
    y = y.astype(bool)
    return {
        "% rollos con etiqueta": 100 * y.mean(),
        "% rollos que cumplen la regla": 100 * r.mean(),
        "P(etiqueta | regla)": y[r].mean() if r.any() else float("nan"),
        "P(etiqueta | no regla)": y[~r].mean(),
        "% de etiquetas explicadas por la regla": 100 * r[y].mean() if y.any() else float("nan"),
    }
