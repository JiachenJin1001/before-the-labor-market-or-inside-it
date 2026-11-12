"""m19: the two groups' earnings processes fitted jointly, with cross-group restrictions.

The paper's minimum-distance estimator (04_method1_md.py, m7_md_cellweighted_boot.py) fits the
permanent-AR(1) process separately to the fifteen autocovariances of each group. This script
stacks the thirty moments and fits the two groups together under restrictions on their parameters:

  free            six parameters, reproduces the two separate fits
  all equal       one process for both groups (three parameters)
  scale           the autocovariances of advantaged children are kappa times those of less
                  advantaged children (four parameters)
  one parameter   permanent variance, persistence, or innovation variance free, the others common
  common eps2     permanent variance and persistence free, innovation variance common (the ridge)

Estimator conventions are those of m7: residual log earnings y_tilde_w demeaned within group and
year; moments weighted by the number of children behind each; bootstrap that resamples children
within each group and re-solves every model in each draw (B = 1000).

Tests of a restriction against the model that nests it: the distance statistic D = Q(restricted)
minus Q(unrestricted), with its null distribution from the same bootstrap draws after recentering
each group's moments on the fitted moments of the restricted model (fixed weights, so D has no
chi-squared reference), B = 500. A Wald test on the three parameter gaps of the free model uses
the bootstrap covariance of the gaps.

Outputs (output/tables/):
  m19_joint_models.csv   point estimates of every model, bootstrap standard errors
  m19_joint_gaps.csv     gaps (H minus L) and kappa, standard errors, percentile intervals
  m19_joint_tests.csv    distance tests and the Wald test
"""
import os as _os, time
_WSROOT = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
import numpy as np, pandas as pd
from scipy import stats
from scipy.optimize import minimize

OUT = _os.path.join(_WSROOT, "output", "tables")
B, BT, SEED = 1000, 500, 20261027
BOUNDS = dict(eta2=(0.0, 2.0), rho=(-0.95, 0.95), eps2=(1e-6, 2.0), kappa=(0.2, 5.0))

d = pd.read_pickle(_os.path.join(_WSROOT, "data/intermediate/panel_resid.pkl")).dropna(subset=["y_tilde_w", "HighParentOcc14"])
piv = d.pivot_table(index="pid", columns="year", values="y_tilde_w")
Y = piv.values; h = d.groupby("pid")["HighParentOcc14"].first().reindex(piv.index).astype(int).values
T = Y.shape[1]; P = [(i, j) for i in range(T) for j in range(i, T)]
print(f"children {len(h):,} (H {int(h.sum())}, L {int((h == 0).sum())}); waves {list(piv.columns)}; {len(P)} moments per group")


def moments(Y):
    Y = Y - np.nanmean(Y, 0)
    om = np.full(len(P), np.nan); n = np.zeros(len(P))
    for k, (i, j) in enumerate(P):
        p = Y[:, i] * Y[:, j]; ok = ~np.isnan(p); c = ok.sum()
        if c >= 2:
            om[k] = p[ok].mean(); n[k] = c
    return om, n


def group_moments(Y, h):
    return {g: moments(Y[h == v]) for g, v in (("H", 1), ("L", 0))}


def model_cov(eta2, rho, eps2):
    return np.array([eta2 + (rho ** (j - i)) * eps2 / (1 - rho ** 2) for i, j in P])


_p = lambda e, r, s: dict(eta2=e, rho=r, eps2=s)
MODELS = {
    "free": (["eta2_H", "rho_H", "eps2_H", "eta2_L", "rho_L", "eps2_L"], lambda t: (_p(t[0], t[1], t[2]), _p(t[3], t[4], t[5]))),
    "all equal": (["eta2", "rho", "eps2"], lambda t: (_p(t[0], t[1], t[2]), _p(t[0], t[1], t[2]))),
    "scale": (["eta2", "rho", "eps2", "kappa"], lambda t: (_p(t[3] * t[0], t[1], t[3] * t[2]), _p(t[0], t[1], t[2]))),
    "eta2 differs": (["eta2_H", "eta2_L", "rho", "eps2"], lambda t: (_p(t[0], t[2], t[3]), _p(t[1], t[2], t[3]))),
    "rho differs": (["eta2", "rho_H", "rho_L", "eps2"], lambda t: (_p(t[0], t[1], t[3]), _p(t[0], t[2], t[3]))),
    "eps2 differs": (["eta2", "rho", "eps2_H", "eps2_L"], lambda t: (_p(t[0], t[1], t[2]), _p(t[0], t[1], t[3]))),
    "common eps2": (["eta2_H", "eta2_L", "rho_H", "rho_L", "eps2"], lambda t: (_p(t[0], t[2], t[4]), _p(t[1], t[3], t[4]))),
}
BASE = dict(eta2=0.11, rho=0.18, eps2=0.32, kappa=1.0)


def fit(mom, model):
    names, fn = MODELS[model]
    def crit(th):
        pH, pL = fn(th); q = 0.0
        for g, p in (("H", pH), ("L", pL)):
            om, n = mom[g]; m = ~np.isnan(om); e = (om - model_cov(p["eta2"], p["rho"], p["eps2"]))[m]
            q += float(e @ (n[m] * e))
        return q
    best = None
    for r0 in (0.05, 0.2, 0.4):
        for e0 in (0.03, 0.12):
            x0 = [dict(BASE, rho=r0, eta2=e0)[nm.split("_")[0]] for nm in names]
            r = minimize(crit, np.array(x0, float), method="L-BFGS-B", bounds=[BOUNDS[nm.split("_")[0]] for nm in names],
                         options=dict(maxiter=5000, ftol=1e-15, gtol=1e-11))
            if best is None or r.fun < best.fun:
                best = r
    pH, pL = fn(best.x)
    return best.x, best.fun, pH, pL


share = lambda p: p["eta2"] / (p["eta2"] + p["eps2"] / (1 - p["rho"] ** 2))
total = lambda p: p["eta2"] + p["eps2"] / (1 - p["rho"] ** 2)


def summ(th, model, pH, pL, q):
    s = dict(model=model, crit=q)
    for k in ("eta2", "rho", "eps2"):
        s[f"{k}_H"], s[f"{k}_L"], s[f"{k}_gap"] = pH[k], pL[k], pH[k] - pL[k]
    s["share_H"], s["share_L"], s["share_gap"] = share(pH), share(pL), share(pH) - share(pL)
    s["var_H"], s["var_L"], s["var_gap"] = total(pH), total(pL), total(pH) - total(pL)
    s["kappa"] = th[3] if model == "scale" else np.nan
    return s


mom = group_moments(Y, h)
point = {m: summ(*(lambda r: (r[0], m, r[2], r[3], r[1]))(fit(mom, m))) for m in MODELS}
fitted = {m: fit(mom, m) for m in MODELS}

# ---------------------------------------------------------------- bootstrap of every model
rng = np.random.default_rng(SEED); iH, iL = np.where(h == 1)[0], np.where(h == 0)[0]
draws = {m: [] for m in MODELS}; t0 = time.time()
for b in range(B):
    idx = np.concatenate([rng.choice(iH, iH.size), rng.choice(iL, iL.size)]); mb = group_moments(Y[idx], h[idx])
    for m in MODELS:
        th, q, pH, pL = fit(mb, m); draws[m].append(summ(th, m, pH, pL, q))
draws = {m: pd.DataFrame(r) for m, r in draws.items()}
print(f"bootstrap B={B}: {time.time() - t0:.0f}s")

COLS = ["eta2_H", "rho_H", "eps2_H", "eta2_L", "rho_L", "eps2_L", "share_H", "share_L", "var_H", "var_L", "kappa"]
models = []
for m in MODELS:
    r = dict(model=m, parameters=len(MODELS[m][0]), crit=point[m]["crit"])
    for c in COLS:
        r[c] = point[m][c]; r[c + "_se"] = draws[m][c].std(ddof=1) if c != "kappa" or m == "scale" else np.nan
    models.append(r)
pd.DataFrame(models).to_csv(_os.path.join(OUT, "m19_joint_models.csv"), index=False)

GAPS = {"free": ["eta2", "rho", "eps2", "share", "var"], "scale": ["kappa"], "eta2 differs": ["eta2", "share"], "rho differs": ["rho"],
        "eps2 differs": ["eps2"], "common eps2": ["eta2", "rho", "share"]}
gaps = []
for m, ks in GAPS.items():
    for k in ks:
        col = "kappa" if k == "kappa" else f"{k}_gap"; x = draws[m][col].values; pt = point[m][col]
        gaps.append(dict(model=m, quantity=col, point=pt, se=x.std(ddof=1), ci95_lo=np.quantile(x, 0.025), ci95_hi=np.quantile(x, 0.975),
                         ci90_lo=np.quantile(x, 0.05), ci90_hi=np.quantile(x, 0.95), mde80=2.8 * x.std(ddof=1), boot_mean=x.mean()))
pd.DataFrame(gaps).to_csv(_os.path.join(OUT, "m19_joint_gaps.csv"), index=False)

# ---------------------------------------------------------------- tests
NEST = [("all equal", "free"), ("all equal", "scale"), ("all equal", "common eps2"), ("common eps2", "free"),
        ("all equal", "eta2 differs"), ("all equal", "rho differs"), ("all equal", "eps2 differs")]
rng = np.random.default_rng(SEED + 1); tests = []; t0 = time.time()
idxs = [np.concatenate([rng.choice(iH, iH.size), rng.choice(iL, iL.size)]) for _ in range(BT)]
mbs = [group_moments(Y[ix], h[ix]) for ix in idxs]
for r_m, u_m in NEST:
    D = fitted[r_m][1] - fitted[u_m][1]; pH, pL = fitted[r_m][2], fitted[r_m][3]
    tgt = {"H": model_cov(pH["eta2"], pH["rho"], pH["eps2"]), "L": model_cov(pL["eta2"], pL["rho"], pL["eps2"])}
    Ds = np.empty(BT)
    for b, mb in enumerate(mbs):
        mc = {g: (mb[g][0] - mom[g][0] + tgt[g], mb[g][1]) for g in ("H", "L")}
        Ds[b] = fit(mc, r_m)[1] - fit(mc, u_m)[1]
    tests.append(dict(test="distance", restricted=r_m, unrestricted=u_m, restrictions=len(MODELS[u_m][0]) - len(MODELS[r_m][0]), statistic=D, p=float(np.mean(Ds >= D)), B=BT))
G = draws["free"][["eta2_gap", "rho_gap", "eps2_gap"]].values; g0 = np.array([point["free"][k] for k in ("eta2_gap", "rho_gap", "eps2_gap")])
V = np.cov(G.T); W = float(g0 @ np.linalg.solve(V, g0)); Wb = np.array([(x - G.mean(0)) @ np.linalg.solve(V, x - G.mean(0)) for x in G])
tests.append(dict(test="Wald on the three gaps of the free model, chi-squared", restricted="all equal", unrestricted="free", restrictions=3, statistic=W, p=float(1 - stats.chi2.cdf(W, 3)), B=B))
tests.append(dict(test="Wald on the three gaps of the free model, bootstrap percentile", restricted="all equal", unrestricted="free", restrictions=3, statistic=W, p=float(np.mean(Wb >= W)), B=B))
tests = pd.DataFrame(tests); tests.to_csv(_os.path.join(OUT, "m19_joint_tests.csv"), index=False)
print(f"tests: {time.time() - t0:.0f}s")

pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
print(pd.DataFrame(models)[["model", "parameters", "crit", "eta2_H", "eta2_L", "rho_H", "rho_L", "eps2_H", "eps2_L", "share_H", "share_L", "kappa", "kappa_se"]].round(4).to_string(index=False))
print(pd.DataFrame(gaps).round(4).to_string(index=False)); print(tests.round(4).to_string(index=False))
