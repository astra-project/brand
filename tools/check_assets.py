# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check the published SVGs against the brand rules.

    uv run tools/check_assets.py

Checks every SVG in logo/, icons/ and social/:

  * parses as XML, has role="img", a <title> and a <desc>, and is labelled by them
  * uses only colours from tokens/colors.json (plus none and currentColor)
  * uses gold only for the selected option, its path, the result and the
    descriptor rule (groups classed astra-universe, astra-path, astra-rule)
  * IDs are unique across all files, so several SVGs can be inlined in one page
  * carries no <style>, except icons/favicon.svg, whose rules are all scoped to
    its own root (an inlined <style> applies to the whole host page)
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NS = "{http://www.w3.org/2000/svg}"
HEX = re.compile(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b")
GOLD_CLASSES = {"astra-universe", "astra-path", "astra-rule"}

tokens = json.loads((ROOT / "tokens" / "colors.json").read_text())
palette, golds = set(), set()
for scheme in ("light", "dark"):
    for key, tok in tokens[scheme].items():
        if key.startswith("$"):
            continue
        palette.add(tok["$value"].upper())
        if key == "gold":
            golds.add(tok["$value"].upper())

errors: list[str] = []
seen_ids: dict[str, Path] = {}


def fail(path: Path, msg: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {msg}")


def walk(el, path: Path, classes: frozenset[str]) -> None:
    classes = classes | set(el.get("class", "").split())
    tag = el.tag.replace(NS, "")
    if el.get("id"):
        if el.get("id") in seen_ids:
            fail(path, f'id "{el.get("id")}" also used in {seen_ids[el.get("id")].relative_to(ROOT)}')
        seen_ids[el.get("id")] = path
    if tag == "style":
        if path != ROOT / "icons" / "favicon.svg":
            fail(path, "<style> is only allowed in icons/favicon.svg")
        else:
            body = re.sub(r"@media[^{]*\{", "", el.text or "")
            for selector in re.findall(r"([^{}]+)\{[^{}]*\}", body):
                if not selector.strip().startswith(".astra-favicon"):
                    fail(path, f'style rule "{selector.strip()}" is not scoped to .astra-favicon')
    for attr in ("fill", "stroke", "stop-color", "color"):
        value = el.get(attr)
        if not value or value in ("none", "currentColor") or value.startswith("url("):
            continue
        if value.upper() not in palette:
            fail(path, f'<{tag} {attr}="{value}"> is not a colour from tokens/colors.json')
        elif value.upper() in golds and not classes & GOLD_CLASSES:
            fail(path, f"gold on <{tag}> outside the selected option, its path, the result or the rule")
    for child in el:
        walk(child, path, frozenset(classes))


svgs = sorted(p for d in ("logo", "icons", "social") for p in (ROOT / d).glob("*.svg"))
if not svgs:
    errors.append("no SVGs found; run tools/build_logo.py first")
for path in svgs:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        fail(path, f"not valid XML: {e}")
        continue
    if root.get("role") != "img":
        fail(path, 'root <svg> needs role="img"')
    title, desc = root.find(f"{NS}title"), root.find(f"{NS}desc")
    if title is None or not (title.text or "").strip() or desc is None or not (desc.text or "").strip():
        fail(path, "needs a non-empty <title> and <desc>")
    elif root.get("aria-labelledby", "").split() != [title.get("id"), desc.get("id")]:
        fail(path, "aria-labelledby must name the <title> and <desc> ids")
    walk(root, path, frozenset())

if errors:
    print("\n".join(errors))
    sys.exit(f"{len(errors)} problem(s) in {len(svgs)} SVG files")
print(f"{len(svgs)} SVG files follow the brand rules")
