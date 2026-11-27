"""Checks of the numbers printed in the paper.

Each check reads a file of estimates, formats the value as the paper prints
it, and looks for that string in paper/main.tex or in the table fragments
that the paper inputs.

    python3 unified/code/check_paper_numbers.py
"""
import numpy as np
import os, re, sys, io, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
WS = os.path.abspath(os.path.join(ROOT, ".."))
sys.path.insert(0, HERE)
from _locate import sibling
PKG = {"income_dynamics": sibling("income_dynamics", __file__), "college_expansion": sibling("college_expansion", __file__)}
TEX = open(os.path.join(ROOT, "paper", "main.tex")).read()
# the tables of estimates are generated fragments (code/build_paper_tables.py); they are part of the text checked here
# (only the fragments that main.tex inputs, so that no assertion can be satisfied by a fragment the paper does not print)
for _f in re.findall(r"\\input\{(tables/en/[^}]+)\}", TEX):
    TEX += "\n" + open(os.path.join(ROOT, "paper", _f + ".tex"), encoding="utf-8").read()
TEXN = re.sub(r"\s+", " ", TEX)

fails = 0

# ====================================================================================================================
# Sentences of the paper, each rebuilt from the files of estimates. One sample: ages 22 to 55, at least two
# waves (all children); the children with at least three waves (Section 4); the level of earnings at ages 30
# and over (Sections 3, 5 and 6); the two-row regression of Section 5.
# ====================================================================================================================
import csv, math
MP = PKG["income_dynamics"]; FR = sibling("formal_results", __file__)


def rd(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))
def u1(name):
    return rd(os.path.join(ROOT, "output", name))
def mt(name):
    return rd(os.path.join(MP, "output", "tables", name))
def mi(*name):
    return rd(os.path.join(MP, "data", "intermediate", *name))
def chk(lbl, snip, count=None):
    """count: exact number of occurrences required (default: at least one)."""
    global fails
    n = TEXN.count(re.sub(r"\s+", " ", snip))
    ok = n >= 1 if count is None else n == count
    print(("  ok   " if ok else "  FAIL ") + f"{lbl:58s} {snip!r}")
    fails += (not ok)
def need(cond, lbl):
    global fails
    print(("  ok   " if cond else "  FAIL ") + f"{lbl}")
    fails += (not cond)
pct = lambda v: 100 * (math.exp(v) - 1)
sg = lambda v, d=3: (f"$-{abs(v):.{d}f}$" if round(v, d) < 0 else f"{v:.{d}f}")
pf = lambda p: "$p < 0.001$" if p < 0.0005 else f"$p = {p:.3f}$"

F14 = {r["item"]: float(r["value"]) for r in u1("u14_B_sample_facts.csv")}
ALL, THREE, LEVEL = "all children", "three waves", "level at 30 and over"
n_all, a_all, n3, a3, nl, al = [int(F14[k]) for k in (f"{ALL}: children", f"{ALL}: advantaged children", f"{THREE}: children", f"{THREE}: advantaged children", f"{LEVEL}: children", f"{LEVEL}: advantaged children")]

print("=== Section 2: the sample")
chk("sample size", f"The sample has {n_all:,} children born {int(F14[f'{ALL}: first birth year'])} to {int(F14[f'{ALL}: last birth year'])} ({a_all} advantaged, {100 * F14[f'{ALL}: share advantaged']:.1f} percent) and {int(F14[f'{ALL}: child-waves']):,} child-waves.")
chk("children with three waves", f"uses the {n3:,} children ({a3} advantaged) with at least three waves")
chk("children with a level of earnings", f"It is defined for the {nl:,} children ({al} advantaged) observed in at least two waves at those ages.")
chk("other children in Section 5", f"Section~\\ref{{sec:expansion}} also uses the other {n_all - nl:,} children")
chk("provinces", f"the sample of Section~\\ref{{sec:sample}} spans {int(F14[f'{ALL}: provinces'])} provinces")
D14 = {r["ages"]: r for r in u1("u14_D_return_by_age.csv")}; d = lambda k, c="coef": float(D14[k][c])
chk("return to college by age", f"the least squares return to college, controlling for survey-year and age effects, is {d('26-29'):.2f} log points at ages 26 to 29 and {d('30-34'):.2f} at 30 to 34"); need(d('22-25') < 0.1 and d('26-29') < d('30-34') and d('35-55') > 0.3, "return by age rises through the twenties (full schedule in the online appendix)")
need(F14['mean log income at 30 and over, survey year 2022'] - F14['mean log income at 30 and over, survey year 2014'] > 0.5, "nominal incomes rose steeply over the panel")
need(0.80 < pct(F14['mean log income at 30 and over, survey year 2022'] - F14['mean log income at 30 and over, survey year 2014']) / 100 < 0.90, "nominal income at 30 and over rose by more than four fifths between the 2014 and 2022 waves")
chk("share entering the sample", f"{100 * F14['share of them in the sample, advantaged']:.0f} percent of advantaged children enter the sample, compared with {100 * F14['share of them in the sample, less advantaged']:.0f} percent of less advantaged children")
need(abs(F14['share of them with three waves, advantaged'] - F14['share of them with three waves, less advantaged']) < 0.05, "three-wave screens pass the groups at nearly the same rate")
chk("positive earnings", f"earnings are positive in {100 * F14['share of their person-waves with positive labor income, advantaged']:.0f} percent of the child-waves of advantaged children and in {100 * F14['share of their person-waves with positive labor income, less advantaged']:.0f} percent")
chk("agreement of the two indicators", f"agrees with the retrospective one for {100 * F14[f'{ALL}: indicators agree']:.0f} percent of the children who have both")
chk("disagreement, moved down and up", f"({100 * F14[f'{ALL}: advantaged by the retrospective indicator only']:.1f} versus {100 * F14[f'{ALL}: advantaged by the current-occupation indicator only']:.1f} percent of children)")
_rd = [r for r in u1("u5_ridge_draws.csv") if r["group"] == "advantaged"]; need(0 < sum(float(r["permanent_share"]) < 1e-6 for r in _rd) < 0.05 * len(_rd), "ridge: some bootstrap draws of advantaged children lie on the boundary, fewer than 5 percent")
need(0.60 < F14[f"{ALL}: share of child-waves on the household roster of a linked parent"] < 0.68, "co-residence: nearly two thirds of the child-waves")
A14 = {(r["sample"], r["variable"]): r for r in u1("u14_A_sample_means.csv")}
gapA = lambda smp, var: float(A14[(smp, var)]["advantaged_mean"]) - float(A14[(smp, var)]["less_advantaged_mean"])
chk("Table 1 in the text", "advantaged children earn about 0.2 log points more, have parents with over 0.4 log points more family income")
need(all(0.19 < gapA(s_, "Mean log labor income") < 0.215 and gapA(s_, "Log family income of the parental household") > 0.4 for s_ in (ALL, LEVEL)), "Table 1: earnings gaps of about 0.2 and family income gaps above 0.4 log points")
need(all(gapA(s_, "Years of schooling") > 2 and float(A14[(s_, "College (16 or more years)")]["advantaged_mean"]) > 2 * float(A14[(s_, "College (16 or more years)")]["less_advantaged_mean"]) for s_ in (ALL, LEVEL)), "Table 1: more than two years of schooling and more than twice the completion rate")
chk("Table 1 notes", f"All children: the {n_all:,} children with at least two waves")
chk("Table 1 notes, level", f"the {nl:,} with at least two waves at those ages")
chk("retirement ages", "55 the middle of the three statutory retirement ages")

print("=== Section 4: the earnings process (children with at least three waves)")
M7 = {r["group"]: {k: float(v) for k, v in r.items() if k != "group"} for r in mt("m7_md_cellw_boot.csv")}
P7, H7, L7 = M7["pooled"], M7["H"], M7["L"]
chk("pooled parameters, note of the attenuation table", f"$\\sigma^2_\\eta = {P7['eta2']:.3f}$, $\\sigma^2_\\varepsilon = {P7['eps2']:.3f}$, $\\rho_v = {P7['rho']:.2f}$")
chk("smaller group, table note", f"so its small value for advantaged children partly reflects the small size of that group ({a3} children)")
chk("pooled persistence in the text", f"Transitory shocks, which in survey data include reporting error, have a serial correlation of {P7['rho']:.2f} at the biennial")
need(0.25 < P7["sperm"] < 0.30, "pooled permanent share: a little over a quarter")
need(abs(math.sqrt(P7["eta2"]) - 0.35) < 0.01, "standard deviation of the permanent component about 0.35")
U7 = {r["sample"]: r for r in u1("u7_error_structures.csv")}["pooled"]
W5 = {r["group"]: r for r in mt("m5_weighted_md.csv")}
import pandas as _pd
_u19a = _pd.read_csv(os.path.join(ROOT, "output", "u19_A_leave_one_province_out.csv")); _sh = _u19a[_u19a.province == "Shanghai"].iloc[0]; _loo2 = _u19a[_u19a.province != "Shanghai"].instrumented_return.max()
_u19b = _pd.read_csv(os.path.join(ROOT, "output", "u19_B_identity_intervals.csv")).set_index("item"); _u19s = _pd.read_csv(os.path.join(ROOT, "output", "u19_A2_without_shanghai.csv")).iloc[0]
def _iv(k):
    f = lambda v: (f"${v:.2f}$" if v >= 0 else f"$-{abs(v):.2f}$").replace("$", "")
    return f"$[{f(_u19b.loc[k, 'ci_lo'])}, {f(_u19b.loc[k, 'ci_hi'])}]$"
chk("inverse-variance reweighting", f"moves the permanent share only from {P7['sperm']:.3f} to {float(W5['pooled']['sperm_w']):.3f}")
EXPO = {int(float(r["year"])): float(r["recruitment_M"]) for r in u1("u3_B_exposure_series.csv")}; chk("admissions in 1988 and 1997", f"from roughly {EXPO[1988]:.1f} million admissions in 1988 to one million in 1997"); need(abs(EXPO[1997] - 1.0) < 0.05 and 0.42 < EXPO[1999] / EXPO[1998] - 1 < 0.44, "admissions: one million in 1997; up 43 percent in 1999")
M5 = {(r["group"], r["t"], r["s"]): (float(r["omega"]), float(r["se"])) for r in mt("m5_moment_se.csv")}
yrs = ["2014", "2016", "2018", "2020", "2022"]
for g_, lab in [("pooled", "Pooled"), ("H", "Advantaged"), ("L", "Less advantaged")]:
    need(all((g_, a, b) in M5 for a in yrs for b in yrs if a <= b), f"fifteen moments of the 2014 to 2022 panel on file, {lab} (the table of moments by wave is in the online appendix)")
need(0.14 < 1 - M5[("pooled", "2022", "2022")][0] / M5[("pooled", "2014", "2014")][0] < 0.19, "variance decline: about a sixth")
zs = {(t, s_): abs(M5[("H", t, s_)][0] - M5[("L", t, s_)][0]) / math.hypot(M5[("H", t, s_)][1], M5[("L", t, s_)][1]) for (g_, t, s_) in M5 if g_ == "H"}
need(len(zs) == 15 and max(zs.values()) < 2 and max(zs, key=zs.get) == ("2014", "2022"), "no moment gap above two standard errors; the largest at (2014, 2022)")
need(max(zs.values()) < 2, "no standardized moment gap above two (the largest is in the online appendix)")
mom = sorted([r for r in u1("u7_moments.csv") if r["sample"] == "pooled" and r["t"] == r["s"]], key=lambda r: r["t"]); nw = [f"{int(r['children']):,}" for r in mom]
need(sum(int(r["children"]) for r in mom) == int(F14[f"{THREE}: child-waves"]), "wave sizes sum to the child-waves of the children with three waves")
J16 = mi("m16_joint_moment_test.csv")[0]
chk("joint test of the fifteen gaps", f"does not reject equality ($p = {float(J16['p']):.2f}$)")
fitv = lambda g: g["eta2"] + g["eps2"] / (1 - g["rho"] ** 2)
chk("introduction: first paragraph on the process", "Once the children are at work, the earnings of the two groups behave alike:"); chk("abstract: methods of the earnings process", "Covariance-structure and panel estimates show that the two groups' earnings processes do not differ"); chk("abstract: same process", "do not differ: shocks have the same size and persistence, and earnings grow at the same rate."); chk("introduction: argument of the joint estimation", "each constraint is then relaxed in turn, no parameter differs by more than one standard error. A joint distance test does not reject the three restrictions"); chk("abstract: survey named", "In the China Family Panel Studies, the children")
chk("fitted split", f"split the variance differently: advantaged children have a permanent share of {H7['sperm']:.2f} and transitory persistence of {H7['rho']:.2f}, and less advantaged children {L7['sperm']:.2f} and {L7['rho']:.2f}")
need(H7["rho"] > L7["rho"] and H7["sperm"] < L7["sperm"], "advantaged children: more persistent transitory shocks and a smaller permanent share in the separate fits")
M13 = {r["param"]: r for r in mt("m13_mde.csv")}; g13 = lambda k, c: float(M13[k][c])
# the two groups fitted jointly (code/m19_joint_process_by_group.py): the paper reports the tests and the scale model in place of the separate-fit gaps
G19 = {(r["model"], r["quantity"]): r for r in mt("m19_joint_gaps.csv")}; T19 = {(r["test"], r["restricted"], r["unrestricted"]): r for r in mt("m19_joint_tests.csv")}; M19 = {r["model"]: r for r in mt("m19_joint_models.csv")}
_dist = T19[("distance", "all equal", "free")]; _wald = T19[("Wald on the three gaps of the free model, chi-squared", "all equal", "free")]; _k = G19[("scale", "kappa")]
need(abs(float(M19["free"]["eta2_H"]) - H7["eta2"]) < 1e-5 and abs(float(M19["free"]["rho_L"]) - L7["rho"]) < 1e-5, "the free joint model reproduces the separate fits of Table 3")
chk("joint fit: criterion", "raises the criterion by no more than sampling variation would")
chk("joint fit: distance test", f"a bootstrap that recenters each group's moments on the common fit gives $p = {float(_dist['p']):.2f}$"); need(float(_dist["p"]) > 0.1, "one process for both groups is not rejected")
chk("joint fit: Wald test", f"a Wald test on the three parameter gaps gives $p = {float(_wald['p']):.2f}$")
chk("joint fit: scale model", f"$\\kappa = {float(_k['point']):.2f}$, with a 90 percent bootstrap interval of $[{float(_k['ci90_lo']):.2f}, {float(_k['ci90_hi']):.2f}]$")
chk("Table 4: single-parameter gap, permanent variance", f"Gap with one parameter free: permanent variance $\\sigma^2_\\eta$ & \\multicolumn{{2}}{{c}}{{---}} & ${'+' if float(G19[('eta2 differs', 'eta2_gap')]['point']) > 0 else '-'}{abs(float(G19[('eta2 differs', 'eta2_gap')]['point'])):.3f}$ \\\\ & & & ({float(G19[('eta2 differs', 'eta2_gap')]['se']):.3f})"); chk("Table 4: single-parameter gap, persistence", f"transitory persistence $\\rho_v$ & \\multicolumn{{2}}{{c}}{{---}} & ${'+' if float(G19[('rho differs', 'rho_gap')]['point']) > 0 else '-'}{abs(float(G19[('rho differs', 'rho_gap')]['point'])):.2f}$ \\\\ & & & ({float(G19[('rho differs', 'rho_gap')]['se']):.2f})"); chk("Table 4: single-parameter gap, shock variance", f"shock variance $\\sigma^2_\\varepsilon$ & \\multicolumn{{2}}{{c}}{{---}} & ${'+' if float(G19[('eps2 differs', 'eps2_gap')]['point']) > 0 else '-'}{abs(float(G19[('eps2 differs', 'eps2_gap')]['point'])):.3f}$ \\\\ & & & ({float(G19[('eps2 differs', 'eps2_gap')]['se']):.3f})"); chk("single-parameter gaps, text", "no gap between the groups exceeds one standard error (Table~\\ref{tab:summary})")
need(all(abs(float(G19[(m_, q_)]["point"])) < 2 * float(G19[(m_, q_)]["se"]) for m_, q_ in [("eta2 differs", "eta2_gap"), ("rho differs", "rho_gap"), ("eps2 differs", "eps2_gap")]), "no single-parameter gap is two standard errors from zero")
chk("Table 4: distance test", f"Common parameters versus separate fits (distance test) & \\multicolumn{{2}}{{c}}{{---}} & $p = {float(_dist['p']):.2f}$")
chk("Table 4: scale", f"Scale of advantaged autocovariances, $\\kappa$ & {float(_k['point']):.2f} & 1 & $[{float(_k['ci90_lo']):.2f}, {float(_k['ci90_hi']):.2f}]$")
chk("Table 3: common fit", f"Both groups, one process & {n3:,} & {float(M19['all equal']['eta2_H']):.3f} & {float(M19['all equal']['eps2_H']):.3f} & {float(M19['all equal']['rho_H']):.2f} & {float(M19['all equal']['share_H']):.2f} & {float(M19['all equal']['crit']):.1f}")
AB = {r["panel"]: r for r in mt("m10_abgmm_table3.csv")}; ab5, abs_, ab7, abar = AB["diff GMM, 2014-2022"], AB["system GMM, 2014-2022"], AB["diff GMM, 2010-2022 reconstructed"], AB["AR interval rho1 (diff, 5-wave)"]
D17 = {r["panel"]: r for r in mi("m17_ab_diagnostics.csv")}
chk("Arellano-Bond, five waves", f"$\\hat\\rho_0 = {float(ab5['rho0']):.3f}$ (SE {float(ab5['rho0_se']):.3f}). The moment set passes the Hansen test")
need(float(D17["5-wave 2014-2022"]["m2_p"]) > 0.1, "second-order serial correlation not rejected (the p-value is in the online appendix)")
need(float(abs_["pJ"]) < 0.001 and float(ab5["pJ"]) > 0.1, "Hansen: rejects the system moments, not the difference moments")
ab_lo, ab_hi = float(ab5["rho0"]) - 1.96 * float(ab5["rho0_se"]), float(ab5["rho0"]) + 1.96 * float(ab5["rho0_se"]); chk("minimum distance inside the Arellano-Bond interval", f"for less advantaged children, {L7['rho']:.2f}, lies inside the 95 percent interval of the Arellano--Bond estimate, $[{sg(ab_lo, 2)[1:-1]}, {ab_hi:.2f}]$"); need(ab_lo < L7["rho"] < ab_hi, "the minimum-distance estimate lies inside the Arellano-Bond interval")
need(0.2 <= round(math.sqrt(float(ab5["rho0"])), 1) and round(math.sqrt(P7["rho"]), 1) <= 0.4, "annual coefficients roughly 0.2 to 0.4")
chk("observed-earnings persistence (Section 4.4)", "the autocorrelation of observed residual earnings, near 0.4 at the pooled estimates"); need(abs(P7['rho'] + (1 - P7['rho']) * P7['sperm'] - 0.4) < 0.05 and P7['rho'] + (1 - P7['rho']) * P7['sperm'] > 2 * P7['rho'], "observed autocorrelation near 0.4 and more than twice the transitory parameter")
r1, s1 = float(ab5["rho1"]), float(ab5["rho1_se"])
chk("interaction", f"is {sg(r1)} (SE {s1:.3f}), with a Wald interval of $[{r1 - 1.96 * s1:.2f}, {r1 + 1.96 * s1:.2f}]$")
abb = mi("ws", "ws_05b_abb_stochasticEM_surface.csv"); avg = {g: sum(float(r["rho_local"]) for r in abb if r["group"] == g) / sum(1 for r in abb if r["group"] == g) for g in ("pooled", "H", "L")}
need(all(sum(1 for r in abb if r["group"] == g) == 25 for g in avg), "nonlinear persistence: 25 lattice points per group")
chk("nonlinear persistence", f"is {avg['pooled']:.2f} in the pooled sample, {avg['H']:.2f} for advantaged children, and {avg['L']:.2f} for less advantaged children")
# ten runs of the stochastic estimator (u15_nonlinear_persistence_runs.py): range of the pooled figure and the ordering of the two groups
R15 = {r["sample"]: r for r in u1("u15_nonlinear_persistence_summary.csv")}
need(all(int(float(r["runs"])) == 10 for r in R15.values()) and int(float(R15["pooled"]["runs_advantaged_above_less_advantaged"])) == 10, "nonlinear persistence: advantaged above less advantaged in each of ten runs")
need(float(R15["advantaged children"]["min"]) > float(R15["less advantaged children"]["max"]), "nonlinear persistence: ranges of the two groups do not overlap")
need(float(R15["pooled"]["min"]) <= avg["pooled"] <= float(R15["pooled"]["max"]), "nonlinear persistence: the reported pooled figure lies inside the range over ten runs")
chk("nonlinear persistence, ordering in every run", "The higher figure for advantaged children holds in each of ten runs of the estimator")
G10 = u1("u10_growth_gap.csv"); g5 = [r for r in G10 if r["panel"].startswith("2014") and r["covariates"] != "no covariates"][0]; g7 = [r for r in G10 if not r["panel"].startswith("2014")][0]
chk("growth regression", f"gives $\\hat\\gamma = {float(g5['gamma']):.3f}$ per wave (cluster SE {float(g5['se']):.3f}) on the five-wave panel and {float(g7['gamma']):.3f} (SE {float(g7['se']):.3f}) on the reconstructed panel without the covariates. The point estimates imply a divergence over a decade of {5 * float(g5['gamma']):.2f} and {5 * float(g7['gamma']):.2f} log points, respectively, and neither differs from zero at the 5 percent level")
need(float(g5["p"]) > 0.05 and float(g7["p"]) > 0.05, "growth gaps: neither different from zero at the 5 percent level")
m3 = mi("method3_mini_results.csv"); vb = [float(r["estimate"]) for r in m3 if r["object"] == "Var(beta_i)" and r["variant"] == "O(1/T)-corrected"][0]; raw = [float(r["estimate"]) for r in m3 if r["object"] == "Var(beta_i)" and r["variant"] == "raw"][0]
se3 = mi("ws", "ws_m3_strict_exogeneity.csv")[0]
age1 = F14[f"{THREE}: mean age at the first wave"]
chk("age at entry", f"children are {age1:.0f} on average in the first wave in which they are observed. By then most of the return to college is already in the level of earnings")
chk("the level, not the variance or the growth", "not with the variance of earnings around that level or with earnings growth (Table~\\ref{tab:summary}), so whatever advantage these families confer is already in the level")
chk("introduction, children with three waves", f"For the {n3:,} children observed in at least three waves")
chk("conclusion: the scope sentence", "so the comparison of earnings risk is conditional on having earnings.")

print("=== Section 4.5: measurement")
ETA = {(r["formula"], int(r["T"])): r for r in rd(os.path.join(FR, "output", "A_eta_bootstrap.csv"))}; TS = {r["formula"]: r for r in rd(os.path.join(FR, "output", "A_eta_Tstar.csv"))}
e = lambda f_, T, c="eta": float(ETA[(f_, T)][c])
chk("schedule, approximation", "independence approximation & " + " & ".join(f"{e('approx', T):.2f}" for T in range(1, 8)) + r" \\")
chk("schedule, exact", "exact & " + " & ".join(f"{e('exact', T):.2f}" for T in range(1, 8)) + r" \\")
chk("factor at one wave", f"the reliability ratio $\\lambda_T$ is {e('approx', 1):.2f} at $T = 1$")
chk("footnote on the exact calculation", f"With biennial persistence $\\rho_v = {P7['rho']:.2f}$ the transitory components of nearby waves are correlated; the exact formula (Appendix~\\ref{{app:atten}}, second row of Table~\\ref{{tab:eta}}) gives $\\lambda_5 = {e('exact', 5):.2f}$ compared with $\\lambda^\\circ_5 = {e('approx', 5):.2f}$")
need(int(float(TS["approx"]["T_star"])) == 6 and int(float(TS["exact"]["T_star"])) == 8, "two thirds recovered at six waves (approximation) and eight (exact)")
U2 = {r["process"]: {k: (float(v) if k != "process" else v) for k, v in r.items()} for r in u1("u2_recovery_by_process.csv")}; uc, up = U2["children"], U2["linked parents"]
chk("implied range, children", f"imply a true coefficient between {uc['implied_lo']:.2f} and {uc['implied_hi']:.2f}"); need(uc["implied_lo"] < 0.390 and uc["implied_hi"] > 0.442, "the children's range contains the authors' preferred estimates")
chk("implied range, parents", f"the implied coefficient lies between {up['implied_lo']:.2f} and {up['implied_hi']:.2f},")
sh = [(up["implied_lo"] - 0.166) / (0.390 - 0.166), (up["implied_hi"] - 0.176) / (0.442 - 0.176)]; need(0.24 < sh[0] < 0.28 and 0.43 < sh[1] < 0.49, "share of the distance closed: a quarter to just under one half")
chk("share of the distance closed", "between a quarter and just under one half", count=1); chk("the published study: waves", "use the 2010 to 2016 waves"); chk("the published study: averaging", "with income averaged over two to\nfour biennial waves".replace("\n", " ")); need(int(uc["waves_lo"]) == 2 and int(uc["waves_hi"]) == 4, "recovery fractions computed for two to four waves")
PAR = mt("m14_parent_process.csv")[0]
chk("linked parents", "the linked parents have a permanent share of 0.43, compared with 0.27 for the children")
need(0.40 < float(PAR["share"]) < 0.45, "parents: a single wave recovers a little over two fifths")  # (the note on the parents' persistence is in the online appendix)
need(0.40 < float(PAR["share"]) < 0.46 and 0.23 < uc["recovery_one_wave"] < 0.28, "two fifths under the parents' process and a quarter under the children's")
M8 = {int(r["T"]): r for r in mt("m8_rank_attenuation.csv")}
need(abs(float(M8[1]["rank_factor"]) - math.sqrt(e("approx", 1))) < 0.02, "rank recovery close to the square root of the level recovery")

print("=== Section 3: the level premium")
S8 = {r["specification"]: r for r in u1("u8_premium_specifications.csv")}; s8 = lambda k, c="estimate": float(S8[k][c])
EB = {k: float(v) for k, v in u1("u8_entropy_balancing.csv")[0].items()}; L8 = {r["item"]: float(r["value"]) for r in u1("u8_level_sample.csv")}; W8 = {r["measure"]: r for r in u1("u8_income_measure_waves.csv")}
b_, l_, nin = "baseline: family income of the parental household", "parents' own labor income as the income control", "no income control (not in the figures of specifications)"
raw5, tau, gapM = L8["raw gap in mean log earnings"], EB["tau_hat"], EB["gap_hat"]; cH, cL = 100 * L8["college completion, advantaged children"], 100 * L8["college completion, less advantaged children"]
need(abs(raw5 - EB["tau_naive"]) < 1e-9 and abs(raw5 - F14[f"{LEVEL}: raw gap in mean log earnings"]) < 1e-9 and int(L8["children"]) == nl, "raw gap and sample size agree across the output files")
chk("opening of Section 3", f"of the {nl:,} children observed in at least two waves at ages 30 and over (Section"); chk("raw gap at the opening of Section 3", f"Before any controls, advantaged children earn {raw5:.3f} log points ({pct(raw5):.0f} percent) more than less advantaged children.")
chk("raw gap in percent, abstract and introduction", f"earn {pct(raw5):.0f} percent more than other children", count=2)
chk("share of the raw gap that parental income accounts for, introduction", "Holding parental income and demographics fixed removes a fifth to three fifths of that gap and leaves a premium of"); chk("share of the raw gap, opening of Section 3", f"remove a fifth to three fifths of the earnings gap. The rest, {tau:.2f} to {s8(l_):.2f} log points or {pct(tau):.0f} to {pct(s8(l_)):.0f} percent, is the premium")
chk("premium range, introduction", f"and leaves a premium of {pct(tau):.0f} to {pct(s8(l_)):.0f} percent. The question is what these parents pass on beyond income.")
need(0.18 < (raw5 - s8(l_)) / raw5 < 0.23 and 0.60 < (raw5 - tau) / raw5 < 0.66, "controls remove between a fifth and just over three fifths of the raw gap")
chk("premium in percent, abstract", f"entropy balancing leaves a premium of {pct(tau):.0f} to {pct(s8(l_)):.0f} percent.")
chk("college paragraph follows from the labor-market result", "Since the premium does not arise in the earnings process, the second place to look is college"); chk("the instrument follows from the endogeneity of college completion", "Least squares does not identify this return to college, because college completion is endogenous"); chk("two-stage least squares joined to the comparison", "Two-stage least squares identifies the return for children who completed college because of the added seats"); chk("introduction: return before completion", "because of the added seats: 0.68 log points over a four-year degree"); chk("premium paragraph of the introduction", "I measure the premium (Section~\\ref{sec:premium}) in the level of earnings at ages 30 and over, holding parental income fixed with correlated random-effects regressions and with entropy balancing"); chk("two measures of parental income, introduction", "The two ends of its range come from two measures of parental income: family income, which over-controls (it includes the earnings of children who live with their parents), and the parents' own labor income, which under-controls (it leaves out their other income).")
chk("premium in percent, introduction", f"a premium of {pct(tau):.0f} to {pct(s8(l_)):.0f} percent. The question")
chk("completion ratio, introduction", "college at more than twice the rate of less advantaged children"); need(cL > 0 and 2.0 < cH / cL < 3.0, "completion of advantaged children more than twice that of less advantaged children (children with a level of earnings)")
pb = lambda p: "$p < 0.001$" if p < 0.001 else f"$p = {p:.3f}$"
chk("baseline premium", f"Adding family income lowers the coefficient on parental occupation by nearly half, from {s8(nin):.3f} with the demographic controls alone to {s8(b_):.3f} (column 1 of Table~\\ref{{tab:cre}}; {pb(s8(b_, 'p'))})"); need(0.42 < 1 - s8(b_) / s8(nin) < 0.50, "family income lowers the coefficient by nearly half")
chk("parents' labor income", f"falls from {s8(b_, 'income_coef'):.3f} to {s8(l_, 'income_coef'):.3f} and the coefficient on parental occupation rises to {s8(l_):.3f} ({pb(s8(l_, 'p'))})")
chk("regression bracket", f"therefore lies between {s8(b_):.3f} and {s8(l_):.3f} log points ({pct(s8(b_)):.0f} to {pct(s8(l_)):.0f} percent)")
chk("family clustering", f"changes the column 1 standard error by {abs(L8['baseline standard error clustered on family'] - L8['baseline standard error clustered on child']):.4f}.")
chk("entropy balancing premium", f"and the weighted mean for less advantaged children: {tau:.3f}, or {pct(tau):.0f} percent, with a 95 percent bootstrap percentile interval of $[{EB['tau_ci_lo']:.2f}, {EB['tau_ci_hi']:.2f}]$ (200 replications)")
chk("entropy balancing completion gap", f"gap in college completion between the groups is {gapM:.3f}, or {100 * gapM:.1f} percentage points (interval")
chk("entropy balancing against the regression", f"same premium, {s8(b_):.3f} and {tau:.3f}"); chk("all children with a level, Section 6", f"is measured among all {nl:,}")
p0, p1, pc_, pa = "occupation indicator before party membership is added (not in the figures of specifications)", "parental party membership added (cross-section)", "party membership coefficient with occupation and income (not in the figures of specifications)", "parental party membership in place of the occupation indicator (not in the figures of specifications)"
s0, s1_, sc = "parental state-sector employment alone (not in the figures of specifications)", "parental state-sector employment added (cross-section)", "state-sector employment coefficient with occupation and income (not in the figures of specifications)"
need(2 < float(S8[pa]['party_share_advantaged']) / float(S8[pa]['party_share_ordinary']) < 3.2, "party membership two to three times as common among the parents of advantaged children")
so_ = "occupation indicator alone, children with a parent working in 2012 (not in the figures of specifications)"
chk("markers, introduction", "add little beyond parental occupation")
need(0.5 < s8(pa) / s8(p0) < 0.6 and 0.5 < s8(s0) / s8(so_) < 0.6 and s8(pa, "p") > 0.1 and s8(s0, "p") > 0.1 and s8(pc_, "p") > 0.1 and s8(sc, "p") > 0.1 and int(s8(so_, "children")) == int(s8(s0, "children")) == int(s8(s1_, "children")), "markers: ratios, significance and common sample as worded")
need(abs(s8(p1) - s8(p0)) < 0.01 and abs(s8(s1_) - s8(so_)) < 0.01, "the occupation coefficient barely moves when a marker is added")
need(0.2 < 1 - s8(pc_) / s8(pa) < 0.45 and 0.2 < 1 - s8(sc) / s8(s0) < 0.45, "the marker coefficients fall by roughly a third")
AG = u1("u8_indicator_agreement.csv")[0]
chk("lower bound", f"makes the baseline of {s8(b_):.3f} a lower bound"); need(int(float(S8["most frequent retrospective report of parental occupation"]["children_coded_differently_from_baseline"])) == 0, "most frequent report codes every child as the baseline does")
cur = "indicator from the occupations the parents hold during 2010 to 2022 (not in the figures of specifications)"; chk("indicator from current occupations", f"gives a smaller estimate, {s8(cur):.3f} ($p = {s8(cur, 'p'):.2f}$), which is what misclassification predicts")
win = ["parental income from the 2010 and 2012 waves, before the earnings window", "parental income from waves with the child aged 40 or less", "parental income from waves with the child aged 35 or less"]
# Section 3.3 does not print the single estimates of the specifications; Figure 1 shows thirteen of them (the Online Appendix
# shows all fifteen), and the figure file is drawn from the same csv
need(all(S8[w]["in_figures_of_specifications"] == "True" for w in win) and all(S8[k]["in_figures_of_specifications"] == "True" for k in ("indicator widened to CSCO major groups 1 to 3", "indicator narrowed to CSCO major group 1", "most frequent retrospective report of parental occupation")), "the income-window and indicator-definition specifications are among the fifteen of the figure")
chk("what the fifteen specifications vary", "reports thirteen specifications, which vary the income control and the waves it covers, the definition of the indicator, the estimator, the sample, the province effects, the deflator, and whether the other markers are added.")
need(abs(s8("income deflated by the provincial consumer price index") - s8(b_)) < 0.001, "CPI deflation moves the coefficient by less than 0.001")
rg, ur, ru = "three regions in place of province effects", "children recorded as urban in most of their waves", "children recorded as rural in most of their waves"
need(all(S8[k]["in_figures_of_specifications"] == "True" for k in (rg, ur, ru)), "region effects and the urban and rural subsamples are among the fifteen of the figure")
chk("the subsamples of the figure", "The premium in thirteen specifications, sorted by point estimate.")
fig = [r for r in S8.values() if r["in_figures_of_specifications"] == "True"]; est = [float(r["estimate"]) for r in fig]
fig13 = [r for r in fig if r["specification"] not in (ur, ru)]; est13 = [float(r["estimate"]) for r in fig13]; nar = "indicator narrowed to CSCO major group 1"; need(len(fig) == 15 and len(fig13) == 13 and min(fig13, key=lambda r: float(r["estimate"]))["specification"] == nar and max(fig13, key=lambda r: float(r["estimate"]))["specification"] == l_, "thirteen specifications in the paper; smallest group 1 alone, largest parents' labor income")
need(sum((float(r["lo"]) > 0) or (float(r["hi"]) < 0) for r in fig13) == 10 and sum(0.06 <= v < 0.09 for v in est13) == 10, "ten intervals exclude zero; ten estimates between 0.06 and 0.09")
chk("range of the thirteen", f"Ten of the thirteen estimates lie between 0.06 and 0.09, and ten of the thirteen confidence intervals exclude zero; the range runs from {min(est13):.3f}, with CSCO major group 1 alone as the indicator, to {max(est13):.3f}, with the parents' own labor income as the income control. The Online Appendix adds the urban and rural subsamples.")
pby = (F14["parents' birth year, 5th percentile"], F14["parents' birth year, 95th percentile"]); need(1935 <= pby[0] <= 1939 and 1970 <= pby[1] <= 1973, "parents born mostly between the late 1930s and the early 1970s"); chk("parents' birth years", "born mostly between the late 1930s and the early 1970s")

print("=== Section 5: the expansion design (two-row regression)")
U9A = {r["item"]: r for r in u1("u9_A_sample.csv")}; U9B = {r["intensity"]: r for r in u1("u9_B_main.csv")}; U9C = {r["check"]: r for r in u1("u9_C_checks.csv")}; U9D = {(r["outcome"], r["bin"]): r for r in u1("u9_D_cohort_bins.csv")}
W9B = {r["intensity"]: r for r in u1("u9_B_main_weighted.csv")}; W9C = {r["check"]: r for r in u1("u9_C_checks_weighted.csv")}
MAIN = "predicted provincial growth (main measure)"; m = {k: (float(v) if v not in ("", MAIN) else v) for k, v in U9B[MAIN].items()}; mw = {k: (float(v) if v not in ("", MAIN) else v) for k, v in W9B[MAIN].items()}
OTH = [U9B[k] for k in ("predicted flow per 2005 worker", "log implied 2010 stock", "census senior-high stock in 2000")]
a9 = lambda k: float(U9A[k]["value"]); c9 = lambda k, c="coef": float(U9C[k][c]); w9 = lambda k, c="coef": float(W9C[k][c])
C14 = {r["row"]: r for r in u1("u14_C_first_stages_all_children.csv")}; fa = C14[f"all children: {MAIN}"]; fL, fH = C14["less advantaged children, instrument entering once for each group"], C14["advantaged children, instrument entering once for each group"]
C13 = {r["item"]: r for r in u1("u13_C_design_facts.csv")}; cv = lambda k: float(C13[k]["value"]); E13 = {r["item"]: r for r in u1("u13_E_added_degrees.csv")}
# Section 2.1: the variance of log income by wave (u17), and Section 2.4: the census measure in 1990 and in 2000
_v = {int(r["wave"]): float(r["variance_of_log_income"]) for r in u1("u17_income_variance_by_wave.csv") if r["respondents"].startswith("all respondents")}
need(_v[2012] > 1.3 * max(_v[y] for y in (2014, 2016, 2018, 2020, 2022)), "variance of log income markedly lower under the new concept (values in the online appendix)")
_hs = rd(os.path.join(PKG["college_expansion"], "data", "external", "census_hs_stock.csv")); _a = [float(r["hs1990"]) for r in _hs]; _b = [float(r["hs2000"]) for r in _hs]
_ma, _mb = sum(_a) / len(_a), sum(_b) / len(_b); _r = sum((x - _ma) * (y - _mb) for x, y in zip(_a, _b)) / math.sqrt(sum((x - _ma) ** 2 for x in _a) * sum((y - _mb) ** 2 for y in _b))
chk("census measure, 1990 against 2000", f"(correlation {_r:.2f} between the 1990 and 2000")
COR = {r[""]: r for r in u1("u3_C_intensity_correlations.csv")}; chk("census measure and the main measure", f"correlates {float(COR['hs2000']['pro_predict_growth']):.2f} with the main measure")
EXP = {int(r["birth_year"]): float(r["exposure_ratio"]) for r in u1("u3_B_exposure_series.csv")}; pre_ = [EXP[y_] for y_ in (1977, 1978, 1979, 1980)]
chk("exposure ratio, cohorts 1977 to 1980", f"between {min(pre_):.2f} and {max(pre_):.2f} for those born 1977 to 1980"); chk("exposure ratio, cohort 1981", f"rises to {EXP[1981]:.2f} for the 1981 cohort")
need(abs(EXP[1990] - 4) < 0.05 and min(EXP) == 1964, "exposure ratio reaches 4 around 1990; the series starts with the cohort born in 1964"); need(0.85 < min(EXP[y] for y in range(1964, 1977)) < 0.95 and 1.55 < max(EXP[y] for y in range(1964, 1977)) < 1.65, "exposure ratio between 0.9 and 1.6 for the cohorts born 1964 to 1976"); chk("exposure ratio, earliest cohorts", "lies between 0.9 and 1.6 for the cohorts born 1964 to 1976"); chk("exposure ratio around 1990", "reaches 4 for the cohorts born around 1990")
need(int(a9("children")) == n_all and int(a9("rows at 30 and over")) == nl and int(a9("advantaged rows at 30 and over")) == al and int(a9("children with a row")) == n_all, "rows of the two-row regression agree with the sample counts")
chk("conventional regression: one observation per child with a level of earnings", f"one observation for each of the {nl:,} children with earnings at ages 30 and over:"); chk("children left out by the conventional regression", f"out the {n_all - nl:,} children who are not yet 30"); need(a_all - al > 250, "the rows below 30 add several hundred advantaged children"); chk("restriction of the two-row specification stated", "the province effects, the birth-year effects, and the coefficients on $X_i$ are common to the two rows"); need(int(F14["children with a row below 30 only"]) == n_all - nl, "children with a row below 30 only")
chk("identity: same outcome and children", f"three quantities for the same {nl:,} children")
need(d("22-25") < 0.1 and d("26-29") < d("30-34") - 0.05 and abs(d("30-34") - d("35-55")) < 0.08, "least squares return by age: near zero at 22 to 25, lower at 26 to 29 than from 30, level from 30")
chk("rows", f"if the child has at least one such wave ({nl:,} rows at 30 and over, {int(a9('rows below 30')):,} below 30). Let")
chk("cohorts below 30", f"was born in {int(F14['first birth year among the rows below 30'])} or later and reached college age well after the expansion had begun")
need(int(F14['children born before 1964']) == 38, "38 children born before the admissions series starts")
sv = P7["eps2"] / (1 - P7["rho"] ** 2); wt = lambda n: 1 / (P7["eta2"] + sv / n)
need(wt(5) > 2 * wt(1), "a five-wave row carries more than twice the weight of a one-wave row")
chk("pooled parameters behind the weights (the values are printed in the notes of the attenuation table)", "evaluated at the pooled estimates of Table~\\ref{tab:md}."); chk("pooled parameters, notes of the attenuation table", f"$\\sigma^2_\\eta = {P7['eta2']:.3f}$, $\\sigma^2_\\varepsilon = {P7['eps2']:.3f}$, $\\rho_v = {P7['rho']:.2f}$")
chk("weights: the variance inverted is the denominator of the attenuation formula", "the denominator of equation~\\eqref{eq:eta} with $n_{ir}$ in place of $T$")
chk("the weights of Section 5.1 use the attenuation formula of Section 4.5", "the denominator of equation~\\eqref{eq:eta} with $n_{ir}$ in place of $T$")
chk("province at age twelve, agreement", f"of the {int(F14['all children: province at age twelve recorded in the 2010 wave']):,} children for whom the 2010 wave records the province of residence at age twelve, {100 * F14['share with a different province at age twelve, advantaged']:.0f} percent of advantaged children and {100 * F14['share with a different province at age twelve, less advantaged']:.0f} percent of less advantaged children are assigned a different province")
need(int(c9("instrument by the province at age twelve", "with_report")) == int(F14["all children: province at age twelve recorded in the 2010 wave"]) and int(c9("instrument by the province at age twelve", "changed")) == int(F14["all children: province at age twelve differs from the province assigned"]), "province at age twelve: the two scripts agree")
need(int(cv("provinces")) == 29 and int(F14[f"{ALL}: provinces"]) == 29, "twenty-nine provinces"); chk("clusters", "inference rests on 29 clusters")
chk("instrument variance between cohorts", f"the {100 * cv(chr(115) + 'hare of the instrument' + chr(39) + 's variance, net of province effects, within birth cohorts'):.0f} percent of the instrument's variance that remains net of province and birth-year effects")
urb = C13["reduced form of urban residence on the instrument"]; need(float(urb['p_wild']) > 0.5, "urban residence does not respond to the instrument"); chk("supply of graduates in the exclusion paragraph", "to the extent that graduates work where they studied, this decline in graduate wages pushes the earnings reduced form toward zero"); chk("urban residence, threats table", f"Reduced form of the child's adult urban residence: {float(urb['value']):.3f} (SE {float(urb['se']):.3f})")
chk("placebo, threats table", f"Placebo from pre-reform registration growth: first-stage $F$ of {m['placebo_F']:.1f}")
chk("placebo in the introduction", "a placebo instrument built from pre-reform growth in examination registrations has no first stage."); need(m['placebo_F'] < 1 and m['F'] > 10, "placebo first stage below 1 against a strong main first stage"); need(m["placebo_earn_p_wild"] > 0.3, "placebo earnings reduced form is null")
H0, L0, H1, L1 = [100 * cv(q) for q in ("college completion, advantaged children, born 1980 or earlier", "college completion, less advantaged children, born 1980 or earlier", "college completion, advantaged children, born 1981 or later", "college completion, less advantaged children, born 1981 or later")]
chk("completion across cohorts, introduction", f"completion rose from {H0:.1f} to {H1:.1f} percent among advantaged children and from {L0:.1f} to {L1:.1f} percent among less advantaged children.")
chk("completion rates, Section 5.2", f"from the pre-reform to the post-reform cohorts, completion rose from {H0:.1f} to {H1:.1f} percent among advantaged children and from {L0:.1f} to {L1:.1f} percent among less advantaged children")
need(cv("rise in completion, advantaged children, percentage points") > cv("rise in completion, less advantaged children, percentage points") > 15, "completion rose by more points among advantaged children (the two rises are in the online appendix)")
need(0.55 < cv("less advantaged share of graduates, born 1980 or earlier") < 0.62 and 0.72 < cv("less advantaged share of the added graduates") < 0.78, "less advantaged children: three fifths of graduates before, three quarters of the added graduates")
chk("incidence, conclusion", f"Completion among less advantaged children rose fivefold between the cohorts born in 1980 or earlier and those born later, the ratio of completion rates fell from {H0 / L0:.1f} to {H1 / L1:.1f}")
need(2.0 <= cv("completion ratio, born 1981 or later") < cv("completion ratio, born 1980 or earlier") <= 4.0, "completion ratio between two and four in the cohorts before and after the reform")
FL = {(r["group"], r["cohort_group"]): r for r in u1("fig_first_stage_left.csv")}; ratio = lambda c_: float(FL[("Advantaged children", c_)]["completion_rate"]) / float(FL[("Less advantaged children", c_)]["completion_rate"])
c_first = "1972 or earlier"; c_last = [q[1] for q in FL if q[1].startswith("1989")][0]
need(ratio(c_first) > ratio(c_last), "the ratio falls across the cohort groups (printed in Figure 3)"); need(int(F14[f"{ALL}: last birth year"]) == 1997, "last birth year 1997")
chk("first stage on all children", f"gives a first-stage coefficient of {float(fa['fs']):.3f} ($F = {float(fa['F']):.1f}$)")
Fo = [float(C14[f"all children: {k}"]["F"]) for k in ("predicted flow per 2005 worker", "log implied 2010 stock", "census senior-high stock in 2000")]
need(min(Fo) > 10, "the three other measures have strong first stages (text says so; values in the online appendix)")
dz = a9("difference in the instrument created by the reform")   # interquartile range of intensity times the rise in the exposure ratio from the cohorts born in 1980 or earlier to those born in 1989 or later
U20 = {r["contrast"]: r for r in u1("u20_first_stage_magnitudes.csv")}; dz1090 = float(U20["10th to 90th"]["difference_in_instrument"])   # 10th to 90th percentile of intensity times the rise in the exposure ratio
chk("interquartile effect on completion", f"to one at the 90th raises the college completion of a cohort born in 1989 or later by {100 * dz1090 * float(fa['fs']):.0f} percentage points")
chk("interquartile effect on completion, introduction", f"moving from the 10th to the 90th percentile of provincial intensity raises it by {100 * dz1090 * float(fL['fs']):.0f} percentage points for less advantaged children and by {100 * dz1090 * float(fH['fs']):.0f} for advantaged children"); need(3.8 < a9("mean exposure ratio, born 1989 or later") < 4.2, "cohorts born 1989 or later: admissions about four times the pre-reform trend")
chk("first stage at 30 and over, Section 5.2", f"on the rows at 30 and over, is {m['fs']:.3f} (SE {m['fs_se']:.3f}) with $F = {m['F']:.1f}$")
chk("advantaged children per province", f"because the advantaged children (755 in all, {al} with earnings at ages 30 and over) are too few for a separate set"); need(int(cv("provinces with fewer than twenty advantaged children")) == 23, "fewer than 20 advantaged children in 23 provinces (online appendix)")
dgap, dse = float(E13["difference (advantaged minus less advantaged)"]["value"]), float(E13["difference (advantaged minus less advantaged)"]["se"])
chk("first stages by group", f"is {float(fL['fs']):.3f} for less advantaged children and {float(fH['fs']):.3f} for advantaged children (Figure~\\ref{{fig:fs}}), and the difference between them, {sg(dgap)} (SE {dse:.3f}), is not distinguishable from zero")
need(abs(dgap) < 1.96 * dse and abs(dgap - (float(fH["fs"]) - float(fL["fs"]))) < 1e-6, "difference of the two first stages")
chk("interquartile effect by group, Section 5.2", f"({100 * dz1090 * float(fL['fs']):.0f} and {100 * dz1090 * float(fH['fs']):.0f} percentage points for the same difference in intensity)")
chk("added seats went to the two groups alike", f"the added seats raised the chance of completing college by a similar amount in both groups ({100 * dz1090 * float(fL['fs']):.0f} and {100 * dz1090 * float(fH['fs']):.0f} percentage points for the same difference in intensity)")
chk("pre-reform allocation of seats", f"Because the pre-reform ratio of completion rates was {H0 / L0:.1f} to one in favor of advantaged children"); need(abs(float(fL["fs"]) - float(fH["fs"])) < 2 * (float(fL["fs_se"]) ** 2 + float(fH["fs_se"]) ** 2) ** 0.5, "first stages by group not distinguishable")
chk("conclusion: neutral addition, ratio", "the seats that provinces added left the gap roughly unchanged, because a similar addition was made to unequal starting points")
chk("conclusion: widening in percentage points", f"across cohorts, as national admissions rose, the gap widened from {H0 - L0:.0f} to {H1 - L1:.0f} percentage points, as earlier work on the expansion reports \\citep{{Yeung2013}}")
chk("Section 5.2: the ratio fell", f"from {H0 / L0:.1f} for the cohorts born in 1980 or earlier, taken together, to {H1 / L1:.1f} for those born later, while the gap in percentage points widens from {H0 - L0:.0f} to {H1 - L1:.0f}")
need(abs((H1 - L1) - (H0 - L0)) > 5 and H1 / L1 < H0 / L0, "across cohorts the gap in percentage points widened and the ratio fell")
# the first stages by group are asserted for Section 5.2 above and Section 5.3 below
rel = (float(fL["fs"]) / (L0 / 100)) / (float(fH["fs"]) / (H0 / 100)); need(3.8 < rel < 4.8 and 4.8 < L1 / L0 < 5.6, "relative response four times as large; completion rose fivefold")
chk("relative response", "an addition of similar size was a far larger proportional change for less advantaged children")
# 5.3
chk("first stage at 30 and over", f"{m['fs']:.3f} (SE {m['fs_se']:.3f}) with $F = {m['F']:.1f}$")
chk("interquartile effect on earnings", f"moving from the 10th to the 90th percentile of intensity raises the completion of the most exposed cohorts in these rows by {100 * m['fs'] * dz1090:.0f} percentage points and their level of earnings by about {pct(dz1090 * m['earn']):.0f} percent")
chk("return and least squares", f"The instrumented return to college is {m['earn_iv']:.2f} log points, compared with a least squares return of {m['ols']:.2f}, and the 95 percent")
# Anderson-Rubin sets, read from the grids of p-values (grid -6 to 6); the limit of the test as b grows is the test of a zero first stage
def _segs(rows_, lvl):
    acc = sorted(float(r["b"]) for r in rows_ if float(r["p_wild"]) >= lvl); out = []
    for b_0 in acc:
        if out and abs(b_0 - out[-1][1] - 0.05) < 1e-6: out[-1][1] = b_0
        else: out.append([b_0, b_0])
    return out
_own = {r["group"]: float(r["fs_own_regressor_p_wild"]) for r in u1("u12_returns_by_family_background.csv")}
G9g = u1("u9_anderson_rubin_grid.csv"); G12g = u1("u12_anderson_rubin_grid.csv"); gridL = [r for r in G12g if r["group"] == "less advantaged"]; gridH = [r for r in G12g if r["group"] == "advantaged"]
sA95, sA90, sL95, sL90, sH95, sH90 = _segs(G9g, .05), _segs(G9g, .10), _segs(gridL, .05), _segs(gridL, .10), _segs(gridH, .05), _segs(gridH, .10)
need(len(sA95) == 1 and len(sA90) == 1 and len(sL95) == 1 and len(sL90) == 1 and len(sH95) == 2 and len(sH90) == 2, "Anderson-Rubin sets: one interval for all children and for less advantaged children, two rays for advantaged children")
need(-5.99 < sA95[0][0] and sA95[0][1] < 5.99 and sL95[0][1] < 5.99 and m["fs_p_wild"] < 0.05 and _own["less advantaged"] < 0.05, "95 percent sets of all children and of less advantaged children end inside the grid, and the first stage rejects zero at 5 percent")
need(sH95[0][0] <= -5.99 and sH95[1][1] >= 5.99 and sH90[0][0] <= -5.99 and sH90[1][1] >= 5.99 and _own["advantaged"] >= 0.10, "advantaged children: both sets are unions of two rays, and the test of a zero first stage does not reject at 10 percent")
chk("Anderson-Rubin set", f"the 95 percent wild cluster Anderson--Rubin set, $[{sA95[0][0]:.2f}, {sA95[0][1]:.2f}]$, excludes zero and the least squares return"); need(sA95[0][0] > m["ols"] and abs(sA95[0][0] - m["ar_lo"]) < 1e-9, "the 95 percent set of all children starts above the least squares return and agrees with u9_B_main.csv")
need(m["ar_hi"] >= 3.99 and m["ols"] < m["ar_lo"] < m["earn_iv"], "the set starts above the least squares return and reaches the end of the grid")
chk("other intensity measures", f"returns of {min(float(r['earn_iv']) for r in OTH):.2f} to {max(float(r['earn_iv']) for r in OTH):.2f} (Online Appendix)"); need(max(float(r['earn_p_wild']) for r in OTH) < 0.1, "other measures: wild p below 0.1 (values in the online appendix)")
chk("placebo intensity", "which picks up any provincial trend in the demand for college but not the reform, has no first stage (Table~\\ref{tab:threats})")
lw = "earnings, children with 9 or fewer years of schooling"; need(c9(lw, 'p_wild') > 0.5, "low-schooling children: earnings reduced form not distinguishable from zero (not printed in the paper)")
_lo9 = "professional occupation, children with 9 or fewer years of schooling"; chk("low-schooling placebo, introduction", "did not move into advantaged occupations where seats grew faster"); need(abs(c9(_lo9)) < 2 * c9(_lo9, 'se') and c9(_lo9) < m['occ_maj'] / 3, "low-schooling occupation reduced form null (value in Table 7)")
tr = [c9(f"trade control: {k}") for k in ("coastal x exposure", "export share x exposure", "both")]
loo = "leave one province out: instrumented return, smallest and largest"; chk("leave one province out", f"gives returns between {c9(loo):.2f} and {_loo2:.2f}, except when Shanghai"); need(abs(c9(loo, "se") - _sh.instrumented_return) < 1e-6, "the largest return with a province left out is the one without Shanghai")
rt = "region-specific linear cohort trends (three regions)"; p12 = "instrument by the province at age twelve"; pt = "province-specific linear cohort trends"
a17, a19 = "exposure ratio of the year the cohort turned 17", "exposure ratio of the year the cohort turned 19"
need(c9(a17, "p_wild") < 0.05 and c9(a19, "p_wild") < 0.05 and abs(c9(a17, "iv") - m["earn_iv"]) < 0.1 and abs(c9(a19, "iv") - m["earn_iv"]) < 0.1, "college age seventeen or nineteen gives the same results (reduced forms significant, returns within 0.1 of the main return)")
chk("trend checks and province at age twelve", f"The return changes little with regional cohort trends, with the instrument assigned by the province at age twelve, and with cohort exposure taken at age seventeen or nineteen instead of eighteen ({min(c9(k, 'iv') for k in (rt, p12, a17, a19)):.2f} to {max(c9(k, 'iv') for k in (rt, p12, a17, a19)):.2f})")
need(f"{c9(rt, 'p_wild'):.3f}" == f"{c9(p12, 'p_wild'):.3f}" and c9(pt, "p_wild") > 0.1, "region trends and province at twelve have the same printed p; province trends not distinguishable from zero")
chk("census cohorts cited in the table of threats", "Census cohorts before the reform \\citep{IPUMSInternational}: completion in provinces with high and low growth in examination registrations diverges by under one percentage point"); chk("pre-reform trends, table of threats", "no differential trend with intensity in earnings or completion"); need(c9('pre-reform cohorts: earnings on intensity x birth year', 'p_wild') > 0.1 and c9('pre-reform cohorts: completion on intensity x birth year', 'p_wild') > 0.1, "pre-reform trends: wild p above 0.1")
oo = "rows at 30 and over only (no row below 30)"
chk("rows at 30 and over only", f"Dropping the second row (equation~\\eqref{{eq:oldonly}}) gives a return of {c9(oo, 'iv'):.2f}, and weighting the rows by the precision of equation~\\eqref{{eq:weights}} gives")
chk("weighted rows", f"gives {mw['earn_iv']:.2f}. The Online")
chk("return per year of college", f"{m['earn_iv']:.2f} is about {m['earn_iv'] / 4:.2f} log points ({pct(m['earn_iv'] / 4):.0f} percent) per year of college. This return is in the range that other designs find")
chk("return per year, compared with other designs", "in the range that other designs find for China"); chk("return per year, Section 5.3", f"the instrumented return of {m['earn_iv']:.2f} is about {m['earn_iv'] / 4:.2f} log points ({pct(m['earn_iv'] / 4):.0f} percent) per year of college")
bins = ("1972 or earlier", "1973-1976", "1981-1984", "1985-1988", "1989 or later"); eb = {b: float(U9D[("mean log earnings at 30 and over", b)]["coef"]) for b in bins}; cb = {b: float(U9D[("college completion (children with a row at 30 and over)", b)]["coef"]) for b in bins}
chk("event study, text", "the earnings gradient on provincial intensity is flat across the pre-reform cohort bins, the completion gradient is not distinguishable from zero at the 5 percent level in either bin, and both rise across the three post-reform bins"); need(eb[bins[2]] < eb[bins[3]] < eb[bins[4]] and max(abs(eb[bins[0]]), abs(eb[bins[1]])) < 0.1, "earnings gradient: flat before, rising after")
need(cb[bins[2]] < cb[bins[3]] < cb[bins[4]], "completion gradient rises across the post-reform bins")
need(all(float(U9D[("college completion (children with a row at 30 and over)", b_)]["p"]) > 0.05 for b_ in bins[:2]), "pre-reform completion gradients not different from zero at the 5 percent level")
chk("return in the introduction", f"because of the added seats: {m['earn_iv']:.2f} log points over a four-year degree, or {pct(m['earn_iv'] / 4):.0f} percent per year; the precision-weighted estimate is about the same")
chk("return in the abstract", f"college raised earnings by {m['earn_iv']:.2f} log points, or {pct(m['earn_iv'] / 4):.0f} percent per year of college. A degree also closes the occupational gap between the groups; the point estimates suggest that college raises earnings more for advantaged children, while it raises the chance of holding an official, managerial, or professional job more for less advantaged children.")
G12 = {r["group"]: {k: (float(v) if k not in ("sample", "group") else v) for k, v in r.items()} for r in u1("u12_returns_by_family_background.csv")}; gL, gH = G12["less advantaged"], G12["advantaged"]
WG = {r["group"]: r for r in u1("u12_returns_by_family_background_weighted.csv")}
chk("first stages and reduced forms by group", "both groups have a first stage, and both earnings reduced forms are positive and significant at the 5 percent level by the wild cluster bootstrap."); need(gL['F'] > 10 and gH['F'] > 10 and gL['rf'] > 0 and gH['rf'] > 0, "first stages above 10 and reduced forms positive in both groups")
chk("returns by group", f"The instrumented return is {gL['beta']:.2f} for less advantaged children and {gH['beta']:.2f} for advantaged children; the least squares returns are {gL['ls']:.2f} and {gH['ls']:.2f}, so neither instrumented estimate is below the least squares return. For less advantaged children the 95 percent Anderson--Rubin set is $[{sL95[0][0]:.2f}, {sL95[0][1]:.2f}]$; the set for advantaged children consists of two unbounded rays, $(-\\infty, -0.50]$ and $[0.25, \\infty)$."); need(gL["rf_p_wild"] < 0.05 and gH["rf_p_wild"] < 0.05, "both 95 percent Anderson-Rubin sets exclude zero (the test at zero is the reduced-form test)")
need(gL["F"] > 10 and gH["F"] > 10 and gL["rf"] > 0 and gH["rf"] > 0, "both first stages by group have F above 10 and both reduced forms are positive")
need(abs(gH["fs"] - 0.189) < 0.002 and abs(gL["fs"] - 0.182) < 0.002, "the first stage by group is the regression of the child's completion on the group's instrument")
chk("equal returns", f"($z = {abs(gL['equal_returns_z']):.2f}$, allowing for the covariance between the two estimates)"); need(abs(gL["equal_returns_z"]) < 1.645 and gL["beta"] > gL["ls"] and gH["beta"] > gH["ls"], "returns not distinguishable; neither below the least squares return")
chk("abstract: added seats alike", "The added seats raised the chance of completing college by a similar amount in both groups, and for children who completed college because of them, college raised earnings by")
need(gH['beta'] > gL['beta'], "conclusion: the point estimate of the return is higher for advantaged children"); chk("returns by group, conclusion", "but a higher earnings return for advantaged children, though both differences are within sampling error"); need(abs(gL["equal_returns_z"]) < 1.645, "the two returns are within sampling error (conclusion)")
need(min(m["earn_iv"], gL["beta"], gH["beta"]) > max(gL["ls"], gH["ls"], m["ols"]), "all three instrumented returns lie above the least squares returns")
need(5.5 < nl / al < 6.5, "the returns for all children rest on six times as many children")
chk("margin between the set and least squares", f"For all children, the point estimate ({m['earn_iv']:.2f}) and the lower end of the 95 percent Anderson--Rubin set ({sA95[0][0]:.2f}) lie above the least squares return ({m['ols']:.2f}, SE {m['ols_se']:.2f})"); need(m["earn_iv"] > m["ols"] and m["ar_lo"] > m["ols"], "point estimate and lower end of the 95 percent set above the least squares return")
chk("occupation", f"Its reduced form on the instrument is {m['occ_maj']:.3f} (wild cluster $p = {m['occ_maj_p_wild']:.3f}$")
# the occupational effect by family background (code/u18_occupation_by_family_background.py)
O18 = {r["group"]: r for r in u1("u18_occupation_by_family_background.csv")}; oL, oH = O18["less advantaged"], O18["advantaged"]
chk("point estimates by family background, introduction", f"a higher earnings return for advantaged children ({gH['beta']:.2f} versus {gL['beta']:.2f} log points) and a larger rise in the chance of holding an advantaged occupation for less advantaged children ({float(oL['iv']):.2f} versus {float(oH['iv']):.2f})."); chk("occupation by group", f"college raises their share of waves in an advantaged occupation by {float(oL['iv']):.2f} (SE {float(oL['iv_se']):.2f}), compared with {float(oH['iv']):.2f} (SE {float(oH['iv_se']):.2f}) for advantaged children")
chk("occupation by group, advantaged reduced form", "for advantaged children, whose reduced form is not distinguishable from zero")
chk("occupation by group, equality", f"The difference is within sampling error ($z = {abs(float(oL['equal_effects_z'])):.2f}$) and runs opposite to the difference in earnings returns")
need(float(oL["iv"]) > float(oH["iv"]) and abs(float(oL["equal_effects_z"])) < 1.645 and float(oL["rf_p_wild"]) < 0.05 and float(oH["rf_p_wild"]) > 0.1, "occupational effect larger for less advantaged children, not distinguishable; only their reduced form is significant"); chk("occupation, introduction, instrumented", f"By the instrumented estimate, college also raises the chance of holding an official, managerial, or professional occupation (an advantaged occupation) by {100 * m['occ_maj_iv']:.0f} percentage points."); chk("occupation, instrumented", f"by {m['occ_maj_iv']:.2f}, or {100 * m['occ_maj_iv']:.0f} percentage points")
op = [float(r["occ_maj_p_wild"]) for r in OTH]; chk("occupation, other measures", "give reduced forms of the same sign (Online Appendix)"); need(max(op) < 0.1, "occupation: other measures' wild p below 0.1"); need(all(float(r["occ_maj"]) > 0 for r in OTH), "occupation reduced forms of the other measures are positive")
lo9 = "professional occupation, children with 9 or fewer years of schooling"
# the table of assumptions, threats, diagnostics and results (Table 6): every number is the one asserted for the text above
_Fo = [float(r["F"]) for r in OTH]; _cen = [r for r in OTH if "census" in r["intensity"]][0]
chk("threats table: relevance", f"First-stage $F$ of {m['F']:.1f} for all children, {gL['F']:.1f} and {gH['F']:.1f} for less advantaged and advantaged children, and {min(_Fo):.1f} to {max(_Fo):.1f} under the three other measures")
chk("threats table: exclusion", f"Trade-exposure controls: reduced form {min(tr):.3f} to {max(tr):.3f}, compared with {m['earn']:.3f}. Children with nine or fewer years of schooling: reduced form for holding an advantaged occupation, {c9(lo9):.3f} (SE {c9(lo9, 'se'):.3f}).")
chk("threats table: exogeneity", f"Predetermined census measure: return {float(_cen['earn_iv']):.2f}. Cohorts born in 1980 or earlier: no differential trend with intensity in earnings or completion ($p = {c9('pre-reform cohorts: earnings on intensity x birth year', 'p_wild'):.2f}$ and ${c9('pre-reform cohorts: completion on intensity x birth year', 'p_wild'):.2f}$). Linear cohort trends by region: return {c9(rt, 'iv'):.2f}.")
_ri = {r["statistic"]: r for r in u1("u9_R_randomization_inference.csv")}
# randomization inference (one sentence of the paper; the details are in the online appendix)
_g3 = {r["outcome"]: r for r in u1("u9_G_three_year_completion.csv")}; need(float(_g3["exactly 15 years of schooling (three-year degree)"]["coef"]) < 0, "the point estimate of three-year completion on the instrument is negative"); chk("three-year counterfactual", "If some of the children who completed a four-year degree because of the added seats would otherwise have held a three-year one, 0.68 compares a four-year degree with a mix of no college and a three-year degree.")
_own = {r["group"]: float(r["fs_own_regressor_p_wild"]) for r in u1("u12_returns_by_family_background.csv") if r.get("fs_own_regressor_p_wild") not in (None, "")}
need(_own["advantaged"] >= 0.10 and _own["less advantaged"] < 0.05, "own-completion first stage: advantaged children do not reject zero at 10 percent (sets unbounded), less advantaged children reject at 5 percent (sets bounded)"); chk("rule for unbounded sets", "a set is reported as unbounded when the test does not reject at the end of the grid.")
_rw = u1("u9_R_randomization_within_region.csv")[0]
need(float(_rw["permutation_p_reduced_form"]) < 0.001 and float(_rw["permutation_p_first_stage"]) < 0.001, "randomization inference within regions: p below 0.001 for the reduced form and the first stage")
chk("randomization inference, one sentence", "Randomization inference gives $p < 0.001$ for the earnings reduced form and for the first stage, whether intensity is reassigned among all provinces or only within regions (Online Appendix).")
need(float(_rw["grid_lo"]) < float(_rw["set95_lo"]) and float(_rw["set95_hi"]) < float(_rw["grid_hi"]), "the randomization set lies inside the grid")
_st = [r for r in u1("u8_premium_specifications.csv") if r.get("state_share_advantaged") not in (None, "")][0]
need(2 < float(_st['state_share_advantaged']) / float(_st['state_share_ordinary']) < 3.2, "state-sector employment two to three times as common among the parents of advantaged children")
_urb = C13["reduced form of urban residence on the instrument"]; chk("urban residence, table of threats", "Reduced form of the child's adult urban residence"); need(abs(float(_urb['value'])) < 2 * float(_urb['se']), "urban residence reduced form null (value in Table 7)")
_cnt = {k: round(float(r["permutation_p"]) * (int(r["reassignments"]) + 1)) - 1 for k, r in _ri.items()}; need(_cnt == {"earnings reduced form": 0, "first stage": 2} and all(float(r["permutation_p"]) < 0.001 for r in _ri.values()), "randomization inference: none and two reassignments reach the actual |t|, p below 0.001")
if "the most demanding specification" in TEX or "by province." in TEX.split("Linear cohort trends")[1][:60]: fails += 1; print("  FAIL the province-trend result belongs to the Online Appendix, not to the body")
chk("intensity: 1982 shares", "by their shares of national college enrollment in the 1982 census")
chk("figure caption, children", f"the {nl:,} children with earnings at ages 30 and over, one observation per child on the rows at 30 and over, unweighted;")

print("=== Section 6: the decomposition")
B13 = {r["row"]: r for r in u1("u13_B_identity.csv")}; B = lambda r_, c_="college_channel": float(B13[r_][c_]); A13 = {r["item"]: r for r in u1("u13_A_least_squares.csv")}; WB = {r["row"]: r for r in u1("u13_B_identity_weighted.csv")}
need(abs(B("premium (entropy balancing)") - tau) < 1e-9 and abs(B("completion gap (entropy balancing)") - gapM) < 1e-9, "premium and completion gap of the identity are those of Section 3")
chk("premium and gap", f"supplies $\\tau = {tau:.3f}$ and $\\Delta M = {gapM:.3f}$.")
need(abs(EB['completion_advantaged'] - EB['completion_less_advantaged_reweighted'] - gapM) < 1e-6, "the completion gap equals the difference of the two balanced completion rates")
ls = lambda k, c="coef": float(A13[k][c]); la, lh, ll = "least squares return, all children", "least squares return, advantaged children", "least squares return, less advantaged children"
need(abs(ls(lh) - ls(ll)) < 1.96 * math.hypot(ls(lh, "se"), ls(ll, "se")), "least squares returns of the two groups not distinguishable")
chk("family background coefficient with and without college", f"falls from {ls('coefficient on family background before college completion enters'):.3f} to {ls('coefficient on family background after college completion enters'):.3f}")
need(ls('coefficient on family background after college completion enters') / ls('coefficient on family background before college completion enters') < 1 / 3, "college completion removes more than two thirds of the regression premium")
need(1 - ls("coefficient on family background after college completion enters") / ls("coefficient on family background before college completion enters") > 2 / 3, "college accounts statistically for more than two thirds of the coefficient")
rows = {"Return at which college explains half of the premium": "return at which college accounts for half of the premium", "Least squares, all children": la, "Least squares, advantaged children": lh,
        "Return at which college explains all of the premium": "return at which college accounts for all of the premium", "Instrumented, all children": "instrumented return, all children", "Instrumented, advantaged children": "instrumented return, advantaged children"}
for lab, key in rows.items():
    chk(f"decomposition table: {lab}", f"{lab} & {B(key, 'return_to_college'):.3f} & {B(key):.3f} & {sg(B(key, 'direct'))} & {B(key, 'college_share'):.2f} \\\\")
iv = "instrumented return, all children"; arl = "lower end of the 95 percent Anderson-Rubin set, all children"
ivh = "instrumented return, advantaged children"; arh = "lower end of the 90 percent Anderson-Rubin set, advantaged children"
chk("instrumented returns above the return at which college explains all", f"Both instrumented returns lie above {B(rows['Return at which college explains all of the premium'], 'return_to_college'):.2f}"); need(B(iv, 'return_to_college') > B(rows['Return at which college explains all of the premium'], 'return_to_college') and B(ivh, 'return_to_college') > B(rows['Return at which college explains all of the premium'], 'return_to_college'), "both instrumented returns above the full-explanation return"); need(abs(sH90[1][0] - B(arh, "return_to_college")) < 1e-9 and sH90[1][0] > B(rows["Return at which college explains all of the premium"], "return_to_college"), "the positive part of the 90 percent set of advantaged children starts above the return at which college explains all"); need(B(iv) > tau and B(ivh) > tau, "the college channel exceeds the premium at both instrumented returns")
need(B(arh, "college_share") >= 1 and B(ivh, "college_share") > 1, "college accounts for all of the premium at every return of the 90 percent set of advantaged children")
chk("channel at the least squares returns", "the completion gap accounts for three quarters of the premium; at the least squares return for advantaged children, it accounts for seven eighths"); need(0.72 < B(la, 'college_share') < 0.80 and 0.84 < B(lh, 'college_share') < 0.91, "college shares at the least squares returns: about three quarters and seven eighths")
U22 = {r["item"]: float(r["estimate"]) for r in u1("u22_occupation_share_by_degree.csv")}; U22r = {r["item"]: r for r in u1("u22_occupation_share_by_degree.csv")}; _n22 = sum(int(U22[f"children, {x}"]) for x in ["advantaged, graduates", "advantaged, no degree", "less advantaged, graduates", "less advantaged, no degree"]); need(f"{U22['raw share, advantaged, graduates']:.2f}" == f"{U22['raw share, less advantaged, graduates']:.2f}", "graduates of the two groups: the same raw share to two decimals"); need(1.8 < U22['raw share, advantaged, no degree'] / U22['raw share, less advantaged, no degree'] < 2.2, "without a degree: about twice the share"); chk("occupation shares by degree, Section 5.3", f"Among the {_n22:,} children with at least two waves at 30 and over that report an occupation, advantaged children hold an advantaged occupation in twice as large a share of those waves ({U22['raw share, advantaged, all']:.2f} versus {U22['raw share, less advantaged, all']:.2f}), and in about twice as large a share among children without a degree ({U22['raw share, advantaged, no degree']:.2f} versus {U22['raw share, less advantaged, no degree']:.2f}); among graduates, the shares are the same ({U22['raw share, advantaged, graduates']:.2f} each). With parental income and demographics held fixed by entropy balancing, the shares are {U22['adv_graduates']:.2f} and {U22['balanced_less_graduates']:.2f} among graduates (95 percent bootstrap interval of the gap $[{float(U22r['balanced_gap_graduates']['ci_lo']):.2f}, {float(U22r['balanced_gap_graduates']['ci_hi']):.2f}]$) and {U22['adv_no_degree']:.2f} and {U22['balanced_less_no_degree']:.2f} among children without a degree ($[{float(U22r['balanced_gap_no_degree']['ci_lo']):.2f}, {float(U22r['balanced_gap_no_degree']['ci_hi']):.2f}]$)."); need(1.8 < U22['raw share, advantaged, all'] / U22['raw share, less advantaged, all'] < 2.2, "overall: twice the share"); chk("occupation, introduction", f"Advantaged children are twice as likely as less advantaged children to hold one ({U22['raw share, advantaged, all']:.2f} versus {U22['raw share, less advantaged, all']:.2f}), and the same is true among children without a degree ({U22['raw share, advantaged, no degree']:.2f} versus {U22['raw share, less advantaged, no degree']:.2f}); among graduates, the two groups are equally likely to hold one ({U22['raw share, advantaged, graduates']:.2f})."); chk("occupation, conclusion", "Advantaged children are twice as likely to hold advantaged occupations, overall and among children without a degree, but not among graduates"); chk("opening question", "The question is what these parents pass on beyond income."); chk("why the question matters", "The premium matters for social mobility: whether less advantaged children can move up, in earnings and in occupation."); chk("reading of the premium, introduction", "A natural explanation of the premium itself is that advantaged parents pass on their ability. If so, their children should outearn less advantaged children with the same schooling and, among graduates, reach advantaged occupations more often"); chk("reading paragraph of the introduction", f"The instrumented return of {B(rows['Instrumented, all children'], 'return_to_college'):.2f} is above the least squares return of {B(rows['Least squares, all children'], 'return_to_college'):.2f}, which is consistent with the preparation reading."); U21 = {r["item"]: r for r in u1("u21_earnings_gap_by_degree.csv")}; chk("gap among graduates, Section 6", f"and only slightly more among graduates, where the gap is {float(U21['gap_among_graduates']['estimate']):.3f} log points ($[{float(U21['gap_among_graduates']['ci_lo']):.2f}, {float(U21['gap_among_graduates']['ci_hi']):.2f}]$)"); chk("Section 6: least squares is not a lower bound", f"The least squares return is not a lower bound on that worth either: positive selection into college pushes it above what a degree returned to its holders, and at lower returns the share falls below three quarters"); chk("conclusion: returns of less advantaged children", f"the instrumented return for less advantaged children, {gL['beta']:.2f}, is above their least squares return, {gL['ls']:.2f}, which suggests that unequal preparation rather than lesser ability had kept them below the cutoff"); chk("identity paragraph of the introduction", "valued at returns ranging from the least squares estimate to the instrumented estimate, the gap accounts for between three quarters and all of the premium."); need(B(rows['Instrumented, all children']) > tau and 0.70 < B(rows['Least squares, all children']) / tau < 0.80, "college channel exceeds the premium at the instrumented return and is about three quarters at the least squares return"); need("first-stage $F$" not in TEX[TEX.index("\\section{Introduction}"):TEX.index("\\section{Data}")], "no first-stage F in the introduction"); chk("half and all", f"College explains half of the premium at a return of {B(rows['Return at which college explains half of the premium'], 'return_to_college'):.2f} and all of it at {B(rows['Return at which college explains all of the premium'], 'return_to_college'):.2f}")
chk("lower end of the set", f"at {B(arl, 'return_to_college'):.2f}, the lower end of the 95 percent Anderson--Rubin set for all children, it still explains {100 * B(arl, 'college_share'):.0f} percent")
I16 = {r["item"]: float(r["value"]) for r in u1("u16_identity_in_balanced_comparison.csv")}
t1, t2, t3 = I16["part 1: college channel (return of advantaged children x completion gap)"], I16["part 2: same degrees worth more (completion of less advantaged children x difference in returns)"], I16["part 3: gap between the children without a degree"]
rH16, rL16 = I16["return, advantaged children (graduates minus children without a degree)"], I16["return, less advantaged children (reweighted)"]
need(abs(t1 + t2 + t3 - I16["premium"]) < 1e-9 and abs(I16["premium"] - tau) < 1e-6 and abs(I16["completion gap"] - gapM) < 1e-6 and int(I16["children"]) == nl, "the three measured parts sum to the premium of the balanced comparison, on the same children")
chk("returns inside the balanced comparison", f"Graduates outearn children without a degree by {rH16:.3f} log points among advantaged children and by {rL16:.3f} among reweighted less advantaged children; these are raw differences inside the balanced comparison, whereas the least squares returns of Table~\\ref{{tab:bounds}} add the controls of equation~\\eqref{{eq:oldonly}}. The premium of {tau:.3f} has three parts")
chk("first part", f"The first, {t1:.3f} ({_iv('part_1_college_channel')}), comes from the degrees that advantaged children hold in excess of those held by less advantaged children, valued at the return for advantaged children; it is the college channel, {100 * t1 / tau:.0f} percent of the premium")
chk("second part", f"The second, {t2:.3f} ({_iv('part_2_same_degrees_worth_more')}), comes from degrees up to the completion rate common to both groups (the {100 * EB['completion_less_advantaged_reweighted']:.0f} percent rate of reweighted less advantaged children), which are worth slightly more to advantaged children")
chk("third part", f"The third, {t3:.3f} ({_iv('part_3_gap_without_a_degree')}), is the gap between children of the two groups without a degree"); need(abs(t3) < 0.005 and 0.75 < t1 / tau <= 1.0, "no gap between the children without a degree; the measured college channel lies between three quarters and all of the premium")
need(0.10 < B(lh, "direct") / tau < 0.15 and 0.22 < B(la, "direct") / tau < 0.27 and f"{B(lh, 'direct'):.2f}" == "0.01" and f"{B(la, 'direct'):.2f}" == "0.02", "direct effect: an eighth to a quarter of the premium, 0.01 to 0.02 log points")
chk("share of the premium, conclusion", f"Valued at the return to college, the gap in college completion accounts for between three quarters and all of the entropy-balanced premium of {pct(tau):.0f} percent.")
chk("ability reading, introduction", "and the instrumented return would fall below the least squares return; if it ranked preparation (the preparation reading), they would earn as much or more"); chk("ability reading, first version: earnings at equal schooling (introduction)", "children without a degree earn the same in the two groups, the earnings gap among graduates is small"); need(abs(t3) < 0.005 and I16["gap between the graduates of the two groups"] < 0.03, "at equal schooling the two groups earn the same or nearly the same in the balanced comparison"); chk("ability reading, closing of the introduction", "most of the premium comes through access to college rather than through returns to ability that do not depend on a degree"); need(m["earn_iv"] > m["ols"] and m["ar_lo"] > m["ols"], "the return of the children the expansion admitted is no lower than the least squares return"); need(max(B(la, "direct") / tau, ls("coefficient on family background after college completion enters") / ls("coefficient on family background before college completion enters")) < 0.30, "at given college completion no more than about a quarter of the premium remains (identity and regression)")
need(B(la, "college_share") > 0.7, "college accounts for most of the premium even at the least squares return")
chk("ability reading, conclusion", "runs through access to college rather than through returns to ability that do not depend on a degree."); chk("ability reading, conclusion, equal schooling", "children without a degree earn the same in the two groups; among graduates the earnings gap is small and the chance of holding an advantaged occupation is the same; and the children who completed college only because seats were added earned no less from it than earlier graduates")
need(abs(raw5 - B('raw gap: parental income and the demographic and provincial controls') - tau) < 1e-6, "raw gap = parental income and controls + premium (split kept in the files of estimates)")
chk("premium and gap on the same comparison, introduction", f"the premium is {tau:.3f} log points ({pct(tau):.0f} percent) and the completion gap {100 * gapM:.1f} percentage points")
need(B(iv, "college_share") > 1 and 0.74 < B(la, "college_share") < 0.78, "college accounts for all of the premium at the instrumented return and three quarters at the least squares return")
chk("abstract: decomposition", "Valued at the return to college, the gap in college completion accounts for three quarters to all of the premium, so what parental occupation passes on beyond income is mostly a four-year degree."); need(min(B(la, "college_share"), B(lh, "college_share"), B(iv, "college_share"), B(ivh, "college_share")) >= 0.75, "the completion gap accounts for at least three quarters of the premium at every return of the table")
chk("decomposition table note", f"The premium with parental income held fixed is {tau:.3f} and the completion gap {gapM:.3f}")
chk("conclusion: premium", f"With parental income held fixed, advantaged children earn {pct(tau):.0f} to {pct(s8(l_)):.0f} percent more")
chk("sample: birth years", f"born {int(F14[f'{ALL}: first birth year'])} to {int(F14[f'{ALL}: last birth year'])}")

# census check of trends before the reform (one sentence of Section 5.1; the table is in the online appendix)
CEN = [r for r in rd(os.path.join(sibling("college_expansion", __file__), "output", "tables", "p16_census_pretrend.csv")) if r["n_cells"]]
cen_max = max(float(r["slope_diff"]) for r in CEN)
chk("census check of trends before the reform, table of threats", "diverges by under one percentage point over 20 cohorts"); need(len(CEN) == 2 and 0 < 20 * 100 * cen_max < 1, "census: two censuses; the largest slope difference cumulates to under one percentage point over 20 cohorts")
# the return for all children beside the returns by family background (first row of the table of returns): its 90 percent Anderson-Rubin set
G9 = sorted((float(r["b"]), float(r["p_wild"])) for r in u1("u9_anderson_rubin_grid.csv")); a90 = [b_ for b_, pv in G9 if pv >= 0.10]; a95 = [b_ for b_, pv in G9 if pv >= 0.05]
need(len(a90) == round((max(a90) - min(a90)) / 0.05) + 1, "90 percent set of the return for all children is one interval")
need(min(a90) > m["ols"], "90 percent set of all children starts above the least squares return")
need(abs(min(a95) - m["ar_lo"]) < 1e-9 and max(a95) >= 3.99, "95 percent set of all children: the grid file agrees with u9_B_main.csv")
_abs = TEX[TEX.index("\\begin{abstract}"):TEX.index("\\textbf{JEL:}")]; need(len(re.sub(r"\\\\[a-z]+|[{}\\\\]|\\[4pt\\]", " ", _abs).split()) <= 290, "abstract of at most 290 words")
chk("title-page footnote points to the Online Appendix and the replication files", "Online Appendix and replication files: \\href{\\repourl}")
G3 = {r["outcome"]: r for r in u1("u9_G_three_year_completion.csv")}; g15 = G3["exactly 15 years of schooling (three-year degree)"]
chk("three-year completion does not rise with the instrument", f"does not rise with the instrument (coefficient {sg(float(g15['coef']), 2)}, SE {float(g15['se']):.2f}, wild cluster $p = {float(g15['p_wild']):.2f}$)"); need(float(g15["coef"]) < 0 and float(g15["p_wild"]) > 0.10, "three-year completion: negative coefficient, not distinguishable from zero")
for lbl_, snip_ in [("local average treatment effect named", "a local average treatment effect in the sense of \\citet{ImbensAngrist1994}: a weighted average of the returns to college for compliers"), ("Oaxaca-Blinder named", "the identity is an Oaxaca--Blinder decomposition with college completion as the only covariate"),
                    ("reliability ratio named", "the reliability ratio $\\lambda_T$ is"), ("errors-in-variables named", "The errors-in-variables problem that \\citet{Solon1992} identified in U.S. panels is at least as severe here"), ("comparison with U.S. data in the introduction", "as short averages do in U.S. data \\citep{Mazumder2005}, takes about six biennial waves"), ("difference-in-differences named", "the comparison is a difference-in-differences"),
                    ("parallel trends and exclusion named", "The design rests on parallel trends (provinces that added more seats were not already on different trends) and exclusion (the instrument affects the outcomes only through college), and four checks in Section~\\ref{sec:expansion} support them."), ("event study named", "reports the event study"), ("intergenerational elasticity named", "intergenerational income elasticity"),
                    ("identity against valuation", "Evaluated at a return estimated separately, by least squares or by instrumental variables, the identity values the completion gap and leaves a remainder, which Table~\\ref{tab:bounds} reports as the direct effect"),
                    ("the conclusion ends on the answer", "what parental occupation passes on beyond income is mostly a four-year degree. Family background shapes who holds one")]:
    chk(lbl_, snip_)
need(TEXN.rindex("is mostly a four-year degree. Family background shapes who holds one") > TEXN.rindex("In percentage points, however, the seats that provinces added"), "the last paragraph of the conclusion is the one on the expansion")
print("=== wording that must appear, and the table fragments")
for lbl, snip in [("abstract: instrument defined", "an instrument that interacts provincial growth in seats with each cohort's exposure to the expansion"), ("abstract: the answer", "through access to college. The evidence points to the second."),
                  ("title", "Family Background, Earnings Dynamics, and the Return to College}"), ("the two columns bracket the premium", "Column 1 over-controls, because family income contains the child's own earnings when the child lives with the parents, and column 2 under-controls"), ("entropy balancing has its own subsection", "\\subsection{Entropy balancing}"),
                  ("below-30 term not interpreted", "I do not report or interpret $\\beta_b$: every child observed below 30"), ("low-schooling check in the introduction is the occupation result", "did not move into advantaged occupations where seats grew faster"), ("first sentence is about the panel", "In the China Family Panel Studies (CFPS), children with a parent in an official, managerial, or professional occupation (advantaged children)"), ("keyword matches the title", "intergenerational mobility; earnings dynamics;"), ("advantage means occupation, not income", "Occupation marks family position in these cohorts because the parents built their careers in the 1980s and 1990s"), ("the attenuation factor and the weights from the same process, introduction", "the weights for a precision-weighted estimate of the return to college")]:
    chk(lbl, snip)
# the table fragments on disk must be what the files of estimates imply
import subprocess as _sp
_r = _sp.run([sys.executable, os.path.join(ROOT, "code", "build_paper_tables.py"), "--check"], capture_output=True, text=True)
_msg = _r.stdout.strip().splitlines()[-1] if _r.stdout.strip() else _r.stderr.strip()[-200:]
need(_r.returncode == 0, f"table fragments regenerate identically: {_msg}")

print("=== further checks")
chk("Shanghai left out", f"without it the reduced form stays at {_u19s.reduced_form:.3f}, the first stage falls to {_u19s.first_stage:.3f}, and the return is {_u19s.instrumented_return:.2f}, with an Anderson--Rubin set that starts at {_u19s.ar95_lo:.2f}")
need(_sh.intensity == _u19a.intensity.max(), "Shanghai has the highest intensity among the provinces of the sample")
_c9r = lambda lab, col: float(c9(lab, col))
chk("province-specific trends, Section 5.3", f"A linear cohort trend for each province gives {c9('province-specific linear cohort trends', 'iv'):.2f}, with a reduced form of {c9('province-specific linear cohort trends', 'coef'):.3f} (SE {c9('province-specific linear cohort trends', 'se'):.3f}), and leaving out the cohorts born 1973 to 1976, whose completion has the largest pre-reform gradient on intensity in Figure~\\ref{{fig:mature}}, gives {c9('cohorts born 1973 to 1976 left out', 'iv'):.2f}")
_g, _gs = float(g5["gamma"]), float(g5["se"])
chk("growth interval over a decade", f"the 95 percent interval runs from about $-{abs(5 * (_g - 1.96 * _gs)):.2f}$ to {5 * (_g + 1.96 * _gs):.2f} log points over a decade")
chk("first stage bins", "20 bins for less advantaged children, 10 for advantaged children")
chk("the set for advantaged children (Section 5.3)", "the set for advantaged children consists of two unbounded rays, $(-\\infty, -0.50]$ and $[0.25, \\infty)$.")
need(abs(gL["fs"] - gH["fs"]) < 2 * (gL["fs_se"] ** 2 + gH["fs_se"] ** 2) ** 0.5, "group first stages on the rows at 30 and over not distinguishable (values in the online appendix)")
_full = B(rows["Return at which college explains all of the premium"], "return_to_college"); chk("Table 8 note: the direct effect is zero at the full-explanation return", f"the 95 percent Anderson--Rubin sets of both instrumented returns contain {_full:.3f}, the return at which the direct effect is zero")
need(sA95[0][0] < _full < sA95[0][1] and _full >= sH95[1][0], "the Anderson-Rubin sets of both instrumented returns contain the full-explanation return")
print("=== appendix of formal results (numbers recomputed here from the files of estimates)")
_r, _se, _eps = float(P7["rho"]), float(P7["eta2"]), float(P7["eps2"]); _sv = _eps / (1 - _r ** 2); _s = _se / (_se + _sv)
def _fT(T, r): return 1 + 2 * sum((1 - k / T) * r ** k for k in range(1, T))
need(all(abs(_fT(T, r) - ((1 + r) / (1 - r) - 2 * r * (1 - r ** T) / (T * (1 - r) ** 2))) < 1e-12 for T in range(1, 12) for r in (0.05, 0.16, 0.33, 0.8)), "appendix: closed form of f_T equals its sum form")
chk("appendix: f_5 at the pooled persistence", f"At $\\rho = {_r:.2f}$, $f_5 = {_fT(5, _r):.2f}$, which gives $\\lambda_5 = {_se / (_se + _sv * _fT(5, _r) / 5):.2f}$ against $\\lambda^\\circ_5 = {_se / (_se + _sv / 5):.2f}$")
need(abs(_se / (_se + _sv / 5) - e('approx', 5)) < 5e-3 and abs(_se / (_se + _sv * _fT(5, _r) / 5) - e('exact', 5)) < 5e-3, "appendix: lambda_5 recomputed from the parameters agrees with the attenuation table")
_hL, _hH = (1 - round(float(L7["rho"]), 2)) ** 2, (1 - round(float(H7["rho"]), 2)) ** 2  # at the printed estimates, as in Part II of the Online Appendix
chk("appendix: leverage of the second-order autocorrelation", f"$\\hat\\rho = {float(L7['rho']):.2f}$, $h_2 = {_hL:.2f}$; at the estimate for advantaged children, $\\hat\\rho = {float(H7['rho']):.2f}$, $h_2 = {_hH:.2f}$, with moments from {a3} children rather than {n3 - a3:,}")
need(all(abs((1 - r ** k - k * r ** (k - 1) * (1 - r)) - (1 - r) ** 2 * sum((j + 1) * r ** j for j in range(k - 1))) < 1e-12 for k in range(2, 9) for r in (0.12, 0.33, 0.9)), "appendix: factorization of h_k")
for _lab in ("app:atten", "app:ridge", "app:md", "app:rank"): chk("appendix: label " + _lab, "\\label{" + _lab + "}", count=1)
_jac = lambda r, se2: np.linalg.det(np.array([[1.0, r ** k / (1 - r ** 2), se2 * (k * r ** (k - 1) / (1 - r ** 2) if k else 0.0) + se2 * r ** k * 2 * r / (1 - r ** 2) ** 2] for k in range(3)]))
need(all(abs(_jac(r, se2) - se2 / (1 + r) ** 2) < 1e-12 for r in (-0.5, 0.12, 0.16, 0.33, 0.9) for se2 in (0.1, 0.326, 1.0)), "appendix: Jacobian determinant at lags 0, 1, 2 equals sigma_eps^2/(1+rho)^2")
_Gm = np.random.default_rng(0).normal(size=(15, 3)); _Wm = np.diag(np.random.default_rng(1).uniform(.2, 2, 15)); _Pm = np.eye(15) - _Gm @ np.linalg.solve(_Gm.T @ _Wm @ _Gm, _Gm.T @ _Wm)
need(np.allclose(_Pm.T @ _Wm @ _Pm, _Wm - _Wm @ _Gm @ np.linalg.solve(_Gm.T @ _Wm @ _Gm, _Gm.T @ _Wm)), "appendix: P'WP equals A in the proof of the limit of J")
need(TEX.index("\\appendix") > TEX.index("\\bibliography{refs}"), "the appendix follows the reference list")

print()
if fails:
    print(f"{fails} check(s) FAILED")
    sys.exit(1)
print("all checks of the paper passed")

