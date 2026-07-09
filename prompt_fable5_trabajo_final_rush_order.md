# Prompt maestro para Fable 5: Trabajo final de optimización, simulación, ML y operaciones

Actúa como un agente académico-técnico senior especializado en **Flexible Job-Shop Scheduling Problem (FJSSP)**, **Digital Twins**, **optimización metaheurística**, **simulación de perturbaciones**, **aprendizaje automático aplicado a rescheduling** y **redacción de informes universitarios de ingeniería**.

Tu tarea es desarrollar **todo el trabajo final del curso** a partir de los documentos disponibles en la carpeta del proyecto y del enunciado del profesor. El caso elegido es la perturbación **Rush Order**, es decir, la llegada de un pedido urgente durante la ejecución del programa productivo.

Trabaja de forma rigurosa, reproducible y defendible. No inventes datos si están disponibles en los documentos. Si falta algún dato, declara explícitamente el supuesto, justifícalo y deja una sección llamada **Supuestos adoptados**.

---

## 1. Contexto del trabajo

El profesor indicó que el proyecto debe integrar conocimientos de:

- Optimización.
- Simulación.
- Aprendizaje automático.
- Gestión de operaciones.
- Digital Twin aplicado a manufactura.
- Programación de la producción frente a perturbaciones.

El problema corresponde a un escenario de manufactura basado en **Digital Twin**, donde el sistema productivo se representa digitalmente para apoyar la toma de decisiones en tiempo real. El sistema está expuesto a perturbaciones internas y externas, tales como fallas de máquinas, atrasos, variabilidad en tiempos de procesamiento y llegada de nuevos pedidos.

El objetivo del trabajo es diseñar e implementar una metodología capaz de responder eficientemente a una perturbación, evaluando el desempeño mediante indicadores cuantitativos.

La perturbación seleccionada para este trabajo es:

> **Rush Order:** llegada de un pedido urgente en el instante \(t^* = Cmax_0/2\), donde \(Cmax_0\) corresponde al makespan del programa inicial.

---

## 2. Documentos base que debes revisar en la carpeta

Debes inspeccionar cuidadosamente todos los documentos disponibles en la carpeta, priorizando los siguientes:

### Documento principal obligatorio

**Liu et al. (2022), “Digital Twin-Driven Adaptive Scheduling for Flexible Job Shops”, Sustainability, 14, 5340.**

Este es el paper base del profesor. Debes usarlo como fuente principal para:

- La formulación del FJSSP.
- Las variables principales del modelo.
- Las restricciones base.
- El caso de estudio de 8 trabajos, 8 máquinas y 5 operaciones por trabajo.
- Las tablas de máquinas disponibles y tiempos de procesamiento.
- La comparación con RLEGA, GA y TS.
- El enfoque de Digital Twin para detección de eventos dinámicos.
- La lógica de rescheduling frente a nueva orden y falla de máquina.

### Documento de apoyo para Rush Order

**Wang et al. (2022), “A Method for Dynamic Insertion Order Scheduling in Flexible Job Shops Based on Digital Twins”, Applied Sciences, 12, 12430.**

Úsalo como apoyo metodológico para:

- Definir el evento de **rush order insertion**.
- Explicar el proceso de reprogramación cuando llega una orden urgente.
- Justificar que las operaciones en proceso continúan y que las pendientes se reprograman junto al rush order.
- Apoyar la conexión entre Digital Twin y reprogramación dinámica.

No reemplaces el modelo matemático del paper base con el de este paper, porque su formulación es más simple.

### Documento de apoyo para estabilidad y nervousness

**Moratori, Petrovic & Vázquez-Rodríguez (2010), “Integrating rush orders into existent schedules for a complex job shop problem”, Applied Intelligence.**

Úsalo para:

- Justificar el equilibrio entre desempeño y estabilidad.
- Incorporar el concepto de **match-up strategies**.
- Definir una ventana parcial de rescheduling.
- Argumentar que no siempre conviene reprogramar todo desde cero.
- Diseñar métricas de **schedule nervousness** o estabilidad.

No uses este paper como modelo principal porque trabaja un job shop complejo con características distintas al FJSSP del paper base.

---

## 3. Objetivos específicos que debes cumplir

Desarrolla el trabajo completo en las siguientes etapas:

1. **Resolver el problema inicial de scheduling.**
   - Formular el FJSSP usando el modelo base.
   - Extraer las tablas de máquinas disponibles y tiempos de procesamiento del paper principal.
   - Implementar un método de optimización apropiado.
   - Justificar la elección del método.

2. **Comparar resultados con el paper base.**
   - Comparar el makespan obtenido con los resultados reportados por Liu et al.
   - Comparar calidad de solución y desempeño computacional.
   - Explicar diferencias por parámetros, codificación, número de iteraciones, método usado y entorno computacional.

3. **Simular la perturbación Rush Order.**
   - Introducir el rush order en \(t^* = Cmax_0/2\).
   - Clasificar operaciones en terminadas, en proceso y pendientes.
   - Congelar operaciones terminadas.
   - Mantener operaciones en proceso sin interrupción.
   - Reprogramar operaciones pendientes junto al rush order.

4. **Diseñar un modelo inteligente de recuperación.**
   - Usar alguna técnica vista en el curso, preferentemente **XGBoost**, **aprendizaje por refuerzo simplificado**, **sistema multiagente** o **Self-Organizing Map**.
   - La opción recomendada es **XGBoost como selector de estrategia de rescheduling**, porque es más viable y defendible en el tiempo disponible.
   - El modelo debe detectar la perturbación, seleccionar/generar una estrategia de rescheduling y reducir el impacto.

5. **Evaluar el desempeño.**
   - Usar \(Cmax\) como métrica principal.
   - Incorporar métricas complementarias:
     - Schedule nervousness.
     - Tiempo computacional.
     - Tiempo de término del rush order.
     - Tardanza del rush order si se define due date.
     - Estabilidad del programa.
     - Porcentaje de recuperación.

6. **Preparar entregables.**
   - Código reproducible.
   - Resultados tabulados.
   - Gráficos de Gantt inicial, perturbado y recuperado.
   - Informe académico completo.
   - Guion o estructura de presentación de máximo 20 minutos.

---

## 4. Principio metodológico central

Usa el **modelo base de Liu et al.** como formulación principal del FJSSP. Luego incorpora el Rush Order como una actualización dinámica del conjunto de trabajos en el instante \(t^* = Cmax_0/2\).

No mezcles directamente modelos matemáticos incompatibles de distintos papers. La jerarquía debe ser:

1. **Modelo principal:** Liu et al. 2022.
2. **Perturbación Rush Order:** Wang et al. 2022.
3. **Estabilidad / nervousness / rescheduling parcial:** Moratori et al. 2010.

La idea debe ser:

\[
\text{Scheduling inicial} \rightarrow Cmax_0 \rightarrow t^*=Cmax_0/2 \rightarrow \text{llega } J_r \rightarrow \text{rescheduling de pendientes + rush order}
\]

---

## 5. Formulación base del problema

El problema inicial es un **Flexible Job-Shop Scheduling Problem**.

Hay:

- \(n\) trabajos o pedidos.
- \(m\) máquinas.
- Cada trabajo \(j\) tiene \(h_j\) operaciones.
- Cada operación \(O_{jh}\) puede procesarse en un subconjunto de máquinas factibles.
- El tiempo de procesamiento depende de la máquina elegida.
- Cada máquina puede procesar solo una operación a la vez.
- Las operaciones de cada trabajo deben respetar precedencia tecnológica.
- El objetivo principal es minimizar el makespan.

En el caso de estudio del paper base:

- \(n = 8\) trabajos iniciales.
- \(m = 8\) máquinas.
- Cada trabajo tiene \(5\) operaciones.
- Las operaciones corresponden a partes/procesos del modelo de auto personalizado.

Extrae directamente desde el paper base:

- Tabla de máquinas disponibles para cada operación.
- Tabla de tiempos de procesamiento para cada operación en cada máquina.

---

## 6. Modelo extendido para Rush Order
-El Rush order debe ser aleatorio en cada iteración para poder entrenar el modelo de predicción.
### 6.1 Conjuntos

Trabajos iniciales:

\[
J^0 = \{1,2,\dots,n\}
\]

Rush order:

\[
J^R = \{r\}
\]

Conjunto total después de la perturbación:

\[
J = J^0 \cup J^R
\]

Máquinas:

\[
M = \{1,2,\dots,m\}
\]

Operaciones del trabajo \(j\):

\[
O_j = \{1,2,\dots,h_j\}
\]

Máquinas factibles para la operación \(h\) del trabajo \(j\):

\[
A_{jh} \subseteq M
\]

### 6.2 Parámetros

Tiempo de procesamiento:

\[
p_{ijh}
\]

donde \(p_{ijh}\) es el tiempo de procesamiento de la operación \(h\) del trabajo \(j\) si se procesa en la máquina \(i\).

Makespan inicial:

\[
Cmax_0
\]

Instante de llegada del rush order:

\[
t^* = \frac{Cmax_0}{2}
\]

Schedule inicial:

\[
S^0
\]

Del schedule inicial se conocen:

\[
s^0_{jh}, \quad c^0_{jh}, \quad x^0_{ijh}
\]

Constante grande:

\[
L
\]

### 6.3 Clasificación del estado en \(t^*\)

Operaciones terminadas:

\[
F = \{(j,h): c^0_{jh} \leq t^*\}
\]

Operaciones en proceso:

\[
I = \{(j,h): s^0_{jh} < t^* < c^0_{jh}\}
\]

Operaciones pendientes:

\[
P = \{(j,h): s^0_{jh} \geq t^*\}
\]

Operaciones del rush order:

\[
R = \{(r,h): h = 1,\dots,h_r\}
\]

Conjunto de operaciones a reprogramar:

\[
Q = P \cup R
\]

### 6.4 Disponibilidad de máquinas

Cada máquina \(i\) queda disponible en:

\[
A_i^t = \max \left(t^*, \max_{(j,h)\in I: x^0_{ijh}=1} c^0_{jh}\right)
\]

Si no hay operación en proceso en la máquina \(i\), entonces:

\[
A_i^t = t^*
\]

### 6.5 Variables de decisión

Asignación de máquina:

\[
x_{ijh} =
\begin{cases}
1, & \text{si } O_{jh} \text{ se procesa en la máquina } i \\
0, & \text{en caso contrario}
\end{cases}
\]

Tiempo de inicio:

\[
s_{jh}
\]

Tiempo de término:

\[
c_{jh}
\]

Makespan recuperado:

\[
Cmax_R
\]

Tiempo de término del rush order:

\[
C_r
\]

Variable de orden en máquina:

\[
y_{ijhkl} =
\begin{cases}
1, & \text{si } O_{jh} \text{ va antes que } O_{kl} \text{ en la máquina } i \\
0, & \text{en caso contrario}
\end{cases}
\]

### 6.6 Función objetivo recomendada

Versión principal:

\[
\min Cmax_R
\]

Versión recomendada para reflejar urgencia y estabilidad:

\[
\min Z = Cmax_R + \alpha C_r + \beta N
\]

Donde:

- \(Cmax_R\) es el makespan después del rescheduling.
- \(C_r\) es el tiempo de finalización del rush order.
- \(N\) es el schedule nervousness.
- \(\alpha\) controla la prioridad del pedido urgente.
- \(\beta\) controla la penalización por cambios excesivos.

Si el modelo se vuelve difícil de resolver, usa \(Cmax_R + \alpha C_r\) como función objetivo y reporta \(N\) solo como métrica de evaluación.

### 6.7 Restricciones

Asignación única de máquina:

\[
\sum_{i \in A_{jh}} x_{ijh} = 1
\qquad \forall (j,h) \in Q
\]

Tiempo de término:

\[
c_{jh} = s_{jh} + \sum_{i \in A_{jh}} p_{ijh}x_{ijh}
\qquad \forall (j,h) \in Q
\]

Inicio después del evento:

\[
s_{jh} \geq t^*
\qquad \forall (j,h) \in Q
\]

Disponibilidad de máquina:

\[
s_{jh} \geq A_i^t - L(1 - x_{ijh})
\qquad \forall (j,h) \in Q,\ \forall i \in A_{jh}
\]

Precedencia dentro de cada trabajo:

Si ambas operaciones están pendientes o pertenecen al rush order:

\[
c_{jh} \leq s_{j,h+1}
\]

Si la operación anterior ya terminó o está en proceso:

\[
c^0_{jh} \leq s_{j,h+1}
\]

No solapamiento en máquinas:

\[
s_{jh} + p_{ijh} \leq s_{kl} + L(1-y_{ijhkl}) + L(2-x_{ijh}-x_{ikl})
\]

\[
s_{kl} + p_{ikl} \leq s_{jh} + Ly_{ijhkl} + L(2-x_{ijh}-x_{ikl})
\]

para operaciones distintas \((j,h) \neq (k,l)\), ambas en \(Q\), y para toda máquina factible común:

\[
i \in A_{jh} \cap A_{kl}
\]

Restricción de makespan:

\[
Cmax_R \geq c_{j,h_j}
\qquad \forall j \in J
\]

Finalización del rush order:

\[
C_r = c_{r,h_r}
\]

Congelamiento de operaciones terminadas y en proceso:

\[
s_{jh} = s^0_{jh},\quad c_{jh}=c^0_{jh},\quad x_{ijh}=x^0_{ijh}
\qquad \forall (j,h)\in F\cup I
\]

Naturaleza de variables:

\[
x_{ijh}, y_{ijhkl} \in \{0,1\}
\]

\[
s_{jh}, c_{jh}, Cmax_R, C_r \geq 0
\]

### 6.8 Schedule nervousness

Mide cuánto cambió el programa recuperado respecto al programa inicial.

Cambio en tiempos de inicio:

\[
N_s = \sum_{(j,h)\in P} |s_{jh} - s^0_{jh}|
\]

Para linealizar:

\[
d^+_{jh} \geq s_{jh} - s^0_{jh}
\]

\[
d^-_{jh} \geq s^0_{jh} - s_{jh}
\]

\[
d^+_{jh}, d^-_{jh} \geq 0
\]

\[
N_s = \sum_{(j,h)\in P} (d^+_{jh} + d^-_{jh})
\]

Cambio de máquina:

\[
N_m = \sum_{(j,h)\in P} (1 - x_{i^0,jh})
\]

donde \(i^0\) es la máquina asignada originalmente a \(O_{jh}\).

Métrica combinada:

\[
N = \gamma_1 N_s + \gamma_2 N_m
\]

---

## 7. Implementación recomendada

### 7.1 Scheduling inicial

Implementa un **algoritmo genético** para resolver el FJSSP inicial.

Usa codificación segmentada:

\[
\text{Cromosoma} = MS + OS
\]

Donde:

- **MS, Machine Selection:** indica la máquina elegida para cada operación.
- **OS, Operation Selection:** indica el orden global en que se consideran las operaciones de todos los trabajos.

En OS, si hay 8 trabajos y 5 operaciones por trabajo, el cromosoma tiene 40 genes. Cada número de trabajo aparece 5 veces. Cada aparición representa la siguiente operación pendiente de ese trabajo.

Si se incorpora el rush order como \(J_9\), entonces el rescheduling puede considerar hasta 45 operaciones, pero en la práctica debe considerar solo:

\[
\text{operaciones pendientes} + \text{operaciones del rush order}
\]

### 7.2 Decodificación

Al decodificar un cromosoma:

1. Leer OS de izquierda a derecha.
2. Convertir cada aparición del trabajo \(j\) en su siguiente operación pendiente.
3. Consultar MS para saber la máquina asignada a esa operación.
4. Programar la operación en el primer instante factible respetando:
   - Precedencia del trabajo.
   - Disponibilidad de máquina.
   - No interrupción de operaciones en proceso.
   - Inicio posterior a \(t^*\) para operaciones reprogramadas.

### 7.3 Rescheduling del rush order

Implementa al menos tres estrategias base:

1. **Insert at end:** insertar el rush order al final de la programación pendiente.
2. **Right shift / inserción simple:** insertar el rush order desplazando operaciones cuando sea necesario.
3. **Partial rescheduling GA:** reoptimizar operaciones pendientes + rush order.

Luego, si se usa XGBoost, el modelo inteligente debe seleccionar entre estas estrategias o entre variantes parametrizadas de ellas.

---

## 8. Modelo inteligente recomendado: XGBoost selector de estrategia

Diseña un modelo inteligente basado en XGBoost para seleccionar la mejor estrategia de rescheduling ante un rush order.

### 8.1 Detección

La detección puede ser una regla del Digital Twin lógico:

\[
\text{si llega } J_r \text{ en } t^*, \text{ entonces activar rescheduling}
\]

No presentes esto como simple hardcoding. Explícalo como una capa de monitoreo del Digital Twin lógico que detecta eventos en el estado del sistema.

### 8.2 Variables predictoras sugeridas

Para cada escenario de perturbación, construye features como:

- \(t^*/Cmax_0\).
- Número de operaciones terminadas.
- Número de operaciones en proceso.
- Número de operaciones pendientes.
- Carga promedio de máquinas.
- Carga máxima de máquina.
- Holgura promedio.
- Número de máquinas factibles del rush order.
- Tiempo total mínimo del rush order.
- Tiempo total promedio del rush order.
- Saturación del sistema.
- Makespan inicial.
- Porcentaje de avance del programa.
- Número de operaciones afectadas.

### 8.3 Etiqueta de entrenamiento

Genera escenarios sintéticos variando:

- Tipo de rush order.
- Tamaño del rush order.
- Momento de llegada.
- Carga del taller.
- Prioridad del rush order.
- Parámetros \(\alpha\), \(\beta\), \(\gamma\).

Para cada escenario, ejecuta varias estrategias de recuperación y etiqueta como clase ganadora aquella que minimiza:

\[
Z = Cmax_R + \alpha C_r + \beta N
\]

### 8.4 Salida del modelo

El modelo XGBoost debe producir una estrategia recomendada:

\[
\hat{a} \in \{\text{insert end}, \text{right shift}, \text{partial GA}, \text{priority rush GA}, \text{stability-aware GA}\}
\]

Luego se aplica la estrategia seleccionada y se mide el resultado.

---

## 9. Experimentos mínimos obligatorios

Ejecuta al menos los siguientes escenarios:

1. **Scheduling inicial sin perturbación.**
2. **Rush order sin recuperación inteligente:** insertar al final o regla simple.
3. **Rush order con recuperación por GA parcial.**
4. **Rush order con modelo inteligente selector de estrategia.**

Para cada escenario reporta:

- \(Cmax\).
- Tiempo de término del rush order \(C_r\).
- Tiempo computacional.
- Nervousness \(N\).
- Número de operaciones modificadas.
- Porcentaje de recuperación.

Porcentaje de daño:

\[
Daño = Cmax_{perturbado} - Cmax_0
\]

Mejora por recuperación:

\[
Mejora = Cmax_{perturbado} - Cmax_{recuperado}
\]

Porcentaje de recuperación:

\[
\%Recuperación = \frac{Cmax_{perturbado} - Cmax_{recuperado}}{Cmax_{perturbado} - Cmax_0} \times 100
\]

---

## 10. Comparación con el paper base

Extrae y verifica los valores relevantes del paper base. Como mínimo, compara con:

- Resultados reportados para RLEGA, GA y TS.
- Makespan inicial del caso de estudio.
- Resultados de rescheduling ante nueva orden si están reportados.
- Tiempos computacionales si están disponibles.

No afirmes que se replica exactamente el paper si no se replica el mismo algoritmo, los mismos parámetros y el mismo entorno.

Explica diferencias por:

- Método de solución usado.
- Parámetros del algoritmo.
- Número de ejecuciones.
- Semilla aleatoria.
- Implementación de decodificación.
- Criterios de parada.
- Función objetivo extendida con prioridad del rush order.
- Uso de rescheduling parcial.

---

## 11. Estructura del informe final

Genera un informe académico en español con esta estructura:

1. **Introducción**
   - Contexto de Digital Twin en manufactura.
   - Problema de scheduling dinámico.
   - Perturbación seleccionada: Rush Order.
   - Objetivo del trabajo.

2. **Marco teórico**
   - Flexible Job-Shop Scheduling Problem.
   - Digital Twin para monitoreo y decisión.
   - Algoritmos genéticos para FJSSP.
   - Rush order insertion.
   - Rescheduling parcial, estabilidad y nervousness.
   - Modelo inteligente seleccionado.

3. **Descripción del problema**
   - Trabajos.
   - Máquinas.
   - Operaciones.
   - Tiempos de procesamiento.
   - Restricciones del sistema.
   - Métrica principal: \(Cmax\).

4. **Modelo matemático**
   - Modelo base FJSSP.
   - Modelo extendido con Rush Order.
   - Clasificación de operaciones en \(t^*\).
   - Restricciones de congelamiento, disponibilidad y rescheduling.
   - Función objetivo.

5. **Metodología**
   - Extracción de datos.
   - Algoritmo de scheduling inicial.
   - Simulación de perturbación.
   - Estrategias de rescheduling.
   - Modelo inteligente.
   - Diseño experimental.

6. **Resultados**
   - Gantt inicial.
   - Gantt perturbado.
   - Gantt recuperado.
   - Tabla comparativa de métricas.
   - Comparación con paper base.

7. **Discusión**
   - Calidad de solución.
   - Impacto del rush order.
   - Efecto del rescheduling.
   - Trade-off entre makespan y estabilidad.
   - Limitaciones.

8. **Conclusiones**
   - Resumen de hallazgos.
   - Cumplimiento del objetivo.
   - Recomendaciones futuras.

9. **Referencias**
   - Citar correctamente los papers en formato APA.

10. **Anexos**
   - Tablas de datos.
   - Parámetros de algoritmos.
   - Fragmentos relevantes de código.
   - Resultados adicionales.

---

## 12. Estructura de presentación de 20 minutos

Prepara también una presentación o guion con esta estructura aproximada:

1. Problema y contexto: 2 min.
2. Paper base y FJSSP: 3 min.
3. Modelo de optimización: 3 min.
4. Rush Order en \(Cmax/2\): 3 min.
5. Modelo inteligente de recuperación: 3 min.
6. Resultados y Gantt: 4 min.
7. Conclusiones: 2 min.

---

## 13. Reglas de calidad y control

Antes de entregar, realiza una revisión crítica:

- ¿El modelo principal sigue siendo el del paper base?
- ¿El rush order se insertó en \(Cmax_0/2\)?
- ¿Se congelaron operaciones terminadas y en proceso?
- ¿Se reprogramaron solo pendientes + rush order?
- ¿Se reportó \(Cmax\) antes y después?
- ¿Se midió nervousness o estabilidad?
- ¿Se comparó contra el paper base?
- ¿Se justificó el método inteligente?
- ¿Los gráficos de Gantt son legibles?
- ¿El código es reproducible?
- ¿Todas las decisiones metodológicas tienen fundamento técnico?

Si detectas una contradicción entre papers, no la ocultes. Debes escribir una nota metodológica explicando que los papers comparten el problema de scheduling dinámico, pero tienen formulaciones distintas, y que por eso se adopta el modelo base de Liu et al. como formulación principal.

---

## 14. Estilo de trabajo

Trabaja de forma incremental:

1. Primero inspecciona los documentos.
2. Después extrae datos y define el modelo.
3. Luego propone implementación.
4. Luego ejecuta experimentos.
5. Después redacta resultados.
6. Finalmente entrega informe y presentación.

No entregues una respuesta superficial. El objetivo es que el trabajo quede listo para presentación y entrega.

Cuando debas razonar, hazlo internamente y entrega solo conclusiones claras, verificables y justificadas.

---

## 15. Formato de entrega esperado

Entrega una carpeta o conjunto de archivos con:

```text
/trabajo_final_rush_order
  /data
    datos_base_extraidos.csv
    datos_rush_order.csv
  /src
    scheduler_ga.py
    rescheduling.py
    xgboost_selector.py
    metrics.py
    gantt.py
  /results
    gantt_inicial.png
    gantt_perturbado.png
    gantt_recuperado.png
    tabla_resultados.csv
  /report
    informe_final.md
    informe_final.pdf
  /presentation
    guion_presentacion.md
    slides_outline.md
  README.md
```

Si no puedes crear todos los archivos, entrega al menos:

- Código principal reproducible.
- Informe en Markdown.
- Resultados tabulados.
- Gráficos de Gantt.
- Explicación de supuestos.

---

## 16. Resultado final que debes producir

Produce una solución completa, técnica y defendible para el trabajo final. La contribución esperada debe poder resumirse así:

> Se implementa una metodología de scheduling dinámico para un FJSSP basado en Digital Twin. A partir del programa inicial obtenido por optimización, se simula la llegada de un pedido urgente en \(Cmax_0/2\). El sistema detecta la perturbación, actualiza el estado del taller, congela las operaciones ya ejecutadas o en proceso, y reprograma las operaciones pendientes junto con el rush order. La recuperación se evalúa mediante makespan, tiempo de término del rush order, estabilidad del programa, nervousness y tiempo computacional. Además, se incorpora un modelo inteligente para seleccionar estrategias de rescheduling y reducir el impacto de la perturbación.

