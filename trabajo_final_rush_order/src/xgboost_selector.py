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
from metrics import ALPHA, BETA

FEATURE_NAMES = [
    "t_frac", "n_terminadas", "n_proceso", "n_pendientes", "carga_media", "carga_max",
    "holgura_media", "rush_maquinas_factibles", "rush_tiempo_min", "rush_tiempo_medio",
    "saturacion", "cmax0", "avance_tiempo_pct", "pendientes_en_maquinas_rush",
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
    # avance en tiempo de trabajo (no en numero de ops, que duplicaria n_terminadas)
    total = sum(e - s for (_, s, e) in s0.values())
    avance_t = sum(s0[op][2] - s0[op][1] for op in state["F"]) / total
    # pendientes que compiten por las maquinas factibles del rush
    rush_m = {m for alts in rush.values() for m, _ in alts}
    afectadas = sum(1 for op in P if s0[op][0] in rush_m)
    return [
        t / cmax0, len(state["F"]), len(state["I"]), len(P),
        float(np.mean(loads)), max(loads), float(np.mean(slack)),
        sum(len(a) for a in rush.values()), rmin, rmean,
        rem / (len(MACHINES) * horizon), cmax0, avance_t, afectadas,
    ]


def build_dataset(n_escenarios=300, seed=0, ga_kw=None, n_seeds=3):
    """Genera escenarios sinteticos y registra el costo de cada estrategia.

    Devuelve (X, y, Z, comp, groups): Z = matriz n x 5 de costos; comp = componentes
    (CmaxR, Cr, N) por estrategia para analisis de sensibilidad de pesos; groups =
    indice del schedule base de cada escenario (para validacion sin fuga).
    Las estrategias con GA se etiquetan con la MEDIANA de n_seeds corridas, porque
    una sola corrida con presupuesto reducido tiene ruido mayor que el margen tipico
    entre estrategias."""
    rng = random.Random(seed)
    ga_kw = ga_kw or {"pop": 30, "gens": 40}
    bases = [solve_initial(seed=s, pop=60, gens=80) for s in range(5)]
    X, comp, groups = [], [], []
    for k in range(n_escenarios):
        b = k % len(bases)
        s0, cmax0 = bases[b]
        t_star = rng.uniform(0.3, 0.7) * cmax0
        st = shop_state(s0, cmax0, random_rush(rng), t_star)
        fila = []
        for name in STRATEGIES:
            if name in ("insert_end", "right_shift"):
                r = apply_strategy(name, st)  # deterministas: una corrida basta
            else:
                rs = sorted((apply_strategy(name, st, seed=1000 * k + i, **ga_kw)
                             for i in range(n_seeds)), key=lambda d: d["z"])
                r = rs[len(rs) // 2]
            fila.append((r["cmax_r"], r["c_r"], r["n"]))
        X.append(features(st))
        comp.append(fila)
        groups.append(b)
    X, comp, groups = np.array(X), np.array(comp), np.array(groups)
    Z = comp[:, :, 0] + ALPHA * comp[:, :, 1] + BETA * comp[:, :, 2]
    return X, Z.argmin(axis=1), Z, comp, groups


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


def evaluate(X, y, Z, groups, seed=0):
    """Validacion cruzada leave-one-group-out por schedule base: los escenarios del
    programa inicial en test nunca se vieron en entrenamiento (sin fuga), y cada
    escenario recibe una prediccion out-of-fold. Reporta calidad de decision (Z y
    regret respecto del oraculo) del selector, el baseline trivial 'siempre
    stability_ga' y el clasificador balanceado (alternativa descartada)."""
    from sklearn.utils.class_weight import compute_sample_weight
    i_stab = STRATEGIES.index("stability_ga")
    oof = np.zeros(len(y), dtype=int)
    oof_clf = np.zeros(len(y), dtype=int)
    for g in np.unique(groups):
        tr, te = groups != g, groups == g
        oof[te] = _predict_idx(train(X[tr], Z[tr], seed=seed), X[te])
        classes = np.unique(y[tr])
        clf = XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.1,
                            random_state=seed, verbosity=0)
        clf.fit(X[tr], np.searchsorted(classes, y[tr]),
                sample_weight=compute_sample_weight("balanced", y[tr]))
        oof_clf[te] = classes[clf.predict(X[te])]

    idx = np.arange(len(y))
    z_or = Z.min(axis=1)

    def resumen(pred):
        return float(Z[idx, pred].mean()), float((Z[idx, pred] - z_or).mean())

    z_sel, reg_sel = resumen(oof)
    z_clf, reg_clf = resumen(oof_clf)
    z_bas, reg_bas = resumen(np.full(len(y), i_stab))
    return {
        "n": len(y), "folds": int(len(np.unique(groups))),
        "distribucion": np.bincount(y, minlength=len(STRATEGIES)).tolist(),
        "accuracy_global": float(np.mean(oof == y)),
        "recall_por_clase": {STRATEGIES[c]: float(np.mean(oof[y == c] == c))
                             for c in np.unique(y)},
        "desvios_de_stability": int(np.sum(oof != i_stab)),
        "z_selector": z_sel, "z_clf_balanceado": z_clf,
        "z_baseline_stability": z_bas, "z_oraculo": float(z_or.mean()),
        "regret_selector": reg_sel, "regret_clf_balanceado": reg_clf,
        "regret_baseline": reg_bas,
        "dif_selector_vs_baseline_por_fold": {
            int(g): round(float(Z[groups == g, oof[groups == g]].mean()
                                - Z[groups == g, i_stab].mean()), 3)
            for g in np.unique(groups)},
    }


if __name__ == "__main__":
    X, y, Z, comp, groups = build_dataset(n_escenarios=30, seed=1,
                                          ga_kw={"pop": 16, "gens": 15}, n_seeds=2)
    assert np.allclose(Z, comp[:, :, 0] + ALPHA * comp[:, :, 1] + BETA * comp[:, :, 2])
    res = evaluate(X, y, Z, groups, seed=1)
    assert res["z_oraculo"] <= min(res["z_selector"], res["z_baseline_stability"]) + 1e-9
    print("OK, distribucion:", res["distribucion"])
    print("recall por clase:", res["recall_por_clase"])
    print(f"Z selector={res['z_selector']:.1f} clf_bal={res['z_clf_balanceado']:.1f} "
          f"baseline={res['z_baseline_stability']:.1f} oraculo={res['z_oraculo']:.1f}")
