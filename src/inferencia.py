"""Estimación e incertidumbre para la Entrega final (plan de análisis, secciones 7–11).

- ``descomposicion`` / ``exceso_sobre_azar``: descomposición anidada de la suma de cuadrados
  de Y con línea base por permutación (dentro de la celda padre) y bootstrap agrupado por
  programa del Skinpass para el intervalo del exceso sobre el azar.
- ``fe_ols``: regresión lineal con efectos fijos de una sola dimensión (transformación
  *within*) y errores agrupados (CR1; Cameron y Miller, 2015).
- ``curva_deciles``: Y dentro de celda por deciles de la exposición dentro de celda.
- ``sensibilidad_ch``: valor de robustez y cota de Cinelli y Hazlett (2020) usando un
  confusor observado de referencia.

Todo es numpy/pandas con semilla fija (``config.SEMILLA``).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .config import SEMILLA


# ============================================================================ descomposición
def _codigos(df: pd.DataFrame, niveles: list[str]) -> list[np.ndarray]:
    """Código entero de cada prefijo de la jerarquía: [nivel0], [nivel0, nivel1], …"""
    cods = []
    for i in range(len(niveles)):
        cods.append(df.groupby(niveles[: i + 1], observed=True, sort=False, dropna=False).ngroup().to_numpy())
    return cods


def _medias(y: np.ndarray, cod: np.ndarray) -> np.ndarray:
    s = np.bincount(cod, weights=y)
    n = np.bincount(cod)
    return (s / n)[cod]


def _fracciones(y: np.ndarray, cods: list[np.ndarray]) -> np.ndarray:
    tss = ((y - y.mean()) ** 2).sum()
    prev = np.full_like(y, y.mean())
    out = []
    for c in cods:
        m = _medias(y, c)
        out.append(((m - prev) ** 2).sum() / tss)
        prev = m
    return np.array(out)


def _fraccion_nivel(y: np.ndarray, padre: np.ndarray | None, hijo: np.ndarray) -> float:
    tss = ((y - y.mean()) ** 2).sum()
    mp = np.full_like(y, y.mean()) if padre is None else _medias(y, padre)
    return float(((_medias(y, hijo) - mp) ** 2).sum() / tss)


def _permutar_dentro(cod: np.ndarray, padre: np.ndarray | None, rng: np.random.Generator) -> np.ndarray:
    """Permuta los códigos de un nivel dentro de cada celda padre (mismos tamaños de grupo)."""
    if padre is None:
        return rng.permutation(cod)
    orden = np.lexsort((rng.random(len(cod)), padre))
    base = np.argsort(padre, kind="stable")
    out = np.empty_like(cod)
    out[base] = cod[orden]
    return out


def descomposicion(df: pd.DataFrame, y: str, niveles: list[str]) -> pd.Series:
    x = df.dropna(subset=[y])
    f = _fracciones(x[y].to_numpy(float), _codigos(x, niveles))
    s = pd.Series(f, index=niveles)
    s["rollo (dentro de la celda más fina)"] = 1 - f.sum()
    return s


def _exceso(y: np.ndarray, cods: list[np.ndarray], n_perm: int, rng) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    obs = _fracciones(y, cods)
    nula = np.zeros((n_perm, len(cods)))
    for k in range(len(cods)):
        padre = cods[k - 1] if k else None
        for r in range(n_perm):
            nula[r, k] = _fraccion_nivel(y, padre, _permutar_dentro(cods[k], padre, rng))
    return obs, nula.mean(0), np.quantile(nula, 0.95, axis=0)


def exceso_sobre_azar(df: pd.DataFrame, y: str, niveles: list[str], grupo_boot: str | None = "programa_skp",
                      n_perm: int = 100, n_boot: int = 200, n_perm_boot: int = 5,
                      metodo: str = "mitades", semilla: int = SEMILLA) -> pd.DataFrame:
    """Fracción observada, media y p95 nulos (permutación) y exceso con IC agrupado por programa.

    ``metodo="mitades"`` (el que usa el artículo; bitácora del plan, v1.2): en cada réplica se
    toma la mitad de los programas del Skinpass sin reemplazo, se recalcula el exceso (con
    ``n_perm_boot`` permutaciones) y el IC es exceso ± 1.96 × DE de las réplicas (jackknife de
    mitades: con d = n/2 la DE entre mitades estima la DE del estimador completo).
    ``metodo="bootstrap"``: programas con reemplazo (cada copia es un programa distinto),
    IC por percentiles. Se conserva para mostrar por qué se descartó: al duplicar programas,
    las fracciones de suma de cuadrados se sesgan y las réplicas no cubren la estimación.
    """
    if metodo not in {"mitades", "bootstrap"}:
        raise ValueError(metodo)
    rng = np.random.default_rng(semilla)
    cols = list(dict.fromkeys([y, *niveles] + ([grupo_boot] if grupo_boot else [])))
    x = df[cols].dropna(subset=[y]).reset_index(drop=True)
    yv = x[y].to_numpy(float)
    cods = _codigos(x, niveles)
    obs, media, p95 = _exceso(yv, cods, n_perm, rng)

    boot = None
    if grupo_boot and n_boot:
        g = x[grupo_boot].astype("string").fillna("NA")
        gcod, guniq = pd.factorize(g)
        filas_por_g = pd.Series(np.arange(len(x))).groupby(gcod).apply(np.asarray).to_dict()
        boot = np.zeros((n_boot, len(niveles)))
        for b in range(n_boot):
            if metodo == "mitades":
                elegidos = rng.choice(len(guniq), len(guniq) // 2, replace=False)
            else:
                elegidos = rng.integers(0, len(guniq), len(guniq))
            idx = np.concatenate([filas_por_g[e] for e in elegidos])
            xb = x.iloc[idx].reset_index(drop=True)
            if metodo == "bootstrap" and grupo_boot in niveles:
                # cada copia de un programa es un programa distinto (no se fusionan duplicados)
                xb[grupo_boot] = np.repeat(np.arange(len(elegidos)), [len(filas_por_g[e]) for e in elegidos])
            cb = _codigos(xb, niveles)
            ob, mb, _ = _exceso(xb[y].to_numpy(float), cb, n_perm_boot, rng)
            boot[b] = ob - mb
    t = pd.DataFrame({"nivel": niveles, "fraccion_observada": obs, "media_nula": media,
                      "p95_nula": p95, "exceso": obs - media})
    if boot is not None:
        if metodo == "mitades":
            de = boot.std(axis=0, ddof=1)
            t["exceso_ic_inf"] = t["exceso"] - 1.96 * de
            t["exceso_ic_sup"] = t["exceso"] + 1.96 * de
        else:
            t["exceso_ic_inf"] = np.quantile(boot, 0.025, axis=0)
            t["exceso_ic_sup"] = np.quantile(boot, 0.975, axis=0)
        t["replicas_media"] = boot.mean(axis=0)
        t["metodo_ic"] = metodo
    t["rollos"] = len(x)
    t["grupos_en_el_nivel"] = [len(np.unique(c)) for c in cods]
    return t


# ============================================================================ regresión FE
def _demean(v: np.ndarray, cod: np.ndarray) -> np.ndarray:
    return v - _medias(v, cod)


def fe_ols(df: pd.DataFrame, y: str, xs: list[str], fe: str, cluster: str) -> pd.DataFrame:
    """OLS con efectos fijos de ``fe`` (within) y errores agrupados por ``cluster`` (CR1).

    Se eliminan las celdas con un solo rollo (no aportan variación dentro de celda). La
    corrección de grados de libertad cuenta los efectos fijos absorbidos (no están
    anidados en los grupos), lo que es conservador.
    """
    x = df.dropna(subset=[y, *xs, fe, cluster]).copy()
    x = x[x.groupby(fe, observed=True)[y].transform("size") > 1]
    cod = pd.factorize(x[fe])[0]
    Y = _demean(x[y].to_numpy(float), cod)
    X = np.column_stack([_demean(x[c].to_numpy(float), cod) for c in xs])
    n, k = X.shape
    n_fe = len(np.unique(cod))
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ Y
    u = Y - X @ beta
    gcod = pd.factorize(x[cluster])[0]
    G = gcod.max() + 1
    scores = np.zeros((G, k))
    np.add.at(scores, gcod, X * u[:, None])
    meat = scores.T @ scores
    df_resid = n - k - n_fe
    c = (G / (G - 1)) * ((n - 1) / df_resid)
    V = c * xtx_inv @ meat @ xtx_inv
    se = np.sqrt(np.diag(V))
    tval = beta / se
    tcrit = stats.t.ppf(0.975, G - 1)
    sd_within = X.std(axis=0)
    out = pd.DataFrame({
        "variable": xs, "coef": beta, "se": se, "t": tval,
        "p": 2 * stats.t.sf(np.abs(tval), G - 1),
        "ic_inf": beta - tcrit * se, "ic_sup": beta + tcrit * se,
        "sd_dentro_celda": sd_within, "efecto_por_sd": beta * sd_within,
        "efecto_por_sd_ic_inf": (beta - tcrit * se) * sd_within,
        "efecto_por_sd_ic_sup": (beta + tcrit * se) * sd_within,
        # R² parcial (t² / (t² + gl)); con errores agrupados es una aproximación descriptiva
        "r2_parcial": tval**2 / (tval**2 + df_resid),
    })
    out["rollos"] = n
    out["grupos_cluster"] = G
    out["celdas_fe"] = n_fe
    out["gl_resid"] = df_resid
    return out


def ssr_fe(df: pd.DataFrame, y: str, xs: list[str], fe: str) -> float:
    """Suma de cuadrados residual de y ~ xs + FE(fe) (para R² parciales de un bloque de FE)."""
    cod = pd.factorize(df[fe])[0]
    Y = _demean(df[y].to_numpy(float), cod)
    if not xs:
        return float((Y**2).sum())
    X = np.column_stack([_demean(df[c].to_numpy(float), cod) for c in xs])
    b, *_ = np.linalg.lstsq(X, Y, rcond=None)
    return float(((Y - X @ b) ** 2).sum())


# ============================================================================ curva por deciles
def curva_deciles(df: pd.DataFrame, y: str, x: str, fe: str, cluster: str, q: int = 10) -> pd.DataFrame:
    """Medias de Y (centrada en su celda) por deciles de x (centrada en su celda), con IC agrupado."""
    d = df.dropna(subset=[y, x, fe, cluster]).copy()
    d = d[d.groupby(fe, observed=True)[y].transform("size") > 1]
    cod = pd.factorize(d[fe])[0]
    d["_y"] = _demean(d[y].to_numpy(float), cod)
    d["_x"] = _demean(d[x].to_numpy(float), cod)
    d["_q"] = pd.qcut(d["_x"], q, labels=False, duplicates="drop")
    filas = []
    for b, g in d.groupby("_q"):
        r = g["_y"] - g["_y"].mean()
        sg = r.groupby(g[cluster]).sum()
        G = len(sg)
        se = np.sqrt((sg**2).sum() * G / max(G - 1, 1)) / len(g)
        filas.append({"decil": int(b) + 1, "x_media": g["_x"].mean(), "y_media": g["_y"].mean(),
                      "ic_inf": g["_y"].mean() - 1.96 * se, "ic_sup": g["_y"].mean() + 1.96 * se,
                      "rollos": len(g), "programas": G})
    return pd.DataFrame(filas)


# ============================================================================ Cinelli–Hazlett
def valor_robustez(t: float, gl: float, q: float = 1.0, alfa: float | None = None) -> float:
    """Valor de robustez RV_q (o RV_{q,α}) de Cinelli y Hazlett (2020)."""
    f = q * abs(t) / np.sqrt(gl)
    if alfa is not None:
        fcrit = stats.t.ppf(1 - alfa / 2, gl - 1) / np.sqrt(gl - 1)
        f = f - fcrit
        if f <= 0:
            return 0.0
    return 0.5 * (np.sqrt(f**4 + 4 * f**2) - f**2)


def cota_ch(r2dxj: float, r2yxj: float, kd: float = 1.0, ky: float = 1.0) -> tuple[float, float]:
    """Cotas de R² parciales de un confusor kd/ky veces tan fuerte como el de referencia.

    Fórmulas de ``ovb_partial_r2_bound`` (Cinelli y Hazlett, 2020, sección 6).
    """
    r2dz = kd * (r2dxj / (1 - r2dxj))
    r2zxj = kd * (r2dxj**2) / ((1 - kd * r2dxj) * (1 - r2dxj))
    r2yz = ((np.sqrt(ky) + np.sqrt(r2zxj)) / np.sqrt(1 - r2zxj)) ** 2 * (r2yxj / (1 - r2yxj))
    return float(r2dz), float(min(r2yz, 1.0))


def sensibilidad_ch(df: pd.DataFrame, y: str, d: str, otros: list[str], fe_completo: str,
                    fe_sin_ref: str, coef: float, se: float, gl: float) -> dict:
    """Sensibilidad a confusión no medida con un bloque de FE observado como referencia.

    El confusor de referencia es la parte de ``fe_completo`` que no está en ``fe_sin_ref``
    (aquí: producto, dentro de dimensión × mes). Sus R² parciales se calculan comparando
    sumas de cuadrados residuales con y sin ese bloque.
    """
    x = df.dropna(subset=[y, d, *otros, fe_completo, fe_sin_ref]).copy()
    x = x[x.groupby(fe_completo, observed=True)[y].transform("size") > 1]
    r2dxj = 1 - ssr_fe(x, d, otros, fe_completo) / ssr_fe(x, d, otros, fe_sin_ref)
    r2yxj = 1 - ssr_fe(x, y, [d, *otros], fe_completo) / ssr_fe(x, y, [d, *otros], fe_sin_ref)
    t = coef / se
    rv = valor_robustez(t, gl)
    rv_a = valor_robustez(t, gl, alfa=0.05)
    r2dz, r2yz = cota_ch(r2dxj, r2yxj)
    sesgo = se * np.sqrt(gl) * np.sqrt(r2yz * r2dz / (1 - r2dz))
    return {
        "t": t, "gl": gl, "RV_q1": rv, "RV_q1_alfa05": rv_a,
        "r2_D_ref": r2dxj, "r2_Y_ref": r2yxj,
        "r2_D_confusor_1x": r2dz, "r2_Y_confusor_1x": r2yz,
        "sesgo_max_1x": sesgo,
        "coef_ajustado_1x": coef - np.sign(coef) * sesgo,
    }


# ============================================================================ utilidades
def bh(p: pd.Series, q: float = 0.05) -> pd.DataFrame:
    """Valores q de Benjamini–Hochberg y rechazo al nivel q."""
    p = p.astype(float)
    m = p.notna().sum()
    orden = p.sort_values()
    rango = np.arange(1, len(orden) + 1)
    qv = (orden * m / rango)[::-1].cummin()[::-1].clip(upper=1)
    qv = qv.reindex(p.index)
    return pd.DataFrame({"q_bh": qv, "rechaza_bh": qv <= q})


def k_que_anula(r2dxj: float, r2yxj: float, coef: float, se: float, gl: float) -> float:
    """Menor k (kd = ky = k) tal que un confusor k veces tan fuerte como la referencia anula la estimación."""
    def sesgo(k):
        r2dz, r2yz = cota_ch(r2dxj, r2yxj, kd=k, ky=k)
        if r2dz >= 1:
            return np.inf
        return se * np.sqrt(gl) * np.sqrt(r2yz * r2dz / (1 - r2dz))
    lo, hi = 1e-6, (1 - r2dxj) / r2dxj * 0.999
    if sesgo(hi) < abs(coef):
        return np.inf
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if sesgo(mid) < abs(coef) else (lo, mid)
    return hi
