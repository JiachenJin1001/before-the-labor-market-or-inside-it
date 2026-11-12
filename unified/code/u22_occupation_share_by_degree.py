"""The share of working years in an official, managerial or professional occupation (CSCO major groups 1-2), by family background and degree (Section 5.3).

Sample: the children of the sample with at least two waves at ages 30 and over that report an occupation. The share is the mean of the indicator over those waves, with no adjustment for survey
year. Reported: the raw share in each of the four cells with the number of children; the same comparison with less advantaged children reweighted by entropy balancing to the parental income and
demographics of advantaged children (the moments of u19, block B, solved on these children); bootstrap intervals for the two gaps (1,000 draws, children resampled within group, weights solved again).
Output: output/u22_occupation_share_by_degree.csv
"""
import os, sys, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "output"); sys.path.insert(0, HERE); os.environ["U9_REPS"] = "9"
src = open(os.path.join(HERE, "u9_mature_age_earnings.py"), encoding="utf-8").read(); src = src[:src.index("# ------------------------------------------------------------------ A. the sample")]
u9 = {"__file__": os.path.join(HERE, "u9_mature_age_earnings.py"), "__name__": "u9"}; exec(compile(src, "u9", "exec"), u9)
c, W0 = u9["c"], u9["W0"]
d = W0[W0.pid.isin(c.pid) & W0.occ_code.notna() & (W0.occ_code > 0) & (W0.age >= 30)].copy(); d["prof"] = (d.occ_code.astype(int).astype(str).str[0].astype(int) <= 2).astype(float)
g = d.groupby("pid").prof.agg(["mean", "size"]).reset_index(); g = g[g["size"] >= 2]
src = open(os.path.join(HERE, "u8_premium_specifications.py"), encoding="utf-8").read(); head = src[:src.index("kid = build_sample()") + len("kid = build_sample()")]
u8 = {"__file__": os.path.join(HERE, "u8_premium_specifications.py"), "__name__": "u8"}; exec(compile(head, "u8", "exec"), u8)
sys.path.insert(0, os.path.join(u8["P"], "code"))
from ws_07b_entropy_balance import entropy_balance
k = u8["kid"].merge(g, on="pid"); k["cohort"] = (k["birth_year"] // 5) * 5; top = u8["kid"]["provcd"].value_counts().head(15).index.tolist(); k["provcd_top"] = np.where(k["provcd"].isin(top), k["provcd"], -1)
cont = k[["ParentInc", "age_first"]].astype(float).values
X = np.hstack([cont, (cont - cont.mean(0)) ** 2, k[["female", "urban"]].astype(float).values, pd.get_dummies(k["cohort"].astype(int), prefix="coh", drop_first=True).astype(float).values, pd.get_dummies(k["provcd_top"].astype(int), prefix="prv", drop_first=True).astype(float).values])
X = X[:, X.std(0) > 0]; t, l = (k["HP14"] == 1).values, (k["HP14"] == 0).values; y, m = k["mean"].values, k["college"].values; it, il = np.where(t)[0], np.where(l)[0]
def bal(a, b, **kw):
    w, _ = entropy_balance(X[b], X[a].mean(0), **kw); wm = lambda mask: float((y[b][mask] * w[mask]).sum() / w[mask].sum())
    a0, a1, b0, b1 = y[a][m[a] == 0].mean(), y[a][m[a] == 1].mean(), wm(m[b] == 0), wm(m[b] == 1)
    return dict(balanced_less_no_degree=b0, balanced_less_graduates=b1, adv_no_degree=a0, adv_graduates=a1, balanced_gap_no_degree=a0 - b0, balanced_gap_graduates=a1 - b1)
def raw(a, b):
    return dict(raw_gap_no_degree=y[a][m[a] == 0].mean() - y[b][m[b] == 0].mean(), raw_gap_graduates=y[a][m[a] == 1].mean() - y[b][m[b] == 1].mean())
pt = {**bal(it, il), **raw(it, il)}; rng = np.random.default_rng(20261101); dr = []
for _ in range(1000):
    a, b = rng.choice(it, len(it)), rng.choice(il, len(il))
    try: dr.append({**bal(a, b, max_iter=200, tol=1e-7), **raw(a, b)})
    except Exception: pass
D = pd.DataFrame(dr); rows = [dict(item=i, estimate=pt[i], se=D[i].std(ddof=1), ci_lo=D[i].quantile(.025), ci_hi=D[i].quantile(.975), draws=len(D)) for i in pt]
for lab, mask in [("advantaged, graduates", t & (m == 1)), ("advantaged, no degree", t & (m == 0)), ("less advantaged, graduates", l & (m == 1)), ("less advantaged, no degree", l & (m == 0))]:
    rows += [dict(item=f"raw share, {lab}", estimate=y[mask].mean()), dict(item=f"children, {lab}", estimate=int(mask.sum()))]
rows += [dict(item="raw share, advantaged, all", estimate=y[t].mean()), dict(item="raw share, less advantaged, all", estimate=y[l].mean())]
R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "u22_occupation_share_by_degree.csv"), index=False); print(R.round(4).to_string(index=False))
