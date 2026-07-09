# Guion de presentación (20 minutos)

## 1. Problema y contexto — 2 min

Taller de manufactura de autos personalizados representado por un Digital Twin. El programa de producción sufre perturbaciones; la nuestra: un **pedido urgente (rush order) que llega a mitad de la ejecución** (t\* = Cmax₀/2). Pregunta central: *¿cómo integrar el pedido urgente minimizando el impacto, sin detener el taller?*

## 2. Paper base y FJSSP — 3 min

- Liu et al. (2022): FJSSP con Digital Twin; caso de laboratorio con **8 trabajos × 8 máquinas × 5 operaciones** (chasis, marco, puertas, cubierta).
- Flexible = cada operación puede ir a varias máquinas con tiempos distintos → decidir asignación **y** secuencia.
- Resultados del paper: RLEGA 397 / GA 411 / TS 435 (mejor makespan); ante nueva orden en t=200 s: 397 → 521.
- Jerarquía metodológica: modelo de Liu et al. como base; Wang et al. (2022) para el evento rush order; Moratori et al. (2010) para estabilidad/nervousness. *(Nota: los papers comparten el problema pero no la formulación; por eso se adopta una sola base.)*

## 3. Modelo de optimización — 3 min

- FJSSP clásico: asignación única, precedencia, no solapamiento, min Cmax.
- **GA con cromosoma MS+OS** (asignación + secuencia con repetición) y decodificador con inserción en huecos.
- Resultado inicial: **Cmax₀ = 382 s en 4.9 s** — mejor que el RLEGA reportado (397). Explicación honesta: decodificador activo + distintos parámetros/semillas; no es una réplica.
- *Mostrar Gantt inicial.*

## 4. Rush Order en Cmax₀/2 — 3 min

- En t\* = 191 s llega J9 (reedición del modelo 8). El DT detecta el evento y clasifica: **18 terminadas (congeladas), 7 en proceso (no se interrumpen), 15 pendientes (reprogramables)**.
- Modelo extendido: reprogramar Q = pendientes + rush, con disponibilidad de máquinas A_i y arranques ≥ t\*.
- Dato clave de la instancia: la cadena mínima del rush suma 321 s → **nadie puede terminar el rush antes de 512 s** (cota inferior).
- *Mostrar Gantt perturbado (insert al final): Cmax = 518.*

## 5. Modelo inteligente de recuperación — 3 min

- 5 estrategias: insert_end, right_shift, GA parcial, GA prioridad-rush, GA estabilidad.
- **XGBoost como selector**: regresor que predice el costo Z = CmaxR + 0.5·Cr + 0.1·N de cada estrategia dado el estado del taller (14 features) y elige la de menor Z predicho.
- Entrenamiento: 300 escenarios sintéticos con **rush aleatorio en cada iteración**, t\* variable y 5 programas iniciales; etiquetas por mediana de 3 corridas de GA (menos ruido). Distribución de ganadoras: stability 204, right_shift 44, insert_end 33, priority 10, partial 9.
- **Validación honesta** (leave-one-group-out, sin fuga): regret medio vs oráculo — baseline "siempre stability" 0.66, selector 1.18, clasificador balanceado 9.43. El selector no supera al baseline porque el margen total es 0.66 puntos de Z: con estos pesos, la política estable es casi inmejorable — y el sistema lo *aprende* en vez de asumirlo.
- **Sensibilidad**: si β (peso de estabilidad) fuera 0, "siempre stability" ganaría solo 25/300 y dominarían los GA. La regla fija sirve solo mientras la política no cambie; el selector se re-entrena solo. Ese es su valor real.

## 6. Resultados y Gantt — 4 min

| Escenario | Cmax | Cr | N | % Recup. |
|---|---|---|---|---|
| Inicial | 382 | – | – | – |
| Rush sin recuperación | 518 | 518 | 0 | 0 |
| GA parcial | **512 (óptimo)** | 512 | 747 | 4.4% |
| right_shift (prioriza el rush) | 583 | **512** | 541 | **−47.8%** |
| XGBoost → stability_ga | 518 | 518 | **0** | 0 |

- Dato para la discusión: right_shift termina el rush en el óptimo (512) pero empuja el makespan a 583 — recuperación *negativa*: priorizar ciegamente al pedido urgente daña más que el propio pedido.

- GA parcial **alcanza la cota inferior**: recuperación óptima en makespan.
- Pero cuesta modificar 12 de las 15 operaciones pendientes (7 cambios de máquina) → según Z, **conviene no tocar el programa**: eso eligió el selector (Z = 777 vs 843 del GA parcial).
- Mensaje central: *la mejor recuperación no siempre es la que más makespan recupera* — el trade-off makespan/estabilidad de Moratori et al. emerge de los datos.

## 7. Conclusiones — 2 min

- Metodología completa y reproducible: GA competitivo (382 < 397), rescheduling parcial óptimo demostrable (512), selector inteligente que decide con criterio cuantitativo.
- El daño del rush (136 s) está dominado por su propia cadena crítica; el valor del sistema está en decidir *cuándo* reoptimizar y cuándo no.
- Futuro: más instancias, falla de máquina (segunda perturbación del paper), calibración de pesos con el decisor.
