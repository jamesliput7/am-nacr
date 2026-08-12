#!/bin/sh
# Rebuild the client PDF from the untouched original, in order.
#
#   1 fix_names     page 18 - Andrew Khoo, Jonathan Bain (in-place, document's own font)
#   2 add_gate_m4   pages 13-14 - fourth Phase-1 gate on the gate row and in the caption
#   3 pages/build   authors the three pages that need real layout, in WeasyPrint 69
#   4 splice        inserts them and fixes footers, contents and bookmarks
#   5 module row    page 24 - vendor and utilities motions replace 13-week cash actuals
#
# Needs: pymupdf, weasyprint, fonttools.
set -e
cd "$(dirname "$0")"
python3 fix_names.py Nymbl_AM_NACR_original.pdf build/stage1.pdf
python3 add_gate_m4.py build/stage1.pdf build/stage2.pdf
( cd pages && python3 build.py )
python3 splice.py build/stage2.pdf build/stage3.pdf
python3 update_module_row.py build/stage3.pdf Nymbl_AM_NACR.pdf
rm -f build/stage1.pdf build/stage2.pdf build/stage3.pdf
echo "built Nymbl_AM_NACR.pdf"
