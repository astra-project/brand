# List the recipes
default:
    @just --list

# Regenerate everything: SVGs, PNGs, tokens, the web guide and branding.pdf
build: png site pdf

# SVGs and tokens/colors.css
svg:
    uv run tools/build_logo.py --svg-only

# SVGs, tokens/colors.css and every PNG and ICO (needs rsvg-convert and ImageMagick)
png:
    uv run tools/build_logo.py

# docs/index.html, the web guide
site:
    uv run tools/build_site.py

# branding.pdf (needs Chromium)
pdf:
    uv run tools/build_pdf.py

# Check every SVG against the brand rules
check:
    uv run tools/check_assets.py

# What CI runs: regenerate the checked files, fail on any difference, check the rules
ci: svg site
    git diff --exit-code
    uv run tools/check_assets.py
