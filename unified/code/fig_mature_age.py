"""Figure 4 of the paper: coefficients on provincial intensity by birth-cohort bin, for college completion (panel a)
and for the level of earnings at 30 and over (panel b).

Plotting only: reads the coefficients and standard errors written by block D of u9_mature_age_earnings.py
(output/u9_D_cohort_bins.csv, the unweighted main run) and draws them with 95 percent intervals; the reference bin,
born 1977 to 1980, is plotted at zero. u9_mature_age_earnings.py calls plot() after block D, and this file can be run
on its own to redraw the figure from the saved estimates.
Output: paper/figures/fig_mature_age.png and fig_mature_age.pdf (5.0 by 1.88 inches, text in 9 points).
"""
import os, sys
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
COLOR = "#08519c"   # all children: the dark blue of the figures


def plot(Dd):
    """Draw the figure from the rows of u9_D_cohort_bins.csv (columns outcome, bin, coef, se)."""
    from fig_style import setup, tr, save, stagger_xticks
    setup(size=9)   # drawn at 5.0 inches: the text prints at 7 points at 0.60 of the text width and at 9.2 points at 0.84
    fig, axes = plt.subplots(1, 2, figsize=(5.0, 1.88), layout="constrained", sharex=True)
    fig.get_layout_engine().set(w_pad=0.02, h_pad=0.02, wspace=0.05)
    # the bins of block D, in order, with the reference bin 1977-1980 in the middle; tick labels in the style of Figure 3
    keys = ["1972 or earlier", "1973-1976", None, "1981-1984", "1985-1988", "1989 or later"]
    labels = ["${\\leq}$1972", "1973–76", "1977–80", "1981–84", "1985–88", "${\\geq}$1989"]
    panels = [("college completion (children with a row at 30 and over)", "(a) College completion", "Coefficient\n(completion share)"),
              ("mean log earnings at 30 and over", "(b) Level of earnings", "Coefficient\n(log earnings)")]
    for ax, (out_, title, ylab) in zip(axes, panels):
        sd = Dd[Dd.outcome == out_].set_index("bin"); xs, ys, es = [], [], []
        for i, k in enumerate(keys):
            if k is None: ax.plot(i, 0, "D", mfc="none", mec=COLOR, ms=5, mew=1.0, zorder=3)
            else: xs.append(i); ys.append(sd.loc[k, "coef"]); es.append(1.96 * sd.loc[k, "se"])
        ax.errorbar(xs, ys, yerr=es, fmt="o", color=COLOR, capsize=2, ms=3.5, lw=1.1)
        ax.axhline(0, color="k", lw=.7); ax.axvline(2.5, color="grey", ls="--", lw=.8)
        stagger_xticks(ax, range(len(labels)), [tr(l) for l in labels])
        ax.set_xlim(-0.6, len(labels) - 0.4)
        ax.set_title(tr(title)); ax.set_xlabel(tr("Birth cohort")); ax.set_ylabel(tr(ylab))
    axes[0].set_ylim(-0.33, 1.12); axes[0].set_yticks([0, 0.4, 0.8]); axes[1].set_yticks([-0.4, 0, 0.4, 0.8])
    axes[0].plot([], [], "D", mfc="none", mec=COLOR, ls="", label=tr("Reference bin\n(omitted)"))
    axes[0].legend(loc="upper left", handlelength=1.2, borderpad=0.3, borderaxespad=0.3)
    return save(fig, "fig_mature_age.png", tight=False)


if __name__ == "__main__":
    out = plot(pd.read_csv(os.path.join(ROOT, "output", "u9_D_cohort_bins.csv"))); print("wrote", out)
