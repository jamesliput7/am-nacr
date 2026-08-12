#!/usr/bin/env python3
"""Check the rebuilt client PDF. Run after build_pdf.sh."""
import re
import sys

import pymupdf

DIAGRAM_RECT = (80.6, 159.9, 514.7, 384.2)   # every gate page places its diagram here


def main(path):
    doc = pymupdf.open(path)
    flat = lambda i: ''.join(doc[i].get_text().split())
    results = []

    def chk(label, cond):
        results.append((label, bool(cond)))

    chk('28 pages', doc.page_count == 28)

    feet = []
    for page in doc:
        nums = [s['text'].strip() for blk in page.get_text('dict')['blocks']
                for ln in blk.get('lines', []) for s in ln['spans']
                if s['bbox'][1] > 800 and re.fullmatch(r'\d{1,2}', s['text'].strip())]
        feet.append(nums[0] if nums else None)
    chk('footer numbers match their position',
        feet[0] is None and feet[-1] is None
        and all(feet[i] == str(i + 1) for i in range(1, 27)))
    chk('contents references updated',
        [s['text'] for blk in doc[1].get_text('dict')['blocks'] for ln in blk.get('lines', [])
         for s in ln['spans'] if s['bbox'][2] > 520 and s['size'] > 9]
        == ['3', '5', '6', '13', '14', '16', '19', '21', '23', '25', '26', '27'])
    chk('no broken bookmarks', not [e for e in doc.get_toc() if e[2] < 1])
    chk('bookmarks for both new pages',
        {('Scope and roadmap, refreshed.', 18), ('The pod, carried into Phase 2.', 20)}
        <= {(t, p) for _, t, p in doc.get_toc()})
    chk('no dead links', not [l for pg in doc for l in pg.get_links() if l.get('page', 0) < 0])

    # page 13/14 - the fourth gate
    chk('p13 gate row has M1-M4', all(g in flat(12) for g in ('M1', 'M2', 'M3', 'M4')))
    chk('p14 caption names M4', 'M4scopeandroadmap' in flat(13))

    # page 18 - M4 gate page. Diagram text is rasterised, as on every other gate page,
    # so assert on the live text and on the diagram's placement instead.
    chk('p18 chip reads gate M4', 'DELIVERYGATES·M4' in flat(17).upper())
    chk('p18 description leads with M4', flat(17).count('M4·Scopeandroadmap,refreshed') == 1)
    chk('p18 diagram placed like the other gate pages',
        any(tuple(round(v, 1) for v in r) == DIAGRAM_RECT
            for x, *_ in doc[17].get_images(full=True) for r in doc[17].get_image_rects(x)))

    # page 19 - proposed team
    names = [s['text'] for blk in doc[18].get_text('dict')['blocks']
             for ln in blk.get('lines', []) for s in ln['spans'] if abs(s['size'] - 13.0) < 0.2]
    chk('p19 shows all nine cards in order',
        names == ['Martyn Mason', 'Ruben Carrera', 'Andros Haggins', 'Delivery Manager',
                  'AI Engineer', 'Cloud Architect', 'QA Engineer',
                  'Andrew Khoo', 'Jonathan Bain'])
    chk('p19 Ruben holds both titles', 'EngagementLead/SolutionArchitect' in flat(18))
    chk('p19 bands its Phase 2 additions', 'ADDEDFORPHASE2' in flat(18).upper())
    chk('p19 clears the footer', max(
        ln['bbox'][3] for blk in doc[18].get_text('dict')['blocks']
        for ln in blk.get('lines', []) if ln['bbox'][3] < 800) < 800)

    # page 20 - pod structure
    chk('p20 counts 4 then 6 roles', '4ROLES' in flat(19).upper() and '6ROLES' in flat(19).upper())
    chk('p20 marks 3 carried and 3 added',
        flat(19).count('Carriedover') == 3 and flat(19).count('AddedforPhase2') == 3)
    chk('p20 lists the Phase 2 additions',
        all(r in flat(19) for r in ('AIEngineer', 'QualityAssurance', 'CloudArchitect')))
    chk('p20 carries the also-at-the-table note',
        'ALSOATTHETABLE' in flat(19).upper() and 'ruben.carrera@nymbl.app' in doc[19].get_text())

    # page 24 - module sizing table
    chk('p24 first module is vendors and utilities',
        'VendorandUtilitiesFirst-DayMotions' in flat(23))
    chk('p24 keeps the tier and sizing',
        'Medium' in doc[23].get_text() and '~$200–275K' in doc[23].get_text())
    chk('p24 what-sizes-it text replaced',
        'Vendorresolution,thepre/post-petitionsplit' in flat(23)
        and 'Twojoinscarryit' not in flat(23))
    chk('no 13-week cash actuals anywhere',
        '13-Week' not in ''.join(p.get_text() for p in doc))

    # page 22 - indicative engagement structure
    chk('p22 Phase 1 scope reworded',
        'reliefcalculationflow' in flat(21).replace('-', '')
        and 'vendorandutilitiesmotions' in flat(21).lower())
    chk('p22 drops the 6-to-4-weeks aside and the 13-week use case',
        '6→4' not in flat(21) and '13-week' not in doc[21].get_text())
    chk('p22 names the Phase 1 exit deliverables',
        'updatedEngage2.0scope' in flat(21) and 'PlatformDevelopmentRoadmap' in flat(21))
    chk('p22 keeps its four rows and their commercials',
        all(v in doc[21].get_text() for v in ('$60K', '$190K', '$100K/mo', '3–5 modules/yr')))
    chk('p22 table clears the footer', max(
        ln['bbox'][3] for blk in doc[21].get_text('dict')['blocks']
        for ln in blk.get('lines', []) if ln['bbox'][3] < 800) < 760)

    # pages 12, 13 (x2), 14, 21 - the remaining vendors-and-utilities rewording
    chk('p12 Q8 answer reworded', 'VendorsandUtilities' in flat(11))
    chk('p13 intro paragraph reworded', 'VendorsandUtilities' in flat(12))
    chk('p13 Phase 1 box reworded and still has all three boxes',
        'flowforVendorsandUtilities' in flat(12) and 'EngageRollout' in flat(12))
    chk('p14 lede reworded', 'VendorsandUtilities' in flat(13))
    chk('p21 Phase 1 bullet reworded', 'VendorsandUtilities' in flat(20))
    chk('no "13-week cash flow use case" survives anywhere',
        not any('13-week\ncash flow use case' in p.get_text() or '13-week cash flow use case' in p.get_text()
                for p in doc))

    whole = ''.join(p.get_text() for p in doc)
    chk('misspelled names gone', 'Andrew Ku' not in whole and 'John Bain' not in whole)
    chk('no 13-week cash flow on the gate pages',
        '13-week' not in doc[17].get_text())

    for label, passed in results:
        print(('  PASS  ' if passed else '  FAIL  ') + label)
    failed = [l for l, p in results if not p]
    print(f'\n{len(results) - len(failed)}/{len(results)} checks passed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'Nymbl_AM_NACR.pdf'))
