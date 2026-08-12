#!/usr/bin/env python3
"""Splice the authored pages into the client PDF and fix the numbering they shift.

  after p17  <- pages/out/m4_gate.pdf        (new page 18, Phase-1 gate M4)
  replace 18 <- pages/out/proposed_team.pdf  (page 19, the 9-role team)
  after that <- pages/out/pod_structure.pdf  (new page 20)

Two pages are added, so every footer number and contents page reference from the old
page 19 onward moves by two. Both are re-set in the document's own Montserrat-Bold.

    python3 splice.py in.pdf out.pdf
"""
import pathlib
import sys

import pymupdf

PAGES = pathlib.Path(__file__).parent / 'pages' / 'out'
NAVY = (0x00 / 255, 0x18 / 255, 0x47 / 255)
RIGHT_EDGE = 544.3

FOOT_BASE, FOOT_SIZE = 819.25, 8.0
TOC_PAGE, TOC_SIZE = 1, 10.5

# original page number -> new page number, for pages that shift
FOOTER_SHIFT = {n: n + 2 for n in range(19, 26)}
# contents row (matched on the span's top edge) -> new page reference
TOC_ROWS = {431.3: '19', 472.8: '21', 514.3: '23', 555.8: '25', 597.3: '26', 638.8: '27'}

# outline entries for the pages being added
NEW_BOOKMARKS = [('Scope and roadmap, refreshed.', 18), ('The pod, carried into Phase 2.', 20)]


def shift_page(old):
    """Old 1-based page number -> new one. Two pages are inserted around page 18."""
    if old < 18:
        return old
    return 19 if old == 18 else old + 2


def montserrat_bold(doc, pno):
    for xref, _, _, name, *_ in doc.get_page_fonts(pno):
        if name.split('+')[-1] == 'Montserrat-Bold':
            return doc.extract_font(xref)[3]
    sys.exit(f'Montserrat-Bold not embedded on page {pno + 1}')


def reset_right_aligned(page, span, new_text, fontfile, font, size, baseline):
    """Replace a right-aligned number in place, keeping its right edge."""
    r = pymupdf.Rect(span['bbox'])
    r.x0 -= 2
    r.x1 += 2
    page.add_redact_annot(r, fill=False)
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    w = font.text_length(new_text, size)
    page.insert_text((RIGHT_EDGE - w, baseline), new_text, fontname='mb',
                     fontfile=fontfile, fontsize=size, color=NAVY)


def main(src, out):
    doc = pymupdf.open(src)
    if doc.page_count != 26:
        sys.exit(f'expected the 26-page document, got {doc.page_count}')

    fontbuf = montserrat_bold(doc, 1)
    tmp = pathlib.Path(out).with_suffix('.mb.ttf')
    tmp.write_bytes(fontbuf)
    font = pymupdf.Font(fontbuffer=fontbuf)

    # renumber footers before inserting, while original indices still hold
    for orig, new in sorted(FOOTER_SHIFT.items(), reverse=True):
        page = doc[orig - 1]
        span = next((s for blk in page.get_text('dict')['blocks'] for ln in blk.get('lines', [])
                     for s in ln['spans']
                     if s['text'].strip() == str(orig) and s['bbox'][1] > 800), None)
        if span is None:
            sys.exit(f'footer number {orig} not found on page {orig}')
        reset_right_aligned(page, span, str(new), str(tmp), font, FOOT_SIZE, FOOT_BASE)
        print(f'  footer p{orig} -> {new}')

    # contents page references
    toc = doc[TOC_PAGE]
    for blk in toc.get_text('dict')['blocks']:
        for ln in blk.get('lines', []):
            for s in ln['spans']:
                key = round(s['bbox'][1], 1)
                if key in TOC_ROWS and s['bbox'][2] > 520:
                    reset_right_aligned(toc, s, TOC_ROWS[key], str(tmp), font,
                                        TOC_SIZE, s['origin'][1])
                    print(f"  contents row @{key} -> {TOC_ROWS[key]}")

    # splice: replace the team page, then insert the two new ones around it
    outline = doc.get_toc()

    team = pymupdf.open(PAGES / 'proposed_team.pdf')
    gate = pymupdf.open(PAGES / 'm4_gate.pdf')
    pod = pymupdf.open(PAGES / 'pod_structure.pdf')

    doc.delete_page(17)                     # drop the old Proposed Team page
    doc.insert_pdf(team, start_at=17)       # its replacement
    doc.insert_pdf(gate, start_at=17)       # M4 gate lands before it
    doc.insert_pdf(pod, start_at=19)        # pod structure lands after it

    # rebuild the outline: deleting a page orphans its bookmark, and the new pages need theirs
    rebuilt = [[lvl, title, shift_page(pg)] for lvl, title, pg in outline]
    rebuilt += [[1, title, pg] for title, pg in NEW_BOOKMARKS]
    rebuilt.sort(key=lambda e: e[2])
    doc.set_toc(rebuilt)

    # the contents link that pointed at the replaced page lost its destination
    for page in doc:
        for link in page.get_links():
            if link.get('page', 0) < 0:
                link['kind'] = pymupdf.LINK_GOTO
                link['page'] = 18                     # 0-based: the new Proposed Team page
                link['to'] = pymupdf.Point(51.02, 790.87)
                link.pop('nameddest', None)
                page.update_link(link)
                print('  repointed a dead contents link to the Proposed Team page')

    doc.save(out, garbage=4, deflate=True)
    tmp.unlink(missing_ok=True)

    check = pymupdf.open(out)
    if check.page_count != 28:
        sys.exit(f'expected 28 pages, got {check.page_count}')
    for pno, want in ((17, 'M4'), (18, 'PROPOSED'), (19, 'POD')):
        assert want in ''.join(check[pno].get_text().split()).upper(), f'page {pno + 1} wrong'
    assert not [e for e in check.get_toc() if e[2] < 1], 'outline has a broken entry'
    assert not [l for pg in check for l in pg.get_links() if l.get('page', 0) < 0], 'dead link'
    print(f'saved {out} ({check.page_count} pages)')


if __name__ == '__main__':
    main(*(sys.argv[1:3] or sys.exit(__doc__)))
