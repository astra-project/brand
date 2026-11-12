# Contributing

Every published asset is generated from a few sources. Edit the sources, rebuild, and commit the sources and the outputs together.

| To change | Edit |
| --- | --- |
| The mark's geometry | `PRIMARY` and `COMPACT` in `tools/build_logo.py` |
| The wordmark, descriptor or lockup layouts | `tools/build_logo.py` |
| A colour | `tokens/colors.json` |
| The guide's text and figures | `tools/build_site.py` (the web guide and the PDF share it) |
| The PDF's page layout | `tools/build_pdf.py` |

Don't edit these by hand; they are overwritten on every build: `logo/`, `icons/`, `social/`, `tokens/colors.css`, `docs/index.html`, `branding.pdf`.

## Building

You need [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just). The scripts declare their Python dependencies inline, so `uv run` installs them.

```sh
just svg     # SVGs and tokens/colors.css
just site    # docs/index.html
just check   # brand rules on every SVG
just build   # everything, including PNGs and branding.pdf
```

PNG export needs `rsvg-convert` (librsvg) and `magick` (ImageMagick 7). The PDF needs Chromium; set `CHROMIUM` to its path if it is not on `PATH` as `chromium` or `google-chrome`.

## What CI checks

On every push and pull request, CI regenerates the SVGs, the colour tokens and the web guide, fails if any of them differ from what is committed, and runs `tools/check_assets.py`. PNGs and the PDF are not compared, because renderer versions change their bytes, so run `just build` before you commit a change that affects them.

`tools/check_assets.py` enforces the rules that keep the logo consistent:

- every colour in an SVG comes from `tokens/colors.json`;
- gold appears only on the selected option, its path, the result and the descriptor rule;
- every SVG has a title, a description and `role="img"`, and its IDs are unique across all files;
- no SVG carries a `<style>`, except `icons/favicon.svg`, whose rules are scoped to its own root.

## Design rules for changes

- Keep the mark asymmetric: the bar rises toward the gold node, and the input stars differ in size. A symmetric A under a star reads as a rocket.
- Keep gold for the selected option, its path and the result.
- Keep the links stopping short of the stars, so the mark needs no knock-out fills.
- Check small sizes: look at the compact mark at 16, 24 and 32 px and the primary mark at 48 px, on light and dark grounds.
