<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="logo/astra-lockup-descriptor-dark.svg">
    <img alt="ASTRA: Agentic Schema for Transparent Research Analysis" src="logo/astra-lockup-descriptor.svg" width="560">
  </picture>
</p>

# ASTRA brand

The logo, colours, type and usage rules for [ASTRA](https://astra-spec.org), the Agentic Schema for Transparent Research Analysis.

- **[branding.pdf](branding.pdf)**: the brand guide, seven pages, to read or send.
- **[docs/index.html](docs/index.html)**: the same guide as a web page, ready for GitHub Pages.

## The mark

The mark is a capital A drawn as a star chart. Read as a spacetime diagram, the same lines are the past light cone of the star at the top: everything that could have influenced it. An `astra.yaml` records exactly that set for a result.

| Element | Meaning |
| --- | --- |
| Star at the apex | The result |
| Two stars at the feet, at two magnitudes | The inputs |
| Crossbar, rising to the right | A decision between options |
| Open ring | An option considered and not taken |
| Gold node and gold link | The option a universe selects, and its path to the result |

Nothing in the mark is symmetric. A symmetric A under a star reads as a rocket; the lit stroke, the rising bar and the unequal stars make it a constellation. [`docs/mark.astra.yaml`](docs/mark.astra.yaml) is the drawing written as an ASTRA analysis.

## Which file do I use?

| You need | Use |
| --- | --- |
| The logo, on a light ground | [`logo/astra-lockup.svg`](logo/astra-lockup.svg) |
| The logo, on a dark ground | [`logo/astra-lockup-dark.svg`](logo/astra-lockup-dark.svg) |
| The full name, for a title page, poster or site hero | [`logo/astra-lockup-descriptor.svg`](logo/astra-lockup-descriptor.svg) (and `-dark`) |
| A square layout, such as a badge or sticker | [`logo/astra-lockup-stacked.svg`](logo/astra-lockup-stacked.svg) (and `-dark`) |
| The mark alone, 48 px and up | [`logo/astra-mark.svg`](logo/astra-mark.svg) (and `-dark`, `-mono`) |
| The mark at 16 to 48 px: app chrome, docs headers | [`logo/astra-compact.svg`](logo/astra-compact.svg) (and `-dark`, `-mono`) |
| One colour: print, embossing, photographs, CSS theming | `logo/astra-mark-mono.svg`, `logo/astra-compact-mono.svg` (they use `currentColor`) |
| A favicon | [`icons/favicon.svg`](icons/favicon.svg), with [`icons/favicon.ico`](icons/favicon.ico) as fallback |
| A home-screen icon, web-app icon or avatar | `icons/apple-touch-icon.png`, `icons/icon-512.png`, `icons/avatar-500.png` |
| A social preview or Open Graph image | [`social/astra-social-card-1280x640.png`](social/astra-social-card-1280x640.png) |
| A PNG of any logo | `logo/png/*@2x.png`, transparent |
| The colours in code or a design tool | [`tokens/colors.css`](tokens/colors.css), [`tokens/colors.json`](tokens/colors.json) |
| The fonts | [`fonts/`](fonts) |

Every SVG is transparent, uses only brand colours, has a title and description for screen readers, and namespaces its IDs so several can be inlined on one page. Its parts carry classes (`astra-links`, `astra-path`, `astra-stars`, `astra-options`, `astra-universe`, `astra-wordmark`, `astra-descriptor`, `astra-rule`, `astra-glyph`), so an inlined copy can be recoloured with CSS.

## On the web

Favicons:

```html
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
```

`favicon.svg` switches to light strokes when the browser is in dark mode. Its style rules are scoped to its own root, so inlining it cannot recolour anything else on the page.

A logo in a GitHub README that follows the reader's theme:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="logo/astra-lockup-dark.svg">
  <img alt="ASTRA" src="logo/astra-lockup.svg" width="320">
</picture>
```

A Zensical or Material for MkDocs site, with the two SVGs copied into `docs/assets/`:

```toml
[project.theme]
favicon = "assets/favicon.svg"
logo = "assets/astra-compact.svg"
```

The colours as CSS custom properties:

```css
@import "tokens/colors.css";  /* --astra-brand-light-ink, --astra-brand-dark-gold, ... */
```

## Colours

| Role | Light grounds | Dark grounds |
| --- | --- | --- |
| Ink: stars, option ring, wordmark | `#221F20` | `#F1EFE9` |
| Link: links between stars, descriptor | `#4E5A70` | `#B4BDCD` |
| Gold: the selected option, its path and the result, nothing else | `#A67C3C` | `#C2924A` |
| Ground | `#F8F7F3` | `#221F20` |
| Rule: hairline frames | `#D2CCBF` | `#4C4747` |

The values come from the Lightcone Research palette. Gold is the colour ASTRA UI gives the `decision` record kind.

## Type

| Face | Use |
| --- | --- |
| Quattrocento | The wordmark and headings |
| Alegreya, small caps | Labels, eyebrows and the descriptor |
| Newsreader | Body text and italic captions |
| IBM Plex Mono | Code and file names (Google Fonts, not bundled) |

The wordmark in the SVGs is outlined, so it renders without the font installed.

## Rules in brief

- Keep clear space of one star height on every side of the mark.
- Minimum sizes: the mark 48 px tall on screen (13 mm in print); the lockup with descriptor 400 px wide; below 48 px, the compact mark.
- Don't level the bar, recolour the gold, stretch the logo, or put the light version on a dark ground.
- Don't add shadows, glows, gradients or outlines, rotate the mark, or rebuild the wordmark in another typeface.

[branding.pdf](branding.pdf) has the full rules with examples.

## Working on the brand

Every file in `logo/`, `icons/`, `social/`, `tokens/colors.css`, `docs/index.html` and `branding.pdf` is generated. Change the sources and rebuild; [CONTRIBUTING.md](CONTRIBUTING.md) explains how.

```sh
just build   # everything: SVGs, PNGs, tokens, the web guide and branding.pdf
just check   # the brand rules, on every SVG
```

## Licences

The repository is under the BSD 3-Clause License ([LICENSE](LICENSE)). The fonts in `fonts/` are under the SIL Open Font License 1.1 (`fonts/OFL-*.txt`).
