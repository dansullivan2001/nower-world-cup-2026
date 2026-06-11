#!/usr/bin/env python3
"""
Build the map corner panel: control descriptions arranged as the World Cup
progression bracket, sized for the white space in the top-right corner of the
A4 Nower map (140mm x 46mm).

The IOF symbol cells are extracted from the Purple Pen control descriptions
PDF, so the panel always matches the planned course. Country flags are drawn
as simplified shapes (recognisable at ~3.5mm).

Bracket: QFs 19/29/39/49 unlock with 5 of 6 from groups A/B/C/D.
SF 79 needs 19+39 (A+C half), SF 89 needs 29+49 (B+D half), Final 99 needs
79+89. Group columns are laid out A, C, B, D so bracket lines don't cross.

Usage:
    python3 make_map_panel.py <control_descriptions.pdf> <out_basename>
Produces <out_basename>.png (600 dpi) and <out_basename>.pdf (140x46mm).

Requires: poppler-utils (pdftoppm), Pillow, numpy, img2pdf.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

DPI = 600
S = DPI / 25.4               # px per mm
W_MM, H_MM = 140, 46

CODES = ['11','12','13','14','15','16','21','22','23','24','25','26',
         '31','32','33','34','35','36','41','42','43','44','45','46',
         '19','29','39','49','79','89','99']

COUNTRIES = {
    '11':'Brazil','12':'Argentina','13':'Mexico','14':'Uruguay','15':'USA','16':'Colombia',
    '21':'England','22':'France','23':'Spain','24':'Portugal','25':'Netherlands','26':'Germany',
    '31':'Morocco','32':'Senegal','33':'Belgium','34':'Japan','35':'S. Korea','36':'Australia',
    '41':'Switzerland','42':'Norway','43':'Turkey','44':'Austria','45':'Denmark','46':'Scotland',
}

GROUPS = {'A': ['11','12','13','14','15','16'], 'B': ['21','22','23','24','25','26'],
          'C': ['31','32','33','34','35','36'], 'D': ['41','42','43','44','45','46']}
GROUP_QF = {'A': '19', 'B': '29', 'C': '39', 'D': '49'}
COL_ORDER = ['A', 'C', 'B', 'D']      # A+C feed SF 79, B+D feed SF 89

GREEN, GOLDTXT = '#1a5c1a', '#8a6d00'
QF_FILL, QF_EDGE, QF_TXT = '#fdf3e7', '#b56a25', '#7a4a14'
SF_FILL, SF_EDGE, SF_TXT = '#f1f3f6', '#7e8794', '#3f4854'
F_FILL,  F_EDGE  = '#fff7d9', '#c9a227'
ROW_TINT = '#eef4ee'
LINE = '#4a5d4a'

FONT_DIR = '/usr/share/fonts/truetype/liberation'


def mm(v):
    return int(round(v * S))


# ---------------------------------------------------------------------------
# Symbol extraction from the Purple Pen descriptions sheet
# ---------------------------------------------------------------------------

def extract_cells(pdf_path):
    """Render the descriptions PDF and crop the used symbol cells per control.

    The sheet is a fixed 142px grid at 600dpi with table origin (583, 583).
    Rows whose code cell (column 2) is empty (e.g. the start triangle) are
    skipped; remaining rows are assigned to CODES in order.
    Returns {code: [PIL.Image, ...]}.
    """
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(['pdftoppm', '-png', '-r', str(DPI), '-f', '1', '-l', '1',
                        pdf_path, f'{td}/cd'], check=True)
        page = Image.open(next(Path(td).glob('cd*.png'))).convert('L')
    a = np.array(page)
    x0, y0, step = 583, 583, 142
    n_rows = (a.shape[0] - y0) // step

    def cell_used(ry, cx):
        probe = a[ry + 12:ry + step - 12, cx + 12:cx + step - 12]
        return (probe < 100).sum() > 60

    cells, idx = {}, 0
    for i in range(n_rows):
        ry = y0 + i * step
        if idx >= len(CODES):
            break
        if not cell_used(ry, 441):          # no code -> start/finish row
            continue
        imgs = []
        for j in range(5):                  # symbol columns C..G
            cx = x0 + j * step
            if cell_used(ry, cx):
                imgs.append(page.crop((cx + 13, ry + 13, cx + step - 13, ry + step - 13)))
        cells[CODES[idx]] = imgs
        idx += 1
    if idx != len(CODES):
        raise SystemExit(f'Expected {len(CODES)} control rows, found {idx}')
    return cells


def cell_rgba(img, size_px):
    """Grayscale cell -> transparent-background black symbol at size_px."""
    img = img.resize((size_px, size_px), Image.LANCZOS)
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    out.putalpha(ImageOps.invert(img))
    return out


# ---------------------------------------------------------------------------
# Simplified country flags (drawn; recognisable at ~3.5mm wide)
# ---------------------------------------------------------------------------

def draw_flag(country, w, h):
    f = Image.new('RGB', (w, h), 'white')
    d = ImageDraw.Draw(f)

    def hbands(*cols, weights=None):
        weights = weights or [1] * len(cols)
        tot, y = sum(weights), 0
        for c, wt in zip(cols, weights):
            y2 = y + h * wt / tot
            d.rectangle([0, int(y), w, int(y2)], fill=c)
            y = y2

    def vbands(*cols, weights=None):
        weights = weights or [1] * len(cols)
        tot, x = sum(weights), 0
        for c, wt in zip(cols, weights):
            x2 = x + w * wt / tot
            d.rectangle([int(x), 0, int(x2), h], fill=c)
            x = x2

    def star(cx, cy, r, col):
        import math
        pts = []
        for k in range(10):
            ang = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.4
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        d.polygon(pts, fill=col)

    def nordic(bg, cross, fimbr=None, cw=0.18):
        d.rectangle([0, 0, w, h], fill=bg)
        cx, cwid = int(w * 0.36), max(2, int(h * cw))
        if fimbr:
            d.rectangle([0, h // 2 - int(cwid * 1.8), w, h // 2 + int(cwid * 1.8)], fill=fimbr)
            d.rectangle([cx - int(cwid * 1.8), 0, cx + int(cwid * 1.8), h], fill=fimbr)
        d.rectangle([0, h // 2 - cwid, w, h // 2 + cwid], fill=cross)
        d.rectangle([cx - cwid, 0, cx + cwid, h], fill=cross)

    c = country
    if c == 'Brazil':
        d.rectangle([0, 0, w, h], fill='#009739')
        d.polygon([(w//2, int(h*0.12)), (int(w*0.88), h//2), (w//2, int(h*0.88)),
                   (int(w*0.12), h//2)], fill='#FEDD00')
        r = int(h * 0.22)
        d.ellipse([w//2 - r, h//2 - r, w//2 + r, h//2 + r], fill='#012169')
    elif c == 'Argentina':
        hbands('#75AADB', 'white', '#75AADB')
        r = int(h * 0.16)
        d.ellipse([w//2 - r, h//2 - r, w//2 + r, h//2 + r], fill='#FCBF49')
    elif c == 'Mexico':
        vbands('#006341', 'white', '#C8102E')
        r = int(h * 0.14)
        d.ellipse([w//2 - r, h//2 - r, w//2 + r, h//2 + r], fill='#8a6d3b')
    elif c == 'Uruguay':
        hbands(*(['white', '#0038A8'] * 4 + ['white']))
        d.rectangle([0, 0, int(w * 0.4), int(h * 5 / 9)], fill='white')
        r = int(h * 0.16)
        d.ellipse([int(w*0.2) - r, int(h*0.28) - r, int(w*0.2) + r, int(h*0.28) + r],
                  fill='#FCBF49')
    elif c == 'USA':
        hbands(*(['#B31942', 'white'] * 3 + ['#B31942']))
        d.rectangle([0, 0, int(w * 0.45), int(h * 4 / 7)], fill='#0A3161')
    elif c == 'Colombia':
        hbands('#FCD116', '#003893', '#CE1126', weights=[2, 1, 1])
    elif c == 'England':
        d.rectangle([0, 0, w, h], fill='white')
        cw_ = max(2, int(h * 0.16))
        d.rectangle([0, h//2 - cw_, w, h//2 + cw_], fill='#C8102E')
        d.rectangle([w//2 - cw_, 0, w//2 + cw_, h], fill='#C8102E')
    elif c == 'France':
        vbands('#0055A4', 'white', '#EF4135')
    elif c == 'Spain':
        hbands('#AA151B', '#F1BF00', '#AA151B', weights=[1, 2, 1])
    elif c == 'Portugal':
        vbands('#046A38', '#DA291C', weights=[2, 3])
        r = int(h * 0.2)
        cx = int(w * 0.4)
        d.ellipse([cx - r, h//2 - r, cx + r, h//2 + r], outline='#FFE900', width=max(2, r//3))
    elif c == 'Netherlands':
        hbands('#AE1C28', 'white', '#21468B')
    elif c == 'Germany':
        hbands('black', '#DD0000', '#FFCC00')
    elif c == 'Morocco':
        d.rectangle([0, 0, w, h], fill='#C1272D')
        star(w // 2, h // 2, h * 0.32, '#006233')
    elif c == 'Senegal':
        vbands('#00853F', '#FDEF42', '#E31B23')
        star(w // 2, h // 2, h * 0.22, '#00853F')
    elif c == 'Belgium':
        vbands('black', '#FDDA24', '#EF3340')
    elif c == 'Japan':
        d.rectangle([0, 0, w, h], fill='white')
        r = int(h * 0.3)
        d.ellipse([w//2 - r, h//2 - r, w//2 + r, h//2 + r], fill='#BC002D')
    elif c == 'S. Korea':
        d.rectangle([0, 0, w, h], fill='white')
        r = int(h * 0.28)
        d.pieslice([w//2 - r, h//2 - r, w//2 + r, h//2 + r], 180, 360, fill='#CD2E3A')
        d.pieslice([w//2 - r, h//2 - r, w//2 + r, h//2 + r], 0, 180, fill='#0047A0')
    elif c == 'Australia':
        d.rectangle([0, 0, w, h], fill='#012169')
        d.rectangle([0, 0, w // 2, h // 2], fill='#012169')
        cw_ = max(1, int(h * 0.07))
        d.line([0, 0, w // 2, h // 2], fill='white', width=cw_ * 2)
        d.line([w // 2, 0, 0, h // 2], fill='white', width=cw_ * 2)
        d.rectangle([w // 4 - cw_, 0, w // 4 + cw_, h // 2], fill='white')
        d.rectangle([0, h // 4 - cw_, w // 2, h // 4 + cw_], fill='white')
        d.rectangle([w // 4 - cw_ // 2, 0, w // 4 + cw_ // 2, h // 2], fill='#E4002B')
        d.rectangle([0, h // 4 - cw_ // 2, w // 2, h // 4 + cw_ // 2], fill='#E4002B')
        for sx, sy in [(0.75, 0.2), (0.65, 0.5), (0.85, 0.55), (0.75, 0.8), (0.25, 0.75)]:
            star(w * sx, h * sy, h * 0.09, 'white')
    elif c == 'Switzerland':
        d.rectangle([0, 0, w, h], fill='#DA291C')
        cw_ = max(2, int(h * 0.13))
        cx, cy, arm = w // 2, h // 2, int(h * 0.3)
        d.rectangle([cx - cw_, cy - arm, cx + cw_, cy + arm], fill='white')
        d.rectangle([cx - arm, cy - cw_, cx + arm, cy + cw_], fill='white')
    elif c == 'Norway':
        nordic('#BA0C2F', '#00205B', fimbr='white', cw=0.12)
    elif c == 'Turkey':
        d.rectangle([0, 0, w, h], fill='#E30A17')
        r = int(h * 0.28)
        cx, cy = int(w * 0.42), h // 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill='white')
        d.ellipse([cx - r + int(r*0.55), cy - int(r*0.8), cx + r + int(r*0.3),
                   cy + int(r*0.8)], fill='#E30A17')
        star(int(w * 0.68), cy, h * 0.14, 'white')
    elif c == 'Austria':
        hbands('#EF3340', 'white', '#EF3340')
    elif c == 'Denmark':
        nordic('#C8102E', 'white', cw=0.14)
    elif c == 'Scotland':
        d.rectangle([0, 0, w, h], fill='#005EB8')
        lw = max(2, int(h * 0.18))
        d.line([0, 0, w, h], fill='white', width=lw)
        d.line([w, 0, 0, h], fill='white', width=lw)
    return f


# ---------------------------------------------------------------------------
# Panel layout (compact: 140 x 46 mm)
# ---------------------------------------------------------------------------

def build(cells):
    img = Image.new('RGB', (mm(W_MM), mm(H_MM)), 'white')
    d = ImageDraw.Draw(img)

    def font(px, bold=False):
        name = 'LiberationSans-Bold.ttf' if bold else 'LiberationSans-Regular.ttf'
        return ImageFont.truetype(f'{FONT_DIR}/{name}', px)

    f_title = font(46, bold=True)
    f_note  = font(38, bold=True)
    f_hdr   = font(44, bold=True)
    f_code  = font(48, bold=True)
    f_ctry  = font(36)
    f_link  = font(36, bold=True)
    f_ko    = font(48, bold=True)
    f_pts   = font(44, bold=True)
    f_cap   = font(32)

    d.rectangle([0, 0, mm(W_MM) - 1, mm(H_MM) - 1], outline=GREEN, width=mm(0.25))

    # title bar with the key rules inline
    d.rectangle([mm(0.7), mm(0.7), mm(W_MM - 0.7), mm(3.9)], fill=GREEN)
    d.text((mm(2.0), mm(2.3)), 'WORLD CUP SCORE', font=f_title, fill='white', anchor='lm')
    d.text((mm(W_MM - 2.0), mm(2.3)),
           'locked knockouts score 0 — qualify first  ·  max 430  ·  late: −1pt / 2 sec',
           font=f_note, fill='#ffe9a8', anchor='rm')

    margin, gap = 1.2, 1.4
    col_w = (W_MM - 2 * margin - 3 * gap) / 4
    col_x = [margin + i * (col_w + gap) for i in range(4)]
    col_cx = [x + col_w / 2 for x in col_x]

    hdr_y0, hdr_y1 = 4.3, 7.3
    rows_y0, row_h = 7.3, 3.9
    link_y0, link_y1 = 30.7, 32.9
    qf_y0, qf_y1 = 32.9, 37.5
    sf_y0, sf_y1 = 39.2, 45.3
    cell_mm = 3.4
    cpx = mm(cell_mm)
    flag_w, flag_h = 3.6, 2.4

    def paste_syms(code, x_mm, yc_mm):
        for k, c in enumerate(cells[code]):
            sym = cell_rgba(c, cpx)
            img.paste(sym, (mm(x_mm + k * (cell_mm + 0.2)), mm(yc_mm) - cpx // 2), sym)

    for gi, g in enumerate(COL_ORDER):
        x = col_x[gi]
        d.rectangle([mm(x), mm(hdr_y0), mm(x + col_w), mm(hdr_y1)], fill=GREEN)
        d.text((mm(x + col_w / 2), mm((hdr_y0 + hdr_y1) / 2)), f'GROUP {g} — 10 pts',
               font=f_hdr, fill='white', anchor='mm')
        for ri, code in enumerate(GROUPS[g]):
            y = rows_y0 + ri * row_h
            if ri % 2 == 0:
                d.rectangle([mm(x), mm(y), mm(x + col_w), mm(y + row_h)], fill=ROW_TINT)
            yc = y + row_h / 2
            d.text((mm(x + 1.0), mm(yc)), code, font=f_code, fill='black', anchor='lm')
            paste_syms(code, x + 5.6, yc)
            flag = draw_flag(COUNTRIES[code], mm(flag_w), mm(flag_h))
            fy = mm(yc) - mm(flag_h) // 2
            img.paste(flag, (mm(x + 17.2), fy))
            d.rectangle([mm(x + 17.2), fy, mm(x + 17.2) + flag.width,
                         fy + flag.height], outline='#999999', width=2)
            d.text((mm(x + 21.6), mm(yc)), COUNTRIES[code], font=f_ctry,
                   fill='#444444', anchor='lm')
        d.rectangle([mm(x), mm(rows_y0), mm(x + col_w), mm(rows_y0 + 6 * row_h)],
                    outline='#bbbbbb', width=2)

        # "any 5 of 6" connector
        cx = col_cx[gi]
        d.text((mm(cx), mm((link_y0 + link_y1) / 2 - 0.25)), 'any 5 of 6', font=f_link,
               fill=GREEN, anchor='mm')
        ay = link_y1 - 0.35
        d.polygon([(mm(cx - 0.8), mm(ay)), (mm(cx + 0.8), mm(ay)), (mm(cx), mm(ay + 0.7))],
                  fill=GREEN)

        # QF box
        qf = GROUP_QF[g]
        d.rounded_rectangle([mm(x + 2), mm(qf_y0), mm(x + col_w - 2), mm(qf_y1)],
                            radius=mm(0.7), fill=QF_FILL, outline=QF_EDGE, width=mm(0.28))
        yc = (qf_y0 + qf_y1) / 2
        d.text((mm(x + 3.2), mm(yc)), qf, font=f_ko, fill=QF_TXT, anchor='lm')
        paste_syms(qf, x + 9.8, yc)
        d.text((mm(x + col_w - 3.2), mm(yc)), '20', font=f_pts, fill=QF_TXT, anchor='rm')

    # bracket elbows QF -> SF
    def elbow(x_from, x_to, y_top, y_mid, y_bot):
        wpx = mm(0.28)
        d.line([mm(x_from), mm(y_top), mm(x_from), mm(y_mid)], fill=LINE, width=wpx)
        d.line([mm(x_from), mm(y_mid), mm(x_to), mm(y_mid)], fill=LINE, width=wpx)
        d.line([mm(x_to), mm(y_mid), mm(x_to), mm(y_bot)], fill=LINE, width=wpx)

    sf1_cx = (col_cx[0] + col_cx[1]) / 2     # under groups A and C
    sf2_cx = (col_cx[2] + col_cx[3]) / 2     # under groups B and D
    for src, dst in [(col_cx[0], sf1_cx), (col_cx[1], sf1_cx),
                     (col_cx[2], sf2_cx), (col_cx[3], sf2_cx)]:
        elbow(src, dst, qf_y1, (qf_y1 + sf_y0) / 2, sf_y0)

    # SF 79 / FINAL 99 / SF 89 row
    def ko_box(x0, x1, fill, edge, label, code, pts, caption, label_col, sym_x):
        d.rounded_rectangle([mm(x0), mm(sf_y0), mm(x1), mm(sf_y1)], radius=mm(0.7),
                            fill=fill, outline=edge, width=mm(0.28))
        yc = sf_y0 + 2.1
        d.text((mm(x0 + 1.4), mm(yc)), label, font=f_ko, fill=label_col, anchor='lm')
        paste_syms(code, x0 + sym_x, yc)
        d.text((mm(x1 - 1.4), mm(yc)), pts, font=f_pts, fill=label_col, anchor='rm')
        d.text((mm((x0 + x1) / 2), mm(sf_y1 - 1.2)), caption, font=f_cap,
               fill='#555555', anchor='mm')

    ko_box(sf1_cx - 16, sf1_cx + 16, SF_FILL, SF_EDGE, '79  SEMI', '79', '30',
           'needs 19 + 39 scored', SF_TXT, 14.0)
    ko_box(sf2_cx - 16, sf2_cx + 16, SF_FILL, SF_EDGE, '89  SEMI', '89', '30',
           'needs 29 + 49 scored', SF_TXT, 14.0)
    ko_box(W_MM / 2 - 13.5, W_MM / 2 + 13.5, F_FILL, F_EDGE, '99  FINAL', '99', '50',
           'needs 79 + 89 scored', GOLDTXT, 14.6)

    # SF -> Final arrows
    ym = sf_y0 + 2.1
    for x_from, x_to in [(sf1_cx + 16, W_MM / 2 - 13.5), (sf2_cx - 16, W_MM / 2 + 13.5)]:
        d.line([mm(x_from), mm(ym), mm(x_to), mm(ym)], fill=LINE, width=mm(0.28))
        tip = 1 if x_to > x_from else -1
        d.polygon([(mm(x_to), mm(ym)), (mm(x_to - tip * 0.8), mm(ym - 0.6)),
                   (mm(x_to - tip * 0.8), mm(ym + 0.6))], fill=LINE)

    return img


def main():
    pdf_path, out_base = sys.argv[1], sys.argv[2]
    cells = extract_cells(pdf_path)
    img = build(cells)
    img.save(out_base + '.png', dpi=(DPI, DPI))
    import img2pdf
    with open(out_base + '.pdf', 'wb') as f:
        f.write(img2pdf.convert(out_base + '.png',
                                layout_fun=img2pdf.get_fixed_dpi_layout_fun((DPI, DPI))))
    print(f'Wrote {out_base}.png and {out_base}.pdf ({W_MM}x{H_MM}mm at {DPI}dpi)')


if __name__ == '__main__':
    main()
