# -*- coding: utf-8 -*-
"""FJSSP inicial: datos del caso de estudio (Liu et al. 2022, Tablas 5 y 6) y GA con
codificacion MS+OS. El mismo decodificador sirve para el scheduling inicial y para el
rescheduling parcial (recibe disponibilidad de maquinas y de trabajos como estado inicial).
"""
import random
from bisect import insort

# (job, operacion) -> [(maquina, tiempo)]. Transcripcion directa de Tablas 5 y 6 del paper base.
DATA = {
    (1, 1): [(3, 38), (8, 49)], (1, 2): [(1, 72), (7, 54)], (1, 3): [(1, 49), (4, 65)],
    (1, 4): [(2, 76), (8, 59)], (1, 5): [(6, 73), (7, 43)],
    (2, 1): [(2, 50), (8, 49)], (2, 2): [(4, 53), (7, 41)], (2, 3): [(3, 62), (5, 66)],
    (2, 4): [(1, 51), (3, 42)], (2, 5): [(2, 49), (3, 70)],
    (3, 1): [(1, 48), (4, 60), (6, 68)], (3, 2): [(4, 53), (5, 59)], (3, 3): [(2, 61), (5, 66)],
    (3, 4): [(3, 42), (8, 59)], (3, 5): [(7, 43)],
    (4, 1): [(4, 60), (8, 49)], (4, 2): [(1, 72), (2, 85)], (4, 3): [(6, 59), (8, 66)],
    (4, 4): [(6, 30)], (4, 5): [(6, 73), (7, 69)],
    (5, 1): [(1, 35), (6, 68)], (5, 2): [(2, 42), (5, 69)], (5, 3): [(1, 67), (4, 49)],
    (5, 4): [(2, 42), (7, 30)], (5, 5): [(3, 70), (8, 88)],
    (6, 1): [(1, 43), (2, 35), (4, 32), (7, 57)], (6, 2): [(1, 68), (6, 67)], (6, 3): [(4, 56), (8, 93)],
    (6, 4): [(1, 68), (3, 105)], (6, 5): [(6, 79)],
    (7, 1): [(1, 48), (6, 32)], (7, 2): [(2, 85), (5, 66)], (7, 3): [(1, 49), (4, 43)],
    (7, 4): [(7, 51), (8, 73)], (7, 5): [(3, 102), (7, 52)],
    (8, 1): [(2, 50), (5, 43), (7, 57)], (8, 2): [(2, 85), (4, 53)], (8, 3): [(5, 66), (8, 60)],
    (8, 4): [(1, 94), (3, 100)], (8, 5): [(3, 90), (8, 71)],
}
MACHINES = list(range(1, 9))


def earliest_start(busy, ready, p):
    """Primer instante >= ready donde cabe un bloque de duracion p (busy: intervalos ordenados)."""
    t = ready
    for s, e in busy:
        if t + p <= s:
            break
        t = max(t, e)
    return t


def decode(ms, order, ops, job_ready=None, mach_busy=None):
    """Decodifica un cromosoma MS+OS a un schedule semi-activo con insercion en huecos.

    ms: {(j,h): (maquina, tiempo)}; order: lista de jobs (cada aparicion = siguiente op pendiente).
    job_ready: {j: instante desde el que j puede continuar}; mach_busy: {m: [(s,e), ...]} ocupacion previa.
    Devuelve (sched {(j,h): (m, inicio, fin)}, cmax de lo programado).
    """
    busy = {m: sorted((mach_busy or {}).get(m, [])) for m in MACHINES}
    ready = dict(job_ready or {})
    pend = {}
    for j, h in sorted(ops):
        pend.setdefault(j, []).append((j, h))
    ptr = {j: 0 for j in pend}
    sched, cmax = {}, 0.0
    for j in order:
        op = pend[j][ptr[j]]
        ptr[j] += 1
        m, p = ms[op]
        s = earliest_start(busy[m], ready.get(j, 0.0), p)
        insort(busy[m], (s, s + p))
        sched[op] = (m, s, s + p)
        ready[j] = s + p
        cmax = max(cmax, s + p)
    return sched, cmax


def _pox(o1, o2, rng):
    """Crossover POX: conserva posiciones de un subconjunto de jobs de o1, rellena con o2."""
    jobs = sorted(set(o1))
    keep = set(rng.sample(jobs, max(1, len(jobs) // 2)))
    rest = iter([j for j in o2 if j not in keep])
    return [j if j in keep else next(rest) for j in o1]


def ga(ops, data, job_ready=None, mach_busy=None, fitness=None,
       pop=80, gens=200, seed=0, pmut=0.15):
    """GA para (re)scheduling. fitness(sched, cmax) -> valor a minimizar; por defecto cmax.
    Devuelve (sched, cmax, fitness_final) del mejor individuo."""
    rng = random.Random(seed)
    ops = sorted(ops)
    tokens = [j for j, _ in ops]

    def new_ind():
        ms = {op: rng.choice(data[op]) for op in ops}
        order = tokens[:]
        rng.shuffle(order)
        return [ms, order]

    def evaluate(ind):
        sched, cmax = decode(ind[0], ind[1], ops, job_ready, mach_busy)
        return (fitness(sched, cmax) if fitness else cmax), sched, cmax

    population = [new_ind() for _ in range(pop)]
    scored = [evaluate(i) for i in population]
    best = min(zip((s[0] for s in scored), population, scored), key=lambda x: x[0])

    for _ in range(gens):
        nxt = [best[1]]  # elitismo
        while len(nxt) < pop:
            a = min(rng.sample(range(pop), 3), key=lambda k: scored[k][0])
            b = min(rng.sample(range(pop), 3), key=lambda k: scored[k][0])
            p1, p2 = population[a], population[b]
            ms = {op: (p1[0][op] if rng.random() < 0.5 else p2[0][op]) for op in ops}
            order = _pox(p1[1], p2[1], rng)
            if rng.random() < pmut:
                op = rng.choice(ops)
                ms[op] = rng.choice(data[op])
            if rng.random() < pmut:
                i, k = rng.randrange(len(order)), rng.randrange(len(order))
                order[i], order[k] = order[k], order[i]
            nxt.append([ms, order])
        population = nxt
        scored = [evaluate(i) for i in population]
        cand = min(zip((s[0] for s in scored), population, scored), key=lambda x: x[0])
        if cand[0] < best[0]:
            best = cand
    return best[2][1], best[2][2], best[0]


def solve_initial(seed=0, pop=120, gens=300):
    """Scheduling inicial de los 8 trabajos. Devuelve (S0, Cmax0)."""
    sched, cmax, _ = ga(list(DATA), DATA, pop=pop, gens=gens, seed=seed)
    return sched, cmax


if __name__ == "__main__":
    # autochequeo: factibilidad del schedule inicial
    s0, cmax0 = solve_initial(seed=1, pop=60, gens=80)
    assert len(s0) == 40
    for (j, h), (m, s, e) in s0.items():
        assert (m, round(e - s)) in [(mm, pp) for mm, pp in DATA[(j, h)]]
        if h > 1:
            assert s0[(j, h - 1)][2] <= s + 1e-9, "precedencia violada"
    by_m = {}
    for (j, h), (m, s, e) in s0.items():
        by_m.setdefault(m, []).append((s, e))
    for m, iv in by_m.items():
        iv.sort()
        assert all(iv[i][1] <= iv[i + 1][0] + 1e-9 for i in range(len(iv) - 1)), "solape en maquina"
    print("OK, Cmax0 =", cmax0)
