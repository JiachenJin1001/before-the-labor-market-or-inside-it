"""Variances and autocovariances of residual log earnings by family background
(Figure 2 of the paper, Section 4.2).

Left panel: the variance of residual log earnings in each wave, advantaged
against less advantaged children. Right panel: the autocovariance at each lag,
averaged over the wave pairs at that lag with inverse-variance weights.
Intervals are 95 percent intervals from the bootstrap standard errors of the
moments (m5_md_weighted_and_ridge.py of the income-dynamics pipeline).
Output: paper/figures/fig_autocov.png and fig_autocov.pdf (5.0 by 2.04 inches, text in 9 points).
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
from _locate import sibling
m = pd.read_csv(os.path.join(sibling("income_dynamics", __file__), "output", "tables", "m5_moment_se.csv"))
m["lag"] = (m.s - m.t) // 2

from fig_style import setup, tr, ADV, LESS, save
setup(size=9)   # drawn at 5.0 inches: the text prints at 7 points at 0.60 of the text width and at 9 points at 0.78
fig, axes = plt.subplots(1, 2, figsize=(5.0, 2.04), layout="constrained")
fig.get_layout_engine().set(w_pad=0.02, h_pad=0.02, wspace=0.04)
# the same order, colors, markers and line styles as Figure 3: less advantaged children first (dark blue, circles,
# solid line), then advantaged children (orange, squares, dashed line); the series are offset slightly so that the
# intervals do not overlap
GROUPS = [("L", tr("Less advantaged children"), LESS, "o-", -1), ("H", tr("Advantaged children"), ADV, "s--", 1)]
ax = axes[0]
for grp, lab, col, fmt, side in GROUPS:
    d = m[(m.group == grp) & (m.lag == 0)]
    ax.errorbar(d.t + 0.15 * side, d.omega, yerr=1.96 * d.se, fmt=fmt, color=col, capsize=2, lw=1.1, ms=3.5, label=lab)
ax.set_xlabel(tr("Survey wave")); ax.set_ylabel(tr("Variance"))
ax.set_title(tr("(a) Variance in each wave")); ax.set_ylim(0, None); ax.set_xticks([2014, 2016, 2018, 2020, 2022])
ax = axes[1]
for grp, lab, col, fmt, side in GROUPS:
    d = m[m.group == grp]
    rows = []
    for lag, x in d.groupby("lag"):
        w = 1 / x.se ** 2
        rows.append(dict(lag=lag, omega=np.average(x.omega, weights=w), se=np.sqrt(1 / w.sum())))
    g = pd.DataFrame(rows)
    ax.errorbar(g.lag + 0.06 * side, g.omega, yerr=1.96 * g.se, fmt=fmt, color=col, capsize=2, lw=1.1, ms=3.5, label=lab)
ax.set_xlabel(tr("Lag (waves, two years apart)")); ax.set_ylabel(tr("Autocovariance"))
ax.set_title(tr("(b) Autocovariance by lag")); ax.set_xticks(range(5))
for ax in axes:
    ax.axhline(0, color="k", lw=.6); ax.grid(alpha=.25)
axes[0].legend(loc="lower left", handlelength=2.0, borderpad=0.3, labelspacing=0.25, borderaxespad=0.3)   # one legend for the two panels
out = save(fig, "fig_autocov.png", tight=False); print("wrote", out)
