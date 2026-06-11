#!/usr/bin/env python3
"""
Build the map corner panel: control descriptions arranged as the World Cup
progression bracket, sized to the white space in the top-right corner of the
A4 Nower map (140mm x 62mm).

The IOF symbol cells are extracted from the Purple Pen control descriptions
PDF, so the panel always matches the planned course.

Usage:
    python3 make_map_panel.py <control_descriptions.pdf> <out_basename>
Produces <out_basename>.png (600 dpi) and <out_basename>.pdf (140x62mm).

Requires: poppler-utils (pdftoppm), Pillow, numpy.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

DPI = 600
S = DPI / 25.4               # px per mm
W_MM, H_MM = 140, 62

CODES = ['11','12','13','14','15','16','21','22','23','24','25','26',
         '31','32','33','34','35','36','41','42','43','44','45','46',
         'QF1','QF2','QF3','QF4','SF1','SF2','F1']

COUNTRIES = {
    '11':'Brazil','12':'Argentina','13':'Mexico','14':'Uruguay','15':'USA','16':'Colombia',
    '21':'England','22':'France','23':'Spain','24':'Portugal','25':'Netherlands','26':'Germany',
    '31':'Morocco','32':'Senegal','33':'Belgium','34':'Japan','35':'S. Korea','36':'Australia',
    '41':'Switzerland','42':'Norway','43':'Turkey','44':'Austria','45':'Denmark','46':'Scotland',
}

GROUPS = {'A': ['11','12','13','14','15','16'], 'B': ['21','22','23','24','25','26'],
          'C': ['31','32','33','34','35','36'], 'D': ['41','42','43','44','45','46']}
GROUP_QF = {'A': 'QF1', 'B': 'QF2', 'C': 'QF3', 'D': 'QF4'}

GREEN, GOLDTXT = '#1a5c1a', '#8a6d00'
QF_FILL, QF_EDGE = '#fdf3e7', '#b56a25'
SF_FILL, SF_EDGE = '#f1f3f6', '#7e8794'
F_FILL,  F_EDGE  = '#fff7d9', '#c9a227'
ROW_TINT = '#eef4ee'

FONT_DIR = '/usr/share/fonts/truetype/liberation'


def mm(v):
    return int(round(v * S))


def extract_cells(pdf_path):
    """Render the Purple Pen descriptions PDF and crop the used symbol cells.

    Returns {code: [PIL.Image, ...]} of grayscale cell images in row order.
    The sheet is a fixed grid: 142px cells at 600dpi, table origin (583, 583),
    columns C..G in positions 0..4, points in position 5.
    """
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(['pdftoppm', '-png', '-r', str(DPI), '-f', '1', '-l', '1',
                        pdf_path, f'{td}/cd'], check=True)
        page = Image.open(next(Path(td).glob('cd*.png'))).convert('L')
    a = np.array(page)
    y0 = x0 = 583
    step = 142
    cells = {}
    for i, code in enumerate(CODES):
        ry = y0 + i * step
        imgs = []
        for j in range(5):
            cx = x0 + j * step
            probe = a[ry + 12:ry + step - 12, cx + 12:cx + step - 12]
            if (probe < 100).sum() > 60:
                imgs.append(page.crop((cx + 13, ry + 13, cx + step - 13, ry + step - 13)))
        cells[code] = imgs
    return cells


def cell_rgba(img, size_px):
    """Grayscale cell -> transparent-background black symbol at size_px."""
    img = img.resize((size_px, size_px), Image.LANCZOS)
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    out.putalpha(ImageOps.invert(img))
    return out


def build(cells):
    img = Image.new('RGB', (mm(W_MM), mm(H_MM)), 'white')
    d = ImageDraw.Draw(img)

    def font(px, bold=False):
        name = 'LiberationSans-Bold.ttf' if bold else 'LiberationSans-Regular.ttf'
        return ImageFont.truetype(f'{FONT_DIR}/{name}', px)

    f_title  = font(57, bold=True)
    f_hdr    = font(55, bold=True)
    f_code   = font(61, bold=True)
    f_ctry   = font(44)
    f_link   = font(45, bold=True)
    f_ko     = font(61, bold=True)
    f_pts    = font(52, bold=True)
    f_cap    = font(40)
    f_foot   = font(47)

    # outer frame
    d.rectangle([0, 0, mm(W_MM) - 1, mm(H_MM) - 1], outline=GREEN, width=mm(0.25))

    # title bar
    d.rectangle([mm(0.8), mm(0.8), mm(W_MM - 0.8), mm(4.8)], fill=GREEN)
    d.text((mm(W_MM / 2), mm(2.8)), 'WORLD CUP SCORE  —  GROUPS UNLOCK THE KNOCKOUTS',
           font=f_title, fill='white', anchor='mm')

    # geometry
    margin, gap = 1.5, 1.5
    col_w = (W_MM - 2 * margin - 3 * gap) / 4       # 33.1mm
    col_x = [margin + i * (col_w + gap) for i in range(4)]
    col_cx = [x + col_w / 2 for x in col_x]

    hdr_y0, hdr_y1 = 5.6, 9.4
    row_h, rows_y0 = 4.8, 9.4
    link_y0, link_y1 = 38.2, 41.0
    qf_y0, qf_y1 = 41.0, 46.8
    sf_y0, sf_y1 = 49.4, 56.6
    cell_mm = 4.2
    cpx = mm(cell_mm)

    def paste_syms(code, x_mm, yc_mm):
        for k, c in enumerate(cells[code]):
            sym = cell_rgba(c, cpx)
            img.paste(sym, (mm(x_mm + k * (cell_mm + 0.2)), mm(yc_mm) - cpx // 2), sym)

    for gi, (g, ctrl_list) in enumerate(GROUPS.items()):
        x = col_x[gi]
        # group header
        d.rectangle([mm(x), mm(hdr_y0), mm(x + col_w), mm(hdr_y1)], fill=GREEN)
        d.text((mm(x + col_w / 2), mm((hdr_y0 + hdr_y1) / 2)), f'GROUP {g} — 10 pts',
               font=f_hdr, fill='white', anchor='mm')
        # control rows
        for ri, code in enumerate(ctrl_list):
            y = rows_y0 + ri * row_h
            if ri % 2 == 0:
                d.rectangle([mm(x), mm(y), mm(x + col_w), mm(y + row_h)], fill=ROW_TINT)
            yc = y + row_h / 2
            d.text((mm(x + 1.2), mm(yc)), code, font=f_code, fill='black', anchor='lm')
            paste_syms(code, x + 6.2, yc)
            d.text((mm(x + 20.2), mm(yc)), COUNTRIES[code], font=f_ctry,
                   fill='#444444', anchor='lm')
        d.rectangle([mm(x), mm(rows_y0), mm(x + col_w), mm(rows_y0 + 6 * row_h)],
                    outline='#bbbbbb', width=2)

        # "any 5 of 6" connector
        cx = col_cx[gi]
        d.text((mm(cx), mm((link_y0 + link_y1) / 2 - 0.3)), 'any 5 of 6', font=f_link,
               fill=GREEN, anchor='mm')
        ay = link_y1 - 0.4
        d.polygon([(mm(cx - 0.9), mm(ay)), (mm(cx + 0.9), mm(ay)), (mm(cx), mm(ay + 0.8))],
                  fill=GREEN)

        # QF box
        qf = GROUP_QF[g]
        d.rounded_rectangle([mm(x + 2), mm(qf_y0), mm(x + col_w - 2), mm(qf_y1)],
                            radius=mm(0.8), fill=QF_FILL, outline=QF_EDGE, width=mm(0.3))
        yc = (qf_y0 + qf_y1) / 2
        d.text((mm(x + 3.4), mm(yc)), qf, font=f_ko, fill='#7a4a14', anchor='lm')
        paste_syms(qf, x + 11.4, yc)
        d.text((mm(x + col_w - 3.4), mm(yc)), '20', font=f_pts, fill='#7a4a14', anchor='rm')

    # bracket elbows QF -> SF
    def elbow(x_from, x_to, y_top, y_mid, y_bot):
        d.line([mm(x_from), mm(y_top), mm(x_from), mm(y_mid)], fill='#4a5d4a', width=mm(0.3))
        d.line([mm(x_from), mm(y_mid), mm(x_to), mm(y_mid)], fill='#4a5d4a', width=mm(0.3))
        d.line([mm(x_to), mm(y_mid), mm(x_to), mm(y_bot)], fill='#4a5d4a', width=mm(0.3))

    sf1_cx = (col_cx[0] + col_cx[1]) / 2
    sf2_cx = (col_cx[2] + col_cx[3]) / 2
    for src, dst in [(col_cx[0], sf1_cx), (col_cx[1], sf1_cx),
                     (col_cx[2], sf2_cx), (col_cx[3], sf2_cx)]:
        elbow(src, dst, qf_y1, (qf_y1 + sf_y0) / 2, sf_y0)

    # SF1 / FINAL / SF2 row
    def ko_box(x0, x1, fill, edge, label, code, pts, caption, label_col, sym_x):
        d.rounded_rectangle([mm(x0), mm(sf_y0), mm(x1), mm(sf_y1)], radius=mm(0.8),
                            fill=fill, outline=edge, width=mm(0.3))
        yc = sf_y0 + 2.6
        d.text((mm(x0 + 1.6), mm(yc)), label, font=f_ko, fill=label_col, anchor='lm')
        paste_syms(code, x0 + sym_x, yc)
        d.text((mm(x1 - 1.6), mm(yc)), pts, font=f_pts, fill=label_col, anchor='rm')
        d.text((mm((x0 + x1) / 2), mm(sf_y1 - 1.4)), caption, font=f_cap,
               fill='#555555', anchor='mm')

    ko_box(sf1_cx - 17, sf1_cx + 17, SF_FILL, SF_EDGE, 'SF1', 'SF1', '30',
           'needs QF1 + QF2 scored', '#3f4854', 15.0)
    ko_box(sf2_cx - 17, sf2_cx + 17, SF_FILL, SF_EDGE, 'SF2', 'SF2', '30',
           'needs QF3 + QF4 scored', '#3f4854', 13.0)
    ko_box(W_MM / 2 - 14.5, W_MM / 2 + 14.5, F_FILL, F_EDGE, 'F1  FINAL', 'F1', '50',
           'needs SF1 + SF2 scored', GOLDTXT, 16.0)

    # SF -> Final arrows
    ym = sf_y0 + 2.6
    for x_from, x_to in [(sf1_cx + 17, W_MM / 2 - 14.5), (sf2_cx - 17, W_MM / 2 + 14.5)]:
        d.line([mm(x_from), mm(ym), mm(x_to), mm(ym)], fill='#4a5d4a', width=mm(0.3))
        tip = 1 if x_to > x_from else -1
        d.polygon([(mm(x_to), mm(ym)), (mm(x_to - tip * 0.9), mm(ym - 0.7)),
                   (mm(x_to - tip * 0.9), mm(ym + 0.7))], fill='#4a5d4a')

    # footer
    d.text((mm(W_MM / 2), mm(59.3)),
           'Locked knockout controls score 0  ·  qualify first, then punch  ·  '
           'max 430 pts  ·  over 60 min: −1 pt per 2 sec',
           font=f_foot, fill='#333333', anchor='mm')

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
