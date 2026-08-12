#!/usr/bin/env python3
"""Add a fourth Phase-1 gate (M4 · ~wk4 · scope and roadmap) to the gate row on page 13.

The row is re-laid out as four evenly spaced columns rather than three. Text is set in
the document's own subset-embedded Montserrat-Ultra-Bold and Raleway, at the original
sizes, colours and baselines, so the rebuilt row is typographically identical to the
one it replaces. M1-M3 keep their original wording.

    python3 add_gate_m4.py in.pdf out.pdf
"""
import pathlib
import sys

import pymupdf

PAGE = 12                    # zero-based; page 13, "The shape of the engagement"
COL_X0, ROW_RIGHT = 125.0, 544.3   # first column start, content right edge
GUTTER = 13.0                # space between columns, chevron sits centred in it
BASE_1, BASE_2 = 427.0, 442.7      # the row's two text baselines
CHEV_BASE, CHEV_SIZE = 435.1, 11.0
SIZE_CODE, SIZE_LABEL = 9.0, 8.6
BLUE = (0x34 / 255, 0x42 / 255, 0xDC / 255)   # gate code + chevron
SLATE = (0x4A / 255, 0x5A / 255, 0x7A / 255)  # gate label
REDACT_MIN_X = 120.0         # keep the navy "PHASE-1 GATES" badge untouched

# page 14's figure caption enumerates the gates too; it has to name M4 or it
# contradicts the row above. Its band is only 38.7pt tall (chart bottom 495.6 ->
# card top 534.3) so it must stay two lines, which costs "delivery" and two articles.
CAP_PAGE = 13
CAP_X, CAP_BASE, CAP_LEAD = 51.0, 512.8, 12.3
CAP_SIZE, CAP_WIDTH = 8.5, 493.3
CAP_COLOR = (0x86 / 255, 0x94 / 255, 0xB0 / 255)
CAP_BAND = (498.0, 532.0)     # y range to clear
CAPTION = ('Six workstreams across the four weeks, with the Phase-1 gates on the same clock: '
           'M1 data in and structured (~week 2), M2 mapping ratified and forecast ties (~week 3), '
           'M3 working flow demonstrated (~week 4), and M4 scope and roadmap (~week 4).')

GATES = [
    ('M1', '\xa0 ~wk2 data in and structured'),
    ('M2', '\xa0 ~wk3 mapping ratified, forecast ties'),
    ('M3', '\xa0 ~wk4 working flow, demonstrated'),
    ('M4', '\xa0 ~wk4 scope and roadmap'),
]


def subset(doc, family, pno=PAGE):
    for xref, _, _, name, *_ in doc.get_page_fonts(pno):
        if name.split('+')[-1] == family:
            return doc.extract_font(xref)[3]
    sys.exit(f'{family} not embedded on page {pno + 1}')


def wrap(font, text, first_width, rest_width, size):
    """Greedy two-line wrap. Returns (line1, line2); line2 may be ''."""
    words, lines, cur = text.split(' '), [], ''
    width = first_width
    for w in words:
        trial = f'{cur} {w}' if cur and not cur.endswith('\xa0') else cur + w
        if cur and font.text_length(trial, size) > width:
            lines.append(cur)
            cur, width = w, rest_width
            if len(lines) == 2:
                sys.exit(f'"{text}" needs more than two lines')
        else:
            cur = trial
    lines.append(cur)
    return (lines + [''])[:2]


def main(src, out):
    doc = pymupdf.open(src)
    page = doc[PAGE]
    mub_buf, ral_buf = subset(doc, 'Montserrat-Ultra-Bold'), subset(doc, 'Raleway')
    mub, ral = pymupdf.Font(fontbuffer=mub_buf), pymupdf.Font(fontbuffer=ral_buf)

    n = len(GATES)
    col_w = (ROW_RIGHT - COL_X0 - GUTTER * (n - 1)) / n
    xs = [COL_X0 + i * (col_w + GUTTER) for i in range(n)]

    laid = []
    for (code, label), x0 in zip(GATES, xs):
        code_w = mub.text_length(code, SIZE_CODE)
        l1, l2 = wrap(ral, label, col_w - code_w, col_w, SIZE_LABEL)
        laid.append((code, x0, code_w, l1, l2))
        print(f'  {code} @ x={x0:7.2f}  "{l1.strip()}" / "{l2}"')

    # clear the old three-gate row, leaving the badge and white page untouched
    removed = 0
    for blk in page.get_text('dict')['blocks']:
        for ln in blk.get('lines', []):
            for sp in ln['spans']:
                b = sp['bbox']
                if b[0] >= REDACT_MIN_X and 405 < b[1] < 450:
                    r = pymupdf.Rect(b)
                    r.x0 -= 1
                    r.x1 += 1
                    page.add_redact_annot(r, fill=False)
                    removed += 1
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    print(f'  cleared {removed} old spans')

    tmp_m = pathlib.Path(out).with_suffix('.mub.ttf')
    tmp_r = pathlib.Path(out).with_suffix('.ral.ttf')
    tmp_m.write_bytes(mub_buf)
    tmp_r.write_bytes(ral_buf)

    for code, x0, code_w, l1, l2 in laid:
        page.insert_text((x0, BASE_1), code, fontname='mub', fontfile=str(tmp_m),
                         fontsize=SIZE_CODE, color=BLUE)
        page.insert_text((x0 + code_w, BASE_1), l1, fontname='ral', fontfile=str(tmp_r),
                         fontsize=SIZE_LABEL, color=SLATE)
        if l2:
            page.insert_text((x0, BASE_2), l2, fontname='ral', fontfile=str(tmp_r),
                             fontsize=SIZE_LABEL, color=SLATE)

    chev_w = mub.text_length('›', CHEV_SIZE)
    for i in range(n - 1):
        cx = xs[i] + col_w + GUTTER / 2
        page.insert_text((cx - chev_w / 2, CHEV_BASE), '›', fontname='mub',
                         fontfile=str(tmp_m), fontsize=CHEV_SIZE, color=BLUE)

    # --- page 14 caption ---
    cap_page = doc[CAP_PAGE]
    cap_buf = subset(doc, 'Raleway-Oblique', CAP_PAGE)
    cap_font = pymupdf.Font(fontbuffer=cap_buf)
    cap_lines = []
    cur = ''
    for w in CAPTION.split(' '):
        trial = f'{cur} {w}'.strip()
        if cur and cap_font.text_length(trial, CAP_SIZE) > CAP_WIDTH:
            cap_lines.append(cur)
            cur = w
        else:
            cur = trial
    cap_lines.append(cur)
    if len(cap_lines) > 2:
        sys.exit(f'caption needs {len(cap_lines)} lines; only two fit above the cards')

    for blk in cap_page.get_text('dict')['blocks']:
        for ln in blk.get('lines', []):
            if CAP_BAND[0] < ln['bbox'][1] < CAP_BAND[1]:
                r = pymupdf.Rect(ln['bbox'])
                r.x0 -= 1
                r.x1 += 1
                cap_page.add_redact_annot(r, fill=False)
    cap_page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)

    tmp_c = pathlib.Path(out).with_suffix('.obl.ttf')
    tmp_c.write_bytes(cap_buf)
    for i, line in enumerate(cap_lines):
        cap_page.insert_text((CAP_X, CAP_BASE + i * CAP_LEAD), line, fontname='obl',
                             fontfile=str(tmp_c), fontsize=CAP_SIZE, color=CAP_COLOR)
        print(f'  caption L{i + 1}: {cap_font.text_length(line, CAP_SIZE):.0f}pt')

    doc.save(out, garbage=4, deflate=True)
    for f in (tmp_m, tmp_r, tmp_c):
        f.unlink(missing_ok=True)

    txt = pymupdf.open(out)[PAGE].get_text()
    for code, _ in GATES:
        assert code in txt, f'{code} missing from output'
    for word in ('scope', 'roadmap'):   # the label wraps, so check its words
        assert word in txt, f'M4 label missing "{word}"'
    assert 'PHASE-1' in txt and 'GATES' in txt, 'badge damaged'
    cap = pymupdf.open(out)[CAP_PAGE].get_text()
    assert 'M4 scope and roadmap' in cap, 'caption missing M4'
    print('verified:', out)


if __name__ == '__main__':
    main(*(sys.argv[1:3] or sys.exit(__doc__)))
