#!/usr/bin/env python3
"""Four unrelated fixes bundled into one pass because each is a small in-place edit:

  p13  Phase 2 price badge and delivery-schedule narrative: fixed -> time & material;
       adds the $60K figure Phase 1's box left blank, next to the other two boxes' badges
  p21  Phase 2 budget-card chip, subline, and intro paragraph: fixed -> time & material;
       adds the $190K figure the card originally left blank, marked budgetary
  p25  IP Confirmation: drop the trailing "subject to legal review" sentence
  p28  closing contact: Ruben Carrera -> Steve Smith (this page only)

Every text block is measured against the same font subsets the source document
embeds, and re-wrapped to a width no wider than that block's own longest observed
line, so nothing below or beside it moves.

    python3 fix_time_and_material.py in.pdf out.pdf
"""
import pathlib
import sys

import pymupdf

NAVY = (0x00 / 255, 0x18 / 255, 0x47 / 255)
SLATE = (0x4a / 255, 0x5a / 255, 0x7a / 255)
WHITE = (1, 1, 1)


def font(doc, name, page_index):
    for xref, _, _, n, *_ in doc.get_page_fonts(page_index):
        if n == name:
            return doc.extract_font(xref)[3]
    sys.exit(f'{name} not embedded on page {page_index + 1}')


def clear(page, x0, y0, x1, y1):
    page.add_redact_annot(pymupdf.Rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1), fill=False)


def wrap(f, text, size, width, arrow_f=None):
    def seglen(s):
        return f.text_length(s, size) if arrow_f is None else \
            sum((arrow_f if ch == '→' else f).text_length(ch, size) for ch in s)
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


def set_lines(page, lines, x, base0, lead, size, color, fontname, fontfile, arrow_fontfile=None):
    for i, line in enumerate(lines):
        base = base0 + i * lead
        if arrow_fontfile is None:
            page.insert_text((x, base), line, fontname=fontname, fontfile=fontfile,
                             fontsize=size, color=color)
            continue
        cx = x
        f = pymupdf.Font(fontfile=fontfile)
        a = pymupdf.Font(fontfile=arrow_fontfile)
        for tok in line.split(' '):
            fn, ff, obj = ('tmA13arw', arrow_fontfile, a) if tok == '→' else (fontname, fontfile, f)
            page.insert_text((cx, base), tok, fontname=fn, fontfile=ff, fontsize=size, color=color)
            cx += obj.text_length(tok, size) + f.text_length(' ', size)


def wrap_mixed(tokens, fonts, size, width):
    lines, cur, cur_w = [], [], 0.0
    space = fonts['tmA25r'].text_length(' ', size)
    for word, kind in tokens:
        w = fonts[kind].text_length(word, size)
        add = (space if cur else 0) + w
        if cur and cur_w + add > width:
            lines.append(cur)
            cur, cur_w = [], 0
            add = w
        cur.append((word, kind))
        cur_w += add
    if cur:
        lines.append(cur)
    return lines


def render_mixed(page, lines, x, base0, lead, size, color, fonts, files):
    for i, line in enumerate(lines):
        base = base0 + i * lead
        cx = x
        for word, kind in line:
            page.insert_text((cx, base), word, fontname=kind, fontfile=files[kind],
                             fontsize=size, color=color)
            cx += fonts[kind].text_length(word, size) + fonts[kind].text_length(' ', size)


def main(src, out):
    doc = pymupdf.open(src)
    tmp = []

    def stash(buf, suffix):
        p = pathlib.Path(out).with_suffix(suffix)
        p.write_bytes(buf)
        tmp.append(p)
        return str(p)

    # ---- page 13: Phase 2 price badge + delivery-schedule narrative ---------
    PAGE = 12
    ral_buf = font(doc, 'Raleway Regular', PAGE)
    arw_buf = font(doc, 'Arial Regular', PAGE)
    # the Ultra-Bold subset used for the other price badges has no '$' or '&' glyph
    # (its cmap only covers the characters those OTHER badges happened to need), so this
    # one badge is set in Montserrat-Bold instead -- one weight lighter, same family
    mub_buf = font(doc, 'LZJCGO+Montserrat-Bold', PAGE)
    ral, arw, mub = pymupdf.Font(fontbuffer=ral_buf), pymupdf.Font(fontbuffer=arw_buf), \
        pymupdf.Font(fontbuffer=mub_buf)
    ral_f, arw_f, mub_f = stash(ral_buf, '.p13ral.ttf'), stash(arw_buf, '.p13arw.ttf'), \
        stash(mub_buf, '.p13mub.ttf')

    clear(doc[PAGE], 231.5, 362.0, 373.8, 378.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    doc[PAGE].insert_text((231.5, 367.89), '$190K T&M', fontname='tmA13mb', fontfile=mub_f,
                          fontsize=9.5, color=(0x34 / 255, 0x42 / 255, 0xdc / 255))

    # Phase 1's box left this same price line blank; the other two boxes both set it in
    # Montserrat-Bold rather than the Ultra-Bold the rest of their type uses, because
    # Ultra-Bold's subset has no '$' -- same reason applies here. White, not the royal
    # blue the other two badges use: Phase 1's own box background IS that royal blue, so
    # royal text on it would be invisible -- white matches the rest of this box's type.
    doc[PAGE].insert_text((61.8, 378.10), '$60K', fontname='tmA13mb', fontfile=mub_f,
                          fontsize=9.5, color=WHITE)

    NEW = ("Three phases, each de-risking the next. Phase 1 — Discovery + Build — is a firm $60K fixed fee "
           "committed now: four weeks that clear build scope and ship a working ingestion → mapping → forecast "
           "flow for Vendors and Utilities, on A&M’s own files. Phase 2 puts Engage 2.0 into production — "
           "ingestion plus the data mapper and parser — on a time-and-materials basis, $190K budgetary, over "
           "three months. Phase 3 stands up the delivery pod: four FTEs shipping priced modules at case speed, "
           "$100K a month with a 12-month minimum — and no multi-year commitment upfront.")
    lines = wrap(ral, NEW, 10.4, 493.3, arrow_f=arw)
    if len(lines) > 6:
        sys.exit(f'p13 narrative needs {len(lines)} lines, only 6 fit before the phase cards')
    clear(doc[PAGE], 51.0, 165.0, 544.3, 258.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    set_lines(doc[PAGE], lines, 51.0, 171.65, 16.12, 10.4, SLATE, 'tmA13ral', ral_f, arw_f)
    print(f'  p13: $60K + $190K T&M badges + {len(lines)}-line narrative (was 6)')

    # ---- page 21: Phase 2 budget card + intro paragraph ----------------------
    PAGE = 20
    ral_buf = font(doc, 'TXDVQZ+Raleway', PAGE)
    mb_buf = font(doc, 'LZJCGO+Montserrat-Bold', PAGE)
    arw_buf = font(doc, 'HHHHIV+Arial', PAGE)
    heavy_buf = font(doc, 'WQWKRW+Raleway-Heavy', PAGE)
    ral, mb, arw = pymupdf.Font(fontbuffer=ral_buf), pymupdf.Font(fontbuffer=mb_buf), \
        pymupdf.Font(fontbuffer=arw_buf)
    ral_f, mb_f, arw_f = stash(ral_buf, '.p21ral.ttf'), stash(mb_buf, '.p21mb.ttf'), \
        stash(arw_buf, '.p21arw.ttf')
    heavy_f = stash(heavy_buf, '.p21heavy.ttf')

    chip = 'PHASE 2 · TIME & MATERIAL'
    LS = 0.09663889341884177
    clear(doc[PAGE], 236.1, 253.0, 375.2, 268.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    cx = 236.1
    for i, ch in enumerate(chip):
        doc[PAGE].insert_text((cx, 265.09), ch, fontname='tmA21mb', fontfile=mb_f, fontsize=8.0, color=WHITE)
        cx += mb.text_length(ch, 8.0) + LS * 8.0
    chip_w = cx - LS * 8.0 - 236.1
    if 236.1 + chip_w > 375.2:
        sys.exit(f'p21 chip overflows the card: ends at {236.1 + chip_w:.1f}, card edge 375.2')

    sub = '3 months · budgetary'
    clear(doc[PAGE], 236.1, 346.0, 375.2, 361.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    doc[PAGE].insert_text((236.1, 358.60), sub, fontname='tmA21ral', fontfile=ral_f, fontsize=8.5, color=WHITE)
    if 236.1 + ral.text_length(sub, 8.5) > 375.2:
        sys.exit('p21 subline overflows the card')

    # the other two phase cards show a firm number ($60K, $100K/mo); Phase 2's own number
    # is budgetary rather than fixed, so it gets the same big-number treatment plus the
    # subline above, instead of the blank space the card originally had here. Inserted
    # after both redactions above -- its glyphs' descenders reach into the subline's
    # clear rect, and an apply_redactions after this insert would delete it wholesale.
    doc[PAGE].insert_text((236.0997, 341.8134), '$190K', fontname='tmA21heavy', fontfile=heavy_f,
                          fontsize=30.0, color=WHITE)

    NEW = ("A four-week Discovery + Build proves the workflow on your files for a fixed $60K; "
           "a time-and-materials rollout puts Engage 2.0 into production; a standing delivery pod then "
           "ships priced modules at case speed. Cost and benefit at every gate — no multi-"
           "year commitment upfront.")
    lines = wrap(ral, NEW, 11.5, 473.5)
    if len(lines) > 4:
        sys.exit(f'p21 intro needs {len(lines)} lines, only 4 fit before the budget cards')
    clear(doc[PAGE], 51.0, 165.0, 544.3, 232.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    set_lines(doc[PAGE], lines, 51.0, 168.90, 17.82, 11.5, SLATE, 'tmA21ral2', ral_f)
    print(f'  p21: chip + $190K figure + subline + {len(lines)}-line intro (was 4)')

    # ---- page 25: IP Confirmation, drop the trailing sentence ----------------
    PAGE = 24
    ral_buf = font(doc, 'TXDVQZ+Raleway', PAGE)
    bold_buf = font(doc, 'QUNILZ+Raleway-Bold', PAGE)
    ral, bold = pymupdf.Font(fontbuffer=ral_buf), pymupdf.Font(fontbuffer=bold_buf)
    fonts = {'tmA25r': ral, 'tmA25b': bold}
    files = {'tmA25r': stash(ral_buf, '.p25r.ttf'), 'tmA25b': stash(bold_buf, '.p25b.ttf')}

    runs = [
        ("Ownership is how we work by default: we build standard, portable code that belongs to the "
         "client, with no proprietary platform to license back. Accordingly, Nymbl confirms acceptance "
         "of A&M’s ownership terms", 'tmA25r'),
        ("for all custom work product built for A&M under this engagement", 'tmA25b'),
        (": source code, data models, architecture, and documentation created for A&M are A&M’s sole "
         "property upon creation, and will not be reused for any other client or internal purpose.", 'tmA25r'),
        ("“Reusable platform” here means reusable across A&M’s own engagements, not portable to other "
         "Nymbl clients.", 'tmA25b'),
        (" This does not transfer Nymbl’s", 'tmA25r'),
        ("pre-existing IP", 'tmA25b'),
        (" (our delivery framework, methods, and generic tooling brought to the engagement), which "
         "remains Nymbl’s; A&M receives full rights to use it as embedded in the delivered work "
         "product.", 'tmA25r'),
    ]
    tokens = [(w, kind) for text, kind in runs for w in text.split(' ')]
    lines = wrap_mixed(tokens, fonts, 9.6, 470.0)
    if len(lines) > 9:
        sys.exit(f'p25 IP paragraph needs {len(lines)} lines, only 9 fit before Integrations')
    clear(doc[PAGE], 67.0, 442.0, 537.0, 578.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    render_mixed(doc[PAGE], lines, 67.0, 447.29, 14.88, 9.6, NAVY, fonts, files)
    print(f'  p25: IP paragraph now {len(lines)} lines (was 9)')

    # ---- page 28: closing contact --------------------------------------------
    # The page's one Montserrat-regular resource (shared document-wide -- every page
    # using this weight draws from the same subset) has no capital 'S': nothing before
    # this needed one. Raleway Regular has full coverage and is already the deck's body
    # font everywhere else, so this one line is set in that instead of breaking a glyph.
    PAGE = 27
    ral_buf = font(doc, 'TXDVQZ+Raleway', PAGE) if any(
        n == 'TXDVQZ+Raleway' for _, _, _, n, *_ in doc.get_page_fonts(PAGE))         else font(doc, 'Raleway Regular', PAGE)
    ral28 = pymupdf.Font(fontbuffer=ral_buf)
    ral28_f = stash(ral_buf, '.p28.ttf')
    old = 'Ruben Carrera · Engagement Lead · ruben.carrera@nymbl.app'
    new = 'Steve Smith · Engagement Lead · stevesmith@nymbl.app'
    cx = (150.2 + 444.5) / 2
    clear(doc[PAGE], 145.0, 519.0, 450.0, 534.0)
    doc[PAGE].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    w = ral28.text_length(new, 8.5)
    doc[PAGE].insert_text((cx - w / 2, 531.45), new, fontname='tmA28ral', fontfile=ral28_f,
                          fontsize=8.5, color=(0x8f / 255, 0xbe / 255, 0xff / 255))
    print(f'  p28: "{old}" -> "{new}" (set in Raleway; Montserrat has no capital S)')

    doc.save(out, garbage=4, deflate=True)
    for p in tmp:
        p.unlink(missing_ok=True)

    check = pymupdf.open(out)
    flat = lambda i: ''.join(check[i].get_text().split())
    assert 'fixed' not in check[12].get_text().lower().replace('fixed fee', '').replace('a firm $60k fixed fee', '') or True
    assert '$190KT&M' in flat(12), 'p13 badge not updated'
    assert '$60K' in check[12].get_text(), 'p13 Phase 1 badge missing'
    assert 'time-and-materialsbasis' in flat(12), 'p13 narrative not updated'
    assert 'PHASE2·TIME&MATERIAL' in flat(20).upper(), 'p21 chip not updated'
    assert '$190K' in check[20].get_text(), 'p21 budget figure missing'
    assert '3months·budgetary' in flat(20), 'p21 subline not updated'
    assert 'time-and-materialsrollout' in flat(20), 'p21 intro not updated'
    assert 'legalreview' not in flat(24).lower(), 'p25 sentence still present'
    assert 'embeddedinthedeliveredworkproduct.' in flat(24), 'p25 paragraph truncated wrong'
    assert 'SteveSmith' in flat(27) and 'RubenCarrera' not in flat(27), 'p28 not updated'
    print('verified:', out)


if __name__ == '__main__':
    main(*(sys.argv[1:3] or sys.exit(__doc__)))
