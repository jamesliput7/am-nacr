#!/usr/bin/env python3
"""Swap the first module in the sizing table for the vendor and utilities motions.

The replacement text wraps to the same line counts as the text it replaces (3 lines
in the module column, 4 in "what sizes it"), so the row keeps its exact envelope and
nothing below it moves. Tier and indicative sizing are untouched.

    python3 update_module_row.py in.pdf out.pdf
"""
import pathlib
import sys

import pymupdf

PAGE = 23                       # zero-based; page 24, "What sizes a module"
NAVY = (0x00 / 255, 0x18 / 255, 0x47 / 255)

MODULE_X, MODULE_SIZE = 61.0, 8.5
MODULE_BASES = (524.07, 536.82, 549.57)
MODULE_TEXT = 'Vendor and Utilities First-Day Motions'
MODULE_W = 83.8                 # column runs 51.0-144.8; text is inset to 61.0

SIZES_X, SIZES_SIZE = 154.8, 9.6
SIZES_BASES = (515.56, 529.96, 544.36, 558.76)
SIZES_TEXT = ('Vendor resolution, the pre/post-petition split, and payment allocation are the '
              'hard parts. Utilities is largely configuration once vendors is built and Phase 1 '
              'has ratified the mapping.')
SIZES_W = 232.0                 # column runs 144.8-387.0

ROW_RULE_Y = 571.9              # the row's bottom rule; nothing may cross it
OLD_FIRST_WORDS = ('13-Week', 'Two joins')


def subset(doc, family, pno=PAGE):
    for xref, _, _, name, *_ in doc.get_page_fonts(pno):
        if name.split('+')[-1] == family:
            return doc.extract_font(xref)[3]
    sys.exit(f'{family} not embedded on page {pno + 1}')


def wrap(font, text, size, width):
    lines, cur = [], ''
    for word in text.split(' '):
        trial = f'{cur} {word}'.strip()
        if cur and font.text_length(trial, size) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    lines.append(cur)
    return lines


def main(src, out):
    doc = pymupdf.open(src)
    page = doc[PAGE]
    mb_buf, ral_buf = subset(doc, 'Montserrat-Bold'), subset(doc, 'Raleway')
    mb, ral = pymupdf.Font(fontbuffer=mb_buf), pymupdf.Font(fontbuffer=ral_buf)

    mod_lines = wrap(mb, MODULE_TEXT, MODULE_SIZE, MODULE_W)
    siz_lines = wrap(ral, SIZES_TEXT, SIZES_SIZE, SIZES_W)
    if len(mod_lines) > len(MODULE_BASES):
        sys.exit(f'module text needs {len(mod_lines)} lines, row holds {len(MODULE_BASES)}')
    if len(siz_lines) > len(SIZES_BASES):
        sys.exit(f'"what sizes it" needs {len(siz_lines)} lines, row holds {len(SIZES_BASES)}')

    # clear the row's first two cells, leaving tier, sizing and the rules alone
    cleared = 0
    for blk in page.get_text('dict')['blocks']:
        for ln in blk.get('lines', []):
            for sp in ln['spans']:
                x0, y0, _, y1 = sp['bbox']
                if 505 < y0 and y1 < ROW_RULE_Y and x0 < 387.0:
                    r = pymupdf.Rect(sp['bbox'])
                    r.x0 -= 1
                    r.x1 += 1
                    page.add_redact_annot(r, fill=False)
                    cleared += 1
    if cleared < 7:
        sys.exit(f'expected the old row text, cleared only {cleared} spans')
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)

    tmp_m = pathlib.Path(out).with_suffix('.mb.ttf')
    tmp_r = pathlib.Path(out).with_suffix('.ral.ttf')
    tmp_m.write_bytes(mb_buf)
    tmp_r.write_bytes(ral_buf)
    for line, base in zip(mod_lines, MODULE_BASES):
        page.insert_text((MODULE_X, base), line, fontname='mb', fontfile=str(tmp_m),
                         fontsize=MODULE_SIZE, color=NAVY)
    for line, base in zip(siz_lines, SIZES_BASES):
        page.insert_text((SIZES_X, base), line, fontname='ral', fontfile=str(tmp_r),
                         fontsize=SIZES_SIZE, color=NAVY)
    print('  module:     ' + ' | '.join(mod_lines))
    print('  what sizes: ' + ' | '.join(siz_lines))

    doc.save(out, garbage=4, deflate=True)
    for f in (tmp_m, tmp_r):
        f.unlink(missing_ok=True)

    txt = pymupdf.open(out)[PAGE].get_text()
    flat = ''.join(txt.split())
    assert 'VendorandUtilitiesFirst-DayMotions' in flat, 'new module name missing'
    assert not any(w.replace(' ', '') in flat for w in OLD_FIRST_WORDS), 'old row text remains'
    assert '~$200–275K' in txt and 'Medium' in txt, 'tier or pricing disturbed'
    print('verified:', out)


if __name__ == '__main__':
    main(*(sys.argv[1:3] or sys.exit(__doc__)))
