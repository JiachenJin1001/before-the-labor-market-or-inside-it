"""What the first stage means in percentage points, for contrasts of provincial intensity wider than the interquartile range (Section 5.2).

Sample: the 4,536 children of the paper's sample. A contrast between two percentiles of provincial intensity among children is multiplied by the
rise in the cohort exposure ratio from the cohorts born in 1980 or earlier to those born in 1989 or later (the difference in the instrument
that u9 uses for the interquartile range) and by the first-stage coefficients of u14 (block C: all children, and each group with the instrument
entering once for each group). No regression is run here.

Output: output/u20_first_stage_magnitudes.csv
"""
import os
import pandas as pd
from sample_mature_age import build_sample
H = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(H, "..", "output")
c = build_sample(level_from=None)
e_late, e_pre = c[c.by >= 1989].exposure_ratio.mean(), c[c.by <= 1980].exposure_ratio.mean()
C14 = pd.read_csv(os.path.join(OUT, "u14_C_first_stages_all_children.csv")).set_index("row")
fs = {"all": float(C14.loc[[r for r in C14.index if r.startswith("all children")][0], "fs"]),
      "less advantaged": float(C14.loc[[r for r in C14.index if r.startswith("less advantaged children, instrument")][0], "fs"]),
      "advantaged": float(C14.loc[[r for r in C14.index if r.startswith("advantaged children, instrument")][0], "fs"])}
rows = []
for lab, lo, hi in [("25th to 75th", .25, .75), ("10th to 90th", .10, .90), ("5th to 95th", .05, .95), ("lowest to highest", 0, 1)]:
    a, b = c.pro_predict_growth.quantile(lo), c.pro_predict_growth.quantile(hi); dz = (b - a) * (e_late - e_pre)
    rows.append(dict(contrast=lab, intensity_low=a, intensity_high=b, difference_in_instrument=dz, **{f"pp_{k}": 100 * dz * v for k, v in fs.items()}))
out = pd.DataFrame(rows); out.to_csv(os.path.join(OUT, "u20_first_stage_magnitudes.csv"), index=False)
print(out.round(3).to_string()); print("exposure", e_late, e_pre); print(fs)
print(c[["pro_predict_growth"]].describe().T.round(3).to_string())
