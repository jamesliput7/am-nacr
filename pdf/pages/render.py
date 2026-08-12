# -*- coding: utf-8 -*-
"""Render an element list to a one-page PDF, calibrated against the source document.

Two problems this solves:

1. Baselines. CSS positions boxes, not baselines. Every text element declares the
   baseline it wants; we render, measure where it actually landed, and shift by the
   difference. The relationship is linear, so one correction pass is exact.
2. Letter-spacing. The chips and band labels in the source document are letter-spaced
   by an em value we can only estimate. Elements may declare a target width; we
   measure and adjust the spacing to hit it.

Also refuses to render text whose glyphs are missing from the extracted subsets --
WeasyPrint would silently fall back to a system font and the page would not match.
"""
import io
import pathlib
import sys

import pymupdf
from fontTools.ttLib import TTFont
from weasyprint import HTML

import template as T

FONT_FOR = {   # (family, weight, style) -> subset file
    ('Mont', 400, 'normal'): 'Montserrat.ttf',
    ('Mont', 700, 'normal'): 'Montserrat-Bold.ttf',
    ('Ral', 400, 'normal'): 'Raleway.ttf',
    ('Ral', 600, 'normal'): 'Raleway-Semi-Bold.ttf',
    ('Ral', 700, 'normal'): 'Raleway-Bold.ttf',
    ('Ral', 800, 'normal'): 'Raleway-Ultra-Bold.ttf',
    ('Ral', 400, 'italic'): 'Raleway-Oblique.ttf',
    ('Arw', 400, 'normal'): 'Arial.ttf',
}
FALLBACK = 'Arial.ttf'      # only reached for glyphs the primary family lacks
_cov = {}


def coverage(fn):
    if fn not in _cov:
        _cov[fn] = {chr(c) for c in TTFont(T.FONT_DIR / fn).getBestCmap()}
    return _cov[fn]


def check_glyphs(elements):
    problems = []
    for el in elements:
        if el['kind'] not in ('text', 'para', 'rich'):
            continue
        style = el.get('style', 'normal')
        for text, weight in el.get('runs', [(el.get('text', ''), el.get('weight', 400))]):
            fn = FONT_FOR.get((el['font'], weight, style))
            if fn is None:
                problems.append(f"no subset for {el['font']} {weight} {style}")
                continue
            allowed = coverage(fn) | (coverage(FALLBACK) if el.get('fallback') else set())
            missing = sorted(set(text) - allowed - {'\n'})
            if missing:
                problems.append(f"{el.get('id')}: {missing} missing from {fn} -- {text[:60]!r}")
    if problems:
        sys.exit('glyph check failed:\n  ' + '\n  '.join(problems))


_ascent = {}


def face_key(el):
    weight = el.get('weight')
    if weight is None:
        weight = el['runs'][0][1] if el.get('runs') else 400
    return (el['font'], weight, el.get('style', 'normal'))


def ascent_factor(key):
    """Fraction of font-size between an element's top edge and its first baseline."""
    if key not in _ascent:
        fam, weight, style = key
        probe, size, want = 'ee', 40.0, 400.0   # 'e' is in every extracted subset
        html = ('<!doctype html><meta charset="utf-8"><style>' + T.font_css() + T.BASE_CSS +
                f"</style><body><div class='abs t' style=\"left:50pt;top:{want}pt;"
                f"font-family:{fam};font-weight:{weight};font-style:{style};"
                f"font-size:{size}pt\">{probe}</div></body>")
        got = measure(HTML(string=html).write_pdf())
        base = next(v[0] for k, v in got.items() if k.startswith('ee'))
        _ascent[key] = (base - want) / size
    return _ascent[key]


def _pos(el, adj):
    """Left/right + top for an absolutely positioned element, from its baseline."""
    x = f"left:{el['x']}pt;" if 'x' in el else f"right:{el['right']}pt;"
    top = el['baseline'] - ascent_factor(face_key(el)) * el['size'] + adj
    return x + f"top:{top:.4f}pt;"


def build_html(elements, adj_base, adj_ls):
    parts = []
    for el in elements:
        k = el['kind']
        if k == 'rect':
            parts.append(f"<div class=abs style=\"left:{el['x']}pt;top:{el['y']}pt;"
                         f"width:{el['w']}pt;height:{el['h']}pt;background:{el['fill']}\"></div>")
        elif k == 'card':
            parts.append(
                f"<div class=abs style=\"left:{el['x']}pt;top:{el['y']}pt;width:{el['w']}pt;"
                f"height:{el['h']}pt;background:{T.CARD_BG};box-sizing:border-box;"
                f"border:0.75pt solid {T.CARD_BORDER};border-top:2pt solid {el['accent']}\"></div>")
        elif k == 'img':
            src = T.data_uri(T.FONT_DIR.parent / 'assets' / (el['src'] + '.png'))
            extra = 'border-radius:50%;' if el.get('round') else ''
            parts.append(f"<img class=abs style=\"left:{el['x']}pt;top:{el['y']}pt;"
                         f"width:{el['w']}pt;height:{el['h']}pt;{extra}\" src=\"{src}\">")
        elif k == 'text':
            ls = el.get('ls', 0) + adj_ls.get(el.get('id'), 0)
            align = f"text-align:{el['align']};width:{el['w']}pt;" if 'align' in el else ''
            parts.append(
                f"<div class='abs t' style=\"{_pos(el, adj_base.get(el.get('id'), 0))}"
                f"font-family:{el.get('stack') or el['font']};font-weight:{el['weight']};"
                f"font-style:{el.get('style', 'normal')};font-size:{el['size']}pt;"
                f"color:{el['color']};letter-spacing:{ls}em;{align}\">"
                f"{el['text']}</div>")
        elif k in ('para', 'rich'):
            runs = el.get('runs') or [(el['text'], el.get('weight', 400))]
            inner = ''.join(f"<span style='font-weight:{w}'>{t}</span>" for t, w in runs)
            parts.append(
                f"<div class='abs blk' style=\"{_pos(el, adj_base.get(el.get('id'), 0))}"
                f"width:{el['w']}pt;font-family:{el.get('stack') or el['font']};font-weight:400;"
                f"font-size:{el['size']}pt;color:{el['color']};"
                f"line-height:{el['lead'] / el['size']:.5f};"
                f"text-align:{el.get('align', 'left')}\">{inner}</div>")
    return ('<!doctype html><meta charset="utf-8"><style>' + T.font_css() + T.BASE_CSS
            + '</style><body>' + ''.join(parts) + '</body>')


def _norm(s):
    """Letter-spacing comes back as real spaces from extraction, so compare without them."""
    return ''.join(s.split())


def measure(pdf_bytes):
    """First-line baseline and width of each rendered text run, keyed by normalised text."""
    doc = pymupdf.open(stream=pdf_bytes, filetype='pdf')
    found = {}
    for blk in doc[0].get_text('dict')['blocks']:
        for ln in blk.get('lines', []):
            for sp in ln['spans']:
                key = _norm(sp['text'])
                if key and key not in found:
                    found[key] = (sp['origin'][1], sp['bbox'][2] - sp['bbox'][0])
    return found


def render(elements, out, passes=3):
    check_glyphs(elements)
    adj_base, adj_ls = {}, {}
    pdf = None
    for _ in range(passes):
        html = build_html(elements, adj_base, adj_ls)
        pdf = HTML(string=html, base_url=str(T.FONT_DIR.parent)).write_pdf()
        got = measure(pdf)
        moved = False
        for el in elements:
            if el['kind'] not in ('text', 'para', 'rich') or not el.get('id'):
                continue
            if not el.get('target_w'):
                continue
            probe = _norm(el.get('text', ''))[:24]
            hit = next((v for k, v in got.items() if probe and k.startswith(probe)), None)
            if not hit:
                continue
            _, width = hit
            if el.get('target_w'):
                n = max(len(el['text']) - 1, 1)
                dw = (el['target_w'] - width) / n / el['size']
                if abs(dw) > 0.0005:
                    adj_ls[el['id']] = adj_ls.get(el['id'], 0) + dw
                    moved = True
        if not moved:
            break
    pathlib.Path(out).write_bytes(pdf)
    return out
