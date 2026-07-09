# Trabajo final: FJSSP con Rush Order sobre Digital Twin

Scheduling dinámico para un Flexible Job-Shop (caso 8 trabajos × 8 máquinas × 5 operaciones
de Liu et al. 2022). Se resuelve el programa inicial con un algoritmo genético, se simula la
llegada de un pedido urgente en t\* = Cmax₀/2 y se recupera el programa reprogramando solo
las operaciones pendientes + rush order. Un selector XGBoost (capa de decisión del Digital
Twin lógico) elige la estrategia de rescheduling que minimiza Z = CmaxR + α·Cr + β·N.

## Estructura

```text
data/          datos extraídos del paper (Tablas 5-6) y rush order canónico
src/           código fuente
  scheduler_ga.py     datos del caso + GA (codificación MS+OS, decodificador con huecos)
  rescheduling.py     clasificación F/I/P en t*, congelamiento y 5 estrategias
  metrics.py          nervousness, daño, mejora, % recuperación, Z
  xgboost_selector.py features del estado del taller + entrenamiento del selector
  gantt.py            diagramas de Gantt
  run_experiments.py  ejecuta los 4 experimentos obligatorios y genera resultados
results/       Gantt inicial / perturbado / recuperado + tabla de resultados
report/        informe final (md/pdf), logica_experimento.md (pipeline detallado +
               auditoria de errores potenciales), marco_metodologico.md (teoria y
               bibliografia de la metodologia)
presentation/  guion y outline de slides (20 min)
```

## Reproducir

```bash
pip install numpy pandas matplotlib xgboost scikit-learn
cd src
python run_experiments.py        # ~5-10 min; escribe data/ y results/
```

Semillas fijas (`SEED = 0` en `run_experiments.py`): los resultados son reproducibles.
Cada módulo tiene un autochequeo: `python scheduler_ga.py`, `python rescheduling.py`, etc.

## Referencias

- Liu et al. (2022). *Digital Twin-Driven Adaptive Scheduling for Flexible Job Shops*. Sustainability 14, 5340. (modelo base y caso de estudio)
- Wang et al. (2022). *A Method for Dynamic Insertion Order Scheduling in Flexible Job Shops Based on Digital Twins*. Applied Sciences 12, 12430. (evento rush order)
- Moratori, Petrovic & Vázquez-Rodríguez (2010). *Integrating rush orders into existent schedules for a complex job shop problem*. Applied Intelligence. (estabilidad / nervousness)
