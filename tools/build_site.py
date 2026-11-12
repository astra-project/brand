# /// script
# requires-python = ">=3.10"
# dependencies = ["fonttools[woff]>=4.50"]
# ///
"""Build docs/index.html, the web version of the ASTRA brand guide.

    uv run tools/build_site.py

The guide's content (figures, rules, colour chips, type specimens, file list)
lives in this module; tools/build_pdf.py imports it to lay out branding.pdf, so
the two never disagree. Run tools/build_logo.py first: the guide inlines the
SVGs it writes.
"""

from __future__ import annotations

import base64
import html
import json
import math
import re
import sys
from contextlib import contextmanager
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import build_logo as B  # noqa: E402

REPO_URL = "https://github.com/astra-project/brand"
PDF_URL = f"{REPO_URL}/blob/main/branding.pdf"
ASSET_DIRS = (ROOT / "logo", ROOT / "icons", ROOT / "social")
f2 = B.f2
_instances = 0


# --- Inlining the published SVGs ----------------------------------------------
def asset(name: str) -> Path:
    for d in ASSET_DIRS:
        if (d / f"{name}.svg").exists():
            return d / f"{name}.svg"
    raise FileNotFoundError(f"{name}.svg: run tools/build_logo.py first")


def svg(name, cls="", decorative=False, width=None, height=None):
    """Inline a published SVG, renaming its ids so repeated copies stay unique."""
    global _instances
    _instances += 1
    s = asset(name).read_text().strip()
    s = re.sub(rf"\b{re.escape(name)}-(t|d)\b", rf"{name}-i{_instances}-\1", s)
    if decorative:
        s = re.sub(r"<title[^>]*>.*?</title><desc[^>]*>.*?</desc>", "", s)
        s = re.sub(r'role="img" aria-labelledby="[^"]*"', 'aria-hidden="true" focusable="false"', s)
    attrs = "".join(f' {k}="{v}"' for k, v in (("class", cls), ("width", width), ("height", height)) if v)
    return s.replace("<svg ", f"<svg{attrs} ", 1)


def data_uri(name):
    return "data:image/svg+xml;base64," + base64.b64encode(asset(name).read_bytes()).decode()


def bare_mark(body, bb, attrs=""):
    vx, vy, vw, vh = B.padded(bb, 6)
    return f'<svg viewBox="{f2(vx)} {f2(vy)} {f2(vw)} {f2(vh)}" aria-hidden="true" focusable="false" {attrs}>{body}</svg>'


@contextmanager
def geometry(**overrides):
    """Temporarily change the mark's geometry (for the don'ts)."""
    saved = dict(B.PRIMARY)
    B.PRIMARY.update(overrides)
    try:
        yield
    finally:
        B.PRIMARY.clear()
        B.PRIMARY.update(saved)


# --- Figures --------------------------------------------------------------------
def construction_svg():
    """The mark as a light-cone diagram: future cone dashed above, time axis."""
    P = B.PRIMARY
    apex, fl = P["apex"], P["foot"]
    fr = (2 * apex[0] - fl[0], fl[1])
    body, _ = B.primary_mark(B.LIGHT)
    dx, dy = fl[0] - apex[0], fl[1] - apex[1]
    up = 0.62
    fut_l, fut_r = (apex[0] - dx * up, apex[1] - dy * up), (apex[0] + dx * up, apex[1] - dy * up)
    n = math.hypot(fr[0] - apex[0], fr[1] - apex[1])
    nx, ny = (fr[1] - apex[1]) / n, -(fr[0] - apex[0]) / n  # outward normal of the right leg
    ang = math.degrees(math.atan2(fr[1] - apex[1], fr[0] - apex[0]))
    lx = apex[0] + (fr[0] - apex[0]) * 0.36 + 8.6 * nx
    ly = apex[1] + (fr[1] - apex[1]) * 0.36 + 8.6 * ny
    return f"""<svg class="plate-svg themed" viewBox="-14 -36 128 136" role="img" aria-label="The ASTRA mark drawn as a light-cone diagram">
<g class="cone-guides" fill="none" stroke-width="0.6" stroke-linecap="round">
  <path stroke-dasharray="1.6 2.2" d="M{f2(apex[0])} {f2(apex[1])}L{f2(fut_l[0])} {f2(fut_l[1])}M{f2(apex[0])} {f2(apex[1])}L{f2(fut_r[0])} {f2(fut_r[1])}"/>
  <path d="M-8 96V-30M-10.2 -26.5L-8 -31L-5.8 -26.5"/>
</g>
<g class="plate-labels">
  <text x="-6.2" y="-20" class="lab-axis">time</text>
  <text x="{f2(apex[0])}" y="-26" text-anchor="middle" class="lab-it">future light cone</text>
  <text transform="translate({f2(lx)} {f2(ly)}) rotate({f2(ang)})" text-anchor="middle" class="lab-it">past light cone</text>
  <text x="{f2(apex[0])}" y="{f2(fl[1] + 4)}" text-anchor="middle" class="lab-it">inputs</text>
</g>
{body}
</svg>"""


def clearspace_svg():
    """Clear space: one star height (x) on every side of the mark."""
    body, (x0, y0, x1, y1) = B.primary_mark(B.LIGHT)
    x = 2 * B.PRIMARY["star"][1]
    m = 3
    w, h = x1 - x0, y1 - y0
    unit = B.twinkle(x0 - x / 2, y0 - x / 2, x * 0.36, x / 2 * 0.92, 0.26)
    return f"""<svg class="cs-svg themed" viewBox="{f2(x0 - x - m)} {f2(y0 - x - m)} {f2(w + 2 * (x + m))} {f2(h + 2 * (x + m))}" role="img" aria-label="Clear space around the mark equals the height of its star">
<g class="cs-guides" fill="none" stroke-width="0.5" stroke-dasharray="1.4 1.6">
  <rect x="{f2(x0)}" y="{f2(y0)}" width="{f2(w)}" height="{f2(h)}"/>
  <rect x="{f2(x0 - x)}" y="{f2(y0 - x)}" width="{f2(w + 2 * x)}" height="{f2(h + 2 * x)}"/>
</g>
<path class="cs-unit" d="{unit}"/>
<g class="plate-labels"><text x="{f2(x0 - x / 2)}" y="{f2(y1 + x / 2 + 1.6)}" text-anchor="middle" class="lab-it">x</text>
<text x="{f2(x1 + x / 2)}" y="{f2(y0 + h / 2 + 1.6)}" text-anchor="middle" class="lab-it">x</text></g>
{body}
</svg>"""


def glyph(kind):
    """Legend glyphs drawn in the mark's own vocabulary."""
    return {
        "star": f'<path class="g-gold" d="{B.twinkle(12, 12, 7.5, 8.6, 0.26)}"/>',
        "foot": '<circle class="g-star" cx="12" cy="12" r="5"/>',
        "bar": '<path class="g-line" d="M3 15L21 9" stroke-width="2" stroke-linecap="round"/>',
        "ring": '<circle class="g-ring" cx="12" cy="12" r="4.4" stroke-width="2.4" fill="none"/>',
        "pick": ('<circle class="g-gold" cx="7.5" cy="16.5" r="4.6"/>'
                 '<path class="g-goldline" d="M12.2 11.8L20 4" stroke-width="2" stroke-linecap="round"/>'),
        "gap": ('<circle class="g-star" cx="5" cy="12" r="3.4"/>'
                '<path class="g-line" d="M11.2 12H21" stroke-width="2" stroke-linecap="round"/>'),
    }[kind]


LEGEND = [
    ("star", "Result", "The four-pointed star at the apex. The A is the past light cone of this event: everything that could have influenced it."),
    ("foot", "Inputs", "The two stars at the feet, drawn at two magnitudes as on a star chart. The data the analysis starts from."),
    ("bar", "Decision", "The crossbar, joining the options for one methodological choice. It rises toward the option that was taken."),
    ("ring", "Option considered", "The open ring. ASTRA keeps the options that were not taken in the record, so the mark does too."),
    ("pick", "Selected option and its path", "The gold node is the option a universe selects; the gold link carries it up to the result. Gold is the colour ASTRA UI gives the <code>decision</code> record kind."),
    ("gap", "Lines stop short", "Links end before each star, as on a celestial chart. No knock-out fills, so the mark sits on any background."),
]


def legend_html(items=LEGEND):
    return "".join(
        f'<div class="leg-row"><svg class="leg-glyph" viewBox="0 0 24 24" aria-hidden="true">{glyph(k)}</svg>'
        f'<div><dt>{t}</dt><dd>{d}</dd></div></div>' for k, t, d in items)


def yaml_html():
    out = []
    for line in (ROOT / "docs" / "mark.astra.yaml").read_text().strip().splitlines():
        e = html.escape(line)
        m = re.match(r"^(\s*)([A-Za-z_]+)(:)(.*)$", e)
        if not m:
            out.append(e)
            continue
        ind, key, colon, rest = m.groups()
        rest = re.sub(r"\{([a-z_.]+)\}", r'<span class="y-ph">{\1}</span>', rest)
        if "crossbar: right" in line:
            rest = rest.replace("right", '<span class="y-pick">right</span>')
        k = f'<span class="y-pick">{key}</span>' if key in ("right", "gold") else f'<span class="y-key">{key}</span>'
        out.append(f"{ind}{k}{colon}{rest}")
    return "\n".join(out)


def ladder(scheme):
    sfx = "" if scheme == "light" else "-dark"
    cells = [(f"astra-compact{sfx}", px) for px in (16, 24, 32)] + [(f"astra-mark{sfx}", px) for px in (48, 64, 96)]
    return "".join(
        f'<figure class="lad"><div class="lad-box">{svg(n, width=px, height=px, decorative=True)}</div>'
        f'<figcaption>{px}</figcaption></figure>' for n, px in cells)


def donts():
    """(title, why, artwork, ground) for each misuse, drawn from the real geometry."""
    gold, slate = B.LIGHT["gold"], "#3F7280"
    body, bb = B.primary_mark(B.LIGHT)
    with geometry(bar_l=61.5, bar_r=61.5, foot_r=(4.2, 4.2)):
        level_body, level_bb = B.primary_mark(B.LIGHT)
    return [
        ("Don't level the bar", "The bar rises toward the selected option. Levelled, with equal stars, the A turns rigid and reads as an object.",
         bare_mark(level_body, level_bb), "light"),
        ("Don't recolour the gold", "Gold marks the selected option, its path and the result. Any other colour there breaks that meaning.",
         bare_mark(body.replace(gold, slate), bb), "light"),
        ("Don't stretch or skew", "Scale the mark and the lockups only in proportion.",
         bare_mark(body, bb, 'preserveAspectRatio="none" class="stretch"'), "light"),
        ("Don't use the light version on a dark ground", "Use the dark version, or the mono version in a light colour.",
         bare_mark(body, bb), "dark"),
    ]


DOS = [
    "Use the light versions on light grounds and the dark versions on dark grounds.",
    "Use the mono version for one-colour printing, embossing, and on photographs.",
    "Keep clear space of one star height on every side.",
    "Below 48 px, use the compact mark.",
    "Typeset the name in running text as ASTRA, in capitals. Spell it out as Agentic Schema for Transparent Research Analysis on first use.",
]
NEVERS = "Never add shadows, glows, gradients or outlines; never rotate the mark; never rebuild the wordmark in another typeface."

SIZES = [
    ("Primary mark", "48 px tall", "13 mm tall"),
    ("Horizontal and stacked lockups", "mark 48 px tall", "mark 13 mm tall"),
    ("Lockup with descriptor", "400 px wide", "106 mm wide"),
    ("Compact mark", "16 to 48 px", "below 13 mm"),
]
SIZES_NOTE = ("Print sizes are the screen sizes at 96 dpi. The descriptor limit keeps its small caps at least 5 px tall.")


def tokens(scheme):
    data = json.loads((ROOT / "tokens" / "colors.json").read_text())[scheme]
    return [(k, v["$value"], v["$description"]) for k, v in data.items() if not k.startswith("$")]


def chips(scheme):
    return "".join(
        f'<div class="chip"><span class="sw" style="background:{hx}"></span><div class="chip-txt"><b>{k.capitalize()}</b>'
        f'<code>{hx}</code><code class="tok">--astra-brand-{scheme}-{k}</code><span>{html.escape(d)}</span></div></div>'
        for k, hx, d in tokens(scheme))


TYPE = [
    ("Quattrocento", "Wordmark and headings", '<span class="ts-word">ASTRA</span><span class="ts-head">What the mark shows</span>'),
    ("Alegreya, small caps", "Labels, eyebrows and the descriptor", '<span class="ts-sc">Agentic Schema for Transparent Research Analysis</span>'),
    ("Newsreader", "Body text and italic captions",
     '<span class="ts-body">A universe picks one option per decision it uses. <em>The same analysis can carry many universes.</em></span>'),
]
TYPE_NOTE = ("Quattrocento, Alegreya and Newsreader are in <code>fonts/</code> under the SIL Open Font License, "
             "and on Google Fonts. Code and file names use IBM Plex Mono, from Google Fonts.")

FILES = [
    ("logo/astra-lockup.svg · -dark", "Horizontal lockup. The default logo."),
    ("logo/astra-lockup-descriptor.svg · -dark", "Lockup with the full name, for title pages, posters and site heroes."),
    ("logo/astra-lockup-stacked.svg · -dark", "Stacked lockup, for square spaces."),
    ("logo/astra-mark.svg · -dark · -mono", "The mark alone, 48 px and up. Mono uses <code>currentColor</code>."),
    ("logo/astra-compact.svg · -dark · -mono", "The compact mark, 16 to 48 px: app chrome, docs headers."),
    ("logo/png/", "Transparent 2× PNG copies of all of the above."),
    ("icons/favicon.svg · favicon.ico · favicon-16/32/48.png", "Favicons. The SVG follows the browser's colour scheme."),
    ("icons/apple-touch-icon.png · icon-512.png · avatar-500.png", "Home-screen icon, web-app icon, GitHub and social avatar."),
    ("social/astra-social-card.svg · -1280x640.png", "GitHub social preview and Open Graph image."),
    ("tokens/colors.json · colors.css", "The brand colours as design tokens and CSS custom properties."),
    ("fonts/", "Quattrocento, Alegreya and Newsreader, with their licences."),
]


def files_html():
    return "".join(f"<tr><td><code>{f}</code></td><td>{d}</td></tr>" for f, d in FILES)


# --- Shared CSS -------------------------------------------------------------------
# Colours of the mark inside .themed follow the page tokens; everything else is
# component styling shared by the web page and the PDF.
COMPONENT_CSS = """
.themed .astra-links, .themed .g-line { stroke: var(--mk-line); }
.themed .astra-stars, .themed .g-star { fill: var(--mk-star); }
.themed .astra-options, .themed .g-ring { stroke: var(--mk-star); }
.themed .astra-universe, .themed .g-gold { fill: var(--mk-gold); }
.themed .astra-path, .themed .g-goldline { stroke: var(--mk-gold); }
.themed .astra-wordmark { fill: var(--ink); }
.themed .astra-descriptor { fill: var(--muted); }
.themed .astra-rule { stroke: var(--gold); }
.themed .astra-glyph { stroke: var(--mk-star); }
.cone-guides, .cs-guides { stroke: var(--subtle); }
.cs-unit { fill: var(--subtle); }
.plate-labels text { fill: var(--subtle); font-family: var(--f-body); }
.lab-it { font-style: italic; font-size: 4.6px; }
.lab-axis { font-family: var(--f-ui) !important; font-variant-caps: all-small-caps; font-size: 4.4px; letter-spacing: 0.12em; }

dl.legend { margin: 0; display: grid; gap: 1em; }
.leg-row { display: grid; grid-template-columns: 2em minmax(0, 1fr); gap: 0.85em; align-items: start; }
.leg-glyph { width: 2em; height: 2em; display: block; }
dt { font-family: var(--f-ui); font-weight: 700; }
dd { margin: 0.1em 0 0; color: var(--muted); line-height: 1.45; }

pre.code { margin: 0; background: var(--code-bg); border: 1px solid var(--rule); border-radius: 3px; padding: 1em 1.1em;
  overflow-x: auto; font-family: var(--f-mono); font-size: 0.8em; line-height: 1.6; color: var(--ink); }
.y-key { color: var(--muted); }
.y-pick { color: var(--gold); font-weight: 600; }
.y-ph { color: var(--eyebrow); }

.spec { border-radius: 3px; border: 1px solid var(--spec-edge); display: grid; place-items: center; min-width: 0; }
.spec.light { background: var(--spec-light); }
.spec.dark { background: var(--spec-dark); border-color: var(--spec-dark); }
.spec svg { width: 100%; height: auto; display: block; }

.ladder { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 1.6em; }
.lad { margin: 0; display: grid; justify-items: center; gap: 0.45em; }
.lad-box { display: grid; place-items: end center; min-height: 96px; }
.lad svg { display: block; }
.lad figcaption { font-family: var(--f-mono); font-size: 0.7em; color: #8B7D70; font-variant-numeric: tabular-nums; }

.chips { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 0 1em; }
.chip { display: grid; grid-template-columns: 3em minmax(0, 1fr); gap: 0.8em; align-items: start; padding: 0.75em 0; border-top: 1px solid var(--rule); }
.sw { width: 3em; height: 3em; border-radius: 50%; box-shadow: inset 0 0 0 1px rgb(127 127 127 / 0.28); }
.chip-txt { display: grid; gap: 0.1em; font-size: 0.86em; min-width: 0; }
.chip-txt b { font-family: var(--f-ui); font-weight: 700; font-size: 1.1em; }
.chip-txt code { color: var(--ink); }
.chip-txt code.tok { color: var(--subtle); font-size: 0.82em; word-break: break-all; }
.chip-txt span { color: var(--muted); font-style: italic; }
.group-label { font-family: var(--f-ui); font-weight: 500; font-variant-caps: all-small-caps; letter-spacing: 0.12em; color: var(--subtle); margin: 0; font-size: 1em; }

.type-row { display: grid; grid-template-columns: minmax(0, 13em) minmax(0, 1fr); gap: 1.2em; padding: 0.9em 0; border-top: 1px solid var(--rule); align-items: baseline; }
.type-row b { font-family: var(--f-ui); font-weight: 700; display: block; }
.type-row small { color: var(--muted); font-style: italic; font-size: 0.9em; }
.ts-word { font-family: var(--f-head); font-size: 2.2em; letter-spacing: 0.15em; margin-right: 0.6em; }
.ts-head { font-family: var(--f-head); font-size: 1.5em; }
.ts-sc { font-family: var(--f-ui); font-weight: 500; font-variant-caps: all-small-caps; letter-spacing: 0.12em; font-size: 1.15em; color: var(--muted); }
.ts-body { font-family: var(--f-body); font-size: 1.1em; }

.donts { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1em; }
.dont { margin: 0; display: grid; gap: 0.6em; align-content: start; }
.dont-art { position: relative; aspect-ratio: 4 / 3; display: grid; place-items: center; }
.dont-art svg { height: 72%; width: auto; }
.dont-art svg.stretch { width: 86%; height: 56%; }
.dont-art::after { content: ""; position: absolute; top: 0.55em; right: 0.55em; width: 1.1em; height: 1.1em;
  background: linear-gradient(45deg, transparent 43%, var(--dont) 43% 57%, transparent 57%),
              linear-gradient(-45deg, transparent 43%, var(--dont) 43% 57%, transparent 57%); }
.dont figcaption b { font-family: var(--f-ui); font-weight: 700; display: block; }
.dont figcaption span { color: var(--muted); font-size: 0.92em; }
ul.dos { margin: 0; padding-left: 1.1em; display: grid; gap: 0.35em; }
ul.dos li::marker { color: var(--gold); }

table.sizes, table.files { width: 100%; border-collapse: collapse; }
table.sizes th, table.sizes td, table.files td { text-align: left; vertical-align: top; padding: 0.55em 0.9em 0.55em 0; border-bottom: 1px solid var(--rule); }
table.sizes th { font-family: var(--f-ui); font-weight: 500; font-variant-caps: all-small-caps; letter-spacing: 0.1em; color: var(--subtle); border-bottom-color: var(--rule-strong); }
table.sizes td:first-child { font-family: var(--f-ui); font-weight: 700; }
table.sizes td { font-variant-numeric: tabular-nums; }
table.files td:first-child { width: 42%; }
table.files td:first-child code { font-size: 0.8em; word-break: break-word; }
table.files td:last-child { color: var(--muted); }
"""

LIGHT_TOKENS = """
  --canvas: #F8F7F3; --surface: #F1EFE9; --ink: #221F20; --muted: #4E5A70; --subtle: #7A6E63;
  --gold: #A67C3C; --eyebrow: #3F7280; --rule: #E4E1D7; --rule-strong: #D2CCBF; --dont: #A45A43;
  --mk-line: #4E5A70; --mk-star: #221F20; --mk-gold: #A67C3C;
  --spec-light: #F8F7F3; --spec-dark: #221F20; --spec-edge: #D2CCBF; --code-bg: #F1EFE9;
"""
DARK_TOKENS = """
  --canvas: #221F20; --surface: #2A2728; --ink: #F1EFE9; --muted: #B4BDCD; --subtle: #9C9085;
  --gold: #C2924A; --eyebrow: #7FA8B5; --rule: #3B3738; --rule-strong: #4C4747; --dont: #C97F66;
  --mk-line: #B4BDCD; --mk-star: #F1EFE9; --mk-gold: #C2924A; --spec-edge: #4C4747; --code-bg: #2A2728;
  color-scheme: dark;
"""
FONT_STACKS = """
  --f-head: "Quattrocento", Georgia, "Times New Roman", serif;
  --f-body: "Newsreader", Georgia, "Times New Roman", serif;
  --f-ui: "Alegreya", "Palatino Linotype", Georgia, serif;
  --f-mono: "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
"""


# --- Web page --------------------------------------------------------------------
WEB_CSS = """
* { box-sizing: border-box; }
body { margin: 0; background: var(--canvas); color: var(--ink); font-family: var(--f-body); font-size: 17px; line-height: 1.55;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 0 4rem; }
.wrap { max-width: 1080px; margin: 0 auto; }
code { font-family: var(--f-mono); font-size: 0.82em; }
a { color: var(--gold); }
:focus-visible { outline: 2px solid var(--eyebrow); outline-offset: 2px; }
.masthead { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 0.5rem 2rem; padding-block: 1.6rem 1rem;
  border-bottom: 1px solid var(--rule-strong); font-family: var(--f-ui); font-weight: 500; font-variant-caps: all-small-caps; letter-spacing: 0.12em; color: var(--muted); }
.masthead a { color: var(--muted); }
.hero { padding-block: clamp(2.5rem, 7vw, 5.5rem) clamp(2rem, 5vw, 3.5rem); display: grid; gap: clamp(1.75rem, 4vw, 3rem); }
.hero-lockup { width: min(100%, 860px); height: auto; display: block; }
.lede { max-width: 40rem; font-size: clamp(1.1rem, 2.2vw, 1.3rem); line-height: 1.5; margin: 0; }
.plate { border-top: 1px solid var(--rule-strong); padding-block: clamp(2rem, 5vw, 3.25rem); display: grid; gap: 1.75rem; }
.plate-head { display: grid; gap: 0.35rem; max-width: 44rem; }
.eyebrow { font-family: var(--f-ui); font-weight: 500; font-variant-caps: all-small-caps; font-size: 0.95rem; letter-spacing: 0.14em; color: var(--eyebrow); }
h2 { font-family: var(--f-head); font-weight: 400; font-size: clamp(1.6rem, 3.6vw, 2.25rem); line-height: 1.15; margin: 0; text-wrap: balance; }
h3 { font-family: var(--f-head); font-weight: 700; font-size: 1.125rem; margin: 0 0 0.4rem; }
.plate-head p { margin: 0.4rem 0 0; color: var(--muted); }
.two { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr); gap: clamp(1.5rem, 4vw, 3.5rem); align-items: start; }
.plate-svg { width: 100%; height: auto; display: block; max-width: 520px; }
.cs-svg { width: 100%; max-width: 420px; height: auto; display: block; }
.yaml { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.25fr); gap: clamp(1.25rem, 3vw, 2.5rem); align-items: start; }
.yaml p { margin: 0; color: var(--muted); }
.fine { margin-top: 0.75rem !important; font-size: 0.9rem; color: var(--subtle) !important; font-style: italic; }
.spec { padding: clamp(1.25rem, 4vw, 2.5rem); }
.pair { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.75rem; }
figure { margin: 0; }
.cap { font-style: italic; font-size: 0.95rem; color: var(--muted); margin-top: 0.7rem; max-width: 46rem; }
.cap b { font-style: normal; font-family: var(--f-ui); font-weight: 700; color: var(--ink); }
.stack-pair .spec svg { width: min(70%, 240px); }
.lockups, .stack { display: grid; gap: 1.5rem; }
.tbl { overflow-x: auto; }
.mock { border: 1px solid var(--rule-strong); border-radius: 3px; overflow: hidden; background: var(--surface); min-width: 0; }
.tabbar { display: flex; align-items: flex-end; gap: 2px; padding: 0.55rem 0.6rem 0; background: var(--rule); }
.tab { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.9rem; border-radius: 6px 6px 0 0; font-family: system-ui, sans-serif; font-size: 12px; color: var(--muted); min-width: 0; }
.tab.on { background: var(--canvas); color: var(--ink); }
.tab span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tab img { flex: none; display: block; }
.docbar { display: flex; align-items: center; gap: 0.6rem; padding: 0.8rem 1rem; background: var(--canvas); border-bottom: 1px solid var(--rule); }
.docbar .name { font-family: var(--f-head); font-size: 1.05rem; letter-spacing: 0.12em; }
.docbar .nav { margin-left: auto; display: flex; gap: 1rem; font-family: var(--f-ui); font-size: 0.85rem; color: var(--muted); flex-wrap: wrap; justify-content: flex-end; }
.docbody { padding: 1rem 1rem 1.25rem; display: grid; gap: 0.5rem; background: var(--canvas); }
.docbody .l { height: 0.55rem; border-radius: 2px; background: var(--rule); }
.mock-cap { padding: 0.55rem 0.9rem; font-family: var(--f-ui); font-weight: 500; font-variant-caps: all-small-caps; letter-spacing: 0.1em; font-size: 0.8rem; color: var(--subtle); border-top: 1px solid var(--rule); }
.social svg { width: 100%; height: auto; display: block; }
.foot { border-top: 1px solid var(--rule-strong); padding-top: 1.25rem; font-size: 0.9rem; color: var(--subtle); font-style: italic; }
@media (max-width: 760px) {
  .two, .yaml, .pair { grid-template-columns: minmax(0, 1fr); }
  .donts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .type-row { grid-template-columns: minmax(0, 1fr); gap: 0.3em; }
}
"""


def web_page():
    head_css = (":root {" + LIGHT_TOKENS + FONT_STACKS + "}\n"
                "@media (prefers-color-scheme: dark) { :root:not([data-theme=\"light\"]) {" + DARK_TOKENS + "} }\n"
                ":root[data-theme=\"dark\"] {" + DARK_TOKENS + "}\n" + COMPONENT_CSS + WEB_CSS)
    dont_figs = "".join(
        f'<figure class="dont"><div class="spec dont-art {ground}">{art}</div><figcaption><b>{t}</b><span>{why}</span></figcaption></figure>'
        for t, why, art, ground in donts())
    size_rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in SIZES)
    type_rows = "".join(f'<div class="type-row"><div><b>{f}</b><small>{u}</small></div><div>{s}</div></div>' for f, u, s in TYPE)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>ASTRA Brand Guide</title>
<meta name="description" content="The ASTRA logo, colours, type and usage rules.">
<link rel="icon" type="image/svg+xml" href="{data_uri('favicon')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Alegreya:wght@400;500;700&family=IBM+Plex+Mono:wght@400&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Quattrocento:wght@400;700&display=swap">
<!-- Generated by tools/build_site.py. Do not edit. -->
<style>
/* Layout: an atlas of plates. Each section is a ruled plate; specimens sit on fixed parchment and charcoal grounds. */
{head_css}
</style>
</head>
<body>
<div class="wrap">
  <header class="masthead"><span>ASTRA · Brand guide</span><span><a href="{PDF_URL}">branding.pdf</a> · <a href="{REPO_URL}">astra-project/brand</a></span></header>

  <section class="hero" aria-label="ASTRA logo">
    {svg("astra-lockup-descriptor", cls="hero-lockup themed")}
    <p class="lede">The mark is a capital A drawn as a star chart. Read as a spacetime diagram, the same lines are the <em>past light cone</em> of the star at the top: everything that could have influenced it. An <code>astra.yaml</code> records exactly that set for a result.</p>
  </section>

  <section class="plate" aria-labelledby="h-mark">
    <div class="plate-head"><span class="eyebrow">Plate I · the mark</span><h2 id="h-mark">What the mark shows</h2>
      <p>Five stars and the links between them, each one a part of an ASTRA analysis. Gold traces a single universe: the option it selects and the path up to the result. Nothing is symmetric, so it reads as a constellation, not an object.</p></div>
    <div class="two">{construction_svg()}<dl class="legend themed">{legend_html()}</dl></div>
    <div class="yaml">
      <div><h3>The mark as an analysis</h3>
        <p>Two inputs, one decision with two options, one output, and a universe named <code>gold</code> that selects the right-hand option. This is the drawing, written in ASTRA.</p>
        <p class="fine">Validated against the analysis JSON Schema in astra-spec at commit e5fe476.</p></div>
      <pre class="code" aria-label="astra.yaml for the mark"><code>{yaml_html()}</code></pre>
    </div>
  </section>

  <section class="plate" aria-labelledby="h-versions">
    <div class="plate-head"><span class="eyebrow">Plate II · versions</span><h2 id="h-versions">Mark and name</h2>
      <p>The wordmark's baseline meets the bottom of the gold node, about the midpoint of the rising bar. Its cap height is 0.34 of the mark's height, which makes its stems the same weight as the mark's lines.</p></div>
    <div class="lockups">
      <figure><div class="pair"><div class="spec light">{svg("astra-lockup")}</div><div class="spec dark">{svg("astra-lockup-dark")}</div></div>
        <figcaption class="cap"><b>Horizontal.</b> The default logo, for site headers, READMEs and slides.</figcaption></figure>
      <figure><div class="pair"><div class="spec light">{svg("astra-lockup-descriptor")}</div><div class="spec dark">{svg("astra-lockup-descriptor-dark")}</div></div>
        <figcaption class="cap"><b>With descriptor.</b> The full name in Alegreya small caps under a gold rule; its baseline meets the bottom of the larger input star. For title pages, posters and the site hero.</figcaption></figure>
      <figure><div class="pair stack-pair"><div class="spec light">{svg("astra-lockup-stacked")}</div><div class="spec dark">{svg("astra-lockup-stacked-dark")}</div></div>
        <figcaption class="cap"><b>Stacked.</b> For square spaces such as a conference badge or a sticker.</figcaption></figure>
    </div>
  </section>

  <section class="plate" aria-labelledby="h-size">
    <div class="plate-head"><span class="eyebrow">Plate III · space and size</span><h2 id="h-size">Room to breathe, two drawings</h2>
      <p>Keep clear space of one star height, <em>x</em>, on every side. Below 48 px the rings and fine links close up, so small sizes use the compact drawing.</p></div>
    <div class="two">
      {clearspace_svg()}
      <div class="stack"><div class="tbl"><table class="sizes"><thead><tr><th scope="col">Minimum size</th><th scope="col">Screen</th><th scope="col">Print</th></tr></thead><tbody>{size_rows}</tbody></table></div>
        <p class="cap">{SIZES_NOTE}</p></div>
    </div>
    <div class="stack">
      <div class="spec light"><div class="ladder">{ladder("light")}</div></div>
      <div class="spec dark"><div class="ladder">{ladder("dark")}</div></div>
    </div>
    <p class="cap"><b>Compact</b> at 16, 24 and 32 px; <b>primary</b> at 48, 64 and 96 px, shown at true pixel size.</p>
  </section>

  <section class="plate" aria-labelledby="h-colour">
    <div class="plate-head"><span class="eyebrow">Plate IV · colour and type</span><h2 id="h-colour">Four colours, three faces</h2>
      <p>The colours come from the Lightcone Research palette; <code>tokens/colors.json</code> is the source. Gold marks one thing only: the selected option, its path and the result.</p></div>
    <div class="stack"><p class="group-label">On light grounds</p><div class="chips">{chips("light")}</div>
      <p class="group-label">On dark grounds</p><div class="chips">{chips("dark")}</div></div>
    <div>{type_rows}<p class="cap">{TYPE_NOTE}</p></div>
  </section>

  <section class="plate" aria-labelledby="h-usage">
    <div class="plate-head"><span class="eyebrow">Plate V · usage</span><h2 id="h-usage">Do and don't</h2></div>
    <ul class="dos">{"".join(f"<li>{d}</li>" for d in DOS)}</ul>
    <div class="donts">{dont_figs}</div>
    <p class="cap">{NEVERS}</p>
  </section>

  <section class="plate" aria-labelledby="h-use">
    <div class="plate-head"><span class="eyebrow">Plate VI · in use</span><h2 id="h-use">Where it appears</h2></div>
    <div class="pair">
      <div class="mock">
        <div class="tabbar"><div class="tab on"><img src="{data_uri('favicon')}" width="16" height="16" alt=""><span>ASTRA · Getting started</span></div><div class="tab"><span>astra-spec on GitHub</span></div></div>
        <div class="docbar themed">{svg("astra-compact", width=26, height=26, decorative=True)}<span class="name">ASTRA</span><span class="nav"><span>Documentation</span><span>Specification</span><span>Community</span></span></div>
        <div class="docbody"><div class="l" style="width:62%"></div><div class="l" style="width:88%"></div><div class="l" style="width:74%"></div><div class="l" style="width:40%"></div></div>
        <div class="mock-cap">Browser tab and docs header</div>
      </div>
      <div class="mock social">{svg("astra-social-card")}<div class="mock-cap">Social preview, 1280 × 640</div></div>
    </div>
  </section>

  <section class="plate" aria-labelledby="h-files">
    <div class="plate-head"><span class="eyebrow">Plate VII · files</span><h2 id="h-files">The kit</h2>
      <p>All SVGs are transparent, use only brand colours, carry a title and description for screen readers, and namespace their IDs so several can be inlined on one page.</p></div>
    <div class="tbl"><table class="files"><tbody>{files_html()}</tbody></table></div>
  </section>

  <p class="foot">ASTRA, the Agentic Schema for Transparent Research Analysis. Source: <a href="{REPO_URL}">{REPO_URL.removeprefix("https://")}</a>.</p>
</div>
</body>
</html>
"""


def main():
    out = ROOT / "docs" / "index.html"
    out.write_text(web_page())
    print(f"{out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
