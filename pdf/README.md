# Client PDF

`Nymbl_AM_NACR.pdf` is built from `Nymbl_AM_NACR_original.pdf` by `./build_pdf.sh`.
The original is never edited in place; re-run the script to rebuild from scratch.

The source PDF is WeasyPrint 69.0 output with subset-embedded fonts. Its HTML/CSS
source was not available, so changes are made two ways:

- **In place**, where a change fits the existing typesetting: `fix_names.py`,
  `add_gate_m4.py`, `update_module_row.py`, `fix_13week_phrase.py`,
  `fix_gate_wording.py` and `fix_time_and_material.py` set replacement text in the
  document's own extracted font subsets, at the original sizes, colours and
  baselines. `fix_13week_phrase.py` reflows five separate paragraphs and a diagram
  box across four pages; `fix_gate_wording.py` rewraps two bold-label-plus-body
  captions word by word so a bold gate label and regular running text (with inline
  arrows in Arial, since Raleway has no U+2192) share the same line correctly.
  `fix_time_and_material.py` bundles four unrelated small edits into one pass: p13's
  price badge and delivery-schedule narrative, p21's budget-card chip/subline/intro
  (with the chip's letter-spacing measured and replayed glyph by glyph, since
  `insert_text` has no `char_spacing` argument), p25's IP Confirmation paragraph
  (dropped a trailing sentence, reflowed 9 lines to 8), and p28's closing contact
  line (`Ruben Carrera` → `Steve Smith`, on that page only — set in Raleway rather
  than the page's own Montserrat, which has no capital `S` anywhere in its subset).
  Every one of these is pre-checked to wrap to no more lines than the text it
  replaces, so nothing below or beside it has to move.
- **Raster patches**, for the two mentions baked into a diagram image rather than
  live text: `fix_gate_diagrams.py` renders a small transparent-background SVG
  containing just the replaced element (a whole box for p16, a title-sized cover rect
  for p17), composites it onto the existing 3600x1860 raster with Pillow, and swaps
  it into the PDF via `Page.replace_image` — every other pixel is untouched.
- **Authored pages**, where a change needs real layout: `pages/build.py` writes new
  pages in WeasyPrint 69.0 (same engine, same fonts, metrics measured off the
  document). `splice.py` inserts new pages, then fixes footer numbers, contents
  references and bookmarks; `replace_page.py` swaps one page for another of the same
  size, leaving numbering alone.

Deleting or replacing a page orphans its bookmark and any link that targeted it, so
both scripts capture the outline first and repoint dead links afterwards.

`pages/fonts/` holds the font subsets extracted from the PDF. They cover only the
glyphs the document already uses, so `pages/render.py` refuses to render text with a
missing glyph rather than letting WeasyPrint fall back to a system font. Two known
gaps: `Montserrat-Bold` has no full stop, and `Raleway-Ultra-Bold` has no `0`, `O`,
`U`, `X`, `Y`, `Z` or `/`.

Run `python3 verify_pdf.py` after building.

**Font-alias collision.** `Page.insert_text(fontname=<alias>, fontfile=<path>)`
silently reuses an existing page resource if any earlier script already registered
that exact alias on that page — even when a completely different `fontfile` is
passed this time. The new text still inserts, but characters missing from the *old*
font's subset render as null glyphs, with no error. Every `fontname=` alias used on
a given page across this whole pipeline's history must be unique — check what
`add_gate_m4.py`, `fix_13week_phrase.py` and `fix_time_and_material.py` already used
on pages 13/14/21 before adding a new script that touches them.

## Status

No "13-week" text remains anywhere in the document — `verify_pdf.py` checks the live
text of every page for it. The two mentions that were baked into diagram rasters
(page 16's M2 box, page 17's M3 source node) are patched images, not text; see
`fix_gate_diagrams.py`.

## Still to port from the HTML deck

Page 16's title still reads "Three testable gates inside the fixed fee," and its
intro says "measured against three testable gates" — both predate the M4 addition and
were never updated to four. Not touched because it wasn't part of any request; flag
if you'd like it fixed.

The Gantt chart on page 15 also needs a design decision before M4 can appear on it:
M4 falls in week 4 alongside M3, so it has nowhere to sit on the existing gate lines.
