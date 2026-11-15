# Reto Ternium · Entrega I — Inmersión y formulación

Investigación preliminar sobre los datos de producción 2025 del Molino Caliente 4 de
Pesquería (MC4_PSQ): 24 archivos quincenales, un renglón por rollo (~150 mil) y 280
columnas. La pregunta original del Socio Formador se refiere al Skinpass, cuyas columnas
vienen 100 % vacías; este trabajo caracteriza la **condición con la que los rollos llegan
al Skinpass** y formula una pregunta respondible con los datos disponibles.

> **Confidencialidad.** Los datos están cubiertos por el acuerdo con Ternium y **nunca se
> suben al repositorio** (ver `.gitignore`). Este repo solo contiene código, figuras
> agregadas y documentos.

## Estructura

```
notebooks/
  01_carga_y_auditoria.ipynb            # lectura de los 24 archivos y auditoría de esquema
  02_diccionario_y_poblacion.ipynb      # diccionario, población de estudio y jerarquía de producto
  03_fenomeno1_etiquetas_de_calidad.ipynb   # F1 (obligatorio): ¿qué significa "calidad"?
  04_fenomeno2_asignacion_de_consignas.ipynb # F2 (obligatorio): ¿de dónde sale la "receta"?
  05_fenomeno6_calidad_del_dato.ipynb   # F6 (elección): la calidad del dato como hallazgo
  06_pregunta_y_evidencia.ipynb         # definición operativa de condición de llegada y evidencia
src/
  config.py       # rutas configurables (TERNIUM_DATA_DIR)
  carga.py        # lectura de los archivos originales, sin ediciones manuales
  depuracion.py   # reglas de limpieza declaradas (L1–L10), con bitácora
  poblacion.py    # variables derivadas, población de estudio y jerarquía
  calidad.py      # familias de defectos, banderas por rollo y reglas de tolerancia
  condicion.py    # definición operativa de "condición de llegada" (pregunta)
  estadistica.py  # proporciones con intervalos, descomposiciones, línea base por permutación
  visualizacion.py / diagramas.py       # estilo de figuras, mapa del proceso y diagrama causal
outputs/
  figuras/        # las 6 figuras del documento + mapa del proceso + diagrama causal
  tablas/         # tablas exportadas (jerarquía, diccionario, umbrales)
docs/
  entrega1.md     # documento de la entrega (máx. 10 páginas)
  referencias.md  # referencias en formato APA
  anexos/         # A: diccionario razonado · B: preguntas al Socio Formador · C: callejones sin salida
data/             # (vacía; ignorada por git) copia local de los 24 xlsx
```

## Cómo reproducir

1. Crear un entorno e instalar dependencias:

   ```
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Apuntar a los datos (cualquiera de las dos opciones):
   - copiar los 24 archivos `MC4_PSQ *.xlsx` a `data/`, **o**
   - `export TERNIUM_DATA_DIR="/ruta/a/los/archivos"`

3. Ejecutar los notebooks en orden (01 → 06). Cada uno corre de principio a fin sin pasos
   manuales. La primera lectura de los 24 archivos toma 1–2 minutos y deja un caché
   parquet en `outputs/cache/` (ignorado por git); las corridas siguientes son rápidas.
   También pueden ejecutarse todos desde la terminal:

   ```
   jupyter execute notebooks/*.ipynb
   ```

Las reglas de limpieza están declaradas en `src/depuracion.py` **antes** de evaluar su
efecto (ningún rollo se elimina: valores imposibles pasan a NaN en columnas derivadas,
con bandera y bitácora). La semilla de toda permutación o muestreo está fija en
`src/config.py` (`SEMILLA = 20251115`).
