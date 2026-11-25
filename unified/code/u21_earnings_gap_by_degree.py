"""The earnings gap between advantaged and less advantaged children, among children without a degree and among graduates.

Sample: the 2,774 children with a level of earnings. Same entropy-balanced comparison as u16_identity_in_balanced_comparison.py and
u19_province_and_identity_intervals.py (block B): the weights are solved on all less advantaged children, not within degree cells.
Reported: children in each cell, raw and balanced means, the gap without a degree (the third part of the identity), the gap among graduates (that
gap plus the difference between the two groups' earnings differences by degree), 1,000 bootstrap draws resampling children within group and
solving the weights again. A least squares regression with the controls gives the same two gaps as a second check.
Output: output/u21_earnings_gap_by_degree.csv
"""
import os, sys, warnings
import numpy as np, pandas as pd, statsmodels.api as sm
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "output"); sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "u8_premium_specifications.py"), encoding="utf-8").read(); head = src[:src.index("kid = build_sample()") + len("kid = build_sample()")]
u8 = {"__file__": os.path.join(HERE, "u8_premium_specifications.py"), "__name__": "u8"}; exec(compile(head, "u8", "exec"), u8)
kid, P = u8["kid"], u8["P"]; sys.path.insert(0, os.path.join(P, "code"))
from ws_07b_entropy_balance import entropy_balance
k = kid.copy(); k["cohort"] = (k["birth_year"] // 5) * 5
top = k["provcd"].value_counts().head(15).index.tolist(); k["provcd_top"] = np.where(k["provcd"].isin(top), k["provcd"], -1)
cont = k[["ParentInc", "age_first"]].astype(float).values
X = np.hstack([cont, (cont - cont.mean(0)) ** 2, k[["female", "urban"]].astype(float).values,
               pd.get_dummies(k["cohort"].astype(int), prefix="coh", drop_first=True).astype(float).values,
               pd.get_dummies(k["provcd_top"].astype(int), prefix="prv", drop_first=True).astype(float).values])
t, c_ = (k["HP14"] == 1).values, (k["HP14"] == 0).values; y, m = k["log_y"].values, k["college"].values; it, ic = np.where(t)[0], np.where(c_)[0]
def gaps(a, b, **kw):
    w, _ = entropy_balance(X[b], X[a].mean(0), **kw); wm = lambda mask: float((y[b][mask] * w[mask]).sum() / w[mask].sum())
    a1, g1, a0, g0 = y[a][m[a] == 0].mean(), y[a][m[a] == 1].mean(), wm(m[b] == 0), wm(m[b] == 1)
    return dict(mean_nodeg_adv=a1, mean_nodeg_less=a0, mean_grad_adv=g1, mean_grad_less=g0, gap_without_degree=a1 - a0, gap_among_graduates=g1 - g0, share_grad_adv=m[a].mean(), share_grad_less=float((m[b] * w).sum())), w
pt, w = gaps(it, ic); rng = np.random.default_rng(20261031); dr = []
for _ in range(1000):
    try: dr.append(gaps(rng.choice(it, len(it)), rng.choice(ic, len(ic)), max_iter=200, tol=1e-7)[0])
    except Exception: pass
D = pd.DataFrame(dr); rows = [dict(item=i, estimate=pt[i], se=D[i].std(ddof=1), ci_lo=D[i].quantile(.025), ci_hi=D[i].quantile(.975)) for i in pt]
for lab, mask, g in [("children, advantaged, without a degree", (t & (m == 0)), None), ("children, advantaged, graduates", (t & (m == 1)), None), ("children, less advantaged, without a degree", (c_ & (m == 0)), None), ("children, less advantaged, graduates", (c_ & (m == 1)), None)]:
    rows.append(dict(item=lab, estimate=int(mask.sum())))
rows += [dict(item="raw gap without a degree", estimate=y[t & (m == 0)].mean() - y[c_ & (m == 0)].mean()), dict(item="raw gap among graduates", estimate=y[t & (m == 1)].mean() - y[c_ & (m == 1)].mean())]
rows += [dict(item="effective number of reweighted less advantaged children, without a degree", estimate=(w[m[ic] == 0].sum() ** 2) / (w[m[ic] == 0] ** 2).sum()), dict(item="effective number of reweighted less advantaged children, graduates", estimate=(w[m[ic] == 1].sum() ** 2) / (w[m[ic] == 1] ** 2).sum())]
Z = np.column_stack([np.ones(len(k)), t.astype(float), m, t * m, k["ParentInc"].astype(float).values, k["age_first"].astype(float).values, k["female"].astype(float).values, k["urban"].astype(float).values,
                     pd.get_dummies(k["cohort"].astype(int), drop_first=True).astype(float).values, pd.get_dummies(k["provcd"].astype(int), drop_first=True).astype(float).values])
ols = sm.OLS(y, Z).fit(cov_type="HC1"); bH, bI = ols.params[1], ols.params[3]; V = ols.cov_params(); seG = float(np.sqrt(V[1, 1] + V[3, 3] + 2 * V[1, 3]))
rows += [dict(item="least squares with controls: gap without a degree", estimate=bH, se=ols.bse[1]), dict(item="least squares with controls: gap among graduates", estimate=bH + bI, se=seG), dict(item="least squares with controls: difference between the two gaps", estimate=bI, se=ols.bse[3])]
R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "u21_earnings_gap_by_degree.csv"), index=False); print(R.round(4).to_string(index=False))
