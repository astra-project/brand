# /// script
# requires-python = ">=3.10"
# dependencies = ["fonttools[woff]>=4.50"]
# ///
"""Build the ASTRA logo kit.

The mark is an "A" drawn as a constellation, which is also a past light cone
(Λ): everything that could have influenced the event at its apex. That set is
what an astra.yaml records for a result.

  * star at the apex     the result, the event whose past cone the A traces
  * two feet             inputs
  * crossbar             a decision between two options: the open ring was
                         considered, the gold node is the one a universe selects;
                         the bar rises toward it
  * gold link            the path that universe takes, from its option up to
                         the result
  * gold                 Antique Gold, the colour ASTRA UI gives the `decision`
                         record kind

Nothing is symmetric on purpose. A symmetric A under a star reads as a rocket;
the lit stroke, the rising bar and the unequal input stars (two magnitudes, as
on a star chart) make it a constellation.

Colours come from tokens/colors.json; text is outlined from the fonts in
fonts/, so the SVGs need no font installed.

Usage:
    uv run tools/build_logo.py              SVGs, tokens/colors.css and PNGs
    uv run tools/build_logo.py --svg-only   SVGs and tokens/colors.css only
PNG export also needs rsvg-convert (librsvg) and magick (ImageMagick 7).
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"
LOGO_DIR, LOGO_PNG_DIR = ROOT / "logo", ROOT / "logo" / "png"
ICON_DIR, SOCIAL_DIR, TOKEN_DIR = ROOT / "icons", ROOT / "social", ROOT / "tokens"

# Byline on the social card.
SOCIAL_BYLINE = "an open specification from Lightcone Research"

# --- Palette: tokens/colors.json ------------------------------------------------
TOKENS = json.loads((TOKEN_DIR / "colors.json").read_text())


def _scheme(name):
    t = {k: v["$value"] for k, v in TOKENS[name].items() if not k.startswith("$")}
    # Drawing roles: stars and rings use ink, links use link, text follows ink/link.
    return dict(star=t["ink"], line=t["link"], gold=t["gold"], text=t["ink"], sub=t["link"],
                ground=t["ground"], rule=t["rule"])


LIGHT, DARK = _scheme("light"), _scheme("dark")


def colors_css():
    lines = ["/* Generated from tokens/colors.json by tools/build_logo.py. Do not edit. */", ":root {"]
    for scheme in ("light", "dark"):
        for key, tok in TOKENS[scheme].items():
            if key.startswith("$"):
                continue
            lines.append(f"  --astra-brand-{scheme}-{key}: {tok['$value']}; /* {tok['$description']} */")
    lines.append("}")
    return "\n".join(lines) + "\n"


def f2(x: float) -> str:
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# --- Geometry ----------------------------------------------------------------
def twinkle(cx, cy, rx, ry, k, cubic=True):
    """Four-pointed star with concave flanks.

    cubic: each flank's control points sit on the two ray axes at k × ray length,
    so the tips leave along their own axis (fine needle points, for large sizes).
    quadratic: one control point pulled to k × the flank midpoint (blunter, sturdier
    tips that survive 16px rendering).
    """
    tips = [(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]
    d = f"M{f2(tips[0][0])} {f2(tips[0][1])}"
    for i in range(4):
        a, b = tips[i], tips[(i + 1) % 4]
        if cubic:
            c1 = (cx + (a[0] - cx) * k, cy + (a[1] - cy) * k)
            c2 = (cx + (b[0] - cx) * k, cy + (b[1] - cy) * k)
            d += f"C{f2(c1[0])} {f2(c1[1])} {f2(c2[0])} {f2(c2[1])} {f2(b[0])} {f2(b[1])}"
        else:
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            d += f"Q{f2(cx + (mx - cx) * k)} {f2(cy + (my - cy) * k)} {f2(b[0])} {f2(b[1])}"
    return d + "Z"


def trimmed(a, b, ta, tb):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    return (a[0] + ux * ta, a[1] + uy * ta), (b[0] - ux * tb, b[1] - uy * tb)


def on_line(a, b, y):
    """Point on segment a-b at height y."""
    t = (y - a[1]) / (b[1] - a[1])
    return (a[0] + (b[0] - a[0]) * t, y)


# Primary mark: fine-line star-chart drawing, for 48px and up.
# Lines stop short of every star, as on a celestial chart; this also keeps the
# drawing correct on any background (no knock-out fills).
PRIMARY = dict(
    apex=(50, 16), foot=(12.5, 87), bar_l=66.5, bar_r=57.5,
    line_w=3.2, gap=2.5,
    foot_r=(4.8, 3.6), ring_r=4.3, ring_w=2.6, pick_r=6.2,
    star=(10, 11.5, 0.26), star_clear=9.5,
)


def primary_mark(c, mono: str | None = None) -> tuple[str, tuple]:
    p = PRIMARY
    apex, fl = p["apex"], p["foot"]
    fr = (2 * apex[0] - fl[0], fl[1])
    bl, br = on_line(apex, fl, p["bar_l"]), on_line(apex, fr, p["bar_r"])
    rfl, rfr = p["foot_r"]
    ring_out = p["ring_r"] + p["ring_w"] / 2
    G = p["gap"]
    star_c, line_c, gold_c = (mono, mono, mono) if mono else (c["star"], c["line"], c["gold"])

    def d(segs):
        return "".join(f"M{f2(a[0])} {f2(a[1])}L{f2(b[0])} {f2(b[1])}" for a, b in segs)

    links = d([
        trimmed(apex, bl, p["star_clear"], ring_out + G),     # left leg, upper
        trimmed(bl, fl, ring_out + G, rfl + G),               # left leg, lower
        trimmed(br, fr, p["pick_r"] + G, rfr + G),            # right leg, lower
        trimmed(bl, br, ring_out + G, p["pick_r"] + G),       # crossbar
    ])
    path = d([trimmed(br, apex, p["pick_r"] + G, p["star_clear"])])  # the lit path
    w = f2(p["line_w"])
    out = [
        f'<g class="astra-links" fill="none" stroke="{line_c}" stroke-width="{w}" stroke-linecap="round">'
        f'<path d="{links}"/></g>',
        f'<g class="astra-path" fill="none" stroke="{gold_c}" stroke-width="{w}" stroke-linecap="round">'
        f'<path d="{path}"/></g>',
        f'<g class="astra-stars" fill="{star_c}">'
        f'<circle cx="{f2(fl[0])}" cy="{f2(fl[1])}" r="{f2(rfl)}"/>'
        f'<circle cx="{f2(fr[0])}" cy="{f2(fr[1])}" r="{f2(rfr)}"/></g>',
        f'<g class="astra-options" fill="none" stroke="{star_c}" stroke-width="{f2(p["ring_w"])}">'
        f'<circle cx="{f2(bl[0])}" cy="{f2(bl[1])}" r="{f2(p["ring_r"])}"/></g>',
        f'<g class="astra-universe" fill="{gold_c}">'
        f'<circle cx="{f2(br[0])}" cy="{f2(br[1])}" r="{f2(p["pick_r"])}"/>'
        f'<path d="{twinkle(apex[0], apex[1], *p["star"])}"/></g>',
    ]
    bbox = (fl[0] - rfl, apex[1] - p["star"][1], fr[0] + rfr, fl[1] + max(rfl, rfr))
    return "".join(out), bbox


# Compact mark: solid strokes on a 32-unit grid, for favicons and UI chrome (≤ 48px).
# Same story at low resolution: the upper right stroke and the star are gold.
COMPACT = dict(
    apex=(16, 7.0), foot=(4.0, 28.3), bar_l=23.0, bar_r=19.6,
    leg_w=3.6, bar_w=2.7,
    star=(4.7, 5.9, 0.22), star_clear=5.2,
)


def compact_mark(c, mono: str | None = None) -> tuple[str, tuple]:
    p = COMPACT
    apex, fl = p["apex"], p["foot"]
    fr = (2 * apex[0] - fl[0], fl[1])
    bl, br = on_line(apex, fl, p["bar_l"]), on_line(apex, fr, p["bar_r"])
    ink, gold = (mono, mono) if mono else (c["star"], c["gold"])
    la, _ = trimmed(apex, fl, p["star_clear"], 0)
    ra, _ = trimmed(apex, fr, p["star_clear"], 0)
    ink_d = (f"M{f2(fl[0])} {f2(fl[1])}L{f2(la[0])} {f2(la[1])}"
             f"M{f2(br[0])} {f2(br[1])}L{f2(fr[0])} {f2(fr[1])}")
    bar_d = f"M{f2(bl[0])} {f2(bl[1])}L{f2(br[0])} {f2(br[1])}"
    gold_d = f"M{f2(br[0])} {f2(br[1])}L{f2(ra[0])} {f2(ra[1])}"
    lw = f2(p["leg_w"])
    out = [
        f'<g class="astra-glyph" fill="none" stroke="{ink}" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="{ink_d}" stroke-width="{lw}"/><path d="{bar_d}" stroke-width="{f2(p["bar_w"])}"/></g>',
        f'<g class="astra-path" fill="none" stroke="{gold}" stroke-linecap="round">'
        f'<path d="{gold_d}" stroke-width="{lw}"/></g>',
        f'<g class="astra-universe" fill="{gold}">'
        f'<path d="{twinkle(apex[0], apex[1], *p["star"], cubic=False)}"/></g>',
    ]
    return "".join(out), (0, 0, 32, 32)


# --- Type: outline brand fonts -------------------------------------------------
class Face:
    def __init__(self, path: Path, location: dict | None = None):
        self.font = TTFont(path)
        self.upm = self.font["head"].unitsPerEm
        self.cmap = self.font.getBestCmap()
        self.gs = self.font.getGlyphSet(location=location) if location else self.font.getGlyphSet()
        self.kern = {}
        if "kern" in self.font:
            self.kern = self.font["kern"].kernTables[0].kernTable
        self.c2sc = self._single_subst("c2sc") if "GSUB" in self.font else {}

    def _single_subst(self, tag):
        gsub = self.font["GSUB"].table
        idx = {i for fr in gsub.FeatureList.FeatureRecord if fr.FeatureTag == tag for i in fr.Feature.LookupListIndex}
        m = {}
        for i in idx:
            for st in gsub.LookupList.Lookup[i].SubTable:
                st = getattr(st, "ExtSubTable", st)
                m.update(getattr(st, "mapping", {}) or {})
        return m

    def cap_height(self):
        return self.font["OS/2"].sCapHeight

    def glyph_names(self, text, small_caps=False):
        names = [self.cmap[ord(ch)] for ch in text]
        return [self.c2sc.get(n, n) if small_caps else n for n in names]

    def set_line(self, text, x, baseline, size, tracking=0.0, small_caps=False, adjust=None):
        """Return (svg path d, advance width). tracking in em; adjust: {index: em} extra space after glyph i."""
        s = size / self.upm
        names = self.glyph_names(text, small_caps)
        d, pen_x = [], 0.0
        for i, n in enumerate(names):
            pen = SVGPathPen(self.gs, ntos=lambda v: f2(v))
            self.gs[n].draw(TransformPen(pen, (s, 0, 0, -s, x + pen_x, baseline)))
            d.append(pen.getCommands())
            adv = self.gs[n].width
            if i + 1 < len(names):
                adv += self.kern.get((n, names[i + 1]), 0)
                adv += (tracking + (adjust or {}).get(i, 0)) * self.upm
            pen_x += adv * s
        return "".join(d), pen_x

    def ink_bounds(self, text, size, tracking=0.0, small_caps=False, adjust=None):
        """Left/right ink extents of a set line (so tracking doesn't leave optical gaps)."""
        from fontTools.pens.boundsPen import BoundsPen
        s = size / self.upm
        names = self.glyph_names(text, small_caps)
        bp = BoundsPen(self.gs)
        pen_x = 0.0
        for i, n in enumerate(names):
            self.gs[n].draw(TransformPen(bp, (s, 0, 0, s, pen_x, 0)))
            adv = self.gs[n].width
            if i + 1 < len(names):
                adv += self.kern.get((n, names[i + 1]), 0) + (tracking + (adjust or {}).get(i, 0)) * self.upm
            pen_x += adv * s
        xmin, _, xmax, _ = bp.bounds
        return xmin, xmax


WORDMARK_FACE = FONTS / "Quattrocento-Regular.woff2"  # stems ≈ the mark's line weight
WORD = "ASTRA"
WORD_TRACK = 0.15            # generous Roman-inscription spacing
WORD_ADJUST = {3: -0.03}     # R→A: the open diagonal reads loose; pull it in
DESCRIPTOR = "AGENTIC SCHEMA FOR TRANSPARENT RESEARCH ANALYSIS"


def wordmark(face: Face, x, baseline, cap_px, colour):
    size = cap_px * face.upm / face.cap_height()
    xmin, xmax = face.ink_bounds(WORD, size, WORD_TRACK, adjust=WORD_ADJUST)
    d, _ = face.set_line(WORD, x - xmin, baseline, size, WORD_TRACK, adjust=WORD_ADJUST)
    return f'<path class="astra-wordmark" fill="{colour}" d="{d}"/>', xmax - xmin


def descriptor(face: Face, x, baseline, width, colour, track=0.12):
    """Small-cap descriptor at fixed tracking, sized so its ink spans exactly `width`."""
    a, b = face.ink_bounds(DESCRIPTOR, 100.0, track, small_caps=True)
    size = 100.0 * width / (b - a)  # ink width scales linearly with size
    a, _ = face.ink_bounds(DESCRIPTOR, size, track, small_caps=True)
    d, _ = face.set_line(DESCRIPTOR, x - a, baseline, size, track, small_caps=True)
    return f'<path class="astra-descriptor" fill="{colour}" d="{d}"/>', size


# --- Documents -----------------------------------------------------------------
def doc(body, vb, title, desc, w=None, h=None, extra_head=""):
    vx, vy, vw, vh = vb
    size = f' width="{f2(w)}" height="{f2(h)}"' if w else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f2(vx)} {f2(vy)} {f2(vw)} {f2(vh)}"{size} '
        f'role="img" aria-labelledby="__ID__-t __ID__-d">'
        f'<title id="__ID__-t">{title}</title><desc id="__ID__-d">{desc}</desc>{extra_head}{body}</svg>\n'
    )


MARK_DESC = ("ASTRA mark: a letter A drawn as a constellation and a past light cone. Two input stars at the feet, "
             "a rising decision crossbar with a considered option as an open ring and the selected option in gold, "
             "and a gold link from the selected option up to a gold four-pointed star, the result, at the apex.")


def padded(bbox, pad):
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    side = max(w, h) + 2 * pad
    return (x0 + w / 2 - side / 2, y0 + h / 2 - side / 2, side, side)


def build_marks():
    files = {}
    for name, scheme in (("astra-mark", LIGHT), ("astra-mark-dark", DARK)):
        body, bb = primary_mark(scheme)
        files[name] = doc(body, padded(bb, 6), "ASTRA", MARK_DESC)
    body, bb = primary_mark(LIGHT, mono="currentColor")
    files["astra-mark-mono"] = doc(body, padded(bb, 6), "ASTRA", MARK_DESC)

    cdesc = "ASTRA compact mark: a solid letter A whose upper right stroke is gold, under a gold four-pointed star."
    for name, scheme in (("astra-compact", LIGHT), ("astra-compact-dark", DARK)):
        body, vb = compact_mark(scheme)
        files[name] = doc(body, vb, "ASTRA", cdesc)
    body, vb = compact_mark(LIGHT, mono="currentColor")
    files["astra-compact-mono"] = doc(body, vb, "ASTRA", cdesc)

    # Favicon: light colours as plain attributes (any renderer), overridden for
    # dark mode by CSS attribute selectors (browsers honour the media query).
    # The rules are scoped to the favicon's own root: an inlined <style> applies
    # to the whole host page, and unscoped rules would recolour other logos there.
    body, vb = compact_mark(LIGHT)
    sc = ".astra-favicon"
    style = (f'<style>@media (prefers-color-scheme:dark){{'
             f'{sc} [stroke="{LIGHT["star"]}"]{{stroke:{DARK["star"]}}}{sc} [stroke="{LIGHT["gold"]}"]{{stroke:{DARK["gold"]}}}'
             f'{sc} [fill="{LIGHT["gold"]}"]{{fill:{DARK["gold"]}}}}}</style>')
    files["favicon"] = doc(body, vb, "ASTRA", cdesc, extra_head=style).replace("<svg ", '<svg class="astra-favicon" ', 1)
    return files


def layout_horizontal(scheme, word: Face, alg: Face | None = None):
    """Mark + wordmark (+ descriptor when `alg` is given). Returns (body, ink bbox).

    The wordmark's baseline meets the bottom of the gold node (the selected
    option), about the midpoint of the rising bar. Cap height 0.34 × mark
    height makes its stems about the mark's line weight. With a descriptor, a gold rule follows, then the full name in
    small caps whose baseline meets the bottom of the larger input star.
    """
    mark, (mx0, my0, mx1, my1) = primary_mark(scheme)
    mh = my1 - my0
    cap = 0.34 * mh
    base = PRIMARY["bar_r"] + PRIMARY["pick_r"]
    x = mx1 + 0.24 * mh
    wm, ww = wordmark(word, x, base, cap, scheme["text"])
    if alg is None:
        return mark + wm, (mx0, my0, x + ww, my1)
    dwidth = ww * 1.9
    dline, _ = descriptor(alg, x, my1, dwidth, scheme["sub"])
    rule_y = base + 0.105 * mh
    rule = (f'<path class="astra-rule" d="M{f2(x)} {f2(rule_y)}H{f2(x + dwidth)}" stroke="{scheme["gold"]}" '
            f'stroke-width="{f2(0.011 * mh)}" fill="none"/>')
    return mark + wm + rule + dline, (mx0, my0, x + dwidth, my1)


def layout_stacked(scheme, word: Face):
    mark, (mx0, my0, mx1, my1) = primary_mark(scheme)
    mh = my1 - my0
    cap = 0.27 * mh
    mcx = (mx0 + mx1) / 2
    _, ww = wordmark(word, 0, 0, cap, scheme["text"])
    base = my1 + 0.21 * mh + cap
    wm, _ = wordmark(word, mcx - ww / 2, base, cap, scheme["text"])
    w = max(mx1 - mx0, ww)
    return mark + wm, (mcx - w / 2, my0, mcx + w / 2, base)


def with_pad(bbox, pad):
    x0, y0, x1, y1 = bbox
    return (x0 - pad, y0 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad)


def build_lockups():
    word = Face(WORDMARK_FACE)
    alg = Face(FONTS / "Alegreya-Variable.woff2", location={"wght": 500})
    pad = 0.16 * (PRIMARY["foot"][1] + max(PRIMARY["foot_r"]) - PRIMARY["apex"][1] + PRIMARY["star"][1])
    files = {}
    for suffix, scheme in (("", LIGHT), ("-dark", DARK)):
        body, bb = layout_horizontal(scheme, word)
        files[f"astra-lockup{suffix}"] = doc(body, with_pad(bb, pad), "ASTRA",
                                             "ASTRA logo: the ASTRA mark followed by the ASTRA wordmark.")
        body, bb = layout_horizontal(scheme, word, alg)
        files[f"astra-lockup-descriptor{suffix}"] = doc(
            body, with_pad(bb, pad), "ASTRA: Agentic Schema for Transparent Research Analysis",
            "ASTRA logo with descriptor: the ASTRA mark, the ASTRA wordmark, and the line "
            "Agentic Schema for Transparent Research Analysis.")
        body, bb = layout_stacked(scheme, word)
        files[f"astra-lockup-stacked{suffix}"] = doc(body, with_pad(bb, pad), "ASTRA",
                                                     "ASTRA logo, stacked: the ASTRA mark above the ASTRA wordmark.")
    return files


def build_social():
    """GitHub / Open Graph preview card, 1280×640, on parchment."""
    word = Face(WORDMARK_FACE)
    alg = Face(FONTS / "Alegreya-Variable.woff2", location={"wght": 500})
    W, H, side = 1280, 640, 104
    body, (x0, y0, x1, y1) = layout_horizontal(LIGHT, word, alg)
    k = (W - 2 * side) / (x1 - x0)
    tx, ty = side - x0 * k, (H - (y1 - y0) * k) / 2 - y0 * k - 8
    g = f'<g transform="translate({f2(tx)} {f2(ty)}) scale({f2(k)})">{body}</g>'
    lc_face = Face(FONTS / "Newsreader-Italic.woff2", location={"wght": 400, "opsz": 24})
    byline = SOCIAL_BYLINE
    by_d, _ = lc_face.set_line(byline, 0, 0, 25)
    _, b = lc_face.ink_bounds(byline, 25)
    by_path = f'<path fill="{LIGHT["sub"]}" transform="translate({f2(W - 64 - b)} {H - 58})" d="{by_d}"/>'
    frame = f'<rect x="28" y="28" width="{W - 56}" height="{H - 56}" fill="none" stroke="{LIGHT["rule"]}" stroke-width="1.5"/>'
    page = f'<rect width="{W}" height="{H}" fill="{LIGHT["ground"]}"/>{frame}{g}{by_path}'
    return doc(page, (0, 0, W, H), "ASTRA", "ASTRA social preview card.", W, H)


def render_png(svg_path: Path, png_path: Path, w: int, h: int | None = None, bg: str | None = None):
    cmd = ["rsvg-convert", "-w", str(w), "-h", str(h or w), "-a" if h is None else "", str(svg_path), "-o", str(png_path)]
    cmd = [c for c in cmd if c]
    if bg:
        cmd[1:1] = ["-b", bg]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--svg-only", action="store_true", help="skip PNG and ICO export")
    args = ap.parse_args()

    for d in (LOGO_DIR, LOGO_PNG_DIR, ICON_DIR, SOCIAL_DIR):
        d.mkdir(parents=True, exist_ok=True)
    (TOKEN_DIR / "colors.css").write_text(colors_css())

    marks = build_marks()
    favicon = marks.pop("favicon")
    outputs = {LOGO_DIR / f"{n}.svg": t for n, t in {**marks, **build_lockups()}.items()}
    outputs[ICON_DIR / "favicon.svg"] = favicon
    outputs[SOCIAL_DIR / "astra-social-card.svg"] = build_social()
    for path, text in outputs.items():
        # IDs are namespaced by file so several SVGs can be inlined in one page.
        path.write_text(text.replace("__ID__", path.stem))
    if args.svg_only:
        return

    logo = lambda n: LOGO_DIR / f"{n}.svg"  # noqa: E731
    ground = LIGHT["ground"]
    # Favicons from the compact mark
    for px in (16, 32, 48):
        render_png(logo("astra-compact"), ICON_DIR / f"favicon-{px}.png", px)
    subprocess.run(["magick", *(str(ICON_DIR / f"favicon-{p}.png") for p in (16, 32, 48)),
                    str(ICON_DIR / "favicon.ico")], check=True)
    # Square icons: the primary mark on parchment, with breathing room
    for name, px, inner in (("apple-touch-icon.png", 180, 144), ("icon-512.png", 512, 410), ("avatar-500.png", 500, 400)):
        tmp = ICON_DIR / f"_{name}"
        render_png(logo("astra-mark"), tmp, inner)
        subprocess.run(["magick", "-size", f"{px}x{px}", f"xc:{ground}", str(tmp), "-gravity", "center",
                        "-composite", str(ICON_DIR / name)], check=True)
        tmp.unlink()
    # 2x rasters of the logos, transparent
    for name in ("astra-mark", "astra-mark-dark", "astra-compact", "astra-compact-dark",
                 "astra-lockup", "astra-lockup-dark", "astra-lockup-descriptor", "astra-lockup-descriptor-dark",
                 "astra-lockup-stacked", "astra-lockup-stacked-dark"):
        width = 1200 if "lockup" in name else 600
        render_png(logo(name), LOGO_PNG_DIR / f"{name}@2x.png", width)
    render_png(SOCIAL_DIR / "astra-social-card.svg", SOCIAL_DIR / "astra-social-card-1280x640.png", 1280, 640)


if __name__ == "__main__":
    main()
