#!/usr/bin/env python3
"""Swap one page of the client PDF for an authored replacement of the same size.

    python3 replace_page.py in.pdf out.pdf <page-number> pages/out/<file>.pdf

Page count is unchanged, so footer numbers, contents references and bookmarks all
still hold. Refuses to run if the replacement is not a single A4 page, or if the
page being replaced does not carry the expected footer number.
"""
import sys

import pymupdf

A4 = (595.28, 841.89)


def main(src, out, page_no, replacement):
    page_no = int(page_no)
    doc = pymupdf.open(src)
    new = pymupdf.open(replacement)
    if new.page_count != 1:
        sys.exit(f'{replacement} has {new.page_count} pages, expected 1')
    for rect, label in ((new[0].rect, replacement), (doc[page_no - 1].rect, f'page {page_no}')):
        if (round(rect.width, 2), round(rect.height, 2)) != A4:
            sys.exit(f'{label} is {rect.width:.2f}x{rect.height:.2f}, expected A4')

    before = doc.page_count
    stamped = [s['text'].strip() for blk in doc[page_no - 1].get_text('dict')['blocks']
               for ln in blk.get('lines', []) for s in ln['spans'] if s['bbox'][1] > 800]
    if str(page_no) not in stamped:
        sys.exit(f'page {page_no} does not carry footer number {page_no}; wrong target?')

    outline = doc.get_toc()          # deleting the page orphans its bookmark
    doc.delete_page(page_no - 1)
    doc.insert_pdf(new, start_at=page_no - 1)
    if doc.page_count != before:
        sys.exit('page count changed')

    doc.set_toc(outline)              # page numbers are unchanged, so restore verbatim
    for page in doc:                  # and any link that pointed at the old page object
        for link in page.get_links():
            if link.get('page', 0) < 0:
                link['kind'] = pymupdf.LINK_GOTO
                link['page'] = page_no - 1
                link['to'] = pymupdf.Point(51.02, 790.87)
                link.pop('nameddest', None)
                page.update_link(link)
                print(f'  repointed a dead link to page {page_no}')

    doc.save(out, garbage=4, deflate=True)

    check = pymupdf.open(out)
    assert check.page_count == before
    assert not [e for e in check.get_toc() if e[2] < 1], 'outline broken by the swap'
    print(f'replaced page {page_no} with {replacement} -> {out}')


if __name__ == '__main__':
    main(*(sys.argv[1:5] or sys.exit(__doc__)))
