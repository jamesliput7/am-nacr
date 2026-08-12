# -*- coding: utf-8 -*-
"""Author the three pages that bring the PDF in line with the HTML deck:

  m4_gate.pdf        new  - Phase-1 gate M4, mirroring the deck's M4 gate panel
  proposed_team.pdf  repl - the 9-role team, Phase 1 pod vs Phase 2 joiners
  pod_structure.pdf  new  - Phase 1 pod carried into Phase 2, mirroring the deck

Run: python3 build.py
"""
import pathlib

import render as R
import template as T

OUT = pathlib.Path(__file__).parent / 'out'
OUT.mkdir(exist_ok=True)

NAVY, ROYAL, TEAL, SLATE = '#001847', '#3442dc', '#028090', '#4a5a7a'
MUTED, ROWBG, GREEN = '#8694b0', '#f5f8fc', '#16735d'


def band(y_base, label, accent, target_w=None, idx=''):
    """Square bullet + letter-spaced band label, as on the source team page."""
    return [
        dict(id=None, kind='rect', x=T.MARGIN_L, y=y_base - 6.47,
             w=T.BULLET, h=T.BULLET, fill=accent),
        dict(id='band' + idx, kind='text', text=label, font='Mont', weight=700,
             size=T.BAND_LABEL_SIZE, color=NAVY, baseline=y_base,
             x=T.BAND_LABEL_X, ls=T.LS_BAND, target_w=target_w),
    ]


def avatar_card(x0, x1, top, accent, img, name, role, role_color, bio_lines, idx):
    cx = (x0 + x1) / 2
    w = x1 - x0
    els = [T.card(x0, x1, top, top + 122.4, accent),
           dict(id=None, kind='img', src=img, round=True, w=T.AVATAR, h=T.AVATAR,
                x=cx - T.AVATAR / 2, y=top + T.AVATAR_TOP),
           dict(id=f'nm{idx}', kind='text', text=name, font='Ral', weight=800,
                size=T.NAME_SIZE, color=T.NAME_COLOR, baseline=top + T.NAME_DY,
                x=x0, align='center', w=w),
           dict(id=f'rl{idx}', kind='text', text=role, font='Mont', weight=700,
                size=T.ROLE_SIZE, color=role_color, baseline=top + T.ROLE_DY,
                x=x0, align='center', w=w)]
    for i, line in enumerate(bio_lines):
        els.append(dict(id=f'bio{idx}{i}', kind='text', text=line, font='Ral', weight=400,
                        size=T.BIO_SIZE, color=T.BIO_COLOR,
                        baseline=top + T.BIO_DY + i * T.BIO_LEAD, x=x0, align='center', w=w))
    return els


def text_card(x0, x1, top, height, accent, name, role, bio_lines, idx):
    x = x0 + T.CARD_PAD_L
    els = [T.card(x0, x1, top, top + height, accent),
           dict(id=f'tn{idx}', kind='text', text=name, font='Ral', weight=800,
                size=T.NAME_SIZE, color=T.NAME_COLOR, baseline=top + T.T_NAME_DY, x=x),
           dict(id=f'tr{idx}', kind='text', text=role, font='Mont', weight=700,
                size=T.ROLE_SIZE, color=ROYAL, baseline=top + T.T_ROLE_DY, x=x)]
    for i, line in enumerate(bio_lines):
        els.append(dict(id=f'tb{idx}{i}', kind='text', text=line, font='Ral', weight=400,
                        size=T.BIO_SIZE, color=T.BIO_COLOR,
                        baseline=top + T.T_BIO_DY + i * T.BIO_LEAD, x=x))
    return els


def note(y_label, label, body, width=None, target_w=None):
    return [
        dict(id='notelbl', kind='text', text=label, font='Mont', weight=700,
             size=T.NOTE_LABEL_SIZE, color=ROYAL, baseline=y_label,
             x=T.MARGIN_L, ls=T.LS_NOTE, target_w=target_w),
        dict(id='notebody', kind='para', text=body, font='Ral', size=T.NOTE_SIZE,
             color=T.BIO_COLOR, baseline=y_label + T.NOTE_LEAD,
             x=T.MARGIN_L, w=width or T.CONTENT_W, lead=T.NOTE_LEAD),
    ]


# ══ page A · Phase-1 gate M4 ═══════════════════════════════════════════════════
def m4_gate(page_no):
    els = T.chrome(page_no, '06', 'PHASE-1 DELIVERY GATES · M4')
    els += T.title(['Scope and roadmap,', 'refreshed.'])
    els.append(dict(id=None, kind='img', src='diagram_m4',
                    x=80.6, y=159.9, w=434.1, h=224.3))
    els.append(dict(
        id='desc', kind='rich', font='Ral', size=9.0, color=T.BIO_COLOR,
        baseline=398.88, x=T.MARGIN_L, w=T.CONTENT_W, lead=13.05,
        runs=[('M4 · Scope and roadmap, refreshed (~week 4).', 700),
              (' Discovery and build findings fold back into two written deliverables: an updated '
               'Engage 2.0 scope, with the rebuild-versus-enhance boundary confirmed, the feature '
               'list settled, and testable acceptance criteria per feature; and a refined Platform '
               'Development Roadmap sequencing the vendor and utilities motions, the Engage 2.0 '
               'rollout, and the modules that follow. Both are issued as written deliverables, not '
               'verbal, and signed off by A&amp;M’s two product owners with the Managing Director '
               'sponsor. Done when the pair is accepted: the agreed basis for Phase 2 scope and '
               'price, so the rollout starts without scope drift.', 400)]))
    return R.render(els, OUT / 'm4_gate.pdf')


# ══ page B · Proposed Team (replaces the existing page) ════════════════════════
# Four bands now, so the "also at the table" note moves to the pod-structure page:
# a fourth band plus that note does not fit above the footer.
JOIN_COL_W = (T.CARD_R - T.CARD_L - 2 * 7.0) / 3


def proposed_team(page_no):
    els = T.chrome(page_no, '07', 'PROPOSED TEAM')
    els += T.title(['A lean, senior pod that', 'scales by track.'])
    els.append(dict(id='lede', kind='text', baseline=T.LEDE_BASE, x=T.MARGIN_L, font='Ral',
                    weight=400, size=T.LEDE_SIZE, color=T.LEDE_COLOR,
                    text='A deliberately lean, senior pod for Phase 1 that carries intact into Phase 2.'))

    els += band(196.17, 'PLATFORM CONSULTANT · OVER THE TOP', TEAL, 230.79, 'a')
    els += avatar_card(T.CARD_L, T.CARD_R, 204.5, TEAL, 'p18_248', 'Martyn Mason',
                       'Platform Consultant · over the top', TEAL,
                       ['Solution and domain coherence across all tracks, so the foundation stays reusable.'], 'mm')

    els += band(330.87, 'PHASE-1 DELIVERY POD', ROYAL, 132.31, 'b')
    els += avatar_card(T.CARD_L, T.COL_L_R, 339.2, ROYAL, 'p18_250', 'Ruben Carrera',
                       'Engagement Lead / Solution Architect', ROYAL,
                       ['Delivery ownership, milestones, and the A&amp;M',
                        'product-owner interface.'], 'rc')
    els += avatar_card(T.COL_R_L, T.CARD_R, 339.2, ROYAL, 'p18_251', 'Andros Haggins',
                       'Technical Architect', ROYAL,
                       ['Data and integration architecture; security and',
                        'isolation validation.'], 'ah')
    els += text_card(T.CARD_L, T.CARD_R, 467.6, 69.1, ROYAL, 'Delivery Manager', 'TBD',
                     ['Sprint cadence, dependencies, and status against the Phase-1 gates.'], 'dm')

    els += band(553.17, 'ADDED FOR PHASE 2', ROYAL, None, 'j')
    joiners = [
        ('AI Engineer', ['Agent patterns, extraction and', 'drafting, and evaluation.']),
        ('Cloud Architect', ['Azure infrastructure, isolation,', 'and AI routing.']),
        ('QA Engineer', ['Accuracy and regression harness;', 'golden-case tests.']),
    ]
    for i, (name, bio) in enumerate(joiners):
        x0 = T.CARD_L + i * (JOIN_COL_W + 7.0)
        els += text_card(x0, x0 + JOIN_COL_W, 561.5, 81.6, ROYAL, name, 'TBD', bio, f'j{i}')

    els += band(659.57, 'A&M · DAY-TO-DAY PRODUCT OWNERS', NAVY, 215.17, 'c')
    els += avatar_card(T.CARD_L, T.COL_L_R, 667.9, NAVY, 'p18_252', 'Andrew Khoo',
                       'NACR · leading this initiative', NAVY,
                       ['Day-to-day product owner, setting priorities and',
                        'requirements with SME input.'], 'ak')
    els += avatar_card(T.COL_R_L, T.CARD_R, 667.9, NAVY, 'p18_252', 'Jonathan Bain',
                       'Director', NAVY,
                       ['Day-to-day product owner alongside Andrew,',
                        'setting priorities and requirements.'], 'jb')
    return R.render(els, OUT / 'proposed_team.pdf')


# ══ page C · Pod Structure ═════════════════════════════════════════════════════
ROW_H, ROW_PITCH = 30.0, 35.0
HDR_DY, META_DY, ROW0_DY = 22.0, 35.5, 50.0


def pod_col(x0, x1, top, accent, phase, meta, roles, idx):
    """A phase column: header, meta line, then a two-line chip per role.

    Two lines because role titles and person names are both variable length; on one
    line the long ones collide.
    """
    height = ROW0_DY + (len(roles) - 1) * ROW_PITCH + ROW_H + 14
    inner_w = x1 - x0 - 2 * T.CARD_PAD_L
    els = [T.card(x0, x1, top, top + height, accent),
           dict(id=f'ph{idx}', kind='text', text=phase, font='Mont', weight=700, size=8.0,
                color=accent, baseline=top + HDR_DY, x=x0 + T.CARD_PAD_L, ls=T.LS_BAND),
           dict(id=f'mt{idx}', kind='text', text=meta, font='Mont', weight=700, size=7.4,
                color=MUTED, baseline=top + META_DY, x=x0 + T.CARD_PAD_L, ls=0.06)]
    for i, (name, sub, sub_color) in enumerate(roles):
        ry = top + ROW0_DY + i * ROW_PITCH
        els += [
            dict(id=None, kind='rect', x=x0 + T.CARD_PAD_L, y=ry, w=inner_w, h=ROW_H, fill=ROWBG),
            dict(id=None, kind='rect', x=x0 + T.CARD_PAD_L, y=ry, w=2.0, h=ROW_H, fill=accent),
            dict(id=f'rn{idx}{i}', kind='text', text=name, font='Mont', weight=700, size=7.8,
                 color=NAVY, baseline=ry + 12.6, x=x0 + T.CARD_PAD_L + 8.0),
            dict(id=f'rt{idx}{i}', kind='text', text=sub, font='Ral', weight=600, size=7.4,
                 color=sub_color, baseline=ry + 23.4, x=x0 + T.CARD_PAD_L + 8.0),
        ]
    return els, top + height


def pod_structure(page_no):
    els = T.chrome(page_no, '07', 'PROPOSED TEAM · POD STRUCTURE')
    els += T.title(['The pod, carried', 'into Phase 2.'])
    els.append(dict(id='lede', kind='text', baseline=T.LEDE_BASE, x=T.MARGIN_L, font='Ral',
                    weight=400, size=T.LEDE_SIZE, color=T.LEDE_COLOR,
                    text='Phase 1 runs a lean four-role pod that carries intact into Phase 2.'))

    top = 204.5
    left, bot_l = pod_col(
        T.CARD_L, T.COL_L_R, top, '#1a5fb4', 'PHASE 1 · DISCOVERY + BUILD',
        '4 WEEKS · $60K FIXED · 4 ROLES',
        [('Platform Consultant', 'Martyn Mason', SLATE),
         ('Engagement Lead / Solution Architect', 'Ruben Carrera', SLATE),
         ('Technical Architect', 'Andros Haggins', SLATE),
         ('Delivery Manager', 'TBD', MUTED)], 'L')
    right, bot_r = pod_col(
        T.COL_R_L, T.CARD_R, top, NAVY, 'PHASE 2 · ENGAGE ROLLOUT',
        '3 MONTHS · $190K FIXED · 6 ROLES',
        [('Solution Architect', 'Carried over · Ruben Carrera', GREEN),
         ('Technical Architect', 'Carried over · Andros Haggins', GREEN),
         ('Delivery Manager', 'Carried over', GREEN),
         ('AI Engineer', 'Added for Phase 2', ROYAL),
         ('Quality Assurance', 'Added for Phase 2', ROYAL),
         ('Cloud Architect', 'Added for Phase 2', ROYAL)], 'R')
    els += left + right

    els += note(max(bot_l, bot_r) + 19.4, 'ACROSS BOTH PHASES',
                'The Platform Consultant stays on across Phase 1 and Phase 2 for solution and '
                'domain coherence, alongside a NACR Managing Director as executive sponsor and '
                'A&amp;M’s two product owners. Ruben Carrera continues as Solution Architect and '
                'the Technical Architect and Delivery Manager continue unchanged, so no one has to '
                'relearn the domain between phases; the AI Engineer, quality assurance, and Cloud '
                'Architect join for the production build. Phase 3 scales the same pod by track.')

    els += [dict(id='alsolbl', kind='text', text='ALSO AT THE TABLE', font='Mont', weight=700,
                 size=T.NOTE_LABEL_SIZE, color=ROYAL, baseline=598.0, x=T.MARGIN_L,
                 ls=T.LS_NOTE, target_w=100.50),
            dict(id='alsobody', kind='para', font='Ral', size=T.NOTE_SIZE, color=T.BIO_COLOR,
                 baseline=598.0 + T.NOTE_LEAD, x=T.MARGIN_L, w=T.CONTENT_W, lead=T.NOTE_LEAD,
                 text='A NACR Managing Director as executive sponsor and domain authority, and a '
                      'Technical Solutions Architect for architecture validation. Solution '
                      'Architects and specialists scale in per track after the build. Point of '
                      'contact for this response: Ruben Carrera (ruben.carrera@nymbl.app). The '
                      'named team is available for the Stage-2 discovery sessions and can begin as '
                      'soon as an agreement is in place.')]
    return R.render(els, OUT / 'pod_structure.pdf')


if __name__ == '__main__':
    print(' ', m4_gate(18))
    print(' ', proposed_team(19))
    print(' ', pod_structure(20))
