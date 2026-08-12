#!/usr/bin/env python3
"""Correct the two misspelled A&M product-owner names on page 18 of the client PDF.

The PDF is WeasyPrint output with subset-embedded fonts, so the replacement text is
set in the document's own Raleway-Ultra-Bold subset (extracted at run time) and
re-centred on each card. Only the name glyphs are touched; no background is painted.

    python3 fix_names.py Nymbl_AM_NACR_original.pdf Nymbl_AM_NACR.pdf
"""
import pathlib
import sys

import pymupdf

NAVY = (0x00 / 255, 0x18 / 255, 0x47 / 255)
FONT_HINT = 'Raleway-Ultra-Bold'
PAGE = 17  # zero-based; page 18, "Proposed Team"

# (page index, old text, new text, x centre of the card the name sits in)
REPLACEMENTS = [
    (PAGE, 'Andrew Ku', 'Andrew Khoo', 176.10),
    (PAGE, 'John Bain', 'Jonathan Bain', 419.20),
]


def main(src, out):
    doc = pymupdf.open(src)

    xref = next((f[0] for f in doc.get_page_fonts(PAGE) if FONT_HINT in f[3]), None)
    if xref is None:
        sys.exit(f'{FONT_HINT} not embedded on page {PAGE + 1}')
    fontbuf = doc.extract_font(xref)[3]
    font = pymupdf.Font(fontbuffer=fontbuf)
    fontpath = pathlib.Path(out).with_suffix('.subset.ttf')
    fontpath.write_bytes(fontbuf)

    plan = []
    for pno, old, new, cx in REPLACEMENTS:
        spans = [sp for blk in doc[pno].get_text('dict')['blocks']
                 for ln in blk.get('lines', []) for sp in ln['spans']
                 if sp['text'] == old]
        if len(spans) != 1:
            sys.exit(f'expected 1 occurrence of "{old}" on page {pno + 1}, found {len(spans)}')
        sp = spans[0]
        plan.append((pno, old, new, cx, sp['bbox'], sp['origin'][1], sp['size']))

    # drop the old glyphs, leaving the card background untouched
    for pno, _, _, _, bbox, _, _ in plan:
        r = pymupdf.Rect(bbox)
        r.x0 -= 1
        r.x1 += 1
        doc[pno].add_redact_annot(r, fill=False)
    for pno in {p[0] for p in plan}:
        doc[pno].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)

    for pno, old, new, cx, _, baseline, size in plan:
        width = font.text_length(new, fontsize=size)
        doc[pno].insert_text((cx - width / 2, baseline), new, fontname='ralub',
                             fontfile=str(fontpath), fontsize=size, color=NAVY)
        print(f'p{pno + 1}: "{old}" -> "{new}" ({width:.1f}pt, centred on {cx})')

    doc.save(out, garbage=4, deflate=True)
    fontpath.unlink(missing_ok=True)

    check = pymupdf.open(out)[PAGE].get_text()
    for _, old, new, *_ in plan:
        assert old not in check and new in check, f'verification failed for {new}'
    print('verified:', out)


if __name__ == '__main__':
    main(*(sys.argv[1:3] or sys.exit(__doc__)))
