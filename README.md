# Reto Ternium · Entrega final — MC4 → Skinpass de Pesquería

Artículo final (revista elegida: *Journal of Manufacturing Systems*) y su análisis reproducible. Liga, rollo por
rollo, los datos de producción 2025 del **Molino Caliente 4 de Pesquería (MC4_PSQ)** con los del **Skinpass de
Pesquería (SKP_PSQ)** y pregunta qué tanto de la corrección de bending que aplica el Skinpass
(Y = bending real − preset) se explica por lo que se sabe antes de procesar el rollo: su producto, su dimensión,
el programa del Skinpass y la corona relativa con que sale del MC4.

> **Confidencialidad.** Los datos están cubiertos por el acuerdo con Ternium y **nunca se suben al repositorio**
> (ver `.gitignore`). Este repo solo contiene código, figuras y tablas agregadas (sin identificadores de rollo,
> clientes ni usuarios) y el artículo.

## Reproducir todo con un solo comando

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.reproducir
```

`python -m src.reproducir` ejecuta los notebooks 07–10 en orden, regenera **todas las figuras y tablas del artículo**
y la tabla completa de contrastes, convierte cada cifra del texto en una macro LaTeX
(`articulo/generado/cifras.tex`) y copia figuras y tablas a `articulo/`. Opciones:

| Opción | Qué hace |
|---|---|
| `--pdf` | además compila `articulo/main.pdf` con `latexmk` (requiere una distribución de LaTeX con `elsarticle`) |
| `--todo` | además re-ejecuta los notebooks 01–06 de la Entrega I |
| `--solo-articulo` | no re-ejecuta notebooks; solo regenera macros, sincroniza `articulo/` y (con `--pdf`) compila |

Tiempo aproximado: 5–6 minutos (la primera lectura de los Excel deja un caché parquet en `outputs/cache/`,
ignorado por git).

### Dónde están los datos

Sin tocar código, por variables de entorno o por carpetas:

| Fuente | Variable de entorno | Carpetas que se buscan si no se define |
|---|---|---|
| 24 archivos quincenales `MC4_PSQ *.xlsx` | `TERNIUM_DATA_DIR` | `data/` o `../data_molino_prev/` |
| 12 archivos mensuales `SKP_PSQ *.xlsx` | `TERNIUM_SKP_DIR` | `ResumenProduccionSKP/` o `../ResumenProduccionSKP/` |

Las semillas están fijas (`src/config.py`, `SEMILLA = 20251115`). Ninguna regla de depuración borra rollos en
silencio: cada exclusión se cuenta (`outputs/tablas/poblacion_pasos.csv`) y se compara contra los incluidos
(`comparacion_exclusiones.csv`).

## Plan de análisis

`docs/plan_de_analisis.md` fija resultado, exposiciones, conjunto de ajuste, unidad de análisis, exclusiones,
anclajes de validación y criterios de refutación **antes** de la estimación principal. Todo cambio posterior está en
su bitácora, con fecha y motivo.

## Estructura

```
notebooks/
  01–06  Entrega I (inmersión en los datos del MC4)
  07_union_mc4_skinpass.ipynb               unión MC4 ↔ Skinpass, población paso a paso, exclusiones, supuestos S1–S6
  08_soporte_y_resultado_principal.ipynb    soporte, descomposición, asociación corona → Y, heterogeneidad (figs. R1–R3)
  09_validacion_y_robustez.ipynb            control negativo, signo físico, R1–R9, programa vs periodo, Cinelli–Hazlett (fig. R4)
  10_modelo_predictivo.ipynb                gradient boosting vs línea base, validación agrupada y temporal (fig. R5),
                                            volumen del experimento y tabla completa de contrastes
src/
  config.py            rutas configurables y semilla
  carga.py, depuracion.py, poblacion.py, calidad.py      MC4 (Entrega I)
  skinpass.py          lectura del Skinpass, agregación por rollo, unión y pasos de población
  inferencia.py        descomposición con línea base por permutación, regresión con efectos fijos y errores
                       agrupados, curva por deciles, sensibilidad de Cinelli y Hazlett
  resultados.py        soporte, resultado principal, heterogeneidad, validación y robustez
  prediccion.py        modelo predictivo y línea base
  contrastes.py        tabla completa de contrastes
  figuras_articulo.py, diagramas_final.py   figuras del artículo (tamaño de impresión, PDF vectorial)
  reproducir.py        el comando único
outputs/
  figuras/articulo/    figuras del artículo (PDF + PNG)
  tablas/              tablas agregadas, cifras.json y contrastes_completos.csv
articulo/              LaTeX (elsarticle, JMS): main.tex, secciones/, referencias.bib, figuras/, generado/
docs/plan_de_analisis.md
```

## Overleaf

La carpeta `articulo/` es autocontenida: después de `python -m src.reproducir`, se puede comprimir y subir tal cual a
Overleaf (compilador pdfLaTeX). Si se edita el texto en Overleaf, las cifras siguen saliendo de
`generado/cifras.tex`; para actualizarlas basta con volver a correr el comando y subir esa carpeta.
