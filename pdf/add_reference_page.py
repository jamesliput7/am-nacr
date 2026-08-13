#!/usr/bin/env python3
"""Insert the new "More cleared, on-point proof." page after page 27.

Two more reference cards (Houlihan Lokey, eCapital) didn't fit on page 27 itself --
the copy for each ran to 13-14 lines at the existing cards' column width, well past
what the two shortest rows on that page have room for -- so they get their own page,
authored in pages/build.py::additional_experience() with the same card chrome as the
original page 27 (rounded corners this time; template.card() grew an optional
`radius` for it) and dropped in right after it.

The closing page carries no visible footer or page number (it's a full-bleed design,
confirmed by its font list: no Montserrat-Bold, no "28" text anywhere on it), so
moving it from index 27 to 28 needs no renumbering at all -- unlike every other page
insertion in this pipeline. Nothing upstream shifts either: no footer, no contents
row, no outline entry but the new page's own.

    python3 add_reference_page.py in.pdf out.pdf
"""
import pathlib
import sys

import pymupdf

PAGES = pathlib.Path(__file__).parent / 'pages' / 'out'
NEW_BOOKMARK = 'More cleared, on-point proof.'


def main(src, out):
    doc = pymupdf.open(src)
    if doc.page_count != 28:
        sys.exit(f'expected the 28-page document, got {doc.page_count}')

    new_page = pymupdf.open(PAGES / 'additional_experience.pdf')
    doc.insert_pdf(new_page, start_at=27)     # lands at index 27, page 28; closing page -> 29

    outline = doc.get_toc()
    outline.append([1, NEW_BOOKMARK, 28])
    doc.set_toc(outline)
    print(f'  bookmark "{NEW_BOOKMARK}" -> 28')

    doc.save(out, garbage=4, deflate=True)

    check = pymupdf.open(out)
    if check.page_count != 29:
        sys.exit(f'expected 29 pages, got {check.page_count}')
    assert 'HOULIHAN' in ''.join(check[27].get_text().split()).upper(), 'page 28 wrong'
    assert 'SteveSmith' in ''.join(check[28].get_text().split()), 'closing page moved wrong'
    assert not [e for e in check.get_toc() if e[2] < 1], 'outline has a broken entry'
    print(f'saved {out} ({check.page_count} pages)')


if __name__ == '__main__':
    main(*(sys.argv[1:3] or sys.exit(__doc__)))
