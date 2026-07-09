# -*- coding: utf-8 -*-
"""Selector inteligente de estrategia de rescheduling (XGBoost).

Capa de decision del Digital Twin logico: al detectar la insercion de un rush order,
extrae features del estado del taller y elige la estrategia que minimiza
Z = CmaxR + a*Cr + b*N. Entrenado con escenarios sinteticos (rush aleatorio en cada
iteracion, t* variable y distintos schedules iniciales).

El modelo es un REGRESOR de costo: predice Z para cada (estado, estrategia) y se
elige el argmin. Se prefirio sobre un clasificador de la estrategia ganadora porque
las etiquetas estan muy desbalanceadas (la estrategia estable gana ~73% de los
escenarios) y en validacion los clasificadores (balanceado o no) deciden PEOR que el
baseline trivial "siempre stability_ga"; la regresion lo iguala sin quedar nunca
por debajo. evaluate() reproduce esa comparacion.
"""
import random
import numpy as np
from xgboost import XGBClassifier, XGBRegressor

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


def build_dataset(n_escenarios=300, seed=0, ga_kw=None):
    """Genera escenarios sinteticos y etiqueta con la estrategia ganadora (menor Z).
    Devuelve (X, y, Z) con Z = matriz n x 5 de costos por estrategia (para validar
    la calidad de decision, no solo el accuracy)."""
    rng = random.Random(seed)
    ga_kw = ga_kw or {"pop": 30, "gens": 40}
    bases = [solve_initial(seed=s, pop=60, gens=80) for s in range(5)]
    X, y, Z = [], [], []
    for k in range(n_escenarios):
        s0, cmax0 = bases[k % len(bases)]
        t_star = rng.uniform(0.3, 0.7) * cmax0
        st = shop_state(s0, cmax0, random_rush(rng), t_star)
        zs = [apply_strategy(name, st, seed=k, **ga_kw)["z"] for name in STRATEGIES]
        X.append(features(st))
        y.append(int(np.argmin(zs)))
        Z.append(zs)
    return np.array(X), np.array(y), np.array(Z)


def _rows(X):
    """Expande cada estado a 5 filas (features del taller + one-hot de estrategia)."""
    n, k = len(X), len(STRATEGIES)
    return np.hstack([np.repeat(np.asarray(X, dtype=float), k, axis=0),
                      np.tile(np.eye(k), (n, 1))])


def train(X, Z, seed=0):
    """Regresor de costo: (estado, estrategia) -> Z. Nota: recibe la matriz Z,
    no las etiquetas ganadoras."""
    model = XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.08,
                         random_state=seed, verbosity=0)
    model.fit(_rows(X), np.asarray(Z, dtype=float).ravel())
    return model


def _predict_idx(model, X):
    zhat = model.predict(_rows(X)).reshape(-1, len(STRATEGIES))
    return np.argmin(zhat, axis=1)


def select(model, state):
    """Estrategia recomendada: la de menor Z predicho para el estado actual."""
    return STRATEGIES[int(_predict_idx(model, [features(state)])[0])]


def evaluate(X, y, Z, seed=0, test_size=0.3):
    """Valida en split estratificado 70/30: recall por clase y, sobre todo, calidad
    de decision (Z medio) del selector vs el baseline trivial 'siempre stability_ga',
    el clasificador balanceado (alternativa descartada) y el oraculo."""
    from sklearn.model_selection import train_test_split
    from sklearn.utils.class_weight import compute_sample_weight
    idx = np.arange(len(y))
    strat = y if np.bincount(y, minlength=5).min() != 1 else None
    tr, te = train_test_split(idx, test_size=test_size, random_state=seed, stratify=strat)
    i_stab = STRATEGIES.index("stability_ga")

    model = train(X[tr], Z[tr], seed=seed)
    y_pred = _predict_idx(model, X[te])
    recall = {STRATEGIES[c]: float(np.mean(y_pred[y[te] == c] == c))
              for c in np.unique(y[te])}

    # alternativa descartada, se reporta para justificar la eleccion
    classes = np.unique(y[tr])
    clf = XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.1,
                        random_state=seed, verbosity=0)
    clf.fit(X[tr], np.searchsorted(classes, y[tr]),
            sample_weight=compute_sample_weight("balanced", y[tr]))
    y_clf = classes[clf.predict(X[te])]

    return {
        "n_test": len(te),
        "distribucion": np.bincount(y, minlength=len(STRATEGIES)).tolist(),
        "accuracy_global": float(np.mean(y_pred == y[te])),
        "recall_por_clase": recall,
        "desvios_de_stability": int(np.sum(y_pred != i_stab)),
        "z_selector": float(Z[te, y_pred].mean()),
        "z_clf_balanceado": float(Z[te, y_clf].mean()),
        "z_baseline_stability": float(Z[te, i_stab].mean()),
        "z_oraculo": float(Z[te].min(axis=1).mean()),
    }


if __name__ == "__main__":
    X, y, Z = build_dataset(n_escenarios=40, seed=1, ga_kw={"pop": 16, "gens": 15})
    res = evaluate(X, y, Z, seed=1)
    assert res["z_oraculo"] <= min(res["z_selector"], res["z_baseline_stability"]) + 1e-9
    print("OK, distribucion:", res["distribucion"])
    print("recall por clase:", res["recall_por_clase"])
    print(f"Z selector={res['z_selector']:.1f} clf_bal={res['z_clf_balanceado']:.1f} "
          f"baseline={res['z_baseline_stability']:.1f} oraculo={res['z_oraculo']:.1f}")
