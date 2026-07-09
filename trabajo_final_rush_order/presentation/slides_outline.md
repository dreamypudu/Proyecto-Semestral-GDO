# Outline de slides (20 min, ~14 láminas)

1. **Portada** — título, integrantes, curso.
2. **Contexto** — Digital Twin en manufactura; scheduling dinámico; por qué las perturbaciones importan.
3. **El problema** — FJSSP: n trabajos, m máquinas, rutas flexibles; objetivo Cmax. Caso 8×8×5 (autos personalizados, Liu et al. 2022).
4. **Paper base** — Liu et al. 2022: RLEGA vs GA vs TS (mejores: 397 / 411 / 435); rescheduling ante nueva orden (397 → 521).
5. **Modelo matemático (1)** — FJSSP base: asignación única, precedencia, no solapamiento.
6. **Modelo matemático (2)** — extensión Rush Order: clasificación F/I/P en t\*, congelamiento, disponibilidad A_i, Q = P ∪ R; objetivo Z = CmaxR + α·Cr + β·N.
7. **Metodología** — GA con cromosoma MS+OS, decodificador con inserción en huecos; mismo decodificador para inicial y rescheduling.
8. **Perturbación** — rush order en t\* = Cmax₀/2 (reedición del modelo 8, como el caso dinámico del paper); pipeline: detectar → clasificar → congelar → reprogramar.
9. **Estrategias de recuperación** — insert_end (baseline), right_shift, GA parcial, GA prioridad rush, GA estabilidad.
10. **Selector inteligente** — XGBoost (regresión de costo): predice Z de cada estrategia desde 14 features del taller y elige el argmin; entrenado con 300 escenarios sintéticos (rush aleatorio); validado contra baseline trivial y oráculo.
11. **Resultados (1)** — Gantt inicial / perturbado / recuperado.
12. **Resultados (2)** — tabla comparativa: Cmax, Cr, N, tiempo, % recuperación por estrategia.
13. **Discusión** — trade-off makespan vs estabilidad; comparación con paper base; limitaciones.
14. **Conclusiones** — hallazgos, cumplimiento del objetivo, trabajo futuro.
