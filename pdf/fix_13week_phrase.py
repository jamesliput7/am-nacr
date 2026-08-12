#!/usr/bin/env python3
"""Replace every remaining "13-week cash flow use case" with "Vendors and Utilities".

Five occurrences survive the vendors-and-utilities rewording done so far, each inside
running prose or a fixed-size box rather than a table cell, so each needs its own
paragraph reflowed rather than a single-line swap:

  p12  Q8 "Sequencing delivery" answer         - a 12-line paragraph
  p13  delivery-schedule intro paragraph       - a 6-line paragraph with inline arrows
  p13  the Phase 1 diagram box                 - a 5-line box, shrinks to 4
  p14  4-Week Discovery + Build lede           - a 4-line paragraph, shrinks to 3
  p21  Phase 1 budget-card bullet              - a 2-line bullet, stays 2 lines

Every replacement was pre-checked to wrap to the same or fewer lines than the text it
replaces, at a width no wider than that text's own longest observed line, so nothing
here should overflow into what sits below or beside it; the script still asserts a
maximum line count per block as a backstop. Two occurrences that don't literally
contain the phrase - "13-week forecast" (pages 16, 17) and the bare "13-week cash
flow" module example (page 23) - are left alone; replacing them can't be a simple
substitution, since the words around them assume "cash flow"/"forecast" is the
subject of the sentence.

    python3 fix_13week_phrase.py in.pdf out.pdf
"""
import pathlib
import sys

import pymupdf

NAVY, MUTED_BLUE, WHITE = (0x00/255, 0x18/255, 0x47/255), (0x4a/255, 0x5a/255, 0x7a/255), (1, 1, 1)


def subset(doc, family, pno):
    for xref, _, _, name, *_ in doc.get_page_fonts(pno):
        if name.split('+')[-1] == family:
            return doc.extract_font(xref)[3]
    sys.exit(f'{family} not embedded on page {pno + 1}')


def wrap(font, text, size, width, arrow_font=None):
    def seglen(s):
        if arrow_font is None:
            return font.text_length(s, size)
        return sum((arrow_font if ch == '→' else font).text_length(ch, size) for ch in s)
    lines, cur = [], ''
    for word in text.split(' '):
        trial = f'{cur} {word}'.strip()
        if cur and seglen(trial) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    lines.append(cur)
    return lines


def clear_region(page, x0, y0, x1, y1):
    page.add_redact_annot(pymupdf.Rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1), fill=False)


def set_lines(page, lines, baselines, x, size, color, fontname, fontfile):
    for line, base in zip(lines, baselines):
        page.insert_text((x, base), line, fontname=fontname, fontfile=fontfile,
                         fontsize=size, color=color)


def main(src, out):
    doc = pymupdf.open(src)
    tmp = []

    def stash(buf, suffix):
        p = pathlib.Path(out).with_suffix(suffix)
        p.write_bytes(buf)
        tmp.append(p)
        return str(p)

    # ---- page 12: Q8 paragraph -----------------------------------------------
    PAGE = 11
    ral_buf = subset(doc, 'Raleway', PAGE)
    ral = pymupdf.Font(fontbuffer=ral_buf)
    ral_file = stash(ral_buf, '.p12ral.ttf')
    OLD = ("We resolve the tension by proving the whole chain end to end on the narrowest scope first. A 4-week "
           "Discovery + Build engineers the context and ships a working data-integration workflow for the 13-week "
           "cash flow use case on A&M’s own files; the Engage 2.0 production rollout (3 months) then takes "
           "ingestion plus the data mapper and parser — the client data-intake front end A&M calls “step one” of "
           "the whole process — into production, starting with the ingestion A&M itself calls the unlock. Utilities "
           "follows as the next motion; vendors and utilities are the two A&M named. Every motion follows the "
           "same shape A&M articulated: ingest the data, prepare relief calculations by bucket, each bucket "
           "becomes a tab in a support binder, then insert the resulting language, tables, and exhibits into the "
           "filing. Build one motion well and motions 2–N are largely configuration; that is the path to ~10 first-day-"
           "motion modules. Speed comes from the shared foundation and automation; accuracy comes from "
           "validation and human-review gates that never move. We then parallel-path so value ships while the "
           "foundation hardens.")
    NEW = OLD.replace('the 13-week cash flow use case on A&M’s own files',
                      'Vendors and Utilities on A&M’s own files')
    lines = wrap(ral, NEW, 10.4, 493.3)
    if len(lines) > 12:
        sys.exit(f'p12 paragraph needs {len(lines)} lines, only 12 fit before the next paragraph')
    clear_region(doc[PAGE], 51.0, 460.0, 544.3, 650.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    baselines = [466.73 + i * 16.12 for i in range(len(lines))]
    set_lines(doc[PAGE], lines, baselines, 51.0, 10.4, MUTED_BLUE, 'ral', ral_file)
    print(f'  p12: {len(lines)} lines (was 12)')

    # ---- page 13: delivery-schedule intro paragraph (has inline arrows) ------
    PAGE = 12
    ral_buf = subset(doc, 'Raleway', PAGE)
    arw_buf = subset(doc, 'Arial', PAGE)
    ral, arw = pymupdf.Font(fontbuffer=ral_buf), pymupdf.Font(fontbuffer=arw_buf)
    ral_file = stash(ral_buf, '.p13ral.ttf')
    arw_file = stash(arw_buf, '.p13arw.ttf')
    OLD = ("Three phases, each de-risking the next. Phase 1 — Discovery + Build — is a firm $60K fixed fee "
           "committed now: four weeks that clear build scope and ship a working ingestion → mapping → forecast "
           "flow for the 13-week cash flow use case, on A&M’s own files. Phase 2 puts Engage 2.0 into production — "
           "ingestion plus the data mapper and parser — for a fixed $190K over three months. Phase 3 stands up "
           "the delivery pod: four FTEs shipping priced modules at case speed, $100K a month with a 12-month "
           "minimum — and no multi-year commitment upfront.")
    NEW = OLD.replace('the 13-week cash flow use case, on A&M’s own files',
                      'Vendors and Utilities, on A&M’s own files')
    lines = wrap(ral, NEW, 10.4, 493.3, arrow_font=arw)
    if len(lines) > 6:
        sys.exit(f'p13 intro paragraph needs {len(lines)} lines, only 6 fit before the phase cards')
    clear_region(doc[PAGE], 51.0, 165.0, 544.3, 258.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    baselines = [171.65 + i * 16.12 for i in range(len(lines))]
    for line, base in zip(lines, baselines):
        x = 51.0
        for tok in line.split(' '):
            font, fn, ff = (arw, 'arw', arw_file) if tok == '→' else (ral, 'ral', ral_file)
            doc[PAGE].insert_text((x, base), tok, fontname=fn, fontfile=ff, fontsize=10.4, color=MUTED_BLUE)
            x += font.text_length(tok, 10.4) + font.text_length(' ', 10.4)
    print(f'  p13 intro: {len(lines)} lines (was 6)')

    # ---- page 13: the Phase 1 diagram box ------------------------------------
    OLD_BOX = ("Discovery that also builds: clears build scope · ships the working ingestion › mapping "
              "› forecast flow for the 13-week cash flow use case")
    NEW_BOX = OLD_BOX.replace('the 13-week cash flow use case', 'Vendors and Utilities')
    lines = wrap(ral, NEW_BOX, 8.4, 126.9)
    if len(lines) > 5:
        sys.exit(f'p13 box needs {len(lines)} lines, only 5 fit before the price badge')
    clear_region(doc[PAGE], 55.0, 320.0, 200.0, 385.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    baselines = [325.95 + i * 11.59 for i in range(len(lines))]
    set_lines(doc[PAGE], lines, baselines, 61.8, 8.4, WHITE, 'ral', ral_file)
    print(f'  p13 box: {len(lines)} lines (was 5)')

    # ---- page 14: 4-Week Discovery + Build lede ------------------------------
    PAGE = 13
    ral_buf = subset(doc, 'Raleway', PAGE)
    ral = pymupdf.Font(fontbuffer=ral_buf)
    ral_file = stash(ral_buf, '.p14ral.ttf')
    OLD = ("A compressed four-week sprint — discovery that also builds. It clears build "
           "scope, produces the data-handling protocols and firm pricing, and ships a "
           "working data-integration workflow for the 13-week cash flow use case on A&M’s "
           "own files.")
    NEW = OLD.replace('the 13-week cash flow use case on A&M’s own files',
                      'Vendors and Utilities on A&M’s own files').replace('  ', ' ')
    NEW = ' '.join(NEW.split())
    lines = wrap(ral, NEW, 11.5, 471.5)
    if len(lines) > 4:
        sys.exit(f'p14 lede needs {len(lines)} lines, only 4 fit before the week accordion')
    clear_region(doc[PAGE], 51.0, 163.0, 544.3, 230.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    baselines = [168.90 + i * 17.82 for i in range(len(lines))]
    set_lines(doc[PAGE], lines, baselines, 51.0, 11.5, MUTED_BLUE, 'ral', ral_file)
    print(f'  p14: {len(lines)} lines (was 4)')

    # ---- page 21: Phase 1 budget-card bullet ---------------------------------
    PAGE = 20
    ral_buf = subset(doc, 'Raleway', PAGE)
    ral = pymupdf.Font(fontbuffer=ral_buf)
    ral_file = stash(ral_buf, '.p21ral.ttf')
    NEW = 'Vendors and Utilities, on your files'
    lines = wrap(ral, NEW, 9.0, 110.1)
    if len(lines) > 2:
        sys.exit(f'p21 bullet needs {len(lines)} lines, only 2 fit in the row')
    clear_region(doc[PAGE], 85.0, 425.0, 200.0, 458.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    baselines = [430.65 + i * 13.5 for i in range(len(lines))]
    set_lines(doc[PAGE], lines, baselines, 90.0, 9.0, WHITE, 'ral', ral_file)
    print(f'  p21: {len(lines)} lines (was 2)')

    doc.save(out, garbage=4, deflate=True)
    for p in tmp:
        p.unlink(missing_ok=True)

    check = pymupdf.open(out)
    flat = lambda i: ''.join(check[i].get_text().split())
    for pno in (11, 12, 13, 20):
        assert '13-week' not in check[pno].get_text() or pno == 12, f'p{pno + 1} still has 13-week text'
    assert 'VendorsandUtilities' in flat(11), 'p12 not updated'
    assert 'VendorsandUtilities' in flat(12), 'p13 not updated'
    assert 'VendorsandUtilities' in flat(13), 'p14 not updated'
    assert 'VendorsandUtilities' in flat(20), 'p21 not updated'
    assert '13-week' not in check[12].get_text(), 'p13 still has 13-week text (paragraph or box)'
    print('verified:', out)


if __name__ == '__main__':
    main(*(sys.argv[1:3] or sys.exit(__doc__)))
