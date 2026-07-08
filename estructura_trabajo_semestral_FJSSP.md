# Estructura de Trabajo Semestral
## Digital Twin FJSSP: Iterated Greedy + XGBoost para recuperación ante Rush Order

Este documento es la hoja de ruta completa del proyecto. Está pensado para ser usado como
brief de desarrollo con asistentes de codificación (Codex, Claude Fable, etc.): cada fase
incluye objetivo, especificación técnica, criterios de aceptación y qué pedirle exactamente
a la IA. No contiene código — solo especificaciones para que la IA lo genere correctamente
y de forma verificable.

---

## 0. Resumen del enfoque

| Etapa del enunciado | Método elegido | Rol |
|---|---|---|
| 1. Scheduling inicial | Iterated Greedy (IG) | Genera el Gantt base y su Cmax |
| 2. Comparación | vs. GA, TS y reglas de despacho del paper | Validación de calidad/tiempo |
| 3. Perturbación | Rush order en t = Cmax/2 | Genera el daño a cuantificar |
| 4. Recuperación inteligente | XGBoost (clasificador de estrategia) + IG como motor de reoptimización | Detecta y decide cómo reparar |
| 5. Evaluación | Cmax, nervousness, tiempo de recuperación | Cierre cuantitativo |

Idea clave que debe quedar clara en todo el proyecto: **XGBoost no genera el schedule**,
solo elige *cuál* de un conjunto acotado de estrategias de reparación aplicar. Quien
efectivamente reoptimiza es Iterated Greedy (reutilizado de la Etapa 1). Esto da coherencia
metodológica de punta a punta y es más fácil de defender en la presentación.

---

## 1. Estructura de carpetas del proyecto

```
proyecto-fjssp-rush-order/
├── data/
│   ├── raw/                     # instancias generadas (paper-like: 20/100 jobs)
│   ├── perturbation_scenarios/  # escenarios sintéticos de rush order para entrenar XGBoost
│   └── processed/               # datasets tabulares listos para XGBoost
├── src/
│   ├── instance_generation/     # generador de instancias FJSSP tipo paper
│   ├── scheduling/
│   │   ├── iterated_greedy/     # IG: destrucción, reconstrucción, aceptación
│   │   ├── baselines/           # GA propio (opcional), reglas de despacho (SPT/LPT/SSO/LSO)
│   │   └── evaluation/          # cálculo de Cmax, validación de factibilidad
│   ├── digital_twin/
│   │   ├── state_tracker.py     # estado del sistema en tiempo t (qué está en curso, holguras)
│   │   └── event_injector.py    # inyecta el rush order en t = Cmax/2
│   ├── recovery/
│   │   ├── strategies/          # las 3 estrategias candidatas (right-shift, IG parcial, IG total)
│   │   ├── feature_builder.py   # construye el vector de estado/features
│   │   └── xgb_selector/        # entrenamiento e inferencia del clasificador
│   └── metrics/                 # Cmax, nervousness, tiempo de recuperación, %recuperación
├── experiments/
│   ├── exp1_validacion_IG/      # réplica de instancias tipo Tabla 4 del paper
│   ├── exp2_generacion_dataset/ # corridas masivas para entrenar XGBoost
│   ├── exp3_evaluacion_final/   # comparación end-to-end
│   └── results/                 # csvs, gráficos, tablas para el informe
├── notebooks/                   # exploración y gráficos finales (Gantt, boxplots, feature importance)
├── report/                      # informe final (LaTeX o Word)
└── README.md
```

---

## 2. Fases de desarrollo (con checkpoints)

### Fase 0 — Generación de instancias
**Objetivo:** poder generar instancias FJSSP reproducibles y parametrizables, siguiendo
la misma lógica del paper (Sección 5.1), para que la comparación de la Etapa 2 sea válida.

**Especificación:**
- Parámetros configurables: número de jobs (20 o 100), número de máquinas (10 o 20),
  número de operaciones por job ~ U(1,10), tiempo de procesamiento ~ U(1,100),
  flexibilidad (20%, 50%, 100% = cuántas máquinas alternativas por operación),
  utilización de máquina objetivo (75% o 90%).
- Debe guardar cada instancia en un formato tabular reproducible (job, operación,
  lista de máquinas candidatas, lista de tiempos correspondientes) y con una semilla
  aleatoria fija para poder reproducir resultados.
- Nombrar cada instancia siguiendo la convención del paper (ej. `S1_20_10_75_20`) para
  facilitar el cruce con la Tabla 4 al comparar.

**Criterio de aceptación:** dado el mismo seed, la instancia generada es idéntica en
corridas repetidas. Validar manualmente 1-2 instancias pequeñas a mano.

**Qué pedirle a la IA:** "Genera un módulo de generación de instancias FJSSP con estos
parámetros exactos [pegar lista], que devuelva una estructura de datos [definir: dict/
dataframe] y permita fijar semilla. No optimices nada todavía, solo generación de datos."

---

### Fase 1 — Iterated Greedy para el scheduling inicial
**Objetivo:** obtener el Gantt inicial y el Cmax base (equivalente a la Figura 6 del paper).

**Especificación del algoritmo:**
- **Representación de solución:** reutilizar el encoding MS+OS del paper (Figura 4) o una
  representación equivalente que permita reconstrucción parcial fácilmente.
- **Construcción inicial:** heurística greedy simple (ej. NEH adaptado a FJSSP, o
  inserción por menor incremento de Cmax) para tener un punto de partida rápido.
- **Fase de destrucción:** remover aleatoriamente un subconjunto de operaciones
  (parametrizar tamaño de destrucción, ej. 20-30% de las operaciones).
- **Fase de reconstrucción:** reinsertar greedily las operaciones removidas, evaluando
  en cada inserción el menor incremento de Cmax (o de una función de costo compuesta
  si se desea incluir holgura).
- **Criterio de aceptación de la nueva solución:** aceptar si mejora, o con un criterio
  tipo "aceptación si no empeora más de X%" para evitar quedar atrapado en óptimos locales
  (opcional, pero recomendable justificarlo).
- **Criterio de paro:** número fijo de iteraciones sin mejora, o tiempo máximo de cómputo
  (importante fijar esto igual para todas las instancias, para que el análisis de
  desempeño computacional de la Etapa 2 sea justo).

**Criterio de aceptación:** el Gantt resultante debe ser 100% factible (validar que no
hay solapamientos de máquina ni violación de precedencia de operaciones) antes de seguir.
Construir un validador de factibilidad como paso obligatorio, no opcional.

**Qué pedirle a la IA:** especificar exactamente la representación de solución elegida,
la función de costo, los parámetros de destrucción/reconstrucción y el criterio de paro,
y pedir explícitamente un validador de factibilidad separado del optimizador (para poder
testear ambos de forma independiente).

---

### Fase 2 — Validación y comparación con el paper
**Objetivo:** cumplir la Etapa 2 del enunciado.

**Qué correr:**
- Las mismas 9 instancias tipo del paper (S1 a S9, Tabla 4) con tu IG, 10 corridas cada una
  (igual que el paper), registrando avg/max/min de Cmax y tiempo de cómputo por corrida.
- Si el tiempo lo permite, implementar también el GA "ordinario" del paper como referencia
  adicional (no obligatorio, pero fortalece mucho la discusión).

**Qué reportar:**
- Tabla comparativa: tus resultados (IG) vs. columnas RLEGA / GA / TS del paper.
- Diferencias explicadas por: falta de acceso a las instancias exactas del paper (generas
  las tuyas con la misma distribución, pero no son las mismas), diferencias de hardware,
  diferencias de criterio de paro, ausencia de ajuste dinámico de parámetros (el paper usa
  RL para eso, tu IG no lo necesita porque tiene menos hiperparámetros).
- Gráfico tipo boxplot (como la Figura 5 del paper) para tus resultados.

**Criterio de aceptación:** que tus resultados sean del mismo orden de magnitud que los
del paper (no tienen que ser mejores ni iguales, pero sí "razonables" — si difieren en
órdenes de magnitud, revisar el validador de factibilidad o la función de costo).

---

### Fase 3 — Simulación del rush order
**Objetivo:** cumplir la Etapa 3 del enunciado.

**Especificación:**
- Sobre el Gantt inicial (Fase 1), calcular Cmax y fijar t* = Cmax/2.
- Congelar el estado del sistema en t*: qué operaciones ya terminaron, cuáles están en
  curso (no pueden interrumpirse), cuáles no han comenzado.
- Generar una nueva orden (rush order) con la misma lógica de generación de instancias
  (Fase 0), pero con un parámetro adicional de "urgencia" (ej. fecha de entrega objetivo
  más ajustada que el resto, o simplemente su inserción se marca como prioritaria).
- Insertar la orden con una política "naive" (ej. right-shift puro, sin reoptimización)
  para tener una medición del daño **antes** de aplicar cualquier inteligencia.

**Métricas de daño a calcular en esta fase (sin recuperación todavía):**
- ΔCmax = Cmax_perturbado_naive − Cmax_inicial.
- Nervousness: número de operaciones cuyo (máquina, tiempo de inicio) cambió respecto
  al Gantt original, y/o suma total de los desplazamientos (right-shifts) en segundos.

**Criterio de aceptación:** el daño debe ser mayor a cero y factible (el Gantt perturbado
naive también debe pasar el validador de factibilidad).

---

### Fase 4 — Generación del dataset de entrenamiento para XGBoost
**Objetivo:** tener suficientes ejemplos etiquetados de "qué estrategia de recuperación
fue mejor" para distintos escenarios de rush order, antes de entrenar el clasificador.

**Especificación:**
- Definir las 3 estrategias candidatas de recuperación (ver Fase 5 del recovery, no
  confundir con esta fase de generación de datos):
  1. Right-shift puro.
  2. IG parcial (destrucción/reconstrucción solo sobre operaciones no iniciadas de los
     jobs directamente afectados por la inserción).
  3. IG total (destrucción/reconstrucción sobre todas las operaciones no iniciadas).
- Para generar el dataset: variar sistemáticamente el momento de la perturbación
  (no solo Cmax/2 — usar varios t para tener diversidad), la "urgencia" de la nueva
  orden, la instancia base (usar varias de las 9 generadas en Fase 0), y correr las
  3 estrategias sobre cada escenario.
- Para cada escenario, registrar: (a) el vector de features del estado en t
  (ver Fase 6), y (b) cuál estrategia dio mejor resultado combinando Cmax y nervousness
  (definir una regla de desempate clara, ej. minimizar Cmax primero, nervousness como
  criterio secundario).
- Apuntar a un mínimo razonable de escenarios (ej. 200-500) para que XGBoost tenga
  suficientes ejemplos por clase — vale la pena verificar que las 3 clases no queden
  muy desbalanceadas, y si quedan, documentarlo y usar balanceo de clases o pesos.

**Criterio de aceptación:** dataset final en formato tabular (una fila por escenario,
columnas = features + etiqueta de estrategia ganadora), sin valores faltantes, con al
menos ~20-30 ejemplos por clase como mínimo aceptable para un curso.

---

### Fase 5 — Entrenamiento del clasificador XGBoost
**Objetivo:** cumplir la Etapa 4 del enunciado (detección + estrategia de rescheduling).

**Especificación de features (estado del sistema en el momento de la perturbación):**
- Holgura promedio y mínima de las máquinas candidatas para la nueva orden.
- Tiempo total de procesamiento de la nueva orden vs. holgura promedio disponible.
- Número de operaciones aún no iniciadas en el sistema (proxy de "cuánto queda por
  reprogramar").
- Congestión relativa de las máquinas requeridas por la nueva orden (ej. carga actual /
  capacidad).
- Fracción del makespan ya transcurrida (t*/Cmax) — para capturar si la perturbación
  llega "temprano" o "tarde".
- (Opcional) Flexibilidad promedio de las operaciones restantes (cuántas máquinas
  alternativas tienen en promedio).

**Especificación del modelo:**
- Clasificación multiclase (3 clases = 3 estrategias).
- Train/test split o validación cruzada (dado que el dataset es de generación propia y
  probablemente no muy grande, k-fold es preferible a un solo split).
- Reportar: accuracy, matriz de confusión, y **feature importance** (esto es clave para
  la discusión — conecta con "qué variables determinan la mejor estrategia").
- Justificar la elección de hiperparámetros principales (profundidad de árbol, número
  de estimadores, learning rate) con una búsqueda simple (grid pequeño o valores por
  defecto documentados, no hace falta un tuning exhaustivo para este curso).

**Criterio de aceptación:** el modelo debe superar claramente a una regla trivial
(ej. "siempre elegir IG total") en el set de validación — si no lo hace, revisar
balance de clases o calidad de features antes de seguir.

**Qué pedirle a la IA:** especificar la lista exacta de features, el número de clases,
el tipo de validación (k-fold), y pedir explícitamente el reporte de feature importance
y matriz de confusión como parte del entregable del entrenamiento (no solo el accuracy).

---

### Fase 6 — Evaluación end-to-end (Etapa 5 del enunciado)
**Objetivo:** medir el desempeño real del sistema completo: perturbación → detección →
recuperación, sobre escenarios de prueba **no vistos** durante el entrenamiento de XGBoost.

**Qué correr:**
- Sobre un conjunto de escenarios de prueba (separados del set de entrenamiento de
  Fase 4), aplicar el pipeline completo: inyectar rush order → construir features →
  XGBoost predice estrategia → aplicar la estrategia predicha con el motor IG →
  medir resultado.

**Métricas finales a reportar (comparando: inicial vs. perturbado sin recuperar vs.
recuperado con el modelo):**
- Cmax en cada etapa.
- % de recuperación = (Cmax_perturbado − Cmax_recuperado) / (Cmax_perturbado − Cmax_inicial).
- Nervousness en cada etapa.
- Tiempo de cómputo de la recuperación (importante para el argumento de "tiempo real"
  del paper).
- Comparar también contra **aplicar siempre la estrategia más costosa (IG total)** como
  referencia — esto muestra si el clasificador realmente aporta valor sobre "reoptimizar
  todo siempre", que sería la alternativa "segura pero cara".

**Criterio de aceptación:** el % de recuperación debe ser sustancialmente mayor a 0%,
y idealmente el tiempo de cómputo de la estrategia elegida por XGBoost debe ser, en
promedio, menor al de aplicar siempre IG total (ese es el argumento de valor agregado
del clasificador).

---

## 3. Plan de experimentos sugerido (resumen)

| Experimento | Qué varía | Repeticiones | Output |
|---|---|---|---|
| Exp. 1 | 9 instancias tipo paper | 10 corridas c/u | Tabla comparativa Etapa 2 |
| Exp. 2 | momento perturbación, urgencia, instancia base | 200-500 escenarios | Dataset de entrenamiento XGBoost |
| Exp. 3 | escenarios de prueba no vistos | 30-50 escenarios | Evaluación final Etapa 5 |

Fijar semillas aleatorias en todos los experimentos y documentarlas, para que todo sea
reproducible por quien revise el trabajo.

---

## 4. Estructura sugerida del informe final

1. **Introducción** — contexto del problema, resumen del paper, objetivo del trabajo.
2. **Metodología**
   - 2.1 Descripción formal del FJSSP (puede reutilizar la formulación del paper, citada).
   - 2.2 Iterated Greedy: justificación de la elección, diseño de destrucción/reconstrucción.
   - 2.3 Simulación de la perturbación (rush order): supuestos y parámetros.
   - 2.4 Modelo de recuperación: estrategias candidatas, features, XGBoost.
3. **Diseño experimental** — instancias, parámetros, criterios de paro, métricas.
4. **Resultados**
   - 4.1 Validación de IG vs. paper (Etapa 2).
   - 4.2 Cuantificación del daño de la perturbación (Etapa 3).
   - 4.3 Desempeño del clasificador (accuracy, feature importance).
   - 4.4 Evaluación end-to-end (Etapa 5).
5. **Discusión crítica** — limitaciones (instancias no idénticas al paper, tamaño del
   dataset de entrenamiento, generalización del clasificador a perturbaciones más severas),
   comparación de paradigmas (IG vs. GA+RL del paper).
6. **Conclusiones y trabajo futuro** (ej. extender a falla de máquina, usar RL en vez de
   XGBoost, aumentar el número de estrategias candidatas).
7. **Referencias** y **Anexos** (parámetros completos, código relevante si se pide).

---

## 5. Estructura sugerida de la presentación (20 min)

1. Motivación y problema (2 min).
2. Resumen del paper y su enfoque (2 min).
3. Metodología propia: IG + XGBoost, con diagrama del pipeline completo (5 min).
4. Resultados clave: tabla comparativa Etapa 2, Gantt antes/después de la perturbación,
   feature importance, métricas finales de recuperación (8 min).
5. Discusión crítica y limitaciones (2 min).
6. Conclusiones (1 min).

---

## 6. Checklist final antes de entregar

- [ ] Validador de factibilidad corre sobre TODAS las soluciones generadas (inicial,
      perturbada naive, y recuperada) — sin excepciones.
- [ ] Semillas fijadas y documentadas en todos los experimentos.
- [ ] Tabla comparativa Etapa 2 completa (avg/max/min, tiempo de cómputo).
- [ ] Dataset de entrenamiento de XGBoost con clases razonablemente balanceadas
      (o balanceo documentado si no lo están).
- [ ] Evaluación end-to-end usa escenarios NO vistos en el entrenamiento (evitar
      data leakage entre Fase 4 y Fase 6).
- [ ] Métricas de nervousness y % de recuperación calculadas y graficadas.
- [ ] Comparación contra la alternativa "siempre IG total" para justificar el valor
      del clasificador.
- [ ] Informe explica explícitamente el rol de XGBoost como *selector de estrategia*,
      no como generador del schedule.
- [ ] Limitaciones del estudio mencionadas explícitamente (instancias propias vs. del
      paper, tamaño de la muestra de entrenamiento, alcance del tipo de perturbación).

---

## 7. Notas para instruir a los asistentes de codificación (Codex / Claude Fable)

Al pedirle a la IA que implemente cada módulo, conviene dar en cada prompt:
1. **Qué fase es** (de las 6 anteriores) y su objetivo puntual.
2. **Inputs/outputs exactos** esperados (estructura de datos, no solo "genera una función").
3. **Restricciones duras** que no se pueden violar (factibilidad del schedule, operaciones
   en curso no se interrumpen, etc.).
4. **Criterio de aceptación** de esa fase (de la tabla de este documento), para que la IA
   pueda auto-verificar o generar tests simples.
5. Pedir siempre, después de generar el módulo, un **caso de prueba pequeño y verificable
   a mano** (ej. una instancia de 2 jobs) antes de correr las instancias grandes — esto
   evita construir todo el pipeline sobre un bug de factibilidad no detectado.

Desarrollar en este orden estricto (Fase 0 → 1 → 2 → 3 → 4 → 5 → 6) es importante:
cada fase depende de que la anterior esté validada, especialmente el validador de
factibilidad, que debe estar listo y probado antes de escribir el optimizador.
