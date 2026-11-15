"""Definición operativa de la condición de llegada al Skinpass (pregunta de investigación).

La definición se declara AQUÍ, antes de cualquier modelo, con tres criterios físicos
construidos solo con mediciones (nunca con etiquetas del sistema; ver Fenómeno 1):

C1 · |cuña| > 1 % del espesor
    Una diferencia de espesor entre orillas mayor al 1 % produce elongación diferencial
    apreciable al estirar parejo (criterio de planeza; Shohet y Townsend, 1968).
C2 · corona relativa alta para su rango de espesor
    Por encima del percentil 90 de la población de estudio dentro del mismo rango de
    espesor objetivo. Es relativa al espesor porque la planeza depende de corona/espesor,
    y por rango porque la corona relativa crece mecánicamente al bajar el espesor.
C3 · temperatura de enrollado real fuera de la tolerancia de la orden
    Fuera de [Temp Enrollado Min, Temp Enrollado Max]. La temperatura de enrollado fija
    la microestructura y la oxidación que el decapado y el Skinpass heredan.

"Mala condición de llegada" = cumple al menos uno de los tres criterios.

Nota de no-tautología: los criterios usan mediciones y tolerancias, no las etiquetas de
defecto. En la pregunta de investigación, estas variables son el RESULTADO; las
explicativas son solo variables conocidas antes de laminar (producto, dimensión,
programa y posición). Ninguna medición aparece en ambos lados.
"""
from __future__ import annotations

import pandas as pd

UMBRAL_CUNA_PCT = 1.0  # % del espesor
PERCENTIL_CORONA = 0.90


def umbrales_corona(p: pd.DataFrame) -> pd.Series:
    """p90 de la corona relativa por rango de espesor, en la población de estudio."""
    return p.groupby("rango_espesor", observed=True)["corona_rel_pct"].quantile(PERCENTIL_CORONA)


def definir_condicion(p: pd.DataFrame) -> pd.DataFrame:
    """Devuelve la población con los tres criterios y la bandera ``mala_condicion``.

    Los rollos sin alguna medición quedan con NaN en ese criterio y se reportan aparte
    (el faltante de corona es informativo; ver Fenómeno 6): no se imputan ni se excluyen
    en silencio.
    """
    out = p.copy()
    u = umbrales_corona(out)
    out["c1_cuna"] = out["cuna_rel_pct"].abs() > UMBRAL_CUNA_PCT
    out["c1_cuna"] = out["c1_cuna"].mask(out["cuna_rel_pct"].isna())
    out["c2_corona"] = out["corona_rel_pct"] > out["rango_espesor"].map(u).astype(float)
    out["c2_corona"] = out["c2_corona"].mask(out["corona_rel_pct"].isna())
    fuera = (out["temp_enrollado_real_l"] < out["Temp Enrollado Min"]) | \
            (out["temp_enrollado_real_l"] > out["Temp Enrollado Max"])
    out["c3_temp"] = fuera.mask(out["temp_enrollado_real_l"].isna() | out["Temp Enrollado Min"].isna())
    criterios = out[["c1_cuna", "c2_corona", "c3_temp"]]
    out["sin_dato"] = criterios.isna().any(axis=1)
    out["mala_condicion"] = criterios.eq(True).any(axis=1).mask(
        criterios.isna().all(axis=1))
    return out
