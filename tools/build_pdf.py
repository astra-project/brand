# /// script
# requires-python = ">=3.10"
# dependencies = ["fonttools[woff]>=4.50", "pypdf>=4"]
# ///
"""Build branding.pdf, the printable ASTRA brand guide (A4 landscape).

    uv run tools/build_pdf.py

Lays out the content of tools/build_site.py as print pages, with the fonts in
fonts/, and prints them with headless Chromium (set CHROMIUM to its path if it
is not on PATH as chromium or google-chrome). Run tools/build_logo.py first.
"""

from __future__ import annotations

import html
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import build_site as G  # noqa: E402

ROOT = G.ROOT
OUT = ROOT / "branding.pdf"
VERSION = "Version 1.0 · November 2026"


def font_faces():
    faces = [
        ("Quattrocento", "normal", "400", "Quattrocento-Regular.woff2"),
        ("Quattrocento", "normal", "700", "Quattrocento-Bold.woff2"),
        ("Alegreya", "normal", "400 900", "Alegreya-Variable.woff2"),
        ("Newsreader", "normal", "200 800", "Newsreader-Variable.woff2"),
        ("Newsreader", "italic", "200 800", "Newsreader-Italic.woff2"),
    ]
    return "".join(
        f'@font-face{{font-family:"{fam}";font-style:{style};font-weight:{wt};font-display:block;'
        f'src:url("{(ROOT / "fonts" / f).as_uri()}") format("woff2")}}\n' for fam, style, wt, f in faces)


PRINT_CSS = """
@page { size: 297mm 210mm; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; }
body { -webkit-print-color-adjust: exact; print-color-adjust: exact; background: var(--canvas); color: var(--ink);
  font-family: var(--f-body); font-size: 9.4pt; line-height: 1.45; }
code { font-family: var(--f-mono); font-size: 0.86em; }
.page { width: 297mm; height: 210mm; padding: 12mm 16mm 13mm; background: var(--canvas); position: relative; overflow: hidden;
  break-after: page; display: grid; grid-template-rows: auto auto minmax(0, 1fr); gap: 5mm; }
.page:last-child { break-after: auto; }
.ph { display: flex; justify-content: space-between; font-family: var(--f-ui); font-weight: 500; font-variant-caps: all-small-caps;
  letter-spacing: 0.12em; color: var(--subtle); border-bottom: 0.3mm solid var(--rule-strong); padding-bottom: 2.2mm; font-size: 9pt; }
.ptitle { display: grid; gap: 1.2mm; max-width: 175mm; }
.eyebrow { font-family: var(--f-ui); font-weight: 500; font-variant-caps: all-small-caps; letter-spacing: 0.14em; color: var(--eyebrow); font-size: 9.5pt; }
h2 { font-family: var(--f-head); font-weight: 400; font-size: 22pt; line-height: 1.1; margin: 0; }
h3 { font-family: var(--f-ui); font-weight: 500; font-variant-caps: all-small-caps; letter-spacing: 0.12em; color: var(--subtle); font-size: 9.5pt; margin: 0 0 1.5mm; }
.ptitle p { margin: 0; color: var(--muted); font-size: 10pt; }
.body { min-height: 0; }
.two { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 12mm; align-items: start; height: 100%; }
.cap { font-style: italic; color: var(--muted); margin: 2mm 0 0; }
.cap b { font-style: normal; font-family: var(--f-ui); font-weight: 700; color: var(--ink); }

/* cover */
.cover { grid-template-rows: minmax(0, 1fr) auto; padding: 16mm 20mm; }
.cover::before { content: ""; position: absolute; inset: 8mm; border: 0.35mm solid var(--rule-strong); pointer-events: none; }
.cover-main { display: grid; align-content: center; gap: 9mm; }
.cover-main svg { width: 205mm; height: auto; }
.cover-main p { margin: 0; max-width: 150mm; font-size: 12pt; color: var(--muted); }
.cover-foot { display: flex; justify-content: space-between; font-family: var(--f-ui); font-weight: 500; font-variant-caps: all-small-caps;
  letter-spacing: 0.12em; color: var(--subtle); font-size: 9.5pt; }

/* the mark */
.mark-fig { height: 128mm; display: grid; place-items: center start; }
.mark-fig svg { height: 100%; width: auto; }
dl.legend { gap: 3mm; font-size: 9.2pt; }

/* versions */
.versions { display: grid; grid-template-columns: 58mm minmax(0, 1fr) minmax(0, 1fr); grid-auto-rows: 40mm; gap: 4mm 5mm; }
.versions .spec { padding: 5mm 8mm; }
.versions .spec svg { max-height: 100%; width: 100%; }
.versions .spec.stacked svg { width: auto; height: 100%; }
.vcap b { font-family: var(--f-ui); font-weight: 700; display: block; font-size: 10pt; }
.vcap span { color: var(--muted); }
.vcap code { color: var(--subtle); font-size: 0.72em; display: block; margin-top: 1.2mm; white-space: nowrap; }

/* space and size */
.cs-fig { height: 118mm; display: grid; place-items: center start; }
.cs-fig svg { height: 100%; width: auto; }
.size-col { display: grid; gap: 6mm; align-content: start; }
.ladder-tile { padding: 4mm 6mm; }
.ladder { gap: 7mm; }

/* colour and type */
.chips { grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 0 4mm; }
.chip { font-size: 8.4pt; padding: 2.5mm 0; }
.sw { width: 11mm; height: 11mm; }
.chip { grid-template-columns: 11mm minmax(0, 1fr); gap: 3mm; }
.colour-type { display: grid; gap: 4mm; align-content: start; }
.type-row { padding: 2.6mm 0; grid-template-columns: 52mm minmax(0, 1fr); }
.ts-word { font-size: 22pt; }
.ts-head { font-size: 15pt; }

/* usage */
.usage { display: grid; gap: 7mm; align-content: start; }
ul.dos { columns: 2; column-gap: 12mm; display: block; }
ul.dos li { margin-bottom: 1.6mm; break-inside: avoid; }
.donts { gap: 5mm; }
.dont-art { padding: 0; }

/* files */
.files-grid { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 12mm; align-items: start; }
table.files { font-size: 8.6pt; }
table.files td { padding: 1.6mm 3mm 1.6mm 0; }
pre.code { font-size: 7.6pt; white-space: pre-wrap; word-break: break-all; }
.snips { display: grid; gap: 5mm; }
"""

FAVICON_SNIPPET = """<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">"""

README_SNIPPET = """<picture>
  <source media="(prefers-color-scheme: dark)"
          srcset="logo/astra-lockup-dark.svg">
  <img alt="ASTRA" src="logo/astra-lockup.svg" width="320">
</picture>"""


def page(n, total, eyebrow, title, intro, body, cls=""):
    head = f'<header class="ph"><span>ASTRA · Brand guide</span><span>{n} / {total}</span></header>'
    t = f'<div class="ptitle"><span class="eyebrow">{eyebrow}</span><h2>{title}</h2>{f"<p>{intro}</p>" if intro else ""}</div>'
    return f'<section class="page {cls}">{head}{t}<div class="body">{body}</div></section>'


def build_html():
    total = 7
    pages = []
    pages.append(f"""<section class="page cover">
  <div class="cover-main">{G.svg("astra-lockup-descriptor", cls="themed")}
    <p>The logo, colours, type and usage rules for ASTRA. Every file named here is in the brand repository.</p></div>
  <div class="cover-foot"><span>Brand guide · {VERSION}</span><span>{G.REPO_URL.removeprefix("https://")}</span></div>
</section>""")

    pages.append(page(2, total, "The mark", "A constellation and a light cone",
        "A capital A drawn as a star chart. Read as a spacetime diagram, the same lines are the past light cone of the star "
        "at the top: everything that could have influenced it, which is what an <code>astra.yaml</code> records for a result.",
        f'<div class="two"><div class="mark-fig">{G.construction_svg()}</div><dl class="legend themed">{G.legend_html()}</dl></div>'))

    rows = [
        ("Horizontal", "The default logo, for site headers, READMEs and slides.", "logo/astra-lockup.svg", "astra-lockup", ""),
        ("With descriptor", "The full name in small caps under a gold rule. For title pages, posters and site heroes.",
         "logo/astra-lockup-descriptor.svg", "astra-lockup-descriptor", ""),
        ("Stacked", "For square spaces such as a badge or a sticker.", "logo/astra-lockup-stacked.svg", "astra-lockup-stacked", "stacked"),
    ]
    cells = "".join(
        f'<div class="vcap"><b>{t}</b><span>{d}</span><code>{f}<br>{f.removesuffix(".svg")}-dark.svg</code></div>'
        f'<div class="spec light {c}">{G.svg(n)}</div><div class="spec dark {c}">{G.svg(n + "-dark")}</div>'
        for t, d, f, n, c in rows)
    pages.append(page(3, total, "Versions", "Mark and name",
        "The wordmark is Quattrocento. Its baseline meets the bottom of the gold node, and its cap height is 0.34 of the "
        "mark's height, so its stems match the mark's lines. Use light versions on light grounds and dark versions on dark grounds.",
        f'<div class="versions">{cells}</div>'))

    size_rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in G.SIZES)
    pages.append(page(4, total, "Space and size", "Room to breathe, two drawings",
        "Keep clear space of one star height, <em>x</em>, on every side. Below 48 px the rings and fine links close up, "
        "so small sizes use the compact drawing.",
        f'''<div class="two"><div class="cs-fig">{G.clearspace_svg()}</div>
          <div class="size-col">
            <div><table class="sizes"><thead><tr><th>Minimum size</th><th>Screen</th><th>Print</th></tr></thead><tbody>{size_rows}</tbody></table>
              <p class="cap">{G.SIZES_NOTE}</p></div>
            <div><h3>Compact at 16, 24, 32 px · primary at 48, 64, 96 px</h3>
              <div class="spec light ladder-tile"><div class="ladder">{G.ladder("light")}</div></div></div>
            <div class="spec dark ladder-tile"><div class="ladder">{G.ladder("dark")}</div></div>
          </div></div>'''))

    type_rows = "".join(f'<div class="type-row"><div><b>{f}</b><small>{u}</small></div><div>{s}</div></div>' for f, u, s in G.TYPE)
    pages.append(page(5, total, "Colour and type", "Four colours, three faces",
        "Gold marks one thing only: the selected option, its path and the result. The values are in "
        "<code>tokens/colors.json</code> and <code>tokens/colors.css</code>.",
        f'''<div class="colour-type">
          <div><h3>On light grounds</h3><div class="chips">{G.chips("light")}</div></div>
          <div><h3>On dark grounds</h3><div class="chips">{G.chips("dark")}</div></div>
          <div>{type_rows}<p class="cap">{G.TYPE_NOTE}</p></div></div>'''))

    dont_figs = "".join(
        f'<figure class="dont"><div class="spec dont-art {ground}">{art}</div><figcaption><b>{t}</b><span>{why}</span></figcaption></figure>'
        for t, why, art, ground in G.donts())
    pages.append(page(6, total, "Usage", "Do and don't", "",
        f'''<div class="usage"><ul class="dos">{"".join(f"<li>{d}</li>" for d in G.DOS)}</ul>
          <div class="donts">{dont_figs}</div><p class="cap">{G.NEVERS}</p></div>'''))

    pages.append(page(7, total, "Files", "The kit",
        f"Download everything from <code>{G.REPO_URL.removeprefix('https://')}</code>. All SVGs are transparent and use only brand colours.",
        f'''<div class="files-grid"><table class="files"><tbody>{G.files_html()}</tbody></table>
          <div class="snips">
            <div><h3>Favicons in a web page</h3><pre class="code">{html.escape(FAVICON_SNIPPET)}</pre></div>
            <div><h3>Logo in a GitHub README, following the reader's theme</h3><pre class="code">{html.escape(README_SNIPPET)}</pre></div>
          </div></div>'''))

    css = ":root {" + G.LIGHT_TOKENS + G.FONT_STACKS + "}\n" + font_faces() + G.COMPONENT_CSS + PRINT_CSS
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>ASTRA Brand Guide</title>
<style>{css}</style></head><body>{"".join(pages)}</body></html>"""


def chromium():
    exe = os.environ.get("CHROMIUM") or next(
        (shutil.which(n) for n in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable") if shutil.which(n)), None)
    if not exe:
        sys.exit("Chromium not found: install it or set CHROMIUM to its path")
    return exe


def main():
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "guide.html"
        src.write_text(build_html())
        raw = Path(tmp) / "raw.pdf"
        subprocess.run([chromium(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--run-all-compositor-stages-before-draw", "--virtual-time-budget=10000",
                        f"--print-to-pdf={raw}", src.as_uri()], check=True, capture_output=True)
        writer = PdfWriter(clone_from=PdfReader(raw))
        writer.add_metadata({"/Title": "ASTRA Brand Guide", "/Author": "ASTRA Project",
                             "/Subject": "The ASTRA logo, colours, type and usage rules",
                             "/Keywords": "ASTRA, brand, logo, guidelines"})
        with open(OUT, "wb") as fh:
            writer.write(fh)
    print(f"{OUT.relative_to(ROOT)} ({len(PdfReader(OUT).pages)} pages, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
