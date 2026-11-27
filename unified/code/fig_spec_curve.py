"""The premium across specifications: fifteen in the figure of the Online Appendix,
thirteen in Figure 1 of the paper.

Reads the estimates and 95 percent intervals written by
u8_premium_specifications.py (the rows marked as belonging to the figure).
The upper panel plots the coefficient on the indicator for advantaged
children, sorted by size; the lower panel marks how each specification
differs from the baseline.
Output: paper/figures/fig_spec_curve.png (all fifteen, used by the Online Appendix); with SPEC_PAPER=1,
paper/figures/fig_spec_curve_paper.png (the thirteen of the paper, without the urban and rural subsamples).
"""
import os
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

CRE, EB, XS = "Correlated random effects", "Entropy balancing", "Cross-section, one observation per child"
# what each specification changes relative to the baseline
CHANGES = {
    "baseline: family income of the parental household": "base",
    "parents' own labor income as the income control": "labor",
    "income deflated by the provincial consumer price index": "cpi",
    "most frequent retrospective report of parental occupation": "altdef",
    "indicator widened to CSCO major groups 1 to 3": "altdef",
    "indicator narrowed to CSCO major group 1": "altdef",
    "three regions in place of province effects": "region",
    "parental income from the 2010 and 2012 waves, before the earnings window": "window",
    "parental income from waves with the child aged 40 or less": "window",
    "parental income from waves with the child aged 35 or less": "window",
    "children recorded as rural in most of their waves": "subsample",
    "children recorded as urban in most of their waves": "subsample",
    "parental party membership added (cross-section)": "marker",
    "parental state-sector employment added (cross-section)": "marker+subsample",
    "entropy balancing": "",
}
# row labels of the lower panel, one line each
FEATS = [("Baseline specification", "base"),
         ("Parents\u2019 own labor income as the income control", "labor"),
         ("Alternative definition of the parental occupation indicator", "altdef"),
         ("Family income from 2010\u201312 waves, or child aged at most 35 or 40", "window"),
         ("Urban, rural, or parent-still-working subsample", "subsample"),
         ("Parental party membership or state-sector employment added", "marker"),
         ("Region effects in place of province effects", "region"),
         ("Income deflated by provincial CPI", "cpi")]

d = pd.read_csv(os.path.join(ROOT, "output", "u8_premium_specifications.csv"))
d = d[d.in_figures_of_specifications].copy()
assert set(d.specification) == set(CHANGES), set(d.specification) ^ set(CHANGES)
PAPER = os.environ.get("SPEC_PAPER") == "1"
if PAPER:
    d = d[~d.specification.isin(["children recorded as rural in most of their waves", "children recorded as urban in most of their waves"])].copy()
    FEATS = [("Subsample with a parent still working", k) if k == "subsample" else (l, k) for l, k in FEATS]
for _, key in FEATS:
    d[key] = d.specification.map(lambda s: int(key in CHANGES[s].split("+")))
d = d.sort_values(["estimate", "base"]).reset_index(drop=True)
colors = {CRE: "#08519c", EB: "#d95f02", XS: "#555555"}   # the dark blue and the orange of the other figures, and a dark grey
marks = {CRE: "o", EB: "s", XS: "^"}
from fig_style import setup, tr, save
setup(size=8)   # drawn at 5.46 inches, the printed width at 0.84 of the text width: the text prints at 8 points there
PT = 72.0
W, H = 5.46, 2.3                     # inches
ROW, XLAB, GAP, TOP = 10.2, 14.0, 5.0, 3.0   # points: row pitch of the lower panel, room for its axis title, gap between the panels, top margin
fig = plt.figure(figsize=(W, H))
a1 = fig.add_axes([0.5, 0.5, 0.4, 0.4]); a2 = fig.add_axes([0.5, 0.1, 0.4, 0.3])
for i, r in d.iterrows():
    a1.plot([i, i], [r.lo, r.hi], color=colors[r.estimator], alpha=.6, lw=1.1)
    a1.plot(i, r.estimate, marks[r.estimator], color=colors[r.estimator], ms=3.8)
    if r.base == 1:
        a1.plot(i, r.estimate, "D", mfc="none", mec="k", ms=7.5, mew=1.0)
        a1.annotate(tr("baseline"), (i, r.hi), xytext=(0, 3), textcoords="offset points", ha="center")
a1.axhline(0, color="k", lw=.7)
a1.set_ylabel(tr("Premium\n(log points)"))
a1.set_xticks([])
lo_, hi_ = a1.get_ylim(); a1.set_ylim(lo_, hi_ + 0.12 * (hi_ - lo_))   # room for the label of the baseline
for j, (nm, key) in enumerate(FEATS):
    on = d.index[d[key] == 1]
    a2.plot(on, [j] * len(on), "o", ms=3.0, color="#333")
a2.set_yticks(range(len(FEATS))); a2.set_yticklabels([tr(f[0]) for f in FEATS])
a2.set_ylim(-.6, len(FEATS) - .4); a2.invert_yaxis(); a2.set_xlim(-0.6, len(d) - 0.4); a1.set_xlim(a2.get_xlim())
a2.set_xticks([]); a2.set_xlabel(tr("Specifications, sorted by point estimate"), labelpad=3); a2.grid(axis="x", alpha=.2)
# layout in points: the row labels set the left edge of both panels; the lower panel has one row pitch per row
fig.canvas.draw(); rend = fig.canvas.get_renderer()
lab_w = max(t.get_window_extent(rend).width for t in a2.get_yticklabels()) * PT / fig.dpi
left = (lab_w + 3.5 + 3.5 + 2.0) / (W * PT); right = 1 - 3.0 / (W * PT)
h2 = ROW * len(FEATS) / (H * PT); b2 = XLAB / (H * PT)
b1 = b2 + h2 + GAP / (H * PT); h1 = 1 - TOP / (H * PT) - b1
a2.set_position([left, b2, right - left, h2]); a1.set_position([left, b1, right - left, h1])
# the legend of the estimators sits in the empty space left of the upper panel, above the row labels
fig.legend(handles=[plt.Line2D([], [], marker=marks[k], ls="", color=c, ms=3.8, label=tr(k)) for k, c in colors.items()],
           loc="center left", bbox_to_anchor=(0.0, b1 + h1 / 2), handletextpad=0.3, borderpad=0.35, labelspacing=0.3, framealpha=0.95)
out = save(fig, "fig_spec_curve_paper.png" if PAPER else "fig_spec_curve.png", tight=False); print("wrote", out, "specifications:", len(d))
print(d[["specification", "estimate", "lo", "hi"]].round(3).to_string())
print("intervals that exclude zero:", int(((d.lo > 0) | (d.hi < 0)).sum()))
