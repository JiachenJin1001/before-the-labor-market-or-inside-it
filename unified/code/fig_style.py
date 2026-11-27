"""Shared style of the figures of the paper and of the Online Appendix.

The figures are drawn close to the size at which they are printed, so that the text inside them prints at about 7 to 10
points. The text is set in Latin Modern Roman, the typeface of the paper, and each figure is saved as a PNG and
as a vector PDF; the paper includes the PDF. The fonts are embedded as TrueType (pdf.fonttype 42), not as Type 3
fonts: the OpenType (CFF) files of Latin Modern in the TeX installation are converted once to TrueType outlines in a
cache folder of the system temporary directory, and matplotlib embeds those. The two family-background groups are drawn in an orange and a dark blue that differ in lightness, so
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


def setup(size=None):
    """Fonts and text sizes. With size, every text element (labels, ticks, legend, panel titles) is set in that size."""
    matplotlib.rcParams.update({"font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9.5, "legend.fontsize": 8, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
                                "mathtext.fontset": "cm", "axes.unicode_minus": True,
                                "pdf.fonttype": 42, "ps.fonttype": 42})   # TrueType embedding, not Type 3
    if size is not None:
        matplotlib.rcParams.update({k: size for k in ("font.size", "axes.labelsize", "axes.titlesize", "legend.fontsize", "xtick.labelsize", "ytick.labelsize")})
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
    """Paths of TrueType copies of the Latin Modern Roman fonts of the TeX installation (empty if kpsewhich does not find
    them). The OpenType files have CFF outlines, which matplotlib cannot embed cleanly as TrueType; each is converted
    once to quadratic (TrueType) outlines and cached."""
    import subprocess, tempfile
    out = []
    cache = os.path.join(tempfile.gettempdir(), "ws_figure_fonts")
    for f in ("lmroman10-regular.otf", "lmroman10-bold.otf", "lmroman10-italic.otf"):
        try:
            p = subprocess.run(["kpsewhich", f], capture_output=True, text=True, timeout=20).stdout.strip()
        except Exception:
            p = ""
        if not p:
            continue
        ttf = os.path.join(cache, os.path.splitext(f)[0] + ".ttf")
        try:
            if not os.path.exists(ttf):
                os.makedirs(cache, exist_ok=True); _otf_to_ttf(p, ttf)
            out.append(ttf)
        except Exception:
            out.append(p)   # fall back to the OpenType file
    return out


def _otf_to_ttf(src, dst):
    """Convert an OpenType font with CFF outlines to a TrueType font (the otf2ttf recipe of fontTools)."""
    from fontTools.ttLib import TTFont, newTable
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    font = TTFont(src)
    order = font.getGlyphOrder(); gs = font.getGlyphSet()
    glyphs = {}
    for name in order:
        pen = TTGlyphPen(gs); gs[name].draw(Cu2QuPen(pen, 1.0, reverse_direction=True)); glyphs[name] = pen.glyph()
    font["loca"] = newTable("loca")
    font["glyf"] = glyf = newTable("glyf"); glyf.glyphOrder = order; glyf.glyphs = glyphs
    del font["CFF "]
    if "VORG" in font: del font["VORG"]
    glyf.compile(font)
    for name in order:   # left side bearing of each glyph from its new bounding box
        g = glyf[name]; adv, _ = font["hmtx"][name]; font["hmtx"][name] = (adv, getattr(g, "xMin", 0))
    font["maxp"] = maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    for k in ("maxZones",): setattr(maxp, k, 1)
    for k in ("maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs", "maxStackElements", "maxSizeOfInstructions"):
        setattr(maxp, k, 0)
    maxp.maxComponentElements = max((len(g.components) if hasattr(g, "components") else 0) for g in glyphs.values())
    maxp.compile(font)
    post = font["post"]; post.formatType = 2.0; post.extraNames = []; post.mapping = {}; post.glyphOrder = order
    font.sfntVersion = "\000\001\000\000"
    font.save(dst)


def save(fig, name, tight=True):
    """Write the figure as name (a PNG at 300 dpi) and as a vector PDF beside it; returns the path of the PNG.
    With tight=False the files keep the canvas size exactly (the layout must then keep everything inside the canvas),
    so that the natural width of the figure, and hence the printed size of its text, is known in advance."""
    out = outpath(name)
    kw = dict(bbox_inches="tight") if tight else {}
    fig.savefig(out, dpi=300, **kw); fig.savefig(os.path.splitext(out)[0] + ".pdf", **kw)
    return out


def outpath(name):
    d = os.path.join(ROOT, "paper", "figures")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def stagger_xticks(ax, positions, labels, step=None):
    """Category tick labels on two alternating rows: the labels at even positions on the first row, those at odd
    positions on the second row, with a longer tick mark leading to them. Used where the labels of neighbouring
    categories would otherwise run into each other at a legible size."""
    import matplotlib as mpl
    positions = list(positions); labels = list(labels)
    size = mpl.rcParams["xtick.major.size"]
    step = mpl.rcParams["xtick.labelsize"] * 1.25 if step is None else step
    ax.set_xticks(positions[0::2]); ax.set_xticklabels(labels[0::2])
    ax.set_xticks(positions[1::2], minor=True); ax.set_xticklabels(labels[1::2], minor=True)
    ax.tick_params(axis="x", which="minor", length=size + step, width=mpl.rcParams["xtick.major.width"],
                   labelsize=mpl.rcParams["xtick.labelsize"])
