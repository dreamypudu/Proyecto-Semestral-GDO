# Marco metodológico: fundamentos teóricos de los experimentos

Este documento desarrolla la teoría detrás de cada decisión metodológica del trabajo: por qué el problema se modela como FJSSP, por qué se resuelve con un algoritmo genético, por qué el rescheduling es parcial y orientado a estabilidad, y por qué el modelo inteligente es un selector de estrategias basado en predicción de costo. Cada sección cierra con la conexión explícita a nuestra implementación.

---

## 1. El problema: Flexible Job-Shop Scheduling (FJSSP)

El *job shop* clásico programa n trabajos, cada uno con una secuencia fija de operaciones, sobre m máquinas, donde cada operación tiene una máquina predeterminada. El **FJSSP** (Brucker & Schlie, 1990) lo generaliza: cada operación puede ejecutarse en un *subconjunto* de máquinas factibles, con tiempo dependiente de la máquina. Esto agrega a la decisión de **secuenciamiento** (orden en cada máquina) una decisión de **ruteo** (asignación operación→máquina).

El job shop con 3 máquinas ya es NP-duro (Garey, Johnson & Sethi, 1976), y el FJSSP lo contiene como caso particular, de modo que no se conocen algoritmos exactos eficientes para instancias generales. Los benchmarks clásicos del problema (Brandimarte, 1993) consolidaron el uso de metaheurísticas como enfoque estándar. La instancia de este trabajo (8 trabajos × 8 máquinas × 5 operaciones, flexibilidad de 1–4 máquinas por operación) proviene del caso de laboratorio de Liu et al. (2022).

**En nuestro trabajo:** el modelo matemático (asignación única, precedencia, no solapamiento disyuntivo, min Cmax) sigue la formulación del paper base; ver informe §4.

## 2. Espacio de soluciones: schedules semi-activos y activos

Dado un orden de operaciones y una asignación de máquinas, aún hay libertad en los tiempos de inicio. Un schedule es **semi-activo** si ninguna operación puede adelantarse sin alterar el orden; es **activo** si ninguna operación puede adelantarse ni siquiera saltando a un hueco ocioso anterior de su máquina sin retrasar a otra. El óptimo de makespan siempre está en el conjunto de schedules activos, que es subconjunto estricto de los semi-activos (Giffler & Thompson, 1960); por eso los decodificadores que insertan en huecos ("gap insertion") exploran un espacio mejor.

**En nuestro trabajo:** el decodificador `earliest_start` programa cada operación en el primer hueco factible de su máquina — genera schedules activos. Esta es la explicación técnica de que nuestro GA alcance Cmax₀ = 382 frente al 397 del RLEGA del paper (que no reporta su esquema de decodificación): no es evidencia de un mejor optimizador, sino posiblemente de un mejor decodificador.

## 3. Algoritmos genéticos para FJSSP

Los algoritmos genéticos (Holland, 1975) evolucionan una población de soluciones codificadas mediante selección, cruce y mutación. Para FJSSP, la codificación dominante en la literatura es la de **dos segmentos MS+OS** (Gao, Sun & Gen, 2008; Zhang, Gao & Shi, 2011): MS (*machine selection*) fija el ruteo y OS (*operation sequence*) es una permutación con repetición de números de trabajo — representación que garantiza factibilidad de precedencia por construcción, porque la k-ésima aparición del trabajo j siempre denota su k-ésima operación. El cruce **POX** (*precedence-preserving order-based crossover*; Zhang et al., 2011) hereda las posiciones de un subconjunto de trabajos de un padre y completa con el orden relativo del otro, preservando la validez de la codificación sin reparaciones.

La elección de un GA frente a otras metaheurísticas se justifica aquí por tres razones: (i) es el método de referencia del propio paper base (RLEGA es un GA mejorado con aprendizaje por refuerzo), lo que hace la comparación interpretable; (ii) la codificación MS+OS acomoda de forma natural el subproblema de rescheduling (basta restringir las operaciones y el estado inicial); (iii) su función de fitness es intercambiable, lo que permite implementar las variantes con prioridad y con estabilidad **sin cambiar el motor de búsqueda**.

**En nuestro trabajo:** `ga()` en `src/scheduler_ga.py`, con torneo k=3, POX, cruce uniforme en MS, mutación de reasignación/intercambio y elitismo.

## 4. Scheduling dinámico y rescheduling

En producción real el programa se ejecuta en un entorno estocástico. La literatura de *rescheduling* (Vieira, Herrmann & Lin, 2003; Ouelhadj & Petrovic, 2009) organiza el campo en tres dimensiones:

- **Entorno**: qué perturbaciones ocurren (fallas, órdenes nuevas, variación de tiempos). La llegada de una orden urgente es una de las perturbaciones canónicas.
- **Política**: *periódica* (reprogramar cada Δt), *dirigida por eventos* (reprogramar cuando algo ocurre) o *híbrida*. La detección por Digital Twin corresponde a una política dirigida por eventos.
- **Método**: *reparación del schedule* (ajustes locales: right-shift, inserción) vs *regeneración total* (resolver de nuevo). La reparación es más rápida y estable; la regeneración puede lograr mejor desempeño a costa de perturbar todo.

Nuestro menú de estrategias recorre exactamente ese espectro: `insert_end` y `right_shift` son reparaciones locales; `partial_ga`, `priority_ga` y `stability_ga` son regeneraciones **parciales** (solo operaciones pendientes + rush), el punto intermedio recomendado por esta literatura.

**En nuestro trabajo:** clasificación del estado en t\* (terminadas/en proceso/pendientes), congelamiento y las 5 estrategias en `src/rescheduling.py`.

## 5. Estabilidad, nervousness y match-up

Reprogramar tiene un costo oculto: cada cambio de horario o de máquina invalida decisiones aguas abajo (materiales, personal, compromisos). Wu, Storer & Chang (1993) formalizaron el rescheduling **biobjetivo** — eficiencia (makespan) *y* estabilidad (desviación respecto del plan original) — y mostraron que pequeños sacrificios de makespan compran grandes ganancias de estabilidad. La estrategia **match-up** (Bean, Birge, Mittenthal & Noon, 1991) reprograma solo dentro de una ventana temporal hasta "reengancharse" con el plan original. Para el caso específico de órdenes urgentes en job shops complejos, Moratori, Petrovic & Vázquez-Rodríguez (2010) muestran que las políticas que restringen los cambios logran calidad comparable a la reoptimización total con mucho menor perturbación.

La métrica de **nervousness** operacionaliza la estabilidad. Usamos la forma aditiva estándar: N = γ₁·Σ|Δinicio| + γ₂·(cambios de máquina), con γ₂ = 10 expresando que un cambio de asignación es un evento organizacionalmente más disruptivo que un desplazamiento temporal pequeño.

**En nuestro trabajo:** `src/metrics.py`; la función objetivo extendida Z = Cmax + α·Cr + β·N con α=0.5, β=0.1 pondera las tres dimensiones (desempeño global, urgencia del rush, estabilidad). El hallazgo empírico central — que la política estable es casi inmejorable bajo Z en esta instancia — es una confirmación cuantitativa del argumento de Wu et al. y Moratori et al.

## 6. Digital Twin en manufactura

El Digital Twin (Grieves & Vickers, 2017) es una réplica virtual de un sistema físico sincronizada con su estado real. En sistemas de producción (Negri, Fumagalli & Macchi, 2017; Tao, Zhang, Liu & Nee, 2019), habilita el ciclo *sensar → detectar evento → decidir → actuar*: el gemelo mantiene el estado del taller (avance de cada operación, disponibilidad de máquinas, cola de pedidos) y ante un evento dinámico dispara el mecanismo de decisión. Liu et al. (2022) y Wang et al. (2022) aplican este ciclo al scheduling dinámico de job shops flexibles: el gemelo detecta la inserción de una orden y activa el rescheduling con el estado real congelado.

**En nuestro trabajo:** al no existir planta física, el Digital Twin se implementa en su capa *lógica*: el estado del taller es el schedule en ejecución simulada, y la detección del evento es una regla sobre el sistema de pedidos (llega J9 en t\* → clasificar estado → decidir). Es una simplificación declarada: el aporte del trabajo está en el mecanismo de decisión, no en la sincronización física.

## 7. Selección de estrategias con aprendizaje automático

### 7.1 El problema de selección de algoritmos

Elegir qué método aplicar según las características de la instancia es el *algorithm selection problem* (Rice, 1976): aprender una función `features(instancia) → algoritmo` que minimice el costo esperado. Su versión moderna con ML es un área establecida (Kerschke, Hoos, Neumann & Trautmann, 2019), y su aplicación al scheduling dinámico — aprender qué regla o estrategia de despacho usar según el estado del taller — tiene una tradición larga (Priore, Gómez, Pino & Rosillo, 2014). Nuestro selector es una instancia exacta de este marco: las "instancias" son estados del taller al llegar un rush order, los "algoritmos" son las 5 estrategias, y el costo es Z.

### 7.2 XGBoost

XGBoost (Chen & Guestrin, 2016) es gradient boosting de árboles de decisión con regularización. Se eligió por las razones habituales en datos tabulares pequeños: buen desempeño sin ingeniería de features intensiva, robustez a escalas y colinealidad, importancia de variables interpretable, e inferencia en microsegundos (compatible con decisión en línea).

### 7.3 Clasificación vs. predicción de costo: la decisión metodológica central

La formulación ingenua es un **clasificador** de la estrategia ganadora. Tiene dos problemas teóricos que nuestros datos exhibieron con claridad:

1. **Desbalance de clases** (He & Garcia, 2009): la estrategia estable gana el 72.7% de los escenarios. Un clasificador tiende al colapso mayoritario; el remedio estándar (re-ponderar clases) fuerza sensibilidad hacia las clases raras.
2. **Pérdida de la estructura de costos** (Elkan, 2001): clasificar trata todos los errores como iguales, pero equivocarse cuando las estrategias están casi empatadas cuesta ~0, y equivocarse cuando la brecha es grande cuesta mucho. El re-ponderado balanceado *agrava* esto: compra aciertos baratos en clases raras pagando errores caros en la mayoritaria. Empíricamente: clasificador balanceado Z=751.4 vs baseline trivial 740.1.

La formulación correcta según la teoría de decisión es **sensible al costo**: aprender el costo esperado de cada acción y elegir el argmin — exactamente la receta de Elkan (2001) para decisiones óptimas bajo costos asimétricos. Nuestro regresor (estado ⊕ estrategia → Z) implementa esto; empíricamente iguala al baseline (740.1) y nunca queda por debajo, porque solo se desvía de la política dominante cuando predice ventaja.

### 7.4 Baselines y oráculo

Toda evaluación de un selector requiere dos referencias (Kerschke et al., 2019): el **single best solver** (aquí, "siempre stability_ga" — el baseline trivial pero fuerte) y el **oráculo/virtual best** (la mejor estrategia por escenario — cota inferior inalcanzable). La *brecha* entre ambos (aquí 2.2 puntos de Z, 0.3%) mide cuánto valor puede aportar como máximo cualquier selector: si es pequeña, ningún método de selección — por sofisticado que sea — puede ganar mucho. Reportar esta brecha es lo que distingue una validación honesta de una tabla de accuracy.

**En nuestro trabajo:** `evaluate()` en `src/xgboost_selector.py` reporta las cuatro políticas (oráculo, baseline, selector, clasificador descartado) sobre el mismo conjunto de test.

## 8. Metodología experimental

Los principios que gobiernan el diseño de los experimentos:

- **Datos de instancia reales, escenarios sintéticos controlados.** La instancia base proviene del paper (nada inventado); la variabilidad para entrenar (rush aleatorio, t\* variable, 5 programas base) se genera con distribuciones declaradas, porque el problema de aprender un selector requiere muchos escenarios y el caso canónico es uno solo.
- **Reproducibilidad por semillas.** Todos los generadores aleatorios (GA, escenarios, XGBoost, split) usan semillas fijas; cualquier número del informe se regenera con `python run_experiments.py`.
- **Verificación por invariantes.** Cada módulo incluye asserts ejecutables de las propiedades que definen una solución válida: precedencia, no solapamiento, congelamiento intacto, inicio ≥ t\*. Esto valida *factibilidad* por construcción; la *optimalidad* se valida donde es posible mediante cotas inferiores aritméticas (Cr ≥ t\* + cadena mínima del rush).
- **Evaluación pareada.** Todas las políticas se evalúan sobre los mismos escenarios de test, de modo que las comparaciones son diferencias pareadas y no dependen de la escala absoluta de Z.
- **Separación entrenamiento/prueba estratificada** (70/30) para las cifras de validación; el modelo desplegado se re-entrena con todos los datos (práctica estándar).

Las limitaciones de este diseño (una sola instancia base, ruido de etiquetado del GA, un solo split sin intervalos de confianza, posible fuga por programas base compartidos) están auditadas en detalle en `logica_experimento.md`, Parte II.

## 9. Referencias

- Bean, J. C., Birge, J. R., Mittenthal, J., & Noon, C. E. (1991). Matchup scheduling with multiple resources, release dates and disruptions. *Operations Research, 39*(3), 470–483.
- Brandimarte, P. (1993). Routing and scheduling in a flexible job shop by tabu search. *Annals of Operations Research, 41*(3), 157–183.
- Brucker, P., & Schlie, R. (1990). Job-shop scheduling with multi-purpose machines. *Computing, 45*(4), 369–375.
- Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. En *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (pp. 785–794).
- Elkan, C. (2001). The foundations of cost-sensitive learning. En *Proceedings of the 17th International Joint Conference on Artificial Intelligence (IJCAI)* (pp. 973–978).
- Garey, M. R., Johnson, D. S., & Sethi, R. (1976). The complexity of flowshop and jobshop scheduling. *Mathematics of Operations Research, 1*(2), 117–129.
- Gao, J., Sun, L., & Gen, M. (2008). A hybrid genetic and variable neighborhood descent algorithm for flexible job shop scheduling problems. *Computers & Operations Research, 35*(9), 2892–2907.
- Giffler, B., & Thompson, G. L. (1960). Algorithms for solving production-scheduling problems. *Operations Research, 8*(4), 487–503.
- Grieves, M., & Vickers, J. (2017). Digital twin: Mitigating unpredictable, undesirable emergent behavior in complex systems. En F.-J. Kahlen, S. Flumerfelt, & A. Alves (Eds.), *Transdisciplinary Perspectives on Complex Systems* (pp. 85–113). Springer.
- He, H., & Garcia, E. A. (2009). Learning from imbalanced data. *IEEE Transactions on Knowledge and Data Engineering, 21*(9), 1263–1284.
- Holland, J. H. (1975). *Adaptation in Natural and Artificial Systems*. University of Michigan Press.
- Kerschke, P., Hoos, H. H., Neumann, F., & Trautmann, H. (2019). Automated algorithm selection: Survey and perspectives. *Evolutionary Computation, 27*(1), 3–45.
- Liu, Z., Wang, Y., Liang, X., & Ma, Y. (2022). Digital twin-driven adaptive scheduling for flexible job shops. *Sustainability, 14*(9), 5340.
- Moratori, P., Petrovic, S., & Vázquez-Rodríguez, J. A. (2010). Integrating rush orders into existent schedules for a complex job shop problem. *Applied Intelligence, 32*(2), 205–215.
- Negri, E., Fumagalli, L., & Macchi, M. (2017). A review of the roles of digital twin in CPS-based production systems. *Procedia Manufacturing, 11*, 939–948.
- Ouelhadj, D., & Petrovic, S. (2009). A survey of dynamic scheduling in manufacturing systems. *Journal of Scheduling, 12*(4), 417–431.
- Priore, P., Gómez, A., Pino, R., & Rosillo, R. (2014). Dynamic scheduling of manufacturing systems using machine learning: An updated review. *Artificial Intelligence for Engineering Design, Analysis and Manufacturing, 28*(1), 83–97.
- Rice, J. R. (1976). The algorithm selection problem. *Advances in Computers, 15*, 65–118.
- Tao, F., Zhang, H., Liu, A., & Nee, A. Y. C. (2019). Digital twin in industry: State-of-the-art. *IEEE Transactions on Industrial Informatics, 15*(4), 2405–2415.
- Vieira, G. E., Herrmann, J. W., & Lin, E. (2003). Rescheduling manufacturing systems: A framework of strategies, policies, and methods. *Journal of Scheduling, 6*(1), 39–62.
- Wang, J., Liu, Y., Ren, S., Wang, C., & Wang, W. (2022). A method for dynamic insertion order scheduling in flexible job shops based on digital twins. *Applied Sciences, 12*(23), 12430.
- Wu, S. D., Storer, R. H., & Chang, P. C. (1993). One-machine rescheduling heuristics with efficiency and stability as criteria. *Computers & Operations Research, 20*(1), 1–14.

> Nota: las referencias corresponden a literatura clásica y consolidada de cada área, citada de memoria del asistente; antes de usarlas en la bibliografía formal del informe conviene verificar volúmenes y páginas contra la fuente original (p. ej. en Google Scholar).
