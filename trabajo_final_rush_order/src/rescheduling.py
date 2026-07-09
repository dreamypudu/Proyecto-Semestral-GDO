# -*- coding: utf-8 -*-
"""Simulacion del Rush Order en t* y estrategias de rescheduling.

Clasifica el estado del taller en t* (terminadas F, en proceso I, pendientes P),
congela F e I, y reprograma Q = P + rush con cinco estrategias:
insert_end, right_shift, partial_ga, priority_ga, stability_ga.
"""
import random
from bisect import insort

from scheduler_ga import DATA, MACHINES, earliest_start, decode, ga
from metrics import nervousness, z_score, ALPHA, BETA

STRATEGIES = ["insert_end", "right_shift", "partial_ga", "priority_ga", "stability_ga"]
RUSH_JOB = 9  # id del trabajo urgente

# Rush order canonico de los experimentos: reedicion del modelo 8, igual que el caso
# dinamico del paper base (nueva orden del "eighth model" en t=200 s).
RUSH_CANONICO = {(RUSH_JOB, h): [(m, p) for m, p in DATA[(8, h)]] for h in range(1, 6)}


def random_rush(rng, n_ops=None):
    """Rush order aleatorio (para entrenar el selector): 3-5 ops, 1-3 maquinas c/u,
    tiempos en el rango empirico de la Tabla 6 (30-105)."""
    n_ops = n_ops or rng.randint(3, 5)
    return {(RUSH_JOB, h): sorted((m, rng.randint(30, 105))
                                  for m in rng.sample(MACHINES, rng.randint(1, 3)))
            for h in range(1, n_ops + 1)}


def shop_state(s0, cmax0, rush_data, t_star):
    """Estado del taller en t*: clasificacion F/I/P, disponibilidad de maquinas y trabajos."""
    F = {op for op, (_, s, e) in s0.items() if e <= t_star}
    I = {op for op, (_, s, e) in s0.items() if s < t_star < e}
    P = {op for op, (_, s, e) in s0.items() if s >= t_star}
    avail = {m: t_star for m in MACHINES}
    for op in I:
        m, _, e = s0[op]
        avail[m] = max(avail[m], e)
    job_ready = {j: t_star for j in {jj for jj, _ in list(P) + list(rush_data)}}
    for op in F | I:
        j = op[0]
        if j in job_ready:
            job_ready[j] = max(job_ready[j], s0[op][2])
    mach_busy = {m: [(0.0, a)] for m, a in avail.items()}
    data = dict(DATA)
    data.update(rush_data)
    return {"s0": s0, "cmax0": cmax0, "t_star": t_star, "F": F, "I": I, "P": sorted(P),
            "Q": sorted(P) + sorted(rush_data), "rush": rush_data, "data": data,
            "job_ready": job_ready, "mach_busy": mach_busy, "avail": avail}


def _keep_pending(state):
    """Deja las ops pendientes exactamente como en S0 (sigue siendo factible) y
    devuelve la ocupacion de maquinas resultante para insertar el rush."""
    busy = {m: sorted(iv) for m, iv in state["mach_busy"].items()}
    sched = {}
    for op in state["P"]:
        m, s, e = state["s0"][op]
        insort(busy[m], (s, e))
        sched[op] = (m, s, e)
    ready = {RUSH_JOB: state["t_star"]}
    return sched, busy, ready


def _greedy_rush(state, sched, busy, ready, gapfill):
    """Programa las ops del rush en orden, eligiendo la maquina de menor completacion."""
    for op in sorted(state["rush"]):
        best = None
        for m, p in state["data"][op]:
            if gapfill:
                s = earliest_start(busy[m], ready.get(op[0], state["t_star"]), p)
            else:
                s = max(ready.get(op[0], state["t_star"]), max(e for _, e in busy[m]))
            if best is None or s + p < best[2]:
                best = (m, s, s + p)
        insort(busy[best[0]], (best[1], best[2]))
        sched[op] = best
        ready[op[0]] = best[2]
    return sched


def _right_shift(state):
    """Insercion con desplazamiento genuino: el rush se programa lo antes posible
    (compitiendo solo con lo congelado) y las pendientes conservan maquina y orden,
    desplazadas a la derecha solo lo necesario (nunca antes de su inicio original)."""
    s0 = state["s0"]
    busy = {m: sorted(iv) for m, iv in state["mach_busy"].items()}
    ready = dict(state["job_ready"])
    sched = _greedy_rush(state, {}, busy, ready, gapfill=True)
    mach_last = {m: 0.0 for m in busy}
    for op in sorted(state["P"], key=lambda o: s0[o][1]):
        m, s_old, e_old = s0[op]
        p = e_old - s_old
        s = earliest_start(busy[m], max(s_old, ready.get(op[0], 0.0), mach_last[m]), p)
        insort(busy[m], (s, s + p))
        sched[op] = (m, s, s + p)
        ready[op[0]] = s + p
        mach_last[m] = s + p
    return sched


def _ga_fitness(state, kind):
    if kind == "partial_ga":
        return None  # solo CmaxR
    s0, P, rush_last = state["s0"], state["P"], max(state["rush"])

    def fit(sched, cmax):
        val = cmax
        if kind in ("priority_ga", "stability_ga"):
            val += ALPHA * sched[rush_last][2]
        if kind == "stability_ga":
            val += BETA * nervousness(s0, sched, P)[2]
        return val
    return fit


def _result_fitness(kind, r):
    """El objetivo de _ga_fitness evaluado sobre un resultado ya construido."""
    val = r["cmax_r"]
    if kind in ("priority_ga", "stability_ga"):
        val += ALPHA * r["c_r"]
    if kind == "stability_ga":
        val += BETA * r["n"]
    return val


def _finish(state, sched):
    """Completa un schedule parcial con lo congelado y calcula todas las metricas."""
    full = {op: v for op, v in state["s0"].items() if op in state["F"] | state["I"]}
    full.update(sched)
    cmax_r = max(e for _, _, e in full.values())
    c_r = full[max(state["rush"])][2]
    ns, nm, n = nervousness(state["s0"], full, state["P"])
    return {"sched": full, "cmax_r": cmax_r, "c_r": c_r, "ns": ns, "nm": nm, "n": n,
            "z": z_score(cmax_r, c_r, n),
            "ops_modificadas": sum(1 for op in state["P"]
                                   if full[op][0] != state["s0"][op][0]
                                   or abs(full[op][1] - state["s0"][op][1]) > 1e-9)}


def apply_strategy(name, state, seed=0, pop=40, gens=60):
    """Ejecuta una estrategia y devuelve el schedule completo (congelado + reprogramado)."""
    if name == "insert_end":
        # baseline sin recuperacion: S0 intacto, rush al final de cada maquina
        sched, busy, ready = _keep_pending(state)
        return _finish(state, _greedy_rush(state, sched, busy, ready, gapfill=False))
    if name == "right_shift":
        return _finish(state, _right_shift(state))
    if name in ("partial_ga", "priority_ga", "stability_ga"):
        sched, _, _ = ga(state["Q"], state["data"], state["job_ready"], state["mach_busy"],
                         fitness=_ga_fitness(state, name), pop=pop, gens=gens, seed=seed)
        # warm start elitista: el GA nunca reporta peor que las heuristicas
        # deterministas segun su propio objetivo (sin esto, un GA mal convergido
        # deja que una heuristica "gane" escenarios que en realidad empata)
        candidatos = [_finish(state, sched),
                      apply_strategy("insert_end", state),
                      apply_strategy("right_shift", state)]
        return min(candidatos, key=lambda r: _result_fitness(name, r))
    raise ValueError(name)


if __name__ == "__main__":
    from scheduler_ga import solve_initial
    s0, cmax0 = solve_initial(seed=1, pop=60, gens=80)
    st = shop_state(s0, cmax0, RUSH_CANONICO, cmax0 / 2)
    assert st["F"] | st["I"] | set(st["P"]) == set(s0), "clasificacion no particiona S0"
    for name in STRATEGIES:
        r = apply_strategy(name, st, seed=2)
        full = r["sched"]
        for op in st["F"] | st["I"]:
            assert full[op] == s0[op], "operacion congelada modificada"
        for op in st["Q"]:
            assert full[op][1] >= st["t_star"] - 1e-9, "reprogramada antes de t*"
            j, h = op
            if h > 1:
                assert full[(j, h - 1)][2] <= full[op][1] + 1e-9, "precedencia violada"
        by_m = {}
        for op, (m, s, e) in full.items():
            by_m.setdefault(m, []).append((s, e))
        for m, iv in by_m.items():
            iv.sort()
            assert all(iv[i][1] <= iv[i + 1][0] + 1e-9 for i in range(len(iv) - 1)), "solape"
        print(f"{name:13s} CmaxR={r['cmax_r']:6.1f} Cr={r['c_r']:6.1f} N={r['n']:7.1f} Z={r['z']:7.1f}")
    print("OK")
