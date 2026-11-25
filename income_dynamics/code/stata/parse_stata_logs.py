"""Collect the Arellano-Bond estimates of the three implementations into one file.

Reads the Stata logs that the two do-files of this folder write when run in
batch mode from this folder (stata-mp -b do 05_method2_abgmm.do, then the same
for 06_system_gmm_xtabond2.do):
  05_method2_abgmm.log         the Mata implementation of the formulas of
                               05_method2_abgmm.py (difference GMM, two-step)
  06_system_gmm_xtabond2.log   xtabond2, block (a) difference GMM and block (b)
                               system GMM, two-step with Windmeijer-corrected
                               standard errors
and the Python estimates of the Arellano-Bond table of the online appendix
(output/tables/m10_abgmm_table3.csv, written by m10_abgmm_table3.py).

Writes output/tables/stata_abgmm_parity.csv, one row per model and
implementation, with the columns
  model, implementation, rho0, rho0_se, rho1, rho1_se, hansen_J, df,
  hansen_p, n_eq, n_children, n_instruments
Rows: difference GMM, five waves (Python, Mata, xtabond2); system GMM, five
waves (Python, xtabond2). The Hansen p-value of the Mata row is computed here
from the statistic and its degrees of freedom. The online appendix reports
these numbers in its section on the diagnostics of the dynamic-panel estimate,
and online_appendix/build/check_part1_numbers.py asserts them.

    python3 parse_stata_logs.py
"""
import os, re
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__)); M = os.path.abspath(os.path.join(HERE, "..", ".."))
log5 = open(os.path.join(HERE, "05_method2_abgmm.log"), encoding="utf-8", errors="ignore").read()
log6 = open(os.path.join(HERE, "06_system_gmm_xtabond2.log"), encoding="utf-8", errors="ignore").read()
m10 = pd.read_csv(os.path.join(M, "output", "tables", "m10_abgmm_table3.csv")).set_index("panel")
rows = []


def num(pattern, text, k=1):
    m = re.search(pattern, text, re.M)
    assert m, pattern
    return float(m.group(k))


# Python (m10_abgmm_table3.csv)
for model, key in [("difference GMM, five waves", "diff GMM, 2014-2022"), ("system GMM, five waves", "system GMM, 2014-2022")]:
    r = m10.loc[key]
    rows.append(dict(model=model, implementation="Python", rho0=r.rho0, rho0_se=r.rho0_se, rho1=r.rho1, rho1_se=r.rho1_se,
                     hansen_J=r.J, df=int(r.df_J), hansen_p=r.pJ, n_eq=int(r.n_eq), n_children=int(r.n_children), n_instruments=int(r.n_inst)))

# Mata (05_method2_abgmm.do): the two-step estimates as the do-file prints them at the end, with full precision
blk = log5[log5.index("05_method2_abgmm.do: complete"):]
rows.append(dict(model="difference GMM, five waves", implementation="Mata",
                 rho0=num(r"^\s*rho_0 = ([-\d.]+)\s+SE = ([\d.]+)", blk), rho0_se=num(r"^\s*rho_0 = ([-\d.]+)\s+SE = ([\d.]+)", blk, 2),
                 rho1=num(r"^\s*rho_1 = ([-\d.]+)\s+SE = ([\d.]+)", blk), rho1_se=num(r"^\s*rho_1 = ([-\d.]+)\s+SE = ([\d.]+)", blk, 2),
                 hansen_J=num(r"Hansen J = ([\d.]+) \(df = (\d+)\)", blk), df=int(num(r"Hansen J = ([\d.]+) \(df = (\d+)\)", blk, 2)),
                 hansen_p=float("nan"), n_eq=int(num(r"N eq = (\d+), G clusters = (\d+)", log5)), n_children=int(num(r"N eq = (\d+), G clusters = (\d+)", log5, 2)),
                 n_instruments=4))
rows[-1]["hansen_p"] = 1 - stats.chi2.cdf(rows[-1]["hansen_J"], rows[-1]["df"])

# xtabond2 (06_system_gmm_xtabond2.do): block (a) difference GMM and block (b) system GMM
a = log6[log6.index("=== (a)"):log6.index("=== (b)")]; b = log6[log6.index("=== (b)"):]
for model, t in [("difference GMM, five waves", a), ("system GMM, five waves", b)]:
    rows.append(dict(model=model, implementation="xtabond2",
                     rho0=num(r"^rho_0 =\s*([-\d.]+)\s+\(SE ([\d.]+)\)", t), rho0_se=num(r"^rho_0 =\s*([-\d.]+)\s+\(SE ([\d.]+)\)", t, 2),
                     rho1=num(r"^rho_1 =\s*([-\d.]+)\s+\(SE ([\d.]+)\)", t), rho1_se=num(r"^rho_1 =\s*([-\d.]+)\s+\(SE ([\d.]+)\)", t, 2),
                     hansen_J=num(r"Hansen test of overid\. restrictions: chi2\((\d+)\)\s*=\s*([\d.]+)\s+Prob > chi2 =\s*([\d.]+)", t, 2),
                     df=int(num(r"Hansen test of overid\. restrictions: chi2\((\d+)\)", t)),
                     hansen_p=num(r"Hansen test of overid\. restrictions: chi2\((\d+)\)\s*=\s*([\d.]+)\s+Prob > chi2 =\s*([\d.]+)", t, 3),
                     n_eq=int(num(r"Number of obs\s*=\s*(\d+)", t)), n_children=int(num(r"Number of groups\s*=\s*(\d+)", t)),
                     n_instruments=int(num(r"Number of instruments = (\d+)", t))))
out = pd.DataFrame(rows)
out.to_csv(os.path.join(M, "output", "tables", "stata_abgmm_parity.csv"), index=False)
print(out.to_string())
