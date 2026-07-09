# Explicación profunda de la presentación — *Estudio de caso con Rush Order*

Documento complementario a `main (1).pdf` (36 diapositivas). Explica cada
diapositiva en profundidad, con la fundamentación de **cada variable, constante,
letra y número** del modelo, y su correspondencia con el código en
`trabajo_final_rush_order/src/`.

Convención de notación (texto plano, sin LaTeX):
- Subíndices se escriben pegados: `s_jh`, `c_jh`, `x_ijh`.
- `Cmax` = makespan; `Cmax0` = makespan del programa inicial; `CmaxR` = makespan tras el rush.
- Conjuntos: F (finalizadas), I (en proceso), P (pendientes), R (rush), Q = P ∪ R.

---

## Diapositiva 1 — Portada

**Contenido:** Título "Trabajo semestral — Estudio de caso con Rush Order",
autores (Valentín Álvarez, Gustavo Lara, Vicente Salgado, Matías Valdebenito,
Carlos Yañez), Universidad de Concepción, 09 de julio de 2026.

**Qué comunicar al presentar:** El trabajo aborda un problema clásico de Gestión
de Operaciones — la programación de producción (*scheduling*) — pero en su
versión **dinámica**: qué hacer cuando, a mitad de la ejecución de un plan
óptimo, entra un pedido urgente que obliga a reprogramar. El "gancho" es que se
resuelve con la lógica de un **Digital Twin** (gemelo digital) que detecta la
perturbación y decide la respuesta.

---

## Diapositiva 2 — Tabla de contenidos

**Estructura:** (1) Introducción, (2) Metodología, (3) Resultados, (4) Discusión,
(5) Bibliografía. Es la estructura estándar de un paper científico (IMRyD:
Introducción–Métodos–Resultados–Discusión), lo que da rigor académico a la
exposición.

---

## Diapositiva 3 — Introducción: Digital Twin

**Definición:** Un *digital twin* (gemelo digital) es una representación digital
**dinámica y sincronizada** de un activo físico, proceso o sistema, que usa datos
en tiempo (casi) real para **simular, predecir y optimizar**.

**Ciclo del DT:** captura de datos → modelado → simulación/predicción →
retroalimentación.

**Fundamentación:** Las dos palabras clave son *dinámica* y *sincronizada*. A
diferencia de un modelo estático (una foto), el gemelo se actualiza con el estado
real. Esto es exactamente lo que necesita el problema: un plan de producción que
**reacciona** a eventos. En este trabajo el "gemelo" no es un modelo 3D físico
sino un **DT lógico**: una capa de software que vigila el estado del sistema de
pedidos y dispara la reprogramación (ver diapositiva 17).

---

## Diapositiva 4 — Arquitectura del Gemelo Digital Operacional

**Figura:** Framework de cuatro capas de Liu et al. (2022), el paper base.

1. **Capa Física:** componentes reales del piso de planta — brazos robóticos,
   AGV (vehículos guiados automáticamente), estaciones de trabajo.
2. **Enlace Bidireccional:** flujo continuo de datos heterogéneos en tiempo real
   entre lo físico y lo virtual (el "sincronismo" de la definición del DT).
3. **Capa de Simulación:** modelo virtual 3D que refleja el estado de producción.
4. **Capa de Servicio:** el sistema inteligente que **detecta perturbaciones** y
   ejecuta el *rescheduling*. **Aquí vive el aporte de este trabajo.**

**Fundamentación:** Se adopta el marco de Liu et al. porque es el paper de donde
provienen los datos de la instancia (Tablas 5 y 6). El trabajo se ubica
explícitamente en la **Capa de Servicio**: no se re-implementa la planta física
ni la visualización 3D, sino la lógica de decisión (detección + rescheduling +
selector ML).

---

## Diapositiva 5 — Introducción: Rush Order

**Definición:** Un *rush order* (pedido urgente) requiere procesamiento acelerado
y entrega prioritaria para cumplir un plazo urgente (Nventory, 2026).

**Tres hechos clave (Trzyna et al., 2012):**
- Se **priorizan en la secuenciación**: se saltan colas y adelantan a pedidos
  estándar, reduciendo su tiempo de espera.
- Suelen ser **más pequeños** que los pedidos estándar (no siempre).
- Suelen tener **mayor margen de beneficio** → justifica económicamente
  perturbar el plan por atenderlos.

**Fundamentación:** Esta diapositiva motiva **por qué** vale la pena reprogramar.
Si el rush no tuviera prioridad ni margen, bastaría ponerlo al final de la cola
(la estrategia `insert_end`). El mayor margen y la urgencia justifican asumir el
costo de reordenar. En el modelo, esa urgencia se traduce en el término `α·Cr`
de la función objetivo (penaliza que el rush termine tarde).

---

## Diapositiva 6 — Introducción: Problema

**Planteamiento en tres niveles:**
- **Enfoque teórico (estático):** minimizar `Cmax` asumiendo que **no** habrá
  imprevistos. Es el FJSSP clásico.
- **Realidad industrial (dinámica):** un plan inicial es **vulnerable**. Llega un
  rush en `t = Cmax/2` y la planificación queda obsoleta.
- **Desafío central:** un modelo inteligente que **detecte** la perturbación y
  ejecute *rescheduling* en tiempo real, equilibrando **eficiencia** (makespan
  bajo) y **estabilidad** (no desarmar el plan).

**Objetivo:** diseñar e implementar una metodología que responda de forma
eficiente a la perturbación, evaluada con **indicadores cuantitativos**.

**Fundamentación del número `Cmax/2`:** el instante de llegada del rush se fija a
la **mitad** del makespan inicial. Es una elección metodológica deliberada: en
`t = Cmax/2` el taller está en régimen mixto — hay operaciones ya terminadas,
otras en proceso y otras pendientes. Esto **maximiza la riqueza del estado** (los
tres conjuntos F/I/P son no vacíos), que es justo el caso interesante para probar
el rescheduling. Si el rush llegara muy temprano casi todo sería reprogramable
(equivale a re-planificar desde cero); muy tarde, casi nada.

---

## Diapositiva 7 — Introducción: Descripción del problema

**Instancia concreta:**
- **Trabajos:** 8 modelos iniciales (J1–J8). Cada uno con **5 operaciones** en
  secuencia fija: chasis → marco → puerta izquierda → puerta derecha → cubierta
  frontal. → 8 × 5 = **40 operaciones**.
- **Máquinas:** 8 brazos robóticos (M1–M8). Cada operación tiene un **subconjunto**
  de máquinas factibles con tiempos distintos (de ahí "flexible").
- **Restricciones:** precedencia tecnológica dentro de cada trabajo; una máquina
  procesa una operación a la vez; **sin interrupción** (non-preemption: una vez
  iniciada, una operación no se pausa).
- **Métrica principal:** makespan `Cmax`.
- **Perturbación:** en `t* = Cmax0/2` llega el rush J9.

**Correspondencia con el código:** los 40 pares `(job, op)` y sus alternativas
`(máquina, tiempo)` son el diccionario `DATA` en
[scheduler_ga.py:10-27](trabajo_final_rush_order/src/scheduler_ga.py#L10-L27).
`MACHINES = list(range(1, 9))` = M1–M8. El rush J9 se define en
[rescheduling.py:15-19](trabajo_final_rush_order/src/rescheduling.py#L15-L19)
(`RUSH_JOB = 9`, y `RUSH_CANONICO` reedita el trabajo 8 como pedido urgente).

**Fundamentación de los números 8, 8 y 5:** provienen directamente de la
instancia del paper base (Liu et al. 2022, Tablas 5 y 6). No son elegidos por los
autores; se transcriben para poder **comparar** el resultado contra el valor que
reporta ese paper (RLEGA = 397 s, ver diapositiva 31).

---

## Diapositiva 8 — Parámetros (nomenclatura del modelo)

Tabla de símbolos. **Fundamentación uno por uno:**

| Símbolo | Significado | Por qué existe |
|---------|-------------|----------------|
| `n` | nº total de trabajos | dimensiona el problema (aquí n = 8, luego 9 con el rush) |
| `m` | nº total de máquinas | recurso compartido (aquí m = 8) |
| `i, e` | índices de **máquina** | dos índices porque las restricciones comparan **pares** de operaciones que pueden caer en la misma máquina |
| `j, k` | índices de **trabajo** | ídem: se comparan dos trabajos distintos j y k |
| `h_j` | nº de operaciones del trabajo j | permite trabajos de distinto largo (aquí todos = 5) |
| `h, l` | índices de **operación** | dos índices para comparar operación h (de j) con operación l (de k) |
| `m_jh` | nº de máquinas opcionales para la operación O_jh | es la "flexibilidad" del FJSSP; si m_jh = 1 para todo, sería un job-shop clásico |
| `O_jh` | operación h del trabajo j | la unidad atómica que se programa |
| `p_ijh` | tiempo de O_jh en la máquina i | el dato de proceso; depende de la máquina (por eso lleva i) |
| `s_jh` | tiempo de **inicio** de O_jh | variable de decisión (cuándo empieza) |
| `c_jh` | tiempo de **término** de O_jh | variable derivada: c_jh = s_jh + p_ijh |
| `L` | número positivo suficientemente grande | constante "Big-M" para linealizar disyunciones (ver ec. 5, 6) |
| `x_ijh` | binaria: 1 si la máquina i se usa para O_jh | variable de **asignación** (el "MS" del cromosoma) |
| `y_ijhkl` | binaria: 1 si O_jh precede a O_kl (en la misma máquina i) | variable de **secuenciación** (el "OS" del cromosoma) |

**Punto clave:** las dos familias de binarias `x` (asignación máquina↔operación) y
`y` (orden entre operaciones) son exactamente las dos partes del cromosoma MS+OS
del GA (diapositiva 15). El modelo matemático exacto usa binarias; el GA las
representa como un diccionario de máquinas (x) y una permutación (y).

**Sobre `L` (Big-M):** es un truco estándar de programación entera. Cuando dos
operaciones comparten máquina, una debe ir antes que la otra (una disyunción
"o... o..."). Para expresar eso con desigualdades lineales se usa una constante `L`
grande que "apaga" la restricción cuando la binaria correspondiente es 0. `L` debe
ser mayor que cualquier tiempo posible del schedule (p. ej. la suma de todos los
`p_ijh`); no tiene significado físico, es un artificio algebraico.

---

## Diapositiva 9 — Modelo matemático base (ecuaciones 1–6)

**(1) Función objetivo:** `f = mín ( máx_{j∈[1,n]} (C_j) )`
Minimizar el máximo tiempo de finalización entre todos los trabajos = minimizar
el **makespan**. `C_j` es cuándo termina el trabajo j (su última operación).

**(2) Duración de operación:** `s_jh + x_ijh·p_ijh ≤ c_jh`
El término no puede ser antes que el inicio más el tiempo de proceso **en la
máquina elegida** (el factor `x_ijh` selecciona el tiempo de la máquina i sólo si
esa máquina fue asignada). En la práctica se cumple con igualdad: c = s + p.

**(3) Precedencia intra-trabajo:** `c_jh ≤ s_j(h+1)`
La operación h+1 de un trabajo no empieza antes de que termine la h. Es la
"secuencia fija" (chasis antes que marco, etc.).

**(4) Definición de makespan:** `c_jh_j ≤ Cmax`
El término de la **última** operación (h_j) de cada trabajo acota `Cmax`.
Combinada con (1), fuerza `Cmax = máx c_jh_j`.

**(5) y (6) No solapamiento en máquina (Big-M):**
`s_jh + p_ijh ≤ s_kl + L(1 − y_ijhkl)` y su simétrica.
Si `y_ijhkl = 1` (O_jh precede a O_kl en la máquina i), el término `L(1−y)=0` y la
restricción obliga `s_jh + p_ijh ≤ s_kl` (O_kl empieza después de que O_jh
termina). Si `y = 0`, `L(1−y)=L` grande relaja la restricción (no aplica). Así se
codifica "en una máquina, una operación a la vez, en algún orden".

**Fundamentación de los rangos de índices** (la columna derecha de la diapositiva):
precisan sobre qué conjuntos se replica cada restricción. Ej. (2) vale para toda
máquina i∈[1,m], trabajo j∈[1,n], operación h∈[1,h_j]. El rango `j∈[0,n]` en (5)
incluye el índice 0 para acomodar operaciones "ficticias" de inicio (un truco
común para uniformar la primera operación).

---

## Diapositiva 10 — Modelo matemático base (ecuaciones 7–10)

**(7) Asignación única:** `Σ_{i=1}^{m_jh} x_ijh = 1`
Cada operación se asigna a **exactamente una** máquina de sus alternativas. Es la
esencia del "flexible": se elige una de las m_jh opciones.

**(8) y (9) Consistencia asignación–secuencia:**
`Σ_j Σ_h y_ijhkl = x_ikl` y `Σ_k Σ_l y_ijhkl = x_ijh`
Ligan las binarias de orden `y` con las de asignación `x`: una operación sólo
puede tener predecesor/sucesor en una máquina si efectivamente está asignada a esa
máquina. (La diapositiva 11 las glosa como "operación cíclica en cada máquina",
que en rigor es la construcción de la secuencia de proceso por máquina.)

**(10) No negatividad:** `s_jh ≥ 0, c_jh ≥ 0`
Los tiempos son no negativos (no hay tiempos "antes del cero").

**Fundamentación:** (7)–(10) completan la formulación MILP (programación lineal
entera mixta). Juntas con (1)–(6) definen **exactamente** el FJSSP. En un solver
exacto (CPLEX/Gurobi) esto se resolvería directo, pero el número de binarias
`y_ijhkl` explota combinatoriamente (~ (operaciones)² × máquinas), por eso se usa
un **GA** (metaheurística) en vez de un solver exacto. El modelo MILP sirve como
**definición formal** de qué es una solución válida; el GA la busca
heurísticamente.

---

## Diapositiva 11 — Descripción del modelo base

Glosa en palabras de las 10 ecuaciones (equivalencia directa):
- (1) objetivo = minimizar el mayor `C_j`.
- (2)(3) restricciones de secuencia de proceso.
- (4) el término de cada trabajo no excede el makespan.
- (5)(6) una máquina, un proceso a la vez.
- (7) cada operación en una sola máquina.
- (8)(9) construcción de la secuencia por máquina.
- (10) variables no negativas.

**Cómo el código garantiza cada restricción** (el decodificador las cumple *por
construcción*, no las chequea a posteriori):
- (2)(3) precedencia → `ready[j] = s + p` en
  [scheduler_ga.py:62](trabajo_final_rush_order/src/scheduler_ga.py#L62).
- (5)(6) no solape → `insort(busy[m], (s, s+p))` +
  `earliest_start` en [scheduler_ga.py:59-60](trabajo_final_rush_order/src/scheduler_ga.py#L59-L60).
- (7) asignación única → `m, p = ms[op]` (el MS asigna una sola máquina).
- El autochequeo en
  [scheduler_ga.py:129-139](trabajo_final_rush_order/src/scheduler_ga.py#L129-L139)
  verifica las tres tras resolver.

---

## Diapositiva 12 — Mecanismo de reprogramación ante un rush order

**Evento:** en `t* = Cmax0/2` llega el rush `J^R = {r}`; el conjunto de trabajos
pasa a `J = J^0 ∪ J^R`. Del schedule inicial `S^0` se conocen `s0_jh, c0_jh,
x0_ijh` (inicio, término y máquina originales de cada operación).

**Clasificación de operaciones en t\*:**
- **F (Terminadas):** `{(j,h) : c0_jh ≤ t*}` → **congeladas** (ya ocurrieron).
- **I (En proceso):** `{(j,h) : s0_jh < t* < c0_jh}` → continúan **sin
  interrupción** (non-preemption).
- **P (Pendientes):** `{(j,h) : s0_jh ≥ t*}` → **reprogramables**.
- **R (Rush):** `{(r,h)}` → operaciones del pedido urgente.
- **Conjunto a reprogramar:** `Q = P ∪ R`.

**Fundamentación de las desigualdades (los `≤`, `<`, `≥`):** definen una
**partición** de S0 según la posición de t* respecto al intervalo [s0, c0] de cada
operación. `c0 ≤ t*` (terminó antes o justo en t*), `s0 < t* < c0` (t* cae dentro),
`s0 ≥ t*` (empieza después). Es exhaustiva y disjunta: cada operación cae en
exactamente una categoría. El autochequeo lo verifica en
[rescheduling.py:167](trabajo_final_rush_order/src/rescheduling.py#L167)
(`F | I | P == set(s0)`).

**Correspondencia con el código:**
[rescheduling.py:33-35](trabajo_final_rush_order/src/rescheduling.py#L33-L35):
```python
F = {op for op, (_, s, e) in s0.items() if e <= t_star}
I = {op for op, (_, s, e) in s0.items() if s < t_star < e}
P = {op for op, (_, s, e) in s0.items() if s >= t_star}
```
`Q = sorted(P) + sorted(rush_data)` en
[rescheduling.py:49](trabajo_final_rush_order/src/rescheduling.py#L49).

**Por qué congelar F ∪ I:** F ya pasó (inmutable). I está físicamente en la
máquina y no se interrumpe (non-preemption). Sólo P y el rush admiten decisión.
Esto reduce el subproblema y es lo que hace el rescheduling **parcial** (no
re-planifica todo).

---

## Diapositiva 13 — Disponibilidad de máquinas y restricciones del rescheduling

**Disponibilidad de cada máquina:**
`A^t_i = máx( t*, máx_{(j,h)∈I : x0_ijh=1} c0_jh )`
Cada máquina está libre desde t*, **salvo** que tenga una operación en proceso
(I) encima: entonces desde que esa termine (`c0_jh`). Si no tiene operación en
proceso, queda libre en t*.

**Restricciones añadidas sobre Q** (además de las del modelo base):
- `s_jh ≥ t*` — nada reprogramado empieza antes del instante de la perturbación.
- `s_jh ≥ A^t_i − L(1 − x_ijh)` — si la operación usa la máquina i (x_ijh=1), no
  puede empezar antes de que esa máquina esté disponible; el Big-M `L` desactiva
  la restricción para las máquinas no elegidas.

**Congelamiento (formal):**
`s_jh = s0_jh, c_jh = c0_jh, x_ijh = x0_ijh   ∀(j,h) ∈ F ∪ I`
Las operaciones congeladas mantienen inicio, término y máquina originales.

**Primera operación pendiente de cada trabajo:** su inicio respeta la precedencia
respecto del término congelado `c0_{j,h−1}` (si su operación anterior está en F o I).

**Correspondencia con el código:**
- `A^t_i` → `avail[m]` en
  [rescheduling.py:36-39](trabajo_final_rush_order/src/rescheduling.py#L36-L39).
- `s_jh ≥ t*` → `job_ready[j] = t_star` inicial +
  `mach_busy = [(0, avail[m])]` en
  [rescheduling.py:40-45](trabajo_final_rush_order/src/rescheduling.py#L40-L45).
- Precedencia con el término congelado → `job_ready[j] = max(..., s0[op][2])` en
  [rescheduling.py:42-44](trabajo_final_rush_order/src/rescheduling.py#L42-L44).
- El autochequeo `full[op][1] >= t_star` y precedencia en
  [rescheduling.py:174-177](trabajo_final_rush_order/src/rescheduling.py#L174-L177).

**Elegancia del diseño:** `mach_busy` y `job_ready` son precisamente los
parámetros opcionales que ya acepta `decode`
([scheduler_ga.py:41](trabajo_final_rush_order/src/scheduler_ga.py#L41)). Por eso
**el mismo GA/decodificador** resuelve el plan inicial y el rescheduling — sólo
cambia el "estado inicial de ocupación".

---

## Diapositiva 14 — Función objetivo con rush order y nervousness

**Objetivo del rescheduling:**
`mín Z = CmaxR + α·Cr + β·N`

Tres términos:
- `CmaxR` — makespan del programa reprogramado (**eficiencia global**).
- `Cr = c_{r,h_r}` — término de la **última** operación del rush (**urgencia**:
  penaliza que el pedido urgente acabe tarde).
- `N` — *nervousness* (**estabilidad**: penaliza mover el plan).

**Nervousness descompuesta:**
`N = γ1·Σ_{(j,h)∈P} |s_jh − s0_jh|  +  γ2·Σ_{(j,h)∈P} (1 − x0_ijh)`
`     └────────── Ns ──────────┘      └──────── Nm ────────┘`
- **Ns** = suma de desplazamientos de inicio de las operaciones pendientes
  (cuánto se corrieron en el tiempo respecto a S0).
- **Nm** = nº de operaciones pendientes que **cambiaron de máquina** (el término
  `1 − x0_ijh` vale 1 cuando la máquina nueva no es la original).

**Fundamentación de las constantes** (valores en
[metrics.py:5-6](trabajo_final_rush_order/src/metrics.py#L5-L6)):

| Constante | Valor | Rol | Por qué ese valor |
|-----------|-------|-----|-------------------|
| `α` (alpha) | 0.5 | peso de la urgencia del rush | media ponderación: el rush importa, pero no domina al makespan global. Su sensibilidad se testea en la diapositiva 26 |
| `β` (beta) | 0.1 | peso de la estabilidad | pequeño: N puede ser numéricamente grande (suma de desplazamientos en segundos + 10 por cada cambio de máquina), así que un peso chico evita que N aplaste a Cmax |
| `γ1` (gamma_S) | 1.0 | peso del desplazamiento temporal Ns | unidad base: 1 segundo de corrimiento = 1 unidad de nervousness |
| `γ2` (gamma_M) | 10.0 | peso del cambio de máquina Nm | **10× más caro** que un segundo de corrimiento: cambiar de máquina implica reconfiguración física (mover herramienta, recalibrar el brazo robótico), mucho más disruptivo que solo retrasar |

**Justificación de la forma aditiva ponderada:** es una **escalarización** de un
problema multiobjetivo (eficiencia vs urgencia vs estabilidad). En vez de buscar
un frente de Pareto, se colapsan los tres objetivos en un escalar Z con pesos que
codifican la preferencia del decisor. Cambiar α, β **cambia qué estrategia gana**
(diapositiva 26), y el aporte del selector ML es adaptarse a esos pesos
(diapositiva 32).

**Correspondencia con el código:** `Z = z_score(cmax_r, c_r, n)` en
[metrics.py:16-17](trabajo_final_rush_order/src/metrics.py#L16-L17);
`nervousness()` en
[metrics.py:9-13](trabajo_final_rush_order/src/metrics.py#L9-L13).

---

## Diapositiva 15 — Metodología: Codificación con GA

**Cromosoma segmentado MS+OS** (dos partes):
- **MS (Machine Selection):** asigna una máquina factible a cada una de las 40
  operaciones. Es la representación de las binarias `x_ijh`.
- **OS (Operation Sequence):** permutación **con repetición** de los trabajos (40
  genes = 8 trabajos × 5 apariciones). La **k-ésima aparición** del trabajo j es
  su k-ésima operación. Es la representación implícita de las binarias `y`.

**Decodificador:**
- Programa cada operación en el **primer hueco factible** de su máquina
  (inserción en huecos), respetando precedencia y disponibilidad.
- **Acepta un estado inicial no vacío** ⇒ reutilizable sin cambios para el
  rescheduling parcial (¡el punto de diseño de la diapositiva 13!).

**Fundamentación del número 40 genes:** el OS tiene un gen por operación (40), no
por trabajo (8), porque cada operación necesita una posición en la secuencia
global de despacho. La repetición del trabajo j exactamente h_j=5 veces garantiza
que se respeta el número de operaciones sin necesidad de codificar el índice de
operación explícitamente (se infiere por orden de aparición).

**Correspondencia con el código:** `ms` y `order` en
[scheduler_ga.py:83-87](trabajo_final_rush_order/src/scheduler_ga.py#L83-L87);
decodificador `decode` con `earliest_start` en
[scheduler_ga.py:31-64](trabajo_final_rush_order/src/scheduler_ga.py#L31-L64).

**Cómo funciona `earliest_start` (inserción en huecos), con ejemplo:**
máquina con intervalos ocupados `[(0,3),(6,10)]`, operación de duración `p=2`
disponible desde `ready=1`:
- t=1 → ¿cabe [1,3] antes del bloque (0,3)? No → salto a t=3.
- t=3 → ¿cabe [3,5] antes del bloque (6,10)? Sí → inicia en 3.
La operación rellena el hueco 3–5 en vez de apilarse al final. Esto produce
schedules más compactos (menor Cmax) que un despacho "siempre al final".

---

## Diapositiva 16 — Scheduling inicial GA: Operadores y justificación

**Operadores genéticos:**
- **Selección por torneo (k=3):** se toman 3 individuos al azar y gana el mejor.
  k=3 es un balance estándar entre presión selectiva (favorecer buenos) y
  diversidad (no siempre gana el élite).
- **Crossover:** POX (Precedence Operation Crossover) en el OS; **uniforme** en el
  MS (cada gen se hereda de un padre al 50%).
- **Mutación:** reasignación de máquina (cambia un gen del MS) e intercambio de
  posiciones (swap en el OS).
- **Elitismo:** el mejor individuo pasa intacto a la siguiente generación.

**Parámetros:** población **120**, **300** generaciones, semilla **0**.

**Fundamentación de los números:**
- **Población 120 / 300 generaciones:** presupuesto de cómputo. Más población =
  más exploración por generación; más generaciones = más refinamiento. 120×300 =
  36.000 evaluaciones, suficiente para converger en una instancia de 40
  operaciones sin costo excesivo (~3.3 s, diapositiva 24).
- **Semilla 0:** fija el generador aleatorio → **reproducibilidad** (el mismo
  resultado en cada corrida). Esencial para un experimento científico.
- **Torneo k=3:** ver arriba.

**Justificación del método (recuadro):** el GA maneja de forma natural la
**codificación mixta** asignación+secuencia del FJSSP; su **fitness es
intercambiable**, lo que permite usar el mismo motor para las variantes con
prioridad de rush (`priority_ga`) y con estabilidad (`stability_ga`).

**Correspondencia con el código:** operadores en
[scheduler_ga.py:97-117](trabajo_final_rush_order/src/scheduler_ga.py#L97-L117);
POX en [scheduler_ga.py:67-72](trabajo_final_rush_order/src/scheduler_ga.py#L67-L72);
parámetros por defecto en `solve_initial`
[scheduler_ga.py:120-123](trabajo_final_rush_order/src/scheduler_ga.py#L120-L123).
El "fitness intercambiable" es el argumento `fitness=` de `ga()`
([scheduler_ga.py:75](trabajo_final_rush_order/src/scheduler_ga.py#L75)) — el
gancho que reutiliza el motor.

---

## Diapositiva 17 — Simulación de la perturbación

**El DT lógico** (capa de monitoreo implementada como **regla sobre el estado**
del sistema de pedidos) ejecuta 5 pasos en `t* = Cmax0/2`:
1. **Detecta** la inserción de J9.
2. **Clasifica** las operaciones en F/I/P.
3. **Congela** F ∪ I.
4. **Calcula** la disponibilidad `A^t_i`.
5. **Construye** el subproblema sobre `Q = P ∪ R`.

**Fundamentación de "DT lógico":** aclara el alcance. No hay sensores físicos ni
modelo 3D; el "gemelo" es una **función** que lee el estado (S0, t*, rush) y
produce el subproblema. Es la materialización de la Capa de Servicio
(diapositiva 4) en código puro. Los 5 pasos corresponden 1:1 con la función
`shop_state()` en
[rescheduling.py:31-50](trabajo_final_rush_order/src/rescheduling.py#L31-L50).

---

## Diapositiva 18 — Estrategias de rescheduling

Cinco estrategias para resolver el subproblema Q, en orden creciente de
"inteligencia":

1. **`insert_end`** (baseline sin recuperación): el programa pendiente queda
   **intacto**; el rush se agrega **al final** de cada máquina. Simple, cero
   perturbación (N=0), pero el rush termina tardísimo.
2. **`right_shift`** (inserción con desplazamiento): el rush se programa **lo
   antes posible** compitiendo sólo con lo congelado; las pendientes conservan su
   máquina y orden, desplazadas a la derecha **sólo lo necesario** (nunca antes de
   su inicio original). Prioriza el término del rush a costa de retrasar el resto.
3. **`partial_ga`:** GA sobre Q minimizando `CmaxR` (sólo eficiencia).
4. **`priority_ga`:** GA sobre Q minimizando `CmaxR + α·Cr` (eficiencia +
   urgencia).
5. **`stability_ga`:** GA sobre Q minimizando `CmaxR + α·Cr + β·N` (eficiencia +
   urgencia + estabilidad) = la función Z completa.

**Fundamentación del diseño incremental:** las 5 estrategias forman una escalera
donde cada una **añade un término** al objetivo. Esto permite aislar el efecto de
cada componente: comparar `partial_ga` vs `priority_ga` mide el impacto de α;
comparar `priority_ga` vs `stability_ga` mide el impacto de β. Las dos primeras
(`insert_end`, `right_shift`) son heurísticas **deterministas** (baseline); las
tres con GA son **optimizadoras**.

**Correspondencia con el código:** `apply_strategy()` en
[rescheduling.py:142-160](trabajo_final_rush_order/src/rescheduling.py#L142-L160);
los objetivos de las GA en `_ga_fitness`
[rescheduling.py:103-115](trabajo_final_rush_order/src/rescheduling.py#L103-L115).

---

## Diapositiva 19 — Estrategias de rescheduling: Warm start elitista

**Warm start elitista:** las tres variantes con GA usan un arranque "caliente": el
resultado reportado **nunca es peor** que las heurísticas deterministas
(`insert_end`, `right_shift`) evaluadas con el objetivo de **la propia variante**.

**Garantiza por construcción:**
- `stability_ga` **domina o iguala** a `insert_end`.
- El ruido de convergencia del GA **no contamina** las etiquetas de entrenamiento
  del selector.

**Fundamentación:** un GA es estocástico; con presupuesto reducido (pop y gens
bajos, usados al generar cientos de escenarios) puede converger mal y devolver una
solución peor que una heurística trivial. Si eso pasara, la etiqueta "mejor
estrategia" del dataset sería **ruido**, no señal. El warm start soluciona esto:
tras correr el GA, se compara su resultado contra `insert_end` y `right_shift`
bajo el objetivo de la variante y se queda con el mejor. Así una estrategia GA es,
por definición, ≥ que las heurísticas → las etiquetas son fiables.

**Correspondencia con el código:**
[rescheduling.py:153-159](trabajo_final_rush_order/src/rescheduling.py#L153-L159):
```python
candidatos = [_finish(state, sched),
              apply_strategy("insert_end", state),
              apply_strategy("right_shift", state)]
return min(candidatos, key=lambda r: _result_fitness(name, r))
```

---

## Diapositiva 20 — Selector inteligente (XGBoost): Features y dataset

**14 features del estado del taller en t\*:** avance, cargas, holguras; tamaño y
flexibilidad del rush; saturación; pendientes que compiten por las máquinas del
rush.

**Dataset artificial: 300 escenarios**, con variación controlada:
- **Rush aleatorio por iteración:** 3–5 operaciones, 1–3 máquinas factibles cada
  una, tiempos `U[30, 105]` (uniforme entre 30 y 105).
- **t\* variable** en `[0.3, 0.7]·Cmax0`.
- **Cinco schedules iniciales distintos** (carga del taller variable).

**Fundamentación de los números:**
- **14 features:** describen el estado sin redundancia. La lista completa está en
  `FEATURE_NAMES`
  [xgboost_selector.py:24-28](trabajo_final_rush_order/src/xgboost_selector.py#L24-L28).
- **300 escenarios:** tamaño de muestra para entrenar un modelo tabular sin
  sobreajuste severo; con 5 estrategias × 3 semillas por GA, ya es costoso de
  generar.
- **3–5 ops, 1–3 máquinas, U[30,105]:** replican el **rango empírico** de la
  Tabla 6 del paper base (los tiempos reales están en 30–105). Mantiene los rush
  sintéticos realistas.
- **t\* en [0.3, 0.7]·Cmax0:** cubre perturbaciones tempranas y tardías alrededor
  de la mitad, para que el modelo generalice a distintos momentos de llegada (no
  sólo Cmax0/2 exacto).
- **5 schedules base:** distintas cargas iniciales del taller → diversidad de
  estados. Además permite validación **sin fuga** (leave-one-group-out por base,
  diapositiva 25).

**Correspondencia con el código:** `features()` y `build_dataset()` en
[xgboost_selector.py:31-90](trabajo_final_rush_order/src/xgboost_selector.py#L31-L90);
`random_rush()` con `randint(30,105)` en
[rescheduling.py:22-28](trabajo_final_rush_order/src/rescheduling.py#L22-L28).

---

## Diapositiva 21 — Selector (XGBoost): Evaluación (distribución de ganadoras)

**Método de etiquetado:** cada escenario se resuelve con las 5 estrategias,
registrando `(CmaxR, Cr, N)`. Las estrategias con GA se etiquetan con la
**mediana de 3 corridas** (semillas distintas), porque una corrida única con
presupuesto reducido tiene ruido mayor que el margen típico entre estrategias.

**Distribución de estrategias ganadoras (300 escenarios):**

| Estrategia | Escenarios ganados |
|------------|-------------------:|
| insert_end | 33 |
| right_shift | 44 |
| partial_ga | 9 |
| priority_ga | 10 |
| **stability_ga** | **204 (68%)** |

**Fundamentación / interpretación:** el fuerte **desbalance** (stability_ga gana
68%, partial_ga sólo 3%) no es un error: es el hallazgo central. Bajo la función Z
(que penaliza la nervousness con β=0.1 y castiga cambios de máquina con γ2=10), la
estrategia **estable** casi siempre minimiza el costo total, porque el margen de
mejora en makespan por resecuenciar es pequeño (diapositiva 31) pero el costo de
desestabilizar es alto. Este desbalance es lo que motiva la decisión de
arquitectura de la diapositiva 22 (regresor en vez de clasificador).

**Nota sobre reproducibilidad:** los números de esta tabla (33/44/9/10/204)
provienen de una corrida de 300 escenarios con las semillas del experimento. Una
corrida rápida de prueba (p. ej. `n_escenarios=20`) da otra distribución (como el
`[1 2 0 4 13]` observado en pruebas) — el patrón cualitativo (stability_ga domina,
partial_ga casi nunca gana) se mantiene.

**Correspondencia con el código:** etiquetas por mediana de n_seeds en
[xgboost_selector.py:81-83](trabajo_final_rush_order/src/xgboost_selector.py#L81-L83);
distribución en el `evaluate()` (`np.bincount`) en
[xgboost_selector.py:150](trabajo_final_rush_order/src/xgboost_selector.py#L150).

---

## Diapositiva 22 — Selector (XGBoost): Arquitectura

**El desbalance motivó la elección.** Se compararon dos formulaciones bajo la
misma validación:
1. **Clasificador** XGBoost de la estrategia ganadora, con pesos balanceados por
   clase.
2. **Regresor de costo** XGBoost que predice `Z` para cada par (estado,
   estrategia) y selecciona el `argmín`.

**Decisión adoptada (recuadro):** el **clasificador decide peor que el baseline
trivial** "elegir siempre stability_ga" — el balanceo de clases fuerza
desviaciones hacia clases minoritarias que cuestan más de lo que aportan. Se
adoptó la **regresión de costo**, que optimiza directamente la **calidad de
decisión** (Z bajo) en vez del *accuracy* de clasificación.

**Fundamentación profunda:** este es el argumento metodológico más fino del
trabajo.
- Un **clasificador** optimiza *accuracy* (acertar la etiqueta). Con 68% de una
  clase, predecir siempre stability_ga ya da 68% de accuracy. Balancear las clases
  (para no ignorar las minoritarias) lo empuja a arriesgar predicciones de clases
  raras; cuando falla, elige una estrategia que cuesta **mucho** más Z.
- Un **regresor de costo** no intenta adivinar la ganadora: **estima el costo Z de
  cada estrategia** y elige la de menor costo predicho. Aunque se equivoque de
  etiqueta, si las dos estrategias tienen Z parecido, el error en Z es pequeño. Es
  decir, optimiza la métrica que **de verdad importa** (regret en Z), no una proxy
  (accuracy).
- Resultado (diapositiva 25): el regresor casi iguala al oráculo; el clasificador
  balanceado queda muy por detrás.

**Correspondencia con el código:** regresor `train()` con `XGBRegressor` sobre
filas expandidas (estado + one-hot de estrategia) en
[xgboost_selector.py:93-116](trabajo_final_rush_order/src/xgboost_selector.py#L93-L116);
comparación contra el clasificador balanceado en `evaluate()`
[xgboost_selector.py:119-163](trabajo_final_rush_order/src/xgboost_selector.py#L119-L163).

---

## Diapositiva 23 — Diseño experimental

**Cuatro escenarios obligatorios con semilla fija:**
1. Scheduling inicial.
2. Rush **sin** recuperación inteligente.
3. Recuperación por GA parcial.
4. Recuperación con selector XGBoost.

**Métricas:** `Cmax`, `Cr`, tiempo computacional, `N`, operaciones modificadas, y
**% de recuperación:**
`%Recup = (Cmax_pert − Cmax_rec) / (Cmax_pert − Cmax0) × 100`

**Fundamentación de la fórmula de %Recuperación:**
- **Denominador** `(Cmax_pert − Cmax0)` = el **daño** que causó el rush (cuánto
  creció el makespan respecto al plan original limpio).
- **Numerador** `(Cmax_pert − Cmax_rec)` = la **mejora** que logra la estrategia
  respecto al baseline perturbado (`insert_end`).
- El cociente ×100 = **qué fracción del daño se recuperó**. 100% = se volvió al
  makespan original; 0% = no se mejoró nada sobre el baseline; **negativo** =
  se empeoró (¡el caso de `right_shift` en la tabla siguiente!).

**Fundamentación de "semilla fija":** los 4 escenarios usan la misma semilla →
**comparación justa y reproducible** (mismas condiciones aleatorias, sólo cambia
la estrategia). Es control experimental básico.

**Correspondencia con el código:** `recovery()` en
[metrics.py:20-25](trabajo_final_rush_order/src/metrics.py#L20-L25).

---

## Diapositiva 24 — Resultados: Comparación de estrategias (tabla principal)

| Escenario | Estrategia | Cmax (s) | Cr (s) | N | Ops. modif. | Tiempo (s) | % Recup |
|-----------|-----------|--------:|------:|----:|-----------:|----------:|-------:|
| 1. Inicial | GA | 382 | – | – | – | 3.3 | – |
| 2. Rush sin recup. | insert_end | 518 | 518 | 0 | 0 | <0.1 | 0 |
| 3. Recup. GA parcial | partial_ga | **512** | **512** | 747 | 12 | 0.6 | 4.4 |
| 4. Recup. inteligente | XGBoost→stability_ga | 518 | 518 | **0** | **0** | 0.7 | 0 |
| (comp.) | right_shift | 583 | 512 | 541 | 4 | <0.1 | **−47.8** |
| (comp.) | priority_ga | 512 | 512 | 693 | 13 | 0.7 | 4.4 |

**Lectura número por número:**
- **Cmax inicial = 382 s:** el plan limpio óptimo (equivale al valor `Cmax0`).
- **Rush lo lleva a 518 s** (`insert_end`): daño de **136 s** (= 518 − 382).
- **partial_ga baja a 512 s:** recupera 6 s de los 136 → 6/136 ≈ **4.4%**. Con N=747
  y 12 operaciones modificadas (¡mucha perturbación por 6 s!).
- **XGBoost → stability_ga = 518 s, N=0, 0 ops modificadas:** el selector elige
  **no tocar** las pendientes. Mismo makespan que el baseline pero **cero
  nervousness**. Bajo Z, es la mejor: recuperar 6 s no compensa mover 12
  operaciones.
- **right_shift = 583 s, %Recup = −47.8%:** **empeora** el makespan (de 518 a 583).
  El negativo indica que retrasó tanto las pendientes al priorizar el rush que el
  makespan global creció. Ilustra que "meter el rush antes" puede ser
  contraproducente para Cmax.
- **priority_ga = 512 s, N=693, 13 ops:** iguala a partial_ga en makespan pero con
  aún más perturbación → peor en Z.

**Fundamentación del mensaje:** la tabla demuestra el **trade-off eficiencia vs
estabilidad**. La mejora máxima en makespan es marginal (6 s, 4.4%) y cuesta
carísimo en estabilidad (N alto, muchas ops movidas). Por eso el selector,
optimizando Z, elige estabilidad (stability_ga con N=0). **El aporte no es bajar
el makespan sino tomar la decisión correcta según la función de costo.**

---

## Diapositiva 25 — Resultados: Decisión y validación del selector

| Política | Z medio | Regret vs oráculo |
|----------|-------:|------------------:|
| Oráculo (mejor estrategia por escenario) | 740.2 | 0 |
| Baseline trivial: siempre stability_ga | 740.8 | **0.66** |
| **Selector (regresión de Z)** | 741.4 | **1.18** |
| Clasificador XGBoost balanceado (descartado) | 749.6 | 9.43 |

**Definiciones:**
- **Oráculo:** un decisor perfecto que siempre elige la estrategia de menor Z
  (conoce el resultado a priori). Es la **cota inferior** de Z; regret = 0 por
  definición.
- **Regret:** cuánto peor decide una política que el oráculo, en promedio
  (`Z_política − Z_oráculo`). Menor es mejor.

**Lectura:**
- El **baseline trivial** (siempre stability_ga) tiene regret **0.66** — ya es
  muy bueno, porque stability_ga gana el 68% de las veces.
- El **selector** tiene regret **1.18** — ligeramente peor que el baseline trivial
  en promedio, pero **muy cerca del oráculo** (a 1.18 de 740).
- El **clasificador balanceado** tiene regret **9.43** — ~8× peor. Confirma la
  decisión de la diapositiva 22: balancear hace decidir mal.

**Fundamentación honesta (importante para la defensa):** el selector **no supera**
al baseline trivial en este experimento (1.18 > 0.66). Esto **no invalida** el
modelo: (a) demuestra que el regresor decide casi tan bien como el oráculo y
**mucho mejor** que el clasificador; (b) el valor del selector es su
**adaptabilidad** a distintos pesos α, β (diapositiva 32) — con otros pesos, la
estrategia óptima cambia (diapositiva 26) y un baseline fijo dejaría de servir,
mientras el selector se re-entrena. El baseline trivial sólo gana **porque en esta
configuración de pesos stability_ga domina**.

**Correspondencia con el código:** `evaluate()` calcula Z medio y regret de las
tres políticas con validación leave-one-group-out en
[xgboost_selector.py:139-163](trabajo_final_rush_order/src/xgboost_selector.py#L139-L163).

---

## Diapositiva 26 — Resultados: Análisis de sensibilidad de α y β

| α | β | insert_end | right_shift | partial_ga | priority_ga | stability_ga |
|--:|--:|-----------:|------------:|-----------:|------------:|-------------:|
| 0.5 | 0.1 (usado) | 33 | 44 | 9 | 10 | **204** |
| 0.5 | 0.0 | 24 | 79 | **97** | 75 | 25 |
| 0.5 | 0.05 | 28 | 46 | 18 | 23 | 185 |
| 0.5 | 0.2 | 51 | 46 | 3 | 5 | 195 |
| 0.0 | 0.1 | 49 | 40 | 17 | 11 | 183 |
| 1.0 | 0.1 | 29 | 46 | 12 | 22 | 191 |

**Fundamentación / lectura:** se varían los pesos y se recuenta qué estrategia
gana los 300 escenarios. El hallazgo clave está en la fila **β = 0.0**: sin
penalización de estabilidad, **stability_ga colapsa de 204 a 25** y
**partial_ga salta de 9 a 97**. Es decir: si no importa la nervousness, conviene
reoptimizar agresivamente (partial_ga); en cuanto se penaliza mover el plan
(β>0), la estrategia estable domina.

- Subir **β** (0.05 → 0.1 → 0.2) refuerza a stability_ga y hunde a
  partial/priority_ga (mover el plan se vuelve caro).
- **α** (0.0, 0.5, 1.0) tiene efecto menor sobre la distribución: la urgencia del
  rush sola no cambia tanto la ganadora, porque el rush termina parecido en varias
  estrategias.

**Mensaje:** valida que los pesos **importan** y que la elección `α=0.5, β=0.1` no
es arbitraria sino un punto donde la estabilidad pesa lo suficiente para
recomendarla. También justifica el selector: **si la empresa cambia sus
preferencias (β), la estrategia óptima cambia**, y el selector se adapta
re-entrenando con los nuevos Z.

---

## Diapositivas 27–30 — Cartas Gantt

Cuatro diagramas de Gantt (máquina en el eje Y, tiempo en el X, cada bloque = una
operación etiquetada `job-op`):

- **Diap. 27 — Gantt Inicial (Cmax0 = 382):** el plan óptimo limpio de los 8
  trabajos en las 8 máquinas. Bloques compactos gracias a la inserción en huecos.
- **Diap. 28 — Gantt Perturbado / insert_end (CmaxR = 518):** línea vertical en
  **t\* = 191** (= 382/2) marca la llegada del rush. Las operaciones del rush
  (9-1…9-5) se apilan **al final** de sus máquinas → el makespan salta a 518. Lo
  anterior a t\* queda congelado; lo posterior, intacto.
- **Diap. 29 — Gantt Recuperado / GA parcial (CmaxR = 512):** el GA reorganiza las
  pendientes + rush. El makespan baja apenas a 512, pero se ve que **muchas
  operaciones cambiaron de posición/máquina** (las 12 ops modificadas, N=747).
- **Diap. 30 — Gantt Recuperado / XGBoost → stability_ga (CmaxR = 518):**
  **idéntico al inicial** en la zona pendiente (nada se movió, N=0); el rush se
  inserta sin desarmar el plan. Mismo Cmax que insert_end pero con estructura
  estable.

**Fundamentación de por qué mostrar los cuatro:** la comparación visual es el
argumento más fuerte de la presentación. Diap. 29 vs 30 muestra **el mismo
makespan-ish** con estructuras opuestas: GA parcial (desorden, 512) vs stability_ga
(orden intacto, 518). El auditor "ve" el trade-off: 6 segundos de makespan no
justifican el caos del Gantt 29. **t\* = 191** confirma numéricamente `Cmax0/2 =
382/2 = 191`.

**Correspondencia con el código:** generación de los Gantt en
[gantt.py](trabajo_final_rush_order/src/gantt.py).

---

## Diapositiva 31 — Discusión (I)

**Calidad de la solución:**
- El GA con decodificación por huecos obtuvo **Cmax = 382 s**, **superando al
  RLEGA (397 s)** — el método del paper base (Reinforcement Learning Enhanced
  Genetic Algorithm). Un GA bien diseñado con inserción en huecos **batió** al
  método más sofisticado del paper de referencia.
- El rescheduling parcial alcanzó la **cota inferior (512 s)** del subproblema →
  **no existe** mejor solución para ese escenario (es óptimo, no sólo bueno).

**Impacto del rush order:**
- El aumento del makespan (**136 s**) está dominado por la **cadena crítica del
  propio pedido urgente** (sus 5 operaciones en secuencia toman su tiempo,
  independientemente de cómo se reordene el resto).
- El margen de mejora por resecuenciar es **reducido (máx. 6 s)**, por las
  características de la instancia, **no** por limitación del método.

**Fundamentación de "cota inferior 512 s":** que partial_ga alcance la cota
inferior significa que el GA encontró el óptimo del subproblema — el makespan no
puede bajar de 512 sin violar restricciones. Esto **fortalece** el resultado: el
poco margen (6 s) es una propiedad **del problema**, no una falla del algoritmo.
Anticipa objeciones del tipo "¿y si el GA no convergió?".

**Fundamentación de "superar a RLEGA":** es el resultado que da legitimidad. 382 <
397 valida que la implementación propia es competitiva con la literatura.

---

## Diapositiva 32 — Discusión (II)

**Trade-off desempeño vs estabilidad:**
- Recuperar sólo **4.4%** del makespan requiere modificar **12 de 15** operaciones,
  incluyendo **7 cambios de máquina**.
- Bajo Z, es más conveniente **mantener un programa estable** que reoptimizar
  completamente.

**Rol del modelo inteligente:**
- El selector XGBoost recomienda la estrategia que minimiza Z, **privilegiando la
  estabilidad cuando corresponde**.
- El principal aporte es su **adaptabilidad** frente a distintos pesos de la
  función objetivo, **más que** pequeñas mejoras en Z.

**Fundamentación de "12 de 15":** de las 15 operaciones pendientes en t\*, la
recuperación agresiva toca 12 (y cambia 7 de máquina, cada cambio cuesta γ2=10 en
N). El mensaje es cuantitativo: **el costo de estabilidad de la mejora es enorme
comparado con su beneficio** (4.4% de makespan). Esto cierra el argumento de todo
el trabajo: en scheduling dinámico real, **estabilidad > optimalidad marginal**,
y un buen sistema debe **saber cuándo no actuar**.

---

## Diapositiva 33 — Conclusión

Resumen de logros:
- Metodología de **scheduling dinámico para FJSSP** en entorno **Digital Twin**.
- GA inicial: **Cmax = 382 s**, superando a RLEGA.
- Rush simulado en `t* = Cmax/2`; **cinco** estrategias de recuperación evaluadas.
- Selector **XGBoost** entrenado con **300 escenarios sintéticos**, elige la de
  menor Z.
- El sistema: **recuperó el makespan óptimo (512 s)** vía GA parcial, y
  **priorizó la estabilidad** cuando la mejora era marginal.

**Fundamentación:** la conclusión enlaza los tres pilares — DT (marco), GA
(motor), XGBoost (decisión) — y el hallazgo transversal: la respuesta inteligente
a una perturbación no siempre es re-optimizar; a veces es **preservar el plan**.
Ese matiz (saber cuándo no actuar) es la contribución conceptual.

---

## Diapositivas 34–36 — Bibliografía

Referencias clave y su rol en el trabajo:

- **Liu et al. (2022), *Sustainability*** — **paper base**: aporta el framework de
  DT (diap. 4) y la instancia (Tablas 5 y 6 → `DATA`). El benchmark RLEGA (397 s)
  sale de aquí.
- **Wang et al. (2022), *Applied Sciences*** — método de inserción de órdenes
  dinámicas en FJSSP con DT; respalda el enfoque de rescheduling por inserción.
- **Moratori, Petrovic & Vázquez-Rodríguez (2010), *Applied Intelligence*** —
  integración de rush orders en schedules existentes; fundamenta el mecanismo de
  congelamiento/reprogramación.
- **Sridharan et al. (1987), *Management Science*** — "freezing the master
  schedule": base teórica del **congelamiento** de F ∪ I.
- **Rangsaritratsamee, Ferrell & Kurz (2004), *Computers & Ind. Eng.*** —
  rescheduling que considera **eficiencia y estabilidad simultáneamente**: la
  fuente conceptual de la función Z (eficiencia + estabilidad).
- **Carlson, Jucker & Kropp (1979), *Management Science*** — "less nervous MRP":
  origen del concepto de **nervousness** (la métrica N).
- **Chen & Guestrin (2016)** — el paper original de **XGBoost** (el algoritmo del
  selector).
- **Grinsztajn, Oyallon & Varoquaux (2022), *NeurIPS*** — "por qué los modelos de
  árboles aún superan al deep learning en datos tabulares": **justifica elegir
  XGBoost** (no una red neuronal) para las 14 features tabulares.
- **Trzyna, Kuyumcu & Lödding (2012), *Procedia CIRP*** — características de tiempo
  de los rush orders: fundamenta la introducción (diap. 5).

**Fundamentación:** la bibliografía cubre las tres patas — scheduling dinámico
(Liu, Wang, Moratori), estabilidad/nervousness (Sridharan, Rangsaritratsamee,
Carlson) y machine learning (Chen, Grinsztajn) — más la motivación del rush
(Trzyna). Cada concepto del trabajo tiene respaldo citado.

---

## Apéndice: tabla de todas las constantes y su origen

| Constante | Valor | Dónde | Fundamentación |
|-----------|-------|-------|----------------|
| n (trabajos) | 8 (+1 rush) | instancia | Tabla 5 Liu et al. |
| m (máquinas) | 8 | instancia | Tabla 5 Liu et al. |
| h_j (ops/trabajo) | 5 | instancia | chasis, marco, 2 puertas, cubierta |
| t\* (llegada rush) | Cmax0/2 = 191 | metodología | maximiza riqueza del estado F/I/P |
| α (peso Cr) | 0.5 | metrics.py | urgencia media; testeado en sensibilidad |
| β (peso N) | 0.1 | metrics.py | estabilidad; N es grande, peso chico |
| γ1 (peso Ns) | 1.0 | metrics.py | 1 seg desplazamiento = 1 unidad |
| γ2 (peso Nm) | 10.0 | metrics.py | cambio de máquina 10× más caro |
| L (Big-M) | grande | modelo MILP | linealiza disyunciones de secuencia |
| población GA | 120 | scheduler_ga.py | presupuesto de exploración |
| generaciones GA | 300 | scheduler_ga.py | presupuesto de refinamiento |
| torneo k | 3 | scheduler_ga.py | presión selectiva estándar |
| pmut | 0.15 | scheduler_ga.py | tasa de mutación moderada |
| semilla | 0 (inicial) | scheduler_ga.py | reproducibilidad |
| escenarios dataset | 300 | xgboost_selector.py | muestra de entrenamiento |
| features | 14 | xgboost_selector.py | estado del taller sin redundancia |
| n_seeds (mediana GA) | 3 | xgboost_selector.py | reduce ruido de etiquetas |
| rush: ops | 3–5 | rescheduling.py | rango realista |
| rush: máquinas/op | 1–3 | rescheduling.py | flexibilidad realista |
| rush: tiempos | U[30,105] | rescheduling.py | rango empírico Tabla 6 |
| t\* dataset | [0.3,0.7]·Cmax0 | xgboost_selector.py | generalización temporal |
| Cmax0 (resultado) | 382 s | experimento | GA inicial, supera RLEGA 397 |
| CmaxR insert_end | 518 s | experimento | daño = 136 s |
| Cmax cota inferior | 512 s | experimento | óptimo del subproblema |
