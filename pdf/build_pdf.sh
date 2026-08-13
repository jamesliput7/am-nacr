#!/bin/sh
# Rebuild the client PDF from the untouched original, in order.
#
#   1 fix_names     page 18 - Andrew Khoo, Jonathan Bain (in-place, document's own font)
#   2 add_gate_m4   pages 13-14 - fourth Phase-1 gate on the gate row and in the caption
#   3 pages/build   authors the three pages that need real layout, in WeasyPrint 69
#   4 splice        inserts them and fixes footers, contents and bookmarks
#   5 replace_page  page 22 - re-authored so the longer Phase 1 scope can reflow
#   6 module row    page 24 - vendor and utilities motions replace 13-week cash actuals
#   7 13week phrase pages 12, 13 (x2), 14, 21 - remaining "13-week cash flow use case" mentions
#   8 gate wording  pages 16, 17 - M2/M3 caption text: "forecast computes"/"13-week forecast"
#   9 gate diagrams pages 16, 17 - the same two mentions, baked into the gate-diagram rasters
#  10 time & material pages 13, 21, 25, 28 - Phase 2 fixed fee -> time & material ($190K budgetary),
#                     IP Confirmation trailing sentence removed, Ruben Carrera -> Steve Smith (p28 only)
#  11 reference page  new page 28 - two more reference cards (Houlihan Lokey, eCapital) that didn't
#                     fit on page 27; closing page becomes 29
#
# Needs: pymupdf, weasyprint, fonttools.
set -e
cd "$(dirname "$0")"
python3 fix_names.py Nymbl_AM_NACR_original.pdf build/stage1.pdf
python3 add_gate_m4.py build/stage1.pdf build/stage2.pdf
( cd pages && python3 build.py )
python3 splice.py build/stage2.pdf build/stage3.pdf
python3 replace_page.py build/stage3.pdf build/stage4.pdf 22 pages/out/engagement_structure.pdf
python3 update_module_row.py build/stage4.pdf build/stage5.pdf
python3 fix_13week_phrase.py build/stage5.pdf build/stage6.pdf
python3 fix_gate_wording.py build/stage6.pdf build/stage7.pdf
python3 fix_gate_diagrams.py build/stage7.pdf build/stage8.pdf
python3 fix_time_and_material.py build/stage8.pdf build/stage9.pdf
python3 add_reference_page.py build/stage9.pdf Nymbl_AM_NACR.pdf
rm -f build/stage1.pdf build/stage2.pdf build/stage3.pdf build/stage4.pdf build/stage5.pdf build/stage6.pdf build/stage7.pdf build/stage8.pdf build/stage9.pdf
echo "built Nymbl_AM_NACR.pdf"
