# Client PDF

`Nymbl_AM_NACR.pdf` is built from `Nymbl_AM_NACR_original.pdf` by `./build_pdf.sh`.
The original is never edited in place; re-run the script to rebuild from scratch.

The source PDF is WeasyPrint 69.0 output with subset-embedded fonts. Its HTML/CSS
source was not available, so changes are made two ways:

- **In place**, where a change fits the existing typesetting: `fix_names.py` and
  `add_gate_m4.py` set replacement text in the document's own extracted font subsets,
  at the original sizes, colours and baselines.
- **Authored pages**, where a change needs real layout: `pages/build.py` writes new
  pages in WeasyPrint 69.0 (same engine, same fonts, metrics measured off the
  document) and `splice.py` inserts them, then fixes footer numbers, contents
  references and bookmarks.

`pages/fonts/` holds the font subsets extracted from the PDF. They cover only the
glyphs the document already uses, so `pages/render.py` refuses to render text with a
missing glyph rather than letting WeasyPrint fall back to a system font. Two known
gaps: `Montserrat-Bold` has no full stop, and `Raleway-Ultra-Bold` has no `0`, `O`,
`U`, `X`, `Y`, `Z` or `/`.

Run `python3 verify_pdf.py` after building.

## Still to port from the HTML deck

The vendors-and-utilities rewording (replacing the 13-week cash flow as the Phase 1
motion) lands mid-paragraph and mid-table on pages 12, 13, 15, 16, 17, 21, 22, 23 and
24, and the module catalogue row on page 24. Those pages would have to be re-authored
in full. The Gantt chart on page 15 also needs a design decision: M4 falls in week 4
alongside M3, so it has nowhere to sit on the existing gate lines.
