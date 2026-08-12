#!/usr/bin/env python3
"""Reword the three "13-week" mentions that aren't the literal cash-flow-use-case
phrase, so no reference to it survives anywhere in the document:

  p16  M2 gate: "forecast computes" -> "calculations compute" (header and body)
  p17  M3 gate: "ingestion -> mapping -> 13-week forecast" -> adds a node,
       "ingestion -> mapping -> relief calculations -> support binder"
  p23  module-pricing lede: "the 13-week cash flow" -> "a vendor-motion relief analysis"

Matches the wording already used for these same gates in the HTML deck. p16 and p17
mix a bold gate label with regular body text on the same wrapped lines, and p17 has
inline arrows in Arial (Raleway has no U+2192), so both are rewrapped word-by-word
with a font chosen per word rather than per line.

    python3 fix_gate_wording.py in.pdf out.pdf
"""
import pathlib
import sys

import pymupdf

SLATE = (0x4a / 255, 0x5a / 255, 0x7a / 255)


def subset(doc, family, pno):
    for xref, _, _, name, *_ in doc.get_page_fonts(pno):
        if name.split('+')[-1] == family:
            return doc.extract_font(xref)[3]
    sys.exit(f'{family} not embedded on page {pno + 1}')


def tokenize(text, kind):
    """kind: 'b' bold, 'r' regular. Splits an arrow out of running regular text."""
    out = []
    for word in text.split(' '):
        out.append((word, 'a' if (kind == 'r' and word == '→') else kind))
    return out


def wrap_mixed(tokens, size, width, fonts):
    lines, cur, cur_w = [], [], 0.0
    space_w = fonts['r'].text_length(' ', size)
    for word, kind in tokens:
        w = fonts[kind].text_length(word, size)
        add = (space_w if cur else 0) + w
        if cur and cur_w + add > width:
            lines.append(cur)
            cur, cur_w = [], 0
            add = w
        cur.append((word, kind))
        cur_w += add
    if cur:
        lines.append(cur)
    return lines


def render_mixed(page, lines, x0, baselines, size, color, fonts, files):
    for line, base in zip(lines, baselines):
        x = x0
        for word, kind in line:
            page.insert_text((x, base), word, fontname=kind, fontfile=files[kind],
                             fontsize=size, color=color)
            x += fonts[kind].text_length(word, size) + fonts['r'].text_length(' ', size)


def clear(page, x0, y0, x1, y1):
    page.add_redact_annot(pymupdf.Rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1), fill=False)


def main(src, out):
    doc = pymupdf.open(src)
    tmp = []

    def stash(buf, suffix):
        p = pathlib.Path(out).with_suffix(suffix)
        p.write_bytes(buf)
        tmp.append(p)
        return str(p)

    # ---- page 16: M2 gate, bold label + regular body on shared lines --------
    PAGE = 15
    bold_buf, reg_buf = subset(doc, 'Raleway-Bold', PAGE), subset(doc, 'Raleway', PAGE)
    bold_f, reg_f = pymupdf.Font(fontbuffer=bold_buf), pymupdf.Font(fontbuffer=reg_buf)
    files = {'b': stash(bold_buf, '.p16b.ttf'), 'r': stash(reg_buf, '.p16r.ttf')}
    fonts = {'b': bold_f, 'r': reg_f}
    header = 'M2 · Mapping ratified, calculations compute (~week 3).'
    body = (' Vendor resolution and the pre/post-petition split land, the '
            'practitioner-approved crosswalk freezes as a deterministic rule, and the '
            'vendor and utilities relief calculations compute — date windows and control '
            'totals passing or failing on their own; a figure that fails to tie is flagged, '
            'never emitted.')
    tokens = tokenize(header, 'b') + tokenize(body.strip(), 'r')
    lines = wrap_mixed(tokens, 9.0, 493.3, fonts)
    if len(lines) > 5:
        sys.exit(f'p16 M2 needs {len(lines)} lines, only 5 fit before the footer')
    clear(doc[PAGE], 51.0, 700.0, 544.3, 745.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    baselines = [706.87 + i * 13.05 for i in range(len(lines))]
    render_mixed(doc[PAGE], lines, 51.0, baselines, 9.0, SLATE, fonts, files)
    print(f'  p16 M2: {len(lines)} lines (was 3)')

    # ---- page 17: M3 gate, bold label + regular body + inline arrows --------
    PAGE = 16
    bold_buf, reg_buf = subset(doc, 'Raleway-Bold', PAGE), subset(doc, 'Raleway', PAGE)
    arw_buf = subset(doc, 'Arial', PAGE)
    bold_f, reg_f, arw_f = (pymupdf.Font(fontbuffer=bold_buf), pymupdf.Font(fontbuffer=reg_buf),
                            pymupdf.Font(fontbuffer=arw_buf))
    files = {'b': stash(bold_buf, '.p17b.ttf'), 'r': stash(reg_buf, '.p17r.ttf'),
            'a': stash(arw_buf, '.p17a.ttf')}
    fonts = {'b': bold_f, 'r': reg_f, 'a': arw_f}
    header = 'M3 · Working flow, demonstrated (~week 4).'
    body = (' The end-to-end flow runs on A&M’s own files — ingestion → mapping → '
            'relief calculations → support binder — with click-through provenance on '
            'every figure and the attestation gate in place. Done when the demonstrated '
            'workflow reproduces the curated golden cases within a documented tolerance, '
            'with a recorded human sign-off: the Phase-1 exit.')
    tokens = tokenize(header, 'b') + tokenize(body.strip(), 'r')
    lines = wrap_mixed(tokens, 9.0, 493.3, fonts)
    if len(lines) > 8:
        sys.exit(f'p17 M3 needs {len(lines)} lines, only 8 fit before the footer')
    clear(doc[PAGE], 51.0, 393.0, 544.3, 445.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    baselines = [398.88 + i * 13.05 for i in range(len(lines))]
    render_mixed(doc[PAGE], lines, 51.0, baselines, 9.0, SLATE, fonts, files)
    print(f'  p17 M3: {len(lines)} lines (was 4)')

    # ---- page 23: module-pricing lede ----------------------------------------
    PAGE = 22
    ral_buf = subset(doc, 'Raleway', PAGE)
    ral = pymupdf.Font(fontbuffer=ral_buf)
    ral_file = stash(ral_buf, '.p23ral.ttf')
    OLD = ("A module is one governed dataset plus the models built on it — the 13-week "
           "cash flow, or the store-footprint analysis. Modules are priced by tier, and every "
           "ratified mapping makes the next similar module cheaper.")
    NEW = OLD.replace('the 13-week cash flow', 'a vendor-motion relief analysis')
    lines2, cur = [], ''
    for word in NEW.split(' '):
        trial = f'{cur} {word}'.strip()
        if cur and ral.text_length(trial, 11.5) > 462.4:
            lines2.append(cur)
            cur = word
        else:
            cur = trial
    lines2.append(cur)
    if len(lines2) > 3:
        sys.exit(f'p23 lede needs {len(lines2)} lines, only 3 fit before the tier cards')
    clear(doc[PAGE], 51.0, 163.0, 544.3, 213.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    baselines2 = [168.90 + i * 17.82 for i in range(len(lines2))]
    for line, base in zip(lines2, baselines2):
        doc[PAGE].insert_text((51.0, base), line, fontname='ral', fontfile=ral_file,
                              fontsize=11.5, color=SLATE)
    print(f'  p23 lede: {len(lines2)} lines (was 3)')

    doc.save(out, garbage=4, deflate=True)
    for p in tmp:
        p.unlink(missing_ok=True)

    check = pymupdf.open(out)
    flat = lambda i: ''.join(check[i].get_text().split())
    assert '13-week' not in check[15].get_text(), 'p16 still has 13-week text'
    assert '13-week' not in check[16].get_text(), 'p17 still has 13-week text'
    assert '13-week' not in check[22].get_text(), 'p23 still has 13-week text'
    assert 'calculationscompute' in flat(15), 'p16 wording not updated'
    assert 'reliefcalculations→supportbinder' in flat(16), 'p17 wording not updated'
    assert 'vendor-motionreliefanalysis' in flat(22), 'p23 wording not updated'
    print('verified:', out)


if __name__ == '__main__':
    main(*(sys.argv[1:3] or sys.exit(__doc__)))
