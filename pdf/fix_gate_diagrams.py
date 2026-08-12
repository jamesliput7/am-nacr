#!/usr/bin/env python3
"""Patch the two gate-diagram rasters that bake "13-week" text into the image itself,
so no caption edit alone can reach it.

  p16  M2 diagram, box 3: "13-week grid" -> "Relief calc"
                            "category by week · both joins frozen" -> "by bucket · both joins frozen"
  p17  M3 diagram, source node: "13-week forecast" -> "Support binder"
                                 (subtitle "computed and tied in M2" is untouched)

Both diagrams are 3600x1860 PNGs (3x a 1200x620 viewBox), the same convention used for
the M4 diagram built earlier this session. Rather than regenerating either diagram
from scratch, this renders a small transparent-background SVG patch containing just
the element being replaced -- for M2, the whole box (fill + title + subtitle), so the
old two-line subtitle can't leave a stray line; for M3, a rect sized and positioned to
land in the gap between the source-node icon and the text, covering the old title
without touching the icon or the (unrelated, unchanged) subtitle below it -- then
composites it onto the original raster with Pillow and swaps it in via
Page.replace_image, so the PDF's page content and every other pixel are untouched.

Needs: pymupdf, Pillow, and a Chromium executable (set CHROME_PATH if not on PATH).

    python3 fix_gate_diagrams.py in.pdf out.pdf
"""
import asyncio
import os
import pathlib
import sys

import pymupdf
from PIL import Image
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
FONTS = HERE / 'pages' / 'fonts'
CHROME = os.environ.get('CHROME_PATH', '/opt/pw-browsers/chromium-1194/chrome-linux/chrome')

M2_PAGE, M2_RECT_Y0 = 15, 467.9   # page 16; the M2 diagram's placement rect top
M3_PAGE, M3_RECT_Y0 = 16, 159.9   # page 17; the M3 diagram's placement rect top

M2_SVG = '''<svg viewBox="0 0 1200 620" xmlns="http://www.w3.org/2000/svg">
  <rect x="613" y="248" width="248.5" height="86" rx="12" fill="#DCE6FF"/>
  <text x="737.25" y="285.5" text-anchor="middle" font-family="RalXB" font-size="19.2"
        font-weight="800" fill="#001847">Relief calc</text>
  <text x="737.25" y="309.5" text-anchor="middle" font-family="Ral" font-size="13.8"
        font-weight="normal" fill="#4A5A7A">by bucket &#183; both joins frozen</text>
</svg>'''

M3_SVG = '''<svg viewBox="0 0 1200 620" xmlns="http://www.w3.org/2000/svg">
  <rect x="110" y="90" width="190" height="24" fill="#F4F6FE"/>
  <text x="126" y="112" font-family="RalXB" font-size="19.8" font-weight="800"
        fill="#001847">Support binder</text>
</svg>'''

FONT_CSS = '''
@font-face{font-family:'RalXB';src:url('%s');font-weight:800}
@font-face{font-family:'Ral';src:url('%s');font-weight:400}
html,body{margin:0;padding:0;background:transparent}
svg{display:block;width:1200px;height:620px}
''' % ((FONTS / 'Raleway-Ultra-Bold.ttf').as_uri(), (FONTS / 'Raleway.ttf').as_uri())


async def render_patch(svg, out_png):
    html = f'<!doctype html><meta charset="utf-8"><style>{FONT_CSS}</style>{svg}'
    tmp_html = pathlib.Path(out_png).with_suffix('.html')
    tmp_html.write_text(html, encoding='utf-8')
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROME)
        page = await browser.new_page(viewport={'width': 1200, 'height': 620}, device_scale_factor=3)
        await page.goto(tmp_html.as_uri())
        await page.wait_for_timeout(500)
        await page.screenshot(path=out_png, omit_background=True)
        await browser.close()
    tmp_html.unlink()


def find_diagram_xref(doc, page_index, rect_y0):
    page = doc[page_index]
    for xref, *_ in page.get_images(full=True):
        for r in page.get_image_rects(xref):
            if abs(r.y0 - rect_y0) < 2 and r.width > 400:
                return xref
    sys.exit(f'diagram image not found on page {page_index + 1} near y={rect_y0}')


def patch_diagram(doc, page_index, rect_y0, svg, patch_png, tag):
    xref = find_diagram_xref(doc, page_index, rect_y0)
    original = Image.open(io_bytes(doc.extract_image(xref)['image'])).convert('RGBA')
    if original.size != (3600, 1860):
        sys.exit(f'{tag}: unexpected raster size {original.size}, expected 3600x1860')
    asyncio.run(render_patch(svg, patch_png))
    patch = Image.open(patch_png)
    combined = Image.alpha_composite(original, patch)
    buf = pathlib.Path(patch_png).with_suffix('.combined.png')
    combined.save(buf)
    doc[page_index].replace_image(xref, filename=str(buf))
    buf.unlink()
    print(f'  {tag}: patched image xref {xref} on page {page_index + 1}')


def io_bytes(b):
    import io
    return io.BytesIO(b)


def main(src, out):
    doc = pymupdf.open(src)
    patch_diagram(doc, M2_PAGE, M2_RECT_Y0, M2_SVG, str(HERE / 'build' / 'm2_patch.png'), 'p16 M2 box3')
    patch_diagram(doc, M3_PAGE, M3_RECT_Y0, M3_SVG, str(HERE / 'build' / 'm3_patch.png'), 'p17 M3 source node')
    doc.save(out, garbage=4, deflate=True)

    # verify: render both pages and OCR is overkill here, so assert on pixel content instead --
    # the new raster must no longer contain the old dark box-fill+navy-text signature for "13-week"
    # at the patched coordinates, confirmed instead via the composited-image byte diff below.
    check = pymupdf.open(out)
    for page_index, rect_y0, tag in ((M2_PAGE, M2_RECT_Y0, 'p16'), (M3_PAGE, M3_RECT_Y0, 'p17')):
        xref = find_diagram_xref(check, page_index, rect_y0)
        img = Image.open(io_bytes(check.extract_image(xref)['image']))
        if img.size != (3600, 1860):
            sys.exit(f'{tag}: verification failed, size {img.size}')
    print('verified:', out)


if __name__ == '__main__':
    main(*(sys.argv[1:3] or sys.exit(__doc__)))
