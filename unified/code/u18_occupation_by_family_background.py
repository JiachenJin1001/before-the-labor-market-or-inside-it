"""The occupational effect of college by family background (Section 5.3 of the paper).

The regression of u12_returns_by_family_background.py (two-row design; the instrument and college completion enter
once per group and row; province effects common; birth-year effects specific to each group) with the occupation
outcome of u9_mature_age_earnings.py: the share of the child's waves at ages 30 and over spent in an official,
managerial or professional occupation (CSCO major groups 1-2), the share below 30 as the second row. For each group:
the first stage (the child's completion x 1[30+] on the group's instrument, wild p), the reduced form (wild p), the
instrumented effect with its clustered standard error, the least squares coefficient, and the test that the two
instrumented effects are equal. Wild cluster bootstrap by province, 9,999 Rademacher draws, null imposed.
Output: output/u18_occupation_by_family_background.csv.
"""
import os, sys, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
REPS = int(os.environ.get("U18_REPS", "9999")); os.environ["U9_REPS"] = str(REPS)
src = open(os.path.join(HERE, "u9_mature_age_earnings.py"), encoding="utf-8").read(); src = src[:src.index("# ------------------------------------------------------------------ A. the sample")]
u9 = {"__file__": os.path.join(HERE, "u9_mature_age_earnings.py"), "__name__": "u9"}; exec(compile(src, "u9", "exec"), u9)
Design, c, cl, tb_X, occ_rows = u9["Design"], u9["c"], u9["cl"], u9["tb_X"], u9["occ_rows"]
KEYS = [("less advantaged", 1), ("advantaged", 1), ("less advantaged", 0), ("advantaged", 0)]

so = occ_rows(c); rng = np.random.default_rng(20261003)
H = so.HP14.values.astype(float); old = so.old.values.astype(float); sw = np.sqrt(so.w.values.astype(float)); y = so.y.values; m = so.college.values; g = so.pc.values
sel = lambda grp, o: (old == o) * (H == (1.0 if grp == "advantaged" else 0.0))
Z4 = {k: so.Z.values * sel(*k) for k in KEYS}; M4 = {k: m * sel(*k) for k in KEYS}; X = tb_X(so, group_fe=True); W = lambda a: sw[:, None] * a
Zm = W(np.column_stack([Z4[k] for k in KEYS] + [X])); En = W(np.column_stack([M4[k] for k in KEYS]))
Xh = np.column_stack([Zm @ np.linalg.lstsq(Zm, En, rcond=None)[0], W(X)]); b = np.linalg.lstsq(Xh, sw * y, rcond=None)[0]
u = sw * y - np.column_stack([En, W(X)]) @ b; bread = np.linalg.pinv(Xh.T @ Xh); meat = np.zeros((Xh.shape[1],) * 2)
for k in np.unique(g): sc = Xh[g == k].T @ u[g == k]; meat += np.outer(sc, sc)
G, n, kk = len(np.unique(g)), len(u), Xh.shape[1]; V = bread @ meat @ bread * G / (G - 1) * (n - 1) / (n - kk)
z_eq = float((b[1] - b[0]) / np.sqrt(V[0, 0] + V[1, 1] - 2 * V[0, 1])); ls = cl(sw * y, np.column_stack([En, W(X)]), g)
rows = []
for i, grp in enumerate(("less advantaged", "advantaged")):
    k1 = (grp, 1); D = Design(so, sw * Z4[k1], W(np.column_stack([Z4[k] for k in KEYS if k != k1] + [X])), rng)
    f = D.rf(sw * m * old); e = D.rf(sw * y)
    rows.append(dict(outcome="share of waves at 30 and over in an official, managerial or professional occupation", group=grp, rows_at_30_and_over=int(sel(grp, 1).sum()),
                     fs=f["coef"], fs_se=f["se"], F=f["t"] ** 2, fs_p_wild=f["p_wild"], rf=e["coef"], rf_se=e["se"], rf_p_wild=e["p_wild"],
                     iv=float(b[i]), iv_se=float(np.sqrt(V[i, i])), ls=float(ls.params[i]), ls_se=float(ls.bse[i]),
                     iv_gap_advantaged_minus_less=float(b[1] - b[0]), iv_gap_se=float(np.sqrt(V[0, 0] + V[1, 1] - 2 * V[0, 1])), equal_effects_z=z_eq))
    print(f"{grp:16s} rows at 30+ {rows[-1]['rows_at_30_and_over']:5d} | fs {f['coef']:+.3f} ({f['se']:.3f}) F {f['t'] ** 2:5.1f} | rf {e['coef']:+.3f} ({e['se']:.3f}) p {e['p_wild']:.3f} | iv {b[i]:+.2f} ({np.sqrt(V[i, i]):.2f}) | ls {ls.params[i]:+.2f}")
print(f"  test of equal effects z = {z_eq:.2f}")
pd.DataFrame(rows).to_csv(os.path.join(HERE, "..", "output", "u18_occupation_by_family_background.csv"), index=False); print("wrote")
