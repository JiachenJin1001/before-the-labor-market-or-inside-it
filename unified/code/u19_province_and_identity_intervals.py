"""Two pieces of supporting evidence not recorded by the earlier runs.

A  Leave-one-province-out by province: the earnings reduced form, the first stage and the instrumented return for the row at 30 and over
   with each province left out in turn, on all children of the sample, with the two-row regression of
   u9_mature_age_earnings.py. u9 keeps only the smallest and largest values; this script records the province.
B  Bootstrap percentile intervals for the three parts of the identity inside the entropy-balanced comparison of
   u16_identity_in_balanced_comparison.py (the 2,774 children with a level of earnings), resampling children within
   group and solving the weights again in each draw, as u8_premium_specifications.py does for the premium. 1,000 draws.
Outputs: output/u19_A_leave_one_province_out.csv, output/u19_B_identity_intervals.csv
"""
import os, sys, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..")); OUT = os.path.join(ROOT, "output"); sys.path.insert(0, HERE)
os.environ["U9_REPS"] = "9"
# ------------------------------------------------------------------ A
src = open(os.path.join(HERE, "u9_mature_age_earnings.py"), encoding="utf-8").read(); src = src[:src.index("# ------------------------------------------------------------------ A. the sample")]
u9 = {"__file__": os.path.join(HERE, "u9_mature_age_earnings.py"), "__name__": "u9"}; exec(compile(src, "u9", "exec"), u9)
s, c, TB = u9["s"], u9["c"], u9["TB"]; rng = np.random.default_rng(20261030)
names = pd.read_csv(os.path.join(OUT, "u3_C_intensity_by_province.csv")).set_index("provcd").province_en.to_dict()
T = TB(s, s.Z.values, rng); base = (T.rf(s.y.values, wild=False)["coef"], T.iv(s.y.values, s.college.values)); rows = []
for p in np.unique(c.pc):
    ss = s[s.pc != p].reset_index(drop=True); T = TB(ss, ss.Z.values, rng); old = ss[ss.old == 1]
    rows.append(dict(province_code=int(p), province=names.get(int(p), ""), children_left_out=int((s[(s.pc == p)].pid.nunique())), rows_30_plus_left_out=int(((s.pc == p) & (s.old == 1)).sum()),
                     intensity=float(c[c.pc == p].pro_predict_growth.iloc[0]), reduced_form=T.rf(ss.y.values, wild=False)["coef"], first_stage=T.fs(ss.college.values, wild=False)["coef"], first_stage_F=T.fs(ss.college.values, wild=False)["t"] ** 2, instrumented_return=T.iv(ss.y.values, ss.college.values)))
A = pd.DataFrame(rows).sort_values("instrumented_return"); A.to_csv(os.path.join(OUT, "u19_A_leave_one_province_out.csv"), index=False)
print("all provinces:", np.round(base, 4)); print(A.round(3).to_string(index=False), flush=True)
# ------------------------------------------------------------------ B
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
t = (k["HP14"] == 1).values; c_ = (k["HP14"] == 0).values; y, m = k["log_y"].values, k["college"].values
def parts(it, ic, **kw):
    w, _ = entropy_balance(X[ic], X[it].mean(0), **kw); y1, m1, y0, m0 = y[it], m[it], y[ic], m[ic]
    wm = lambda v, mask: float((v[mask] * w[mask]).sum() / w[mask].sum())
    a1, g1 = y1[m1 == 0].mean(), y1[m1 == 1].mean(); a0, g0 = wm(y0, m0 == 0), wm(y0, m0 == 1); M1, M0 = m1.mean(), float((m0 * w).sum()); b1, b0 = g1 - a1, g0 - a0
    return dict(premium=y1.mean() - (y0 * w).sum(), completion_gap=M1 - M0, return_advantaged=b1, return_less_advantaged=b0, part_1_college_channel=b1 * (M1 - M0), part_2_same_degrees_worth_more=M0 * (b1 - b0), part_3_gap_without_a_degree=a1 - a0, parts_2_and_3=M0 * (b1 - b0) + a1 - a0)
it, ic = np.where(t)[0], np.where(c_)[0]; point = parts(it, ic); rng = np.random.default_rng(20261031); draws = []
for _ in range(1000):
    try:
        d = parts(rng.choice(it, len(it)), rng.choice(ic, len(ic)), max_iter=200, tol=1e-7)
        if all(np.isfinite(v) for v in d.values()): draws.append(d)
    except Exception: pass
D = pd.DataFrame(draws)
B = pd.DataFrame([dict(item=i, estimate=point[i], se=D[i].std(ddof=1), ci_lo=D[i].quantile(.025), ci_hi=D[i].quantile(.975), draws=len(D)) for i in point]); B.to_csv(os.path.join(OUT, "u19_B_identity_intervals.csv"), index=False); print(B.round(4).to_string(index=False))
# ------------------------------------------------------------------ A2: the province with the largest leave-one-out return
# wild cluster p-values (9,999 draws) and the lower end of the 95 percent Anderson-Rubin set (step 0.05, as in u9), without Shanghai
u9_ = {"__file__": os.path.join(HERE, "u9_mature_age_earnings.py"), "__name__": "u9"}; os.environ["U9_REPS"] = "9999"
_s = open(os.path.join(HERE, "u9_mature_age_earnings.py"), encoding="utf-8").read(); exec(compile(_s[:_s.index("# ------------------------------------------------------------------ A. the sample")], "u9", "exec"), u9_)
s_, TB_ = u9_["s"], u9_["TB"]; ss = s_[s_.pc != 31].reset_index(drop=True); T = TB_(ss, ss.Z.values, np.random.default_rng(20261032)); old = ss.old.values.astype(float)
rf_, fs_ = T.rf(ss.y.values), T.fs(ss.college.values); grid = np.round(np.arange(0.0, 6.001, 0.05), 2); pv = np.array([T.rf(ss.y.values - b * ss.college.values * old)["p_wild"] for b in grid]); inside = grid[pv >= 0.05]
pd.DataFrame([dict(left_out="Shanghai", reduced_form=rf_["coef"], reduced_form_se=rf_["se"], reduced_form_p_wild=rf_["p_wild"], first_stage=fs_["coef"], first_stage_se=fs_["se"], first_stage_F=fs_["t"] ** 2, first_stage_p_wild=fs_["p_wild"], instrumented_return=T.iv(ss.y.values, ss.college.values), ar95_lo=float(inside.min()), ar95_hi_on_grid_to_6=float(inside.max()))]).to_csv(os.path.join(OUT, "u19_A2_without_shanghai.csv"), index=False)
print(open(os.path.join(OUT, "u19_A2_without_shanghai.csv")).read())
