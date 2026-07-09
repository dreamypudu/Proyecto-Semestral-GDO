# -*- coding: utf-8 -*-
"""Selector inteligente de estrategia de rescheduling (XGBoost).

Capa de decision del Digital Twin logico: al detectar la insercion de un rush order,
extrae features del estado del taller y predice que estrategia minimiza
Z = CmaxR + a*Cr + b*N. Entrenado con escenarios sinteticos (rush aleatorio en cada
iteracion, t* variable y distintos schedules iniciales).
"""
import random
import numpy as np
from xgboost import XGBClassifier

from scheduler_ga import DATA, MACHINES, solve_initial
from rescheduling import STRATEGIES, shop_state, random_rush, apply_strategy

FEATURE_NAMES = [
    "t_frac", "n_terminadas", "n_proceso", "n_pendientes", "carga_media", "carga_max",
    "holgura_media", "rush_maquinas_factibles", "rush_tiempo_min", "rush_tiempo_medio",
    "saturacion", "cmax0", "avance_pct", "ops_afectadas",
]


def features(state):
    s0, cmax0, t = state["s0"], state["cmax0"], state["t_star"]
    P, rush = state["P"], state["rush"]
    load = {m: 0.0 for m in MACHINES}
    for op in P:
        m, s, e = s0[op]
        load[m] += e - s
    loads = list(load.values())
    slack = [(s0[op][1] - t) / cmax0 for op in P] or [0.0]
    rmin = sum(min(p for _, p in alts) for alts in rush.values())
    rmean = sum(sum(p for _, p in alts) / len(alts) for alts in rush.values())
    rem = sum(loads) + rmin
    horizon = max(cmax0 - t, 1.0)
    return [
        t / cmax0, len(state["F"]), len(state["I"]), len(P),
        float(np.mean(loads)), max(loads), float(np.mean(slack)),
        sum(len(a) for a in rush.values()), rmin, rmean,
        rem / (len(MACHINES) * horizon), cmax0, len(state["F"]) / len(s0), len(P),
    ]


def build_dataset(n_escenarios=150, seed=0, ga_kw=None):
    """Genera escenarios sinteticos y etiqueta con la estrategia ganadora (menor Z)."""
    rng = random.Random(seed)
    ga_kw = ga_kw or {"pop": 30, "gens": 40}
    # ponytail: 3 schedules iniciales bastan para variar la carga del taller; mas seeds si
    # el selector generaliza mal.
    bases = [solve_initial(seed=s, pop=60, gens=80) for s in (0, 1, 2)]
    X, y = [], []
    for k in range(n_escenarios):
        s0, cmax0 = bases[k % len(bases)]
        t_star = rng.uniform(0.3, 0.7) * cmax0
        st = shop_state(s0, cmax0, random_rush(rng), t_star)
        zs = [apply_strategy(name, st, seed=k, **ga_kw)["z"] for name in STRATEGIES]
        X.append(features(st))
        y.append(int(np.argmin(zs)))
    return np.array(X), np.array(y)


def train(X, y, seed=0):
    """Entrena sobre las clases observadas (no toda estrategia gana alguna vez)."""
    classes = np.unique(y)
    enc = {c: i for i, c in enumerate(classes)}
    model = XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.1,
                          random_state=seed, verbosity=0)
    model.fit(X, np.array([enc[c] for c in y]))
    model.strategy_classes_ = classes
    return model


def select(model, state):
    """Estrategia recomendada para el estado actual del taller."""
    idx = int(model.predict(np.array([features(state)]))[0])
    return STRATEGIES[model.strategy_classes_[idx]]


if __name__ == "__main__":
    X, y = build_dataset(n_escenarios=20, seed=1, ga_kw={"pop": 16, "gens": 15})
    m = train(X, y)
    assert m.predict(X[:1]).shape == (1,)
    print("OK, distribucion de etiquetas:", np.bincount(y, minlength=len(STRATEGIES)))
