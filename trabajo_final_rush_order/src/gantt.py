# -*- coding: utf-8 -*-
"""Diagramas de Gantt del schedule (matplotlib)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scheduler_ga import MACHINES
from rescheduling import RUSH_JOB

_COLORS = plt.cm.tab10.colors


def plot_gantt(sched, title, path, t_star=None):
    """sched: {(j,h): (m, s, e)}. El rush (J9) se dibuja en rojo con borde grueso."""
    fig, ax = plt.subplots(figsize=(11, 4.5))
    for (j, h), (m, s, e) in sorted(sched.items()):
        rush = j == RUSH_JOB
        color = "crimson" if rush else _COLORS[(j - 1) % 10]
        ax.barh(m, e - s, left=s, height=0.7, color=color,
                edgecolor="black", linewidth=1.4 if rush else 0.5)
        ax.text(s + (e - s) / 2, m, f"{j}-{h}", ha="center", va="center",
                fontsize=7, color="white", fontweight="bold")
    if t_star is not None:
        ax.axvline(t_star, color="black", linestyle="--", linewidth=1.2)
        ax.text(t_star, len(MACHINES) + 0.6, f" t*={t_star:.0f}", fontsize=8)
    cmax = max(e for _, _, e in sched.values())
    ax.axvline(cmax, color="gray", linestyle=":", linewidth=1)
    ax.text(cmax, 0.3, f"Cmax={cmax:.0f}", fontsize=8, ha="right")
    ax.set_yticks(MACHINES)
    ax.set_yticklabels([f"M{m}" for m in MACHINES])
    ax.set_xlabel("Tiempo (s)")
    ax.set_title(title)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
