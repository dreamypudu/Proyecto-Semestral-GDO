# -*- coding: utf-8 -*-
"""Ejecuta los 4 experimentos obligatorios y genera todos los entregables:
data/*.csv, results/gantt_*.png, results/tabla_resultados.csv.

Escenarios: (1) scheduling inicial, (2) rush sin recuperacion inteligente (insert_end),
(3) recuperacion por GA parcial, (4) recuperacion con selector XGBoost.
Reproducible: semillas fijas.
"""
import csv
import os
import time

import numpy as np

from scheduler_ga import DATA, solve_initial
from rescheduling import STRATEGIES, RUSH_CANONICO, shop_state, apply_strategy
from metrics import recovery
from xgboost_selector import FEATURE_NAMES, build_dataset, train, select, features
from gantt import plot_gantt

try:  # como notebook no existe __file__; se asume cwd = src/
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = os.getcwd()
BASE = os.path.normpath(os.path.join(_HERE, ".."))
SEED = 0
GA_FINAL = {"pop": 80, "gens": 150}  # presupuesto GA para los experimentos finales


def export_data():
    os.makedirs(f"{BASE}/data", exist_ok=True)
    with open(f"{BASE}/data/datos_base_extraidos.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["job", "operacion", "maquina", "tiempo"])
        for (j, h), alts in sorted(DATA.items()):
            for m, p in alts:
                w.writerow([j, h, m, p])
    with open(f"{BASE}/data/datos_rush_order.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["job", "operacion", "maquina", "tiempo"])
        for (j, h), alts in sorted(RUSH_CANONICO.items()):
            for m, p in alts:
                w.writerow([j, h, m, p])


def main():
    os.makedirs(f"{BASE}/results", exist_ok=True)
    export_data()
    rows = []

    # 1. Scheduling inicial
    t0 = time.time()
    s0, cmax0 = solve_initial(seed=SEED)
    t_ini = time.time() - t0
    print(f"[1] Scheduling inicial: Cmax0={cmax0:.0f} ({t_ini:.1f}s)")
    plot_gantt(s0, f"Gantt inicial (Cmax0={cmax0:.0f})", f"{BASE}/results/gantt_inicial.png")
    rows.append(["1_inicial", "-", cmax0, "-", t_ini, 0, 0, 0, "-", "-", "-"])

    # Perturbacion: rush order (reedicion del modelo 8) en t* = Cmax0/2
    t_star = cmax0 / 2
    st = shop_state(s0, cmax0, RUSH_CANONICO, t_star)
    print(f"    t*={t_star:.0f} | terminadas={len(st['F'])} en proceso={len(st['I'])} "
          f"pendientes={len(st['P'])}")

    # 2. Rush sin recuperacion inteligente
    t0 = time.time()
    base = apply_strategy("insert_end", st, seed=SEED)
    t_base = time.time() - t0
    cmax_pert = base["cmax_r"]
    plot_gantt(base["sched"], f"Gantt perturbado - insert al final (CmaxR={cmax_pert:.0f})",
               f"{BASE}/results/gantt_perturbado.png", t_star=t_star)
    rows.append(["2_rush_sin_recuperacion", "insert_end", cmax_pert, base["c_r"], t_base,
                 base["n"], base["nm"], base["ops_modificadas"], 0.0, 0.0, 0.0])

    # 3. Recuperacion por GA parcial
    t0 = time.time()
    rec = apply_strategy("partial_ga", st, seed=SEED, **GA_FINAL)
    t_rec = time.time() - t0
    d, m, pct = recovery(cmax0, cmax_pert, rec["cmax_r"])
    plot_gantt(rec["sched"], f"Gantt recuperado - GA parcial (CmaxR={rec['cmax_r']:.0f})",
               f"{BASE}/results/gantt_recuperado.png", t_star=t_star)
    rows.append(["3_recuperacion_ga_parcial", "partial_ga", rec["cmax_r"], rec["c_r"], t_rec,
                 rec["n"], rec["nm"], rec["ops_modificadas"], d, m, pct])

    # 4. Recuperacion con selector XGBoost
    print("[4] Entrenando selector XGBoost (escenarios sinteticos, rush aleatorio)...")
    t0 = time.time()
    X, y = build_dataset(n_escenarios=150, seed=SEED)
    model = train(X, y, seed=SEED)
    t_train = time.time() - t0
    print(f"    dataset={len(y)} escenarios, etiquetas={np.bincount(y, minlength=5)}, "
          f"entrenamiento total {t_train:.0f}s")
    t0 = time.time()
    elegida = select(model, st)
    smart = apply_strategy(elegida, st, seed=SEED, **GA_FINAL)
    t_smart = time.time() - t0
    d, m, pct = recovery(cmax0, cmax_pert, smart["cmax_r"])
    print(f"    estrategia elegida: {elegida}")
    plot_gantt(smart["sched"],
               f"Gantt recuperado - XGBoost elige '{elegida}' (CmaxR={smart['cmax_r']:.0f})",
               f"{BASE}/results/gantt_recuperado_xgboost.png", t_star=t_star)
    rows.append(["4_recuperacion_xgboost", elegida, smart["cmax_r"], smart["c_r"], t_smart,
                 smart["n"], smart["nm"], smart["ops_modificadas"], d, m, pct])

    # Comparacion de las 5 estrategias sobre el escenario canonico (para el informe)
    for name in STRATEGIES:
        t0 = time.time()
        r = apply_strategy(name, st, seed=SEED, **GA_FINAL)
        dt = time.time() - t0
        d, m, pct = recovery(cmax0, cmax_pert, r["cmax_r"])
        rows.append([f"estrategia_{name}", name, r["cmax_r"], r["c_r"], dt,
                     r["n"], r["nm"], r["ops_modificadas"], d, m, pct])

    header = ["escenario", "estrategia", "Cmax", "Cr_rush", "tiempo_seg",
              "nervousness_N", "cambios_maquina_Nm", "ops_modificadas",
              "dano", "mejora", "pct_recuperacion"]
    with open(f"{BASE}/results/tabla_resultados.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows([[f"{v:.1f}" if isinstance(v, float) else v for v in row] for row in rows])

    # importancia de features del selector (anexo del informe)
    imp = sorted(zip(FEATURE_NAMES, model.feature_importances_), key=lambda x: -x[1])
    with open(f"{BASE}/results/importancia_features.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["feature", "importancia"])
        w.writerows([[n, f"{v:.4f}"] for n, v in imp])

    print("\n" + " | ".join(header))
    for row in rows:
        print(" | ".join(f"{v:.1f}" if isinstance(v, float) else str(v) for v in row))


if __name__ == "__main__":
    main()
