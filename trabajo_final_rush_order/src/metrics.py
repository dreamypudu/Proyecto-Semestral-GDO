# -*- coding: utf-8 -*-
"""Metricas de evaluacion: nervousness, danio, mejora y porcentaje de recuperacion."""

# ponytail: pesos fijos declarados como supuesto en el informe (seccion Supuestos adoptados)
GAMMA_S, GAMMA_M = 1.0, 10.0   # N = g1*Ns + g2*Nm
ALPHA, BETA = 0.5, 0.1         # Z = CmaxR + a*Cr + b*N


def nervousness(s0, s_new, pending):
    """Ns: suma |s - s0| de ops pendientes reprogramadas; Nm: cambios de maquina."""
    ns = sum(abs(s_new[op][1] - s0[op][1]) for op in pending)
    nm = sum(1 for op in pending if s_new[op][0] != s0[op][0])
    return ns, nm, GAMMA_S * ns + GAMMA_M * nm


def z_score(cmax_r, c_r, n):
    return cmax_r + ALPHA * c_r + BETA * n


def recovery(cmax0, cmax_pert, cmax_rec):
    """Danio, mejora y % de recuperacion respecto al baseline perturbado."""
    dano = cmax_pert - cmax0
    mejora = cmax_pert - cmax_rec
    pct = 100.0 * mejora / dano if dano > 0 else 0.0
    return dano, mejora, pct


if __name__ == "__main__":
    s0 = {(1, 1): (1, 0, 10), (1, 2): (2, 10, 20)}
    s1 = {(1, 1): (1, 5, 15), (1, 2): (3, 15, 25)}
    ns, nm, n = nervousness(s0, s1, [(1, 1), (1, 2)])
    assert (ns, nm) == (10, 1) and n == 20.0
    assert recovery(100, 140, 110) == (40, 30, 75.0)
    print("OK")
