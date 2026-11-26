# Plan de análisis · Entrega final

*Versión 1 · 25-nov-2026 · Borrador para revisión del equipo.*
*Este plan fija las reglas de diseño **antes** de correr la estimación principal (guía de la Entrega final, Parte 2, §3).
Cualquier cambio posterior se registra en la bitácora al final, con fecha y motivo.*
*Ya no es posible hacer consultas al Socio Formador: cada ambigüedad se resuelve con un **supuesto explícito**,
la evidencia que lo respalda y una prueba de sensibilidad que muestra cuánto depende el resultado de él (sección 14).*

> **Transparencia.** El 25-nov hicimos una exploración rápida de la unión MC4–Skinpass para decidir si la
> pregunta era viable (sección 13). Esas cifras **no** son resultados del artículo: los resultados se recalculan
> con este plan congelado, en los notebooks 07–10.

---

## 1. Pregunta, afirmación esperada y clase de contribución

**Pregunta.**

> En los rollos que el MC4 de Pesquería envió al Skinpass de Pesquería en 2025, ¿qué tanto depende la
> corrección de bending que aplica el Skinpass de lo que se sabe antes de procesarlo —su producto, su
> dimensión, el programa del Skinpass y la corona relativa con que sale del MC4—, y cuál de esas cosas pesa más?

**Relación con la Entrega I.** Conserva la estructura de la pregunta anterior ("¿qué tanto depende… de lo que se
sabe antes…, y cuál pesa más?"). Cambia el resultado: ya no es el índice compuesto de "mala condición" del MC4,
sino una medición del Skinpass. La corona relativa del MC4 pasa de ser parte del resultado a ser una de las
fuentes de variación. El acuñamiento sale de la pregunta (sección 5).

**Afirmación más fuerte que esperamos poder sostener** (peldaños 1 y 2 de la escalera):
"Observamos que la corrección de bending varía más entre programas del Skinpass que entre productos, y la corona
relativa de salida del MC4 se asocia con ella, ajustando por producto, dimensión y mes, con una magnitud pequeña."
No contiene "causa", "óptimo" ni "si se cambia".

**Clase de contribución.** Descriptiva para la decisión (descomposición de la variación) con una asociación
ajustada (corona → corrección) y un componente predictivo con encuadre honesto (sección 8.E).

**Lo que la pregunta NO puede afirmar.** Que un preset distinto mejore la calidad; que los productos respondan
distinto a la misma receta (interacción); que el programa influya por desgaste de rodillos (no hay registro).

---

## 2. Datos y unión

| Fuente | Contenido | Uso |
|---|---|---|
| `data_molino_prev/` | 24 archivos quincenales MC4_PSQ 2025, hoja `ResumenProduccion`, 149,734 rollos × 280 columnas | Condición de salida del MC4, producto, dimensión |
| `ResumenProduccionSKP/` | 12 archivos mensuales SKP_PSQ 2025, hoja `ResumenProduccion`, 58,786 registros × 208 columnas | Configuración y resultado del Skinpass |
| `skp_data/` | Señales de bending de 2026 (25 Hz) | **Fuera de alcance**: ningún rollo liga con 2025 (verificado: 0 coincidencias) |

**Llave.** `Material Entrada` (Skinpass) = `Material Salida` (MC4).

**Rollos divididos.** Un rollo del MC4 puede salir del Skinpass en varias piezas (`…PS100`, `…PS101`, …):
8,787 rollos. Las piezas comparten programa del Skinpass (solo 1 excepción). Reglas de agregación por rollo MC4:

- variables numéricas (bending, tensión, fuerza, elongación): **promedio ponderado por el peso de cada pieza**;
- banderas de defecto y dictamen: "alguna pieza";
- fecha del Skinpass: la de la primera pieza; programa del Skinpass: el de la primera pieza.

**Registros del Skinpass que no ligan** (1,687): reprocesos de piezas ya pasadas (`…PS…`) y rollos laminados en
diciembre de 2024. Se cuentan y se excluyen.

---

## 3. Población, unidad de análisis y grupos

**Criterios de inclusión** (en este orden; se reporta cuántos rollos quedan en cada paso):

| Paso | Criterio | Rollos (exploración) |
|---|---|---|
| 0 | Rollos MC4 2025 | 149,734 |
| 1 | `Ruta Teórica` contiene `SKP_PSQ`, **cualquier forma final** | 50,016 |
| 2 | Tiene registro en el Skinpass 2025 | 47,410 |
| 3 | `Fecha Inicio` MC4 < 2025-12-01 (censura de fin de año) | 44,313 |
| 4 | Con bending real y preset | 44,272 |
| 5 | Además con corona relativa válida (solo para la asociación 8.C) | 43,208 |

- **Los 2,428 rollos de "Otras" formas finales se incluyen.** Justificación: pasan por el Skinpass igual que los
  `*-SKP` (93.8 % CALIENTE-BOB, 95.3 % DECAPADO-BOB, 96.7 % FRIO-BOB, contra 94–95 % de los `*-SKP`).
- **Censura de diciembre.** Solo 74.5 % de los rollos MC4 de diciembre aparece en el Skinpass 2025; el resto se
  procesó en enero de 2026 (desfase mediano MC4 → Skinpass: 125 h). Por eso el corte en el paso 3.
- **Comprobación de exclusión** (guía, Fenómeno 6): para cada paso se compara la distribución de producto,
  espesor y corona relativa entre incluidos y excluidos.

**Unidad.** El rollo del MC4. Se reporta siempre el número de rollos **y** el de programas.

**Grupos de dependencia.** Programa del Skinpass (principal: ~831 programas, mediana ~62 rollos); alternativos:
programa del MC4, día y semana del Skinpass.

**Producto.** `Norma | Grado` (Entrega I). **Dimensión.** Rango de espesor objetivo × rango de ancho objetivo
(especificación del pedido, no valores medidos). **Tipo de material.** Tercer campo de `Forma Final`
(CALIENTE, DECAPADO, FRIO).

---

## 4. Resultado

**Resultado principal.** Corrección de bending:

  `Y = Bending Prom. Real [kN] − Preset Bending` (kN, ponderado por pieza)

Es lo que el lazo de control del Skinpass ajustó más allá de lo que fijó la receta. Si el preset anticipara el
bending que el rollo necesita, Y sería cero. Supone que `Preset Bending` está en kN, como el valor real (supuesto S1), y que un preset de 0 significa
"sin preset" (S2; 11 % de los registros, 20 % en modo Fuerza). Ver sección 14.

**Indicadores secundarios** (guía, Parte 2, §4):

1. Bending real promedio (kN).
2. % de rollos con algún defecto registrado **por inspector** en el Skinpass (`Registro Automatico = 0`; 6.6 %).
3. % de rollos RETENIDO en el Skinpass (8.3 %). Se reporta como indicador, no como resultado: solo hay
   retenidos cuando hay defecto (0.0 % sin defecto) y sus causas principales son reglas de espesor y peso.
4. Elongación lograda (%), en rollos en modo Elongación.

**Etiquetas descartadas como resultado** (Fenómeno 1, extendido al Skinpass): `ESPESOR (+/-)` del Skinpass
(regla automática sobre el diámetro interior/exterior del rollo: "Incumple en diam interno"); dictamen y
resolución de ambos molinos.

---

## 5. Fuentes de variación y variables

**Conocidas antes de procesar el rollo en el Skinpass:** tipo de material, producto, dimensión, mes, programa del
Skinpass y la condición de salida del MC4.

**Exposición principal.** Corona relativa de salida del MC4: `Corona Salida / (Espesor × 1000) × 100` (% del
espesor; corona en µm, supuesto S6), **continua, sin cortes convencionales**.

**Exposición secundaria.** Desviación de la temperatura de enrollado: real − objetivo (°C).

**Acuñamiento: fuera de la pregunta.** Ternium indicó que no es prioritario (Anexo B, R1) y en la exploración no
mostró relación consistente con el bending ni con los defectos del Skinpass (|t| entre 1.2 y 2.3). Se conserva solo
como comprobación de robustez (R7).

**Tabla de variables y papeles**

| Variable | Papel en el diagrama | ¿Entra al ajuste? | Por qué |
|---|---|---|---|
| Producto, dimensión | Confusor (el pedido fija la corona del MC4 y la receta del Skinpass) | Sí | Abre el camino pedido → corona y pedido → preset |
| Mes | Confusor (mezcla de pedidos, estado de medidores) | Sí | La corona y la condición cambian durante el año |
| Programa del Skinpass | Fuente de variación de Y; no causa la corona | Solo en sensibilidad | Mejora precisión; no es confusor de corona → Y |
| Corona relativa MC4 | Exposición | — | Pregunta |
| Desv. temp. enrollado | Exposición secundaria | — | Pregunta |
| Preset Bending | Componente de Y | **No** | Y = real − preset; usarlo como explicativa crea acoplamiento mecánico |
| Fuerza, tensión, elongación reales del Skinpass | Respuestas simultáneas / mediadores | **No** | Se generan en el mismo proceso que Y |
| Dictamen, defectos, resolución, calidad sugerida (MC4 y Skinpass) | Posteriores al resultado | **No** | Etiquetas derivadas (Fenómeno 1) |
| Inclusiones (MC4) | Control negativo | No (solo V1) | Origen en el acero, aguas arriba |
| Acuñamiento | Comprobación | Solo R7 | Sección 5 |

---

## 6. Diagrama causal (cambios respecto a la Entrega I)

Se **agregan**: (1) nodo **periodo** (fecha), con flechas a mezcla de pedidos, programas y estado de medidores;
(2) **programa del Skinpass** (rodillos, operador, campaña), con flechas a preset y a bending real;
(3) **preset → bending real**, dentro de un **lazo cerrado** con el medidor de planeza del Skinpass (no observado);
(4) **planeza de entrada** (no observada) entre corona del MC4 y bending real; (5) **rodillo de trabajo del
Skinpass** (observado en `Rodillo de Trabajo`: 35 rodillos, cada uno en ~28 programas), como parte del programa.

Se **corrige**: el Skinpass va **antes** del decapado (`MC4 → SKP → DEC3`, en las rutas), no después.

Conjunto de ajuste para corona → Y: {producto, dimensión, mes}. Variables no observadas que quedan:
planeza de entrada, estado de rodillos (MC4 y Skinpass), decisiones del operador (sección 10).

---

## 7. Diagnóstico de soporte (se reporta antes de cualquier estimación)

Por producto: rollos, programas del Skinpass, meses, celdas producto × dimensión × mes con ≥ 5 rollos,
rango y desviación de la corona relativa dentro de celda, y % con preset = 0. Productos sin variación de corona
dentro de celda salen de la asociación con una nota.

---

## 8. Análisis

**A. Soporte** (sección 7).

**B. Principal descriptivo.** Descomposición anidada de Y: tipo → producto → dimensión → programa del Skinpass →
rollo (`src/estadistica.descomposicion_anidada`). Para cada nivel, línea base por permutación (100 repeticiones,
`SEMILLA = 20251115`). Se reporta la fracción **por encima del azar**, con intervalo por bootstrap agrupado por
programa del Skinpass (200 réplicas). Se repite con el programa antes del producto para mostrar cuánto depende
del orden.

**C. Principal de asociación.** Regresión lineal con efectos fijos de celda (producto × dimensión × mes):
`Y ~ corona_rel + desv_temp_enrollado`, errores agrupados por programa del Skinpass (Cameron y Miller, 2015).
Se reporta el efecto en kN por punto de corona relativa y por una desviación estándar, con IC 95 %, y la curva
por deciles de corona (dentro de celda). Se reporta también la R² parcial de la corona.

**D. Heterogeneidad.** La misma pendiente por producto (productos con ≥ 300 rollos), **todas** en una sola
figura con IC; FDR de Benjamini–Hochberg; nota explícita de la maldición del ganador (Smith y Winkler, 2006).
Tabla completa en `outputs/tablas/contrastes_completos.csv`.

**E. Predictivo ("permite anticipar").** ¿La información previa al Skinpass anticipa Y?

Se usa **un solo modelo de aprendizaje automático**, comparado contra una línea base sencilla, como pide la guía
(Parte 2, §3: "siempre comparados contra una línea base sencilla… bajo la misma validación temporal y agrupada").
La línea base no es un segundo modelo: es la referencia que dice si el modelo aporta algo.

| | Qué es | Variables |
|---|---|---|
| Línea base | Media de Y por producto × dimensión en los datos de entrenamiento (lo que haría una receta por producto) | Producto, dimensión |
| Modelo | Gradient boosting (`HistGradientBoostingRegressor`, semilla fija) | Producto, dimensión, tipo de material, mes, corona relativa, desv. temp. enrollado, espesor y ancho objetivo, temp. enrollado objetivo |

Validación: `GroupKFold` (k = 5) por programa del Skinpass, para que ningún programa quede dividido entre
entrenamiento y prueba, **y** una partición temporal (entrenar ene–ago, evaluar sep–nov). Métricas: MAE y RMSE
(kN) y R² fuera de muestra, con su variación entre pliegues, siempre junto a la línea base. Se reporta también
un `KFold` aleatorio, solo para mostrar cuánto infla el desempeño mezclar rollos del mismo programa.
El preset **no** entra como variable (es componente de Y). La importancia de variables se describe como "lo que
usa el modelo para predecir", nunca como efecto (Shmueli, 2010). Hiperparámetros: búsqueda pequeña dentro de
los pliegues de entrenamiento. **Criterio:** si el modelo no mejora claramente a la línea base, se reporta como
resultado: la información previa al Skinpass, incluida la corona del MC4, no anticipa la corrección de bending
mejor que el producto.

La regresión de 8.C no es un modelo predictivo: es la estimación de la asociación, con su intervalo.

## 9. Anclajes de validación y criterios de refutación

| # | Anclaje | Qué refutaría la conclusión |
|---|---|---|
| V1 | Control negativo: inclusiones del MC4 (origen proveedor) → Y | Asociación con IC que excluye 0 y magnitud comparable a la de la corona |
| V2 | Consistencia física: signo de corona → Y (más corona de entrada → bending más negativo; a confirmar con Lenard, 2014, cap. 12 y Ginzburg y Ballas, 2000) | Signo positivo con IC que excluye 0, o magnitud físicamente implausible |
| V3 | Robustez (multiverso; Steegen et al., 2016): R1–R7 abajo, mostradas juntas | La pendiente cambia de signo, o el orden programa > producto se invierte |
| V4 | Programa vs. periodo: sustituir programa del Skinpass por día y por semana | No refuta; si dan lo mismo, se escribe "programa/periodo" |

**Alternativas de robustez.** R1 umbral de corona imposible (L1 actual; p0.5–p99.5; > 600 µm). R2 definición de
producto (Norma; Norma | Grado; + Subnorma). R3 corte de censura (1-dic; 15-nov; sin corte). R4 rollos
divididos (ponderado; primera pieza; excluir divididos). R5 preset = 0 (incluir; excluir). R6 incluir los 733
rollos vistos en el Skinpass sin `SKP_PSQ` en la ruta. R7 agregar acuñamiento como covariable.
R8 excluir registros con preset mayor que el máximo bending real observado (689 kN; 2,141 registros), por si el
preset está saturado o en otra escala (S1). R9 sustituir programa del Skinpass por rodillo de trabajo (S4).

---

## 10. Confusión no medida

Planeza de entrada, estado de rodillos y decisiones del operador. Se reporta el valor de robustez de
Cinelli y Hazlett (2020) para la pendiente de corona, usando **producto** como confusor de referencia: "un
confusor no medido tendría que ser tan fuerte como el producto para anular la asociación".

---

## 11. Multiplicidad

Contrastes planeados: 1 pendiente principal + 1 secundaria; 1 control negativo; ~70 pendientes por producto (D);
9 alternativas de robustez × 2 resultados; 4 indicadores secundarios. Todos se reportan en
`contrastes_completos.csv`; en el cuerpo, solo los que responden la pregunta, con la cuenta total.

---

## 12. Traducción, experimento y datos faltantes (para Discusión y Conclusiones)

- Cada hallazgo en su peldaño, con las cuatro piezas (qué, qué implica, qué no implica, qué lo cerraría).
- **Experimento (EVOP; Box, 1957).** En una familia de productos, alternar por programa del Skinpass el preset
  estándar y un preset ajustado por la corona del MC4, dentro del rango ya usado. Unidad: programa (~62 rollos).
  Bloqueo: producto × dimensión. Resultado primario: |Y|; secundarios: defectos de inspector, elongación,
  retenidos. Volumen: se calculará con la variación de Y entre programas (sección 8.B). Reglas de paro.
- **Datos del Skinpass que faltan:** planeza de salida continua a lo ancho, campaña de rodillos por rollo,
  quién fija el preset y con qué lógica, segmento estable del rollo separado del enhebrado.

---

## 13. Exploración previa (25-nov-2026): lo que ya vimos

Para transparencia; **no** se citan como resultados.

- 94–97 % de los rollos con `SKP_PSQ` en la ruta aparece en el Skinpass 2025, en todas las formas finales.
- Fracción de la variación de Y: producto 9.7 %, dimensión 6.5 %, programa del Skinpass 61.4 % (azar 39.3 %).
  Agrupando por día en vez de programa: 56.8 % (azar 36.3 %).
- Corona relativa → Y dentro de producto × espesor × ancho × mes: −4.3 kN por punto (t agrupado = −4.1),
  correlación dentro de celda −0.02. El preset no responde a la corona (t = 0.3).
- Control negativo (inclusiones → Y): t = 0.0.
- El acuñamiento no se asocia de forma consistente con bending ni con defectos del Skinpass.

---

## 14. Supuestos, evidencia y sensibilidad

No hay más consultas posibles al Socio Formador. Cada supuesto se escribe en Metodología con su evidencia; las
limitaciones que dejan se escriben como hallazgos en la Discusión.

| # | Supuesto | Evidencia en los datos | Si es falso… | Sensibilidad |
|---|---|---|---|---|
| S1 | `Preset Bending` está en kN, como `Bending Prom. Real [kN]` | Misma escala: p1–p99 de −300 a 700 (preset) y de −355 a 449 (real); el real sigue al preset (pendiente 0.40, r = 0.51) | Y mezclaría unidades | R8; además se reporta el **bending real** (no depende de S1) como indicador secundario |
| S2 | Preset = 0 significa "sin preset", no "bending apagado" | Con preset 0 el bending real sigue activo (mediana −50 kN; real = 0 en solo 0.1 %) | Y en esos rollos sería otra cosa | R5 (incluir / excluir) |
| S3 | El preset se fija antes de procesar el rollo y no reacciona a ese rollo | Es único dentro de programa × producto × dimensión en 79 % de los grupos; no se asocia con la corona del rollo (t = 0.3) | El preset sería una respuesta, no una receta | Se describe; afecta la lectura, no el cálculo |
| S4 | El programa del Skinpass agrupa rollos con el mismo rodillo de trabajo | 73.5 % de los programas usa un solo rodillo; cada rodillo aparece en ~28 programas | El peso del programa no reflejaría estado de rodillos | R9 (rodillo en vez de programa) |
| S5 | El bending real responde a un lazo automático de planeza | El real se aparta del preset (mediana −45 kN); las señales de 2026 registran modo "AUTOMATICO BENDING" | El bending real sería una decisión manual | Se describe como supuesto del diagrama |
| S6 | `Corona Salida` está en µm | Mediana 60 µm (p5–p95: 42–220) con espesor mediano de 3.5 mm: corona relativa de 1.7 %, orden físicamente plausible | Cambia la escala de la pendiente (kN por punto), no su signo ni la descomposición | Se reporta la pendiente también por desviación estándar |

## 15. Entregables en el repositorio

- `src/skinpass.py`: lectura de los 12 archivos, agregación por rollo, unión con MC4.
- `notebooks/07_union_mc4_skinpass.ipynb`: unión, población y comprobación de exclusiones.
- `notebooks/08_soporte_y_resultado_principal.ipynb`: secciones 7, 8.B, 8.C, 8.D.
- `notebooks/09_validacion_y_robustez.ipynb`: secciones 9 y 10.
- `notebooks/10_modelo_predictivo.ipynb`: sección 8.E.
- `outputs/tablas/contrastes_completos.csv`.
- Un solo comando en el README regenera todas las figuras y tablas del artículo.

---

## Bitácora de cambios

| Fecha | Cambio | Motivo |
|---|---|---|
| 25-nov-2026 | Versión 1 | — |
| 25-nov-2026 | Versión 1.1: preguntas a Ternium → supuestos S1–S6 con evidencia; un solo modelo de ML contra línea base; R8 y R9 | Sin más consultas posibles al Socio Formador; la guía pide un análisis principal, no un catálogo de modelos |
