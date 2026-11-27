"""College completion and whom the reform moved (Figure 3 of the paper, two panels), on all children of the paper's
sample (sample_mature_age.py: ages 22 to 55, at least two waves of positive labor income), one observation per child.

(a) College completion rate of each birth-cohort group, by family background:
    the share of the children of the group who completed a four-year degree,
    in percent, with 95 percent intervals from the binomial standard error;
    the label at each point is the rate, and the number under each cohort
    group is the ratio of the rate of advantaged children to the rate of
    less advantaged children. Cohort groups: born 1972 or earlier and 1973-1980
    (before the reform), then 1981-1984, 1985-1988, 1989-1997.
    The output file also keeps the graduates of each group per 100 children
    of the cohort group.
(b) Binned scatter of college completion on the instrument by family
    background (20 bins of less advantaged and 10 bins of advantaged children,
    equal numbers of children), in the specification with the instrument
    entering separately for the two groups, province effects common to the
    groups and birth-year effects specific to each group; both variables are
    residualized on the other group's instrument and the controls, and the
    fitted lines have the group first-stage slopes.
Output: paper/figures/fig_first_stage.png and output/fig_first_stage_left.csv
"""
import os, sys
import numpy as np, pandas as pd, statsmodels.api as sm
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
WS = os.path.abspath(os.path.join(ROOT, ".."))
sys.path.insert(0, HERE)
from _locate import sibling
P = sibling("college_expansion", __file__)
from sample_mature_age import build_sample

c = build_sample(level_from=None).reset_index(drop=True)
canon = pd.read_csv(os.path.join(P, "data", "external", "expansion_intensity_canonical.csv"))
names = dict(zip(canon.provcd, canon.province_en))

from fig_style import setup, tr, ADV, LESS, LANG, stagger_xticks
setup(size=9)   # drawn at 5.0 inches: the text prints at 7 points at 0.60 of the text width and at 9.8 points at 0.84
fig, axes = plt.subplots(1, 2, figsize=(5.0, 2.6), layout="constrained", gridspec_kw=dict(width_ratios=[1.3, 1]))
fig.get_layout_engine().set(w_pad=0.02, h_pad=0.02, wspace=0.05)

# (a) college completion rate of each cohort group, by family background
EDGES = [1940, 1972, 1980, 1984, 1988, 1997]
LABS = ["1972 or earlier", "1973\u20131980", "1981\u20131984", "1985\u20131988", "1989\u20131997"]   # the names in the output file
TICKS = ["${\\leq}$1972", "1973\u201380", "1981\u201384", "1985\u201388", "${\\geq}$1989"]   # the tick labels, in the style of Figure 4 (the sample's last birth year is 1997)
c["grp"] = pd.cut(c.by, EDGES, labels=False)
n_cohort = c.groupby("grp").college.size()
rows = []
ax = axes[0]
for h, lab, sty, col in [(0, "Less advantaged children", "o-", LESS), (1, "Advantaged children", "s--", ADV)]:
    g = c[c.HP14 == h].groupby("grp").college.agg(["sum", "count", "mean"]).reset_index()
    g["n_cohort"] = n_cohort.loc[g.grp].values
    p = g["mean"]
    se = np.sqrt(p * (1 - p) / g["count"])
    ax.errorbar(g.grp, 100 * p, yerr=196 * se, fmt=sty, color=col, capsize=2, lw=1.1, ms=3.5, label=tr(lab))
    for x, y in zip(g.grp, 100 * p):
        # offsets of the percent labels, chosen so that no label sits on a line, an interval, the reform line or the zero line
        if h: dx, dy_, ha = {0: (-4, 3, "right"), 1: (-4, 3, "right"), 2: (4, -11, "left")}.get(x, (4, 3, "left"))
        else: dx, dy_, ha = {0: (-4, 3, "right"), 1: (-4, 3, "right")}.get(x, (4, -10, "left"))
        ax.annotate(f"{y:.0f}%", (x, y), xytext=(dx, dy_), textcoords="offset points", ha=ha, color=col)
    for _, r in g.iterrows():
        rows.append(dict(group=lab, cohort_group=LABS[int(r.grp)], graduates=int(r["sum"]), children_in_group=int(r["count"]),
                         children_in_cohort=int(r.n_cohort), graduates_per_100_children=100 * r["sum"] / r.n_cohort, completion_rate=r["mean"]))
ax.axvline(1.5, color="grey", linestyle="--", lw=.9)
ax.text(1.56, 1.5, tr("reform"), color="grey")   # below the lines, clear of the legend
# ratio of the completion rate of advantaged children to that of less advantaged children, under each cohort group
rate = pd.DataFrame(rows).pivot(index="cohort_group", columns="group", values="completion_rate").loc[LABS]
for x, r in enumerate(rate["Advantaged children"] / rate["Less advantaged children"]):
    ax.text(x, -7.2, (tr("ratio ") if x == 0 else "") + f"{r:.1f}", ha="center", color="#333")
ax.axhline(0, color="k", lw=.6)
stagger_xticks(ax, range(5), [tr(t) for t in TICKS])   # alternate rows, so that the labels do not run into each other
ax.set_xlabel(tr("Birth cohort")); ax.set_ylabel(tr("College completion rate (percent)"))
ax.set_ylim(-11, 88); ax.set_yticks(range(0, 81, 20)); ax.set_xlim(-0.8, 4.85)
ax.set_title(tr("(a) College completion by birth cohort")); ax.legend(loc="upper left", handlelength=2.0, borderpad=0.3, labelspacing=0.25, borderaxespad=0.3); ax.grid(alpha=.25)
left = pd.DataFrame(rows)
# pre- and post-reform summary of the same quantity (cohorts born 1980 or earlier against 1981 or later)
for h, lab in [(0, "Less advantaged children"), (1, "Advantaged children")]:
    for post, per in [(0, "born 1980 or earlier"), (1, "born 1981 or later")]:
        d = c[c.by >= 1981] if post else c[c.by <= 1980]
        dg = d[d.HP14 == h]
        rows.append(dict(group=lab, cohort_group=per, graduates=int(dg.college.sum()), children_in_group=len(dg), children_in_cohort=len(d),
                         graduates_per_100_children=100 * dg.college.sum() / len(d), completion_rate=dg.college.mean()))
left = pd.DataFrame(rows)
left.to_csv(os.path.join(ROOT, "output", "fig_first_stage_left.csv"), index=False)

# (b) binned scatter of the first stage by family background, in the specification of
#     code/u14_sample_facts.py (block C), at the child level: one regression with the instrument entering
#     separately for the two groups, province effects common to the groups, birth-year effects
#     specific to each group, parental income, gender and urban residence, and the group indicator
def dummies(s, prefix):
    return pd.get_dummies(s.astype(int), prefix=prefix, drop_first=True).astype(float)


H = c.HP14.values.astype(float)
X = pd.concat([c[["ParentInc", "female", "urban"]].astype(float), dummies(c.pc, "p"), dummies(c.by, "b"), c[["HP14"]].astype(float),
               dummies(c.by, "hb").multiply(c.HP14, axis=0)], axis=1)
X = X.loc[:, X.std() > 0].assign(const=1.0).values
ZG = {0: c.Z.values * (1 - H), 1: c.Z.values * H}
full = sm.OLS(c.college.values.astype(float), np.column_stack([ZG[0], ZG[1], X])).fit(cov_type="cluster", cov_kwds={"groups": c.pc.values})
ax = axes[1]
for h, lab, col, mk, nb in [(0, "Less advantaged children", LESS, "o", 20), (1, "Advantaged children", ADV, "s", 10)]:
    W = np.column_stack([ZG[1 - h], X])
    zr = sm.OLS(ZG[h], W).fit().resid; mr = sm.OLS(c.college.values.astype(float), W).fit().resid
    sel = np.where(H == h)[0]; order = sel[np.argsort(zr[sel])]; bins = np.array_split(order, nb)
    bx = [zr[b].mean() for b in bins]; bym = [mr[b].mean() for b in bins]
    ax.scatter(bx, bym, color=col, s=14, marker=mk, zorder=3, alpha=.9)
    xg = np.linspace(min(bx), max(bx), 50)
    ax.plot(xg, np.mean(bym) + full.params[h] * (xg - np.mean(bx)), color=col, linewidth=1.3, linestyle="--" if h else "-", label=f"{tr(lab).replace(' children', '')}:\n{tr('slope')} {full.params[h]:.3f} (SE {full.bse[h]:.3f})")
ax.axhline(0, color="k", lw=.6); ax.axvline(0, color="k", lw=.6)
ax.set_xlabel(tr("Instrument $Z$, residualized"))
ax.set_ylabel(tr("College completion, residualized"))
ax.set_ylim(None, 0.245); ax.set_yticks([-0.05, 0, 0.05, 0.1, 0.15, 0.2])
ax.set_title(tr("(b) First stage")); ax.legend(loc="upper left", handlelength=2.0, borderpad=0.3, labelspacing=0.3, borderaxespad=0.3); ax.grid(alpha=.25)

from fig_style import save
out = save(fig, "fig_first_stage.png", tight=False)
print("wrote", out, "group slopes", round(full.params[0], 3), round(full.params[1], 3))
