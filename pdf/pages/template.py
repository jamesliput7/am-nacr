# -*- coding: utf-8 -*-
"""Shared page template for pages authored to match Nymbl_AM_NACR.pdf.

Every metric here was measured off the existing document (see MEASURED below), and
the type is set in the fonts extracted from that PDF, so generated pages sit in the
document without a visible seam. Text is positioned by baseline; `calibrate.py`
closes the residual gap between a requested baseline and where WeasyPrint puts it.
"""
import base64
import pathlib

FONT_DIR = pathlib.Path(__file__).parent / 'fonts'

# ── measured off the source PDF ───────────────────────────────────────────────
PAGE_W, PAGE_H = 595.28, 841.89          # A4
MARGIN_L, CONTENT_R = 51.0, 544.3
CONTENT_W = CONTENT_R - MARGIN_L         # 493.3

HEADER_TEXT = 'Prepared for Alvarez & Marsal · NACR'
HEADER_BASE, HEADER_SIZE, HEADER_COLOR = 28.02, 7.0, '#b6c0d4'
LOGO_X, LOGO_Y, LOGO_W, LOGO_H = 459.2, 51.0, 85.1, 22.5

CHIP_BASE, CHIP_SIZE = 62.61, 8.5
CHIP_NUM_COLOR, CHIP_LABEL_COLOR = '#8694b0', '#3442dc'
CHIP_LABEL_X = 70.1                      # label starts here; number sits at MARGIN_L

TITLE_SIZE, TITLE_COLOR = 29.0, '#001847'
TITLE_BASE_1, TITLE_LEAD = 98.24, 30.45

RULE_X, RULE_Y, RULE_W, RULE_H, RULE_COLOR = 51.0, 144.7, 40.5, 2.2, '#3442dc'

LEDE_BASE, LEDE_SIZE, LEDE_COLOR = 168.90, 11.5, '#4a5a7a'

FOOT_TEXT = 'Nymbl · Highly Confidential'
FOOT_BASE, FOOT_SIZE, FOOT_COLOR = 818.89, 7.0, '#9aa7bf'
PAGENO_BASE, PAGENO_SIZE, PAGENO_COLOR = 819.25, 8.0, '#001847'

# band + card system (page 18)
BULLET, BAND_LABEL_X, BAND_LABEL_SIZE = 6.8, 64.8, 8.5
BAND_TO_CARD = 8.33                      # band label baseline -> card top
CARD_TO_BAND = 16.47                     # card bottom -> next band label baseline
CARD_L, CARD_R = 58.0, 537.3
COL_L_R, COL_R_L = 294.1, 301.1          # two-column split
CARD_BG, CARD_BORDER = '#ffffff', '#e4ebf4'
AVATAR, AVATAR_TOP = 36.9, 9.2           # size, offset from card top
NAME_DY, ROLE_DY, BIO_DY, BIO_LEAD = 64.44, 81.41, 98.05, 12.5      # avatar cards
T_NAME_DY, T_ROLE_DY, T_BIO_DY = 23.63, 40.60, 57.24                # text-only cards
CARD_PAD_L = 10.8
NAME_SIZE, ROLE_SIZE, BIO_SIZE = 13.0, 8.4, 8.8
NAME_COLOR, BIO_COLOR = '#001847', '#4a5a7a'

NOTE_LABEL_SIZE, NOTE_SIZE, NOTE_LEAD = 7.5, 9.2, 14.26

# letter-spacing, in em; calibrated against the source document
LS_CHIP, LS_BAND, LS_NOTE = 0.176, 0.153, 0.175

FACES = [   # (family, weight, style, filename)
    ('Mont', 400, 'normal', 'Montserrat.ttf'),
    ('Mont', 700, 'normal', 'Montserrat-Bold.ttf'),
    ('Ral', 400, 'normal', 'Raleway.ttf'),
    ('Ral', 600, 'normal', 'Raleway-Semi-Bold.ttf'),
    ('Ral', 700, 'normal', 'Raleway-Bold.ttf'),
    ('Ral', 800, 'normal', 'Raleway-Ultra-Bold.ttf'),
    ('Ral', 400, 'italic', 'Raleway-Oblique.ttf'),
    # the source document sets its arrows in Arial because Raleway has no U+2192;
    # declaring it after Ral in a font stack reproduces that fallback
    ('Arw', 400, 'normal', 'Arial.ttf'),
]
ARROW_STACK = 'Ral, Arw'


def font_css():
    out = []
    for fam, weight, style, fn in FACES:
        b64 = base64.b64encode((FONT_DIR / fn).read_bytes()).decode()
        out.append(f"@font-face{{font-family:'{fam}';font-weight:{weight};font-style:{style};"
                   f"src:url(data:font/ttf;base64,{b64}) format('truetype')}}")
    return ''.join(out)


def data_uri(path):
    b64 = base64.b64encode(pathlib.Path(path).read_bytes()).decode()
    return f'data:image/png;base64,{b64}'


BASE_CSS = f"""
@page{{size:{PAGE_W}pt {PAGE_H}pt;margin:0}}
html,body{{margin:0;padding:0;background:#fff;-weasy-hyphens:none}}
body{{position:relative;width:{PAGE_W}pt;height:{PAGE_H}pt;overflow:hidden}}
.abs{{position:absolute;margin:0;padding:0}}
.t{{white-space:pre;line-height:1}}
.blk{{line-height:1}}
"""


def chrome(page_no, chip_num, chip_label):
    """Header, logo, section chip, title rule position, footer - identical on every page."""
    return [
        dict(id='hdr', kind='text', text=HEADER_TEXT, font='Mont', weight=400,
             size=HEADER_SIZE, color=HEADER_COLOR, baseline=HEADER_BASE, right=PAGE_W - 543.9),
        dict(id='logo', kind='img', src='logo', x=LOGO_X, y=LOGO_Y, w=LOGO_W, h=LOGO_H),
        dict(id='chipnum', kind='text', text=chip_num, font='Mont', weight=700, size=CHIP_SIZE,
             color=CHIP_NUM_COLOR, baseline=CHIP_BASE, x=MARGIN_L, ls=LS_CHIP),
        dict(id='chiplbl', kind='text', text=chip_label, font='Mont', weight=700, size=CHIP_SIZE,
             color=CHIP_LABEL_COLOR, baseline=CHIP_BASE, x=CHIP_LABEL_X, ls=LS_CHIP),
        dict(id='rule', kind='rect', x=RULE_X, y=RULE_Y, w=RULE_W, h=RULE_H, fill=RULE_COLOR),
        dict(id='foot', kind='text', text=FOOT_TEXT, font='Mont', weight=400, size=FOOT_SIZE,
             color=FOOT_COLOR, baseline=FOOT_BASE, x=MARGIN_L),
        dict(id='pageno', kind='text', text=str(page_no), font='Mont', weight=700,
             size=PAGENO_SIZE, color=PAGENO_COLOR, baseline=PAGENO_BASE,
             right=PAGE_W - CONTENT_R),
    ]


def title(lines):
    return [dict(id=f'title{i}', kind='text', text=t, font='Ral', weight=800, size=TITLE_SIZE,
                 color=TITLE_COLOR, baseline=TITLE_BASE_1 + i * TITLE_LEAD, x=MARGIN_L)
            for i, t in enumerate(lines)]


def card(x0, x1, y0, y1, accent, radius=0):
    """White card with a hairline border and a coloured top edge.

    `radius` is 0 (square corners, pages 18-22) unless a page needs the rounded
    corners the original page 27 reference cards use.
    """
    return dict(id=None, kind='card', x=x0, y=y0, w=x1 - x0, h=y1 - y0, accent=accent,
                radius=radius)
