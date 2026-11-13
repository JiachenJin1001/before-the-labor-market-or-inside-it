"""Shared style of the figures of the paper and of the Online Appendix.

The figures are drawn close to the size at which they are printed, so that the text inside them prints at about 7 to 9
points. The text is set in Latin Modern Roman, the typeface of the paper, and each figure is saved as a PNG and
as a vector PDF; the paper includes the PDF. The two family-background groups are drawn in an orange and a dark blue that differ in lightness, so
that they remain distinguishable in a black-and-white print, and they also differ in marker shape.
"""
import os
import matplotlib
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
LANG = "en"
ADV, LESS = "#d95f02", "#08519c"        # advantaged children (orange), less advantaged children (dark blue)
SHRINK = 0.64                           # canvas size in inches as a fraction of the nominal size


def fs(size):
    """Canvas size in inches: the nominal size times SHRINK."""
    return (size[0] * SHRINK, size[1] * SHRINK)


def setup():
    matplotlib.rcParams.update({"font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9.5, "legend.fontsize": 8, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
                                "mathtext.fontset": "cm"})   # fonts are embedded as outlines (matplotlib default), which every viewer renders
    lm = [p for p in _latin_modern() if os.path.exists(p)]
    if lm:
        from matplotlib import font_manager
        for p in lm: font_manager.fontManager.addfont(p)
        matplotlib.rcParams.update({"font.family": "serif", "font.serif": ["Latin Modern Roman", "CMU Serif", "Times New Roman", "DejaVu Serif"]})
    else:
        matplotlib.rcParams.update({"font.family": "serif", "font.serif": ["CMU Serif", "Times New Roman", "DejaVu Serif"]})


def tr(s):
    """The label as drawn (every figure script passes its labels through this function)."""
    return s


def _latin_modern():
    """Paths of the Latin Modern Roman font files of the TeX installation (empty if kpsewhich does not find them)."""
    import subprocess
    out = []
    for f in ("lmroman10-regular.otf", "lmroman10-bold.otf", "lmroman10-italic.otf"):
        try:
            p = subprocess.run(["kpsewhich", f], capture_output=True, text=True, timeout=20).stdout.strip()
        except Exception:
            p = ""
        if p: out.append(p)
    return out


def save(fig, name):
    """Write the figure as name (a PNG at 300 dpi) and as a vector PDF beside it; returns the path of the PNG."""
    out = outpath(name)
    fig.savefig(out, dpi=300, bbox_inches="tight"); fig.savefig(os.path.splitext(out)[0] + ".pdf", bbox_inches="tight")
    return out


def outpath(name):
    d = os.path.join(ROOT, "paper", "figures")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)
