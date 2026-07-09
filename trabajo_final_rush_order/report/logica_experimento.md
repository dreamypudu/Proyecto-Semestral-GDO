# Lógica completa del experimento y revisión crítica de errores potenciales

Este documento explica, etapa por etapa, qué hace exactamente el experimento, dónde está implementado cada paso, y — en la segunda parte — una **auditoría honesta de los errores potenciales** detectados al revisar el propio trabajo, con evidencia numérica de su impacto.

---

## Parte I: La lógica del experimento

### Visión general

```
Tablas 5-6 del paper (datos)
        │
        ▼
[1] GA resuelve el scheduling inicial ──► S0, Cmax0 = 382
        │
        ▼
[2] En t* = Cmax0/2 = 191 llega el rush order J9
    Clasificar operaciones: terminadas (18) / en proceso (7) / pendientes (15)
    Congelar terminadas + en proceso
        │
        ▼
[3] Reprogramar {pendientes + rush} con 5 estrategias ──► cada una recibe nota Z
        │
        ▼
[4] Selector XGBoost: entrenado con 300 escenarios sintéticos,
    predice la nota Z de cada estrategia y elige la mínima
        │
        ▼
[5] Validación: ¿decide mejor que "elegir siempre la estable"?
```

### Etapa 0: Datos (sin inventar nada)

Las tablas de máquinas factibles y tiempos provienen de las Tablas 5 y 6 de Liu et al. (2022), transcritas al diccionario `DATA` en `src/scheduler_ga.py` (líneas 10–28) y exportadas a `data/datos_base_extraidos.csv` para auditoría. Interpretación posicional: si la Tabla 5 dice que J1-O1 puede ir en las máquinas `[3,8]` y la Tabla 6 dice tiempos `[38,49]`, entonces máquina 3 tarda 38 s y máquina 8 tarda 49 s.

El rush order canónico J9 es una reedición del modelo 8 (`RUSH_CANONICO`, `src/rescheduling.py`), igual que el evento dinámico del paper ("a newly issued eighth model").

### Etapa 1: Scheduling inicial con GA

- **Cromosoma MS+OS** (`src/scheduler_ga.py`, función `ga`): MS asigna una máquina factible a cada una de las 40 operaciones; OS es una lista de 40 números de trabajo donde la k-ésima aparición del trabajo j significa "su k-ésima operación".
- **Decodificador** (`decode` + `earliest_start`): recorre OS y programa cada operación en el **primer hueco factible** de su máquina (inserción en huecos), respetando precedencia dentro del trabajo.
- **Operadores**: torneo k=3, crossover POX en OS (conserva las posiciones de la mitad de los trabajos de un padre y rellena con el otro), crossover uniforme en MS, mutación (reasignar máquina / intercambiar posiciones), elitismo de 1.
- **Resultado**: Cmax₀ = 382 s con población 120 × 300 generaciones, semilla 0 (~4 s). El paper reporta RLEGA 397 / GA 411 / TS 435 como mejores valores.

*Verificación integrada*: ejecutar `python scheduler_ga.py` corre asserts de factibilidad (tiempos válidos según DATA, precedencia, no solapamiento por máquina).

### Etapa 2: Perturbación y congelamiento

En t\* = 382/2 = 191, `shop_state` (`src/rescheduling.py`) clasifica cada operación del programa inicial:

- **Terminada** (F): terminó antes o en t\* → `c0 ≤ 191`. Resultado: 18 operaciones. Se congelan.
- **En proceso** (I): empezó antes y termina después → `s0 < 191 < c0`. Resultado: 7. No se interrumpen (no-preemption); su máquina queda bloqueada hasta que terminen: `A_i = max(t*, c0 de la op en proceso)`.
- **Pendiente** (P): empieza en o después de t\* → `s0 ≥ 191`. Resultado: 15. Son las únicas reprogramables.

El subproblema de rescheduling es entonces Q = 15 pendientes + 5 del rush = 20 operaciones, con dos condiciones de frontera: ninguna puede empezar antes de t\*, y cada trabajo con operaciones congeladas hereda como instante de disponibilidad el término de su última operación congelada.

*Verificación integrada*: `python rescheduling.py` verifica con asserts que F∪I∪P particiona exactamente S0, que ninguna operación congelada cambia, que todo lo reprogramado empieza ≥ t\*, y que no hay solapes ni violaciones de precedencia en el schedule final de cada estrategia.

### Etapa 3: Las cinco estrategias

| Estrategia | Qué hace con las 15 pendientes | Qué hace con el rush | Objetivo del GA |
|---|---|---|---|
| `insert_end` | Nada (quedan igual que en S0) | Al final de cada máquina | — (determinista) |
| `right_shift` | Nada | En el primer hueco factible | — (determinista) |
| `partial_ga` | Reoptimiza | Reoptimiza | Cmax |
| `priority_ga` | Reoptimiza | Reoptimiza | Cmax + 0.5·Cr |
| `stability_ga` | Reoptimiza | Reoptimiza | Cmax + 0.5·Cr + 0.1·N |

El GA de rescheduling **reutiliza el mismo decodificador** de la etapa 1: solo cambia el estado inicial (máquinas bloqueadas hasta A_i, trabajos disponibles según congelamiento).

### Etapa 4: La nota Z y las métricas

Definidas en `src/metrics.py`:

- **Z = Cmax + 0.5·Cr + 0.1·N**, donde N = Ns + 10·Nm (Ns = suma de |desplazamiento de inicio| de las pendientes; Nm = número de cambios de máquina).
- Ejemplo con el escenario canónico: no tocar nada → Z = 518 + 0.5·518 + 0 = **777**; reoptimizar todo → Z = 512 + 0.5·512 + 0.1·747 = **842.7**. Ganar 6 s de makespan cuesta 65.7 puntos de Z en estabilidad.
- **Cota inferior verificable**: la cadena mínima del rush J9 suma 43+53+60+94+71 = 321 s y no puede empezar antes de t\*=191, luego Cr ≥ 512 y Cmax ≥ 512. `partial_ga` alcanza 512: es **óptimo demostrable** en makespan, independiente de cualquier GA.

### Etapa 5: Dataset del selector

`build_dataset` (`src/xgboost_selector.py`) genera 300 escenarios: rush aleatorio (3–5 operaciones, 1–3 máquinas por operación, tiempos U[30,105]), t\* aleatorio en [0.3, 0.7]·Cmax₀, sobre 5 programas iniciales distintos. En cada escenario ejecuta las 5 estrategias (los GA con presupuesto reducido: población 30, 40 generaciones) y registra las 5 notas Z. La ganadora (menor Z) es la "etiqueta". Distribución: `[34, 8, 18, 22, 218]` — stability gana el 72.7%.

### Etapa 6: El selector y su validación

- **Arquitectura**: regresor XGBoost que recibe (14 features del taller + one-hot de la estrategia) y predice Z. Para decidir, se predicen las 5 notas y se toma el argmin (`train`, `select` en `src/xgboost_selector.py`).
- **Validación** (`evaluate`): split estratificado 70/30. En el test (n=90) se compara el Z promedio real de: lo que eligió el selector (740.1), el baseline trivial "siempre stability" (740.1), el clasificador balanceado descartado (751.4) y el oráculo (737.9). Resultados en `results/evaluacion_selector.csv`.

### Etapa 7: Los 4 experimentos obligatorios

`run_experiments.py` ejecuta con semillas fijas: (1) scheduling inicial, (2) rush sin recuperación, (3) recuperación GA parcial, (4) recuperación con selector. Produce los Gantts, `tabla_resultados.csv` y la evaluación del selector. Todo es reproducible: `python run_experiments.py`.

---

## Parte II: Revisión crítica — errores potenciales detectados

Auditoría del propio trabajo, ordenada de mayor a menor impacto. Cada punto indica evidencia y si afecta las conclusiones. **Tras la auditoría, los errores corregibles fueron corregidos y el pipeline completo se re-ejecutó**; el estado de cada uno:

| Error | Estado | Corrección aplicada y verificación |
|---|---|---|
| E1 ruido de etiquetado | ✅ Corregido | Etiquetas = mediana de 3 corridas de GA por estrategia (`build_dataset`, `n_seeds=3`) |
| E2 sin warm start | ✅ Corregido | Warm start elitista: el GA nunca reporta peor que las heurísticas deterministas según su propio objetivo (`apply_strategy`); verificado: stability_ga ≡ insert_end en el escenario canónico |
| E3 fuga en el split | ✅ Corregido | Validación leave-one-group-out por schedule base: test nunca comparte programa inicial con train (`evaluate`) |
| E4 un split sin CI | ✅ Corregido | Predicciones out-of-fold para los 300 escenarios + diferencia selector-baseline reportada por fold (consistente: +0.0 a +1.3 en los 5 folds) |
| E5 features duplicadas | ✅ Corregido | `avance_tiempo_pct` = fracción del *tiempo de trabajo* completado; `pendientes_en_maquinas_rush` = pendientes que compiten con el rush. Verificado: las 14 features tienen importancia > 0 |
| E6 right_shift no desplazaba | ✅ Corregido | Implementación genuina (rush primero, pendientes desplazadas sin retroceder). Verificado: ahora gana 44/300 escenarios y en el caso canónico logra Cr = 512 óptimo con Cmax = 583 |
| E7 riesgo de typo en tablas | ✅ Verificado sin error | `src/verificar_datos.py` compara DATA contra el PDF: 81/81 pares idénticos |
| E8 lectura de 382 vs 397 | 📄 Documentado | Inherente a la comparación; declarado en informe §6.4 |
| E9 escalas mezcladas en Z | ✅ Mitigado | Se reporta además el *regret* por escenario (selector 1.18, baseline 0.66, clasificador 9.43) |
| E10 modelo desplegado ≠ validado | 📄 Documentado | Práctica estándar; con LOGO cada escenario tiene predicción out-of-fold |
| E11 pesos sin sensibilidad | ✅ Corregido | `results/sensibilidad_pesos.csv`: con β=0 la política estable gana solo 25/300 (dominarían los GA); con β≥0.05 domina. La dominancia de stability es consecuencia de β, no ley del taller |
| E12 métricas relativas a insert_end | 📄 Documentado | El caso ahora aparece en los datos: right_shift tiene %recuperación = −47.8% en el escenario canónico |

Los hallazgos originales se conservan a continuación como registro de la auditoría (los números citados corresponden a la versión previa a las correcciones).

### E1. Ruido de etiquetado: las etiquetas del dataset dependen de la suerte del GA ⚠️ impacto alto en los conteos, no en la conclusión

Las estrategias 3–5 se evalúan con **una sola corrida** de GA con presupuesto pequeño (población 30, 40 generaciones). Medición directa (mismo escenario canónico, 5 semillas):

```
partial_ga   Z = [826.5, 834.3, 858.6, 849.4, 861.0]  → rango 34.5
stability_ga Z = [786.9, 798.9, 810.7, 784.1, 796.7]  → rango 26.6
```

El rango de variación por semilla (26–35 puntos de Z) es **más de 10 veces** el margen promedio entre el baseline y el oráculo (2.2). Consecuencia: en escenarios donde dos estrategias están casi empatadas, *cuál queda etiquetada como ganadora es parcialmente aleatorio*. La distribución exacta `[34, 8, 18, 22, 218]` no debe leerse como verdad fina; sí es robusta la conclusión gruesa (la política estable domina, el margen recuperable es pequeño). Mitigación posible: etiquetar con la mediana de 3–5 semillas por estrategia (costo: ×3–5 en tiempo de generación).

### E2. `stability_ga` sin warm start: se le exige redescubrir la solución trivial ⚠️ sesga etiquetas a favor de `insert_end`

La población inicial del GA es aleatoria: no se siembra con la solución incumbente ("no tocar nada + rush al final"). Con el presupuesto de entrenamiento, `stability_ga` obtiene Z entre 784 y 811 en el escenario canónico — **peor que el 777 determinista de `insert_end`**, cuando con presupuesto completo sí lo encuentra (777). Es decir: parte de las 34 victorias de `insert_end` en el dataset son escenarios donde `stability_ga` "habría empatado o ganado" si hubiera partido de la solución incumbente. El fix estándar es incluir el incumbente en la población inicial (garantiza `stability_ga` ≤ `insert_end` siempre). No altera la conclusión final (la política elegida sería la misma), pero habría dado un dataset más limpio.

### E3. Posible fuga de información en el split de validación ⚠️ afecta al accuracy, poco a la comparación de Z

Los 300 escenarios se generan sobre solo **5 programas iniciales base**, y el split 70/30 es por escenario, no por programa base: escenarios de entrenamiento y de test comparten el mismo programa inicial (mismas cargas de máquina de fondo). Lo riguroso sería un *group split* (programas base completos fuera del entrenamiento). El accuracy de 0.74 puede estar algo inflado por esto. La comparación de Z entre políticas sobre el **mismo** test sigue siendo justa (todas las políticas ven los mismos escenarios), que es la métrica en que se basa la conclusión.

### E4. Un solo split, test de n=90, sin intervalos de confianza ⚠️ diferencias pequeñas no son significativas

Toda la validación usa un único split con semilla fija. Con n=90 y la variabilidad de Z entre escenarios, la diferencia selector-vs-baseline (740.09 vs 740.09, empate exacto porque el selector se desvía solo 2 veces) no es distinguible de cero — está bien reportado como empate. La distancia del clasificador balanceado (+11.3) sí es consistente y se replicó en ambas corridas independientes del pipeline. Mejora pendiente: validación cruzada o bootstrap para reportar intervalos.

### E5. Features redundantes por descuido: `ops_afectadas` duplica `n_pendientes` — impacto nulo, pero es un error

En `features()` la variable 14 (`ops_afectadas`) se definió como |P|, idéntica a la variable 4 (`n_pendientes`). Además `avance_pct` = |F|/40 es colineal con `n_terminadas` = |F|. Evidencia en `results/importancia_features.csv`: ambas redundantes tienen importancia 0.0000 (el árbol usa la copia y descarta el duplicado). No daña al modelo (los árboles toleran colinealidad), pero dos de las "14 features" no aportan información nueva: efectivamente son 12.

### E6. `right_shift` no desplaza nada: el nombre promete más de lo que hace

La implementación deja las pendientes fijas e inserta el rush en huecos (documentado con comentario en el código). Una right-shift genuina desplazaría operaciones pendientes hacia la derecha para abrirle espacio antes al rush. Consecuencia: la estrategia queda casi dominada (gana solo 8/300, únicamente cuando existen huecos aprovechables). El repertorio real de comportamientos distintos es más estrecho de lo que sugieren los 5 nombres.

### E7. Transcripción manual de las tablas del paper — riesgo residual de typo

Las Tablas 5–6 se transcribieron a mano desde el texto extraído del PDF. Se revisaron contra el texto extraído y la estructura es consistente (81 pares operación-máquina), pero no existe fuente machine-readable oficial para contrastar. Un typo en un tiempo cambiaría los valores absolutos (382, 512, 518...) aunque no la lógica. Mitigación: `data/datos_base_extraidos.csv` permite auditar contra el PDF en un minuto.

### E8. "382 < 397" no significa que nuestro GA sea mejor que RLEGA

El decodificador con inserción en huecos construye schedules de una clase más rica que la decodificación semi-activa habitual; además difieren presupuesto, semillas y número de corridas. La comparación con el paper es de *orden de magnitud y coherencia*, no un benchmark cabeza a cabeza. Así está declarado en el informe (§6.4), se reitera aquí porque es fácil sobre-leer ese número.

### E9. Promediar Z entre escenarios mezcla escalas

Z crece con Cmax₀ y t\*: un escenario con rush largo pesa más en el promedio que uno corto. Las comparaciones entre políticas son **pareadas** (todas se evalúan en los mismos escenarios), así que el ranking es válido; pero el valor absoluto "740.1" no tiene interpretación física directa. Una alternativa más limpia habría sido reportar *regret* medio (Z de la política − Z del oráculo, por escenario): 2.2 para el baseline y el selector, 13.5 para el clasificador balanceado.

### E10. El modelo desplegado no es el modelo validado

Como es práctica estándar, las cifras de validación provienen del modelo entrenado con el 70% de los datos, y el modelo final del experimento 4 se entrena con el 100%. La decisión que toma en el escenario canónico (stability_ga) coincide con la del modelo validado, pero en rigor la cifra de validación es del modelo hermano, no del desplegado.

### E11. Pesos de Z fijados por juicio, sin análisis de sensibilidad

α=0.5, β=0.1, γ₂=10 determinan qué estrategia "gana": con β=0 ganaría `partial_ga`/`priority_ga` en la mayoría de los escenarios y toda la historia cambiaría. Los valores están declarados como supuesto en el informe, pero no se exploró cómo se mueve la frontera de decisión al variarlos. Es la limitación más importante de cara a defender el trabajo: conviene poder responder "¿y si β fuera 0?" (respuesta: el selector se reentrenaría con las nuevas etiquetas; la arquitectura no cambia).

### E12. Definiciones dependientes del baseline elegido

"Daño" y "% de recuperación" se definen respecto a `insert_end` como programa perturbado de referencia. Si otra estrategia fuera peor que `insert_end` en algún escenario, el % de recuperación podría ser negativo o mayor a 100. En los datos observados no ocurre, pero la métrica hereda esa fragilidad de definición.

### Resultados después de las correcciones

La re-ejecución completa con todos los fixes cambió los números (todos regenerables con `python run_experiments.py`):

- **Distribución de etiquetas** (mediana de 3 semillas + warm start + right_shift genuino): `[33, 44, 9, 10, 204]` — right_shift pasó de 8 a 44 victorias (ahora es una estrategia real) y stability bajó de 73% a 68%.
- **Validación LOGO sin fuga** (out-of-fold, 300 escenarios): regret medio vs oráculo — baseline 0.66, selector 1.18, clasificador balanceado 9.43. Bajo validación estricta el selector queda **levemente por debajo** del baseline trivial (+0.5 Z, consistente en los 5 folds): el "empate" de la validación anterior estaba parcialmente inflado por la fuga (E3). El margen total baseline–oráculo se redujo de 2.2 a 0.66 al limpiar el ruido de etiquetado — confirmando que gran parte del "margen" anterior era ruido (E1).
- **Sensibilidad de pesos** (E11): con β=0 ganarían los GA (97+75+79 vs 25 de stability); con β≥0.05 domina stability. Esto reencuadra el valor del selector: no es ganar décimas de Z con los pesos vigentes (imposible: 0.66 de margen), sino adaptarse por re-entrenamiento si la política de la empresa (β) cambia.
- **Escenario canónico**: sin cambios en lo esencial (382 → 518 → 512 óptimo; XGBoost sigue eligiendo stability_ga). Novedad: right_shift ahora exhibe el trade-off opuesto — Cr = 512 (óptimo para el rush) con Cmax = 583 y recuperación **negativa** (−47.8%).

### Qué conclusiones sobreviven

Robustas (independientes de los errores encontrados y de sus correcciones):
- **Cmax recuperado = 512 es óptimo**: cota inferior aritmética, independiente de todo GA.
- **El clasificador decide mucho peor que el baseline trivial** (regret 9.43 vs 0.66): la formulación correcta del selector es predicción de costo, no clasificación.
- **El margen recuperable sobre la política estable es mínimo** con los pesos vigentes — y las correcciones lo *redujeron* (2.2 → 0.66), reforzando la conclusión.

Corregidas por la auditoría (los números finales del informe ya las reflejan):
- La distribución de victorias y el rol de right_shift.
- La validación (ahora sin fuga, con regret y con evidencia por fold).
- La justificación del selector (adaptabilidad ante cambio de pesos, cuantificada).
