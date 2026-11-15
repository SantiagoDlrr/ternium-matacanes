"""Herramientas estadísticas simples (Entrega I: proporciones, intervalos, descomposiciones)."""
from __future__ import annotations

import numpy as np
import pandas as pd

SEMILLA = 20251115  # fija para permutaciones y cualquier muestreo


def wilson(y: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de Wilson al 95 % para una proporción."""
    if n == 0:
        return (np.nan, np.nan)
    p = y / n
    den = 1 + z**2 / n
    centro = (p + z**2 / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    return centro - h, centro + h


def newcombe(y1: int, n1: int, y0: int, n0: int) -> tuple[float, float, float]:
    """Diferencia de proporciones p1 - p0 con intervalo híbrido de Newcombe (método 10)."""
    p1, p0 = y1 / n1, y0 / n0
    l1, u1 = wilson(y1, n1)
    l0, u0 = wilson(y0, n0)
    d = p1 - p0
    return d, d - np.sqrt((p1 - l1) ** 2 + (u0 - p0) ** 2), d + np.sqrt((u1 - p1) ** 2 + (p0 - l0) ** 2)


def benjamini_hochberg(p: pd.Series, q: float = 0.05) -> pd.Series:
    """Devuelve True para las hipótesis rechazadas controlando la FDR en q."""
    p = p.astype(float)
    orden = p.sort_values()
    m = len(orden)
    umbral = q * np.arange(1, m + 1) / m
    ok = orden.values <= umbral
    k = np.max(np.where(ok)[0]) + 1 if ok.any() else 0
    rech = pd.Series(False, index=p.index)
    rech.loc[orden.index[:k]] = True
    return rech


def p_dos_proporciones(y1: int, n1: int, y0: int, n0: int) -> float:
    """Valor p bilateral (prueba z con proporción combinada)."""
    from math import erf, sqrt

    pc = (y1 + y0) / (n1 + n0)
    se = sqrt(pc * (1 - pc) * (1 / n1 + 1 / n0))
    if se == 0:
        return 1.0
    z = abs(y1 / n1 - y0 / n0) / se
    return 2 * (1 - 0.5 * (1 + erf(z / sqrt(2))))


def descomposicion_anidada(df: pd.DataFrame, y: str, niveles: list[str]) -> pd.Series:
    """Fracción de la suma de cuadrados total atribuible a cada nivel de una jerarquía anidada.

    Cada nivel se mide como la dispersión de las medias de sus celdas alrededor de la media
    de la celda padre. Es descriptiva (suma de cuadrados, no componentes de varianza
    insesgados): con celdas pequeñas, los niveles finos absorben parte del ruido. Por eso se
    acompaña de una línea base por permutación (``linea_base_permutacion``).
    """
    x = df.dropna(subset=[y])
    g = x[y].mean()
    tot = ((x[y] - g) ** 2).sum()
    out = {}
    for i, nivel in enumerate(niveles):
        m = x.groupby(niveles[: i + 1], observed=True)[y].transform("mean")
        mp = x.groupby(niveles[:i], observed=True)[y].transform("mean") if i else g
        out[nivel] = ((m - mp) ** 2).sum() / tot
    out["rollo (dentro de la celda más fina)"] = 1 - sum(out.values())
    s = pd.Series(out)
    s["n"] = len(x)
    return s


def linea_base_permutacion(df: pd.DataFrame, y: str, niveles: list[str], n_perm: int = 20,
                           semilla: int = SEMILLA) -> pd.Series:
    """Fracción que el ÚLTIMO nivel obtendría por puro azar.

    Se permutan las etiquetas del último nivel dentro de su celda padre (mismos tamaños de
    grupo), se recalcula su fracción y se reporta la media y el p95 de la distribución nula.
    """
    rng = np.random.default_rng(semilla)
    x = df.dropna(subset=[y]).copy()
    padre, hoja = niveles[:-1], niveles[-1]
    vals = []
    for _ in range(n_perm):
        x["_perm"] = x.groupby(padre, observed=True)[hoja].transform(lambda s: rng.permutation(s.values))
        vals.append(descomposicion_anidada(x, y, padre + ["_perm"])["_perm"])
    vals = np.array(vals)
    return pd.Series({"media nula": vals.mean(), "p95 nula": np.quantile(vals, 0.95)})


def r2_grupo(df: pd.DataFrame, y: str, claves: list[str]) -> float:
    """R² de las medias de grupo (fracción de varianza entre grupos)."""
    x = df.dropna(subset=[y])
    m = x.groupby(claves, observed=True)[y].transform("mean")
    return 1 - ((x[y] - m) ** 2).sum() / ((x[y] - x[y].mean()) ** 2).sum()


def fraccion_determinada(df: pd.DataFrame, y: str, claves: list[str]) -> float:
    """% de rollos cuyo valor de ``y`` es único dentro de su combinación de ``claves``."""
    x = df.dropna(subset=[y])
    k = x.groupby(claves, observed=True)[y].transform("nunique")
    return 100 * (k == 1).mean()
