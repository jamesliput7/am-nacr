# Client PDF

`Nymbl_AM_NACR.pdf` is built from `Nymbl_AM_NACR_original.pdf` by `./build_pdf.sh`.
The original is never edited in place; re-run the script to rebuild from scratch.

The source PDF is WeasyPrint 69.0 output with subset-embedded fonts. Its HTML/CSS
source was not available, so changes are made two ways:

- **In place**, where a change fits the existing typesetting: `fix_names.py`,
  `add_gate_m4.py`, `update_module_row.py` and `fix_13week_phrase.py` set replacement
  text in the document's own extracted font subsets, at the original sizes, colours
  and baselines. The last of these reflows five separate paragraphs and a diagram box
  across four pages, each pre-checked to wrap to no more lines than the text it
  replaces so nothing below or beside it has to move.
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

## Still to port from the HTML deck

Three mentions remain that don't literally say "13-week cash flow use case," so a
find-and-replace can't touch them without leaving the surrounding sentence broken:

- p16: "...the practitioner-approved crosswalk freezes as a deterministic rule, and
  the 13-week forecast computes..." (the M2 gate description)
- p17: "...ingestion → mapping → 13-week forecast..." (the M3 gate description)
- p23: "A module is one governed dataset plus the models built on it — the 13-week
  cash flow, or the store-footprint analysis." (an example on the module-pricing lede)

Each would need its own rewording, not a substitution, since "13-week forecast" and
"13-week cash flow" are the grammatical subject of their sentences.

The Gantt chart on page 15 also needs a design decision before M4 can appear on it:
M4 falls in week 4 alongside M3, so it has nowhere to sit on the existing gate lines.
