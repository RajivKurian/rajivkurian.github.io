#!/usr/bin/env python3
"""Draw the datapath and worked fixed-point example as editable SVG text."""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'assets/figures'


class Diagram:
    def __init__(self, width, height, title):
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img"><title>{escape(title)}</title>',
                      '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10" fill="#747d86"/></marker></defs>',
                      '<rect width="100%" height="100%" fill="#faf9f6"/>']

    def text(self, x, y, text, size=14, anchor='middle', color='#41484b'):
        self.parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="system-ui,sans-serif" font-size="{size}" fill="{color}">{escape(text)}</text>')

    def box(self, x, y, w, h, lines, color='#d8d4ca'):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#f5f1e8" stroke="{color}"/>')
        for i, line in enumerate(lines):
            self.text(x+w/2, y+h/2+(i-(len(lines)-1)/2)*20+5, line)

    def path(self, points, dashed=False):
        self.parts.append(f'<path d="{points}" fill="none" stroke="#747d86" stroke-width="1.5" marker-end="url(#arrow)"'+(' stroke-dasharray="5 4"' if dashed else '')+'/>')

    def save(self, name):
        (OUT/name).write_text('\n'.join(self.parts+['</svg>'])+'\n')


def pipeline():
    d=Diagram(780,575,'Eight quadratic rows and two cubic rows: table selection and Horner pipelines')
    d.box(210,15,350,75,['FP32 input x','Unpack: n = floor(x), f = x − n','Retain F fractional bits of f'])
    d.path('M385 90 V105 H5 V365 H20')
    d.path('M5 185 H20')
    d.text(24,97,'fraction f',anchor='start')
    d.path('M560 52 H760 V527 H560',True)
    d.text(736,115,'n')
    d.text(20,138,'Eight quadratics · two arithmetic stages',anchor='start',color='#1460aa')
    d.box(20,150,140,70,['Top 3 bits → j','Other F−3 bits','→ residual t'])
    d.box(185,150,120,70,['8-row table','a, b, c'])
    d.path('M160 185 H185')
    d.box(335,150,155,70,['s = a·t + b','round → register'],color='#1460aa')
    d.box(545,150,155,70,['y = s·t + c','round → register'],color='#1460aa')
    d.path('M305 185 H335');d.path('M490 185 H545')
    d.text(517,174,'s',size=12)
    d.text(517,237,'carry t, c',size=12)
    d.path('M90 220 V265 H412 V220')
    d.text(237,257,'t: F−3 bits',size=13)
    d.path('M700 185 H730 V470 H385 V490')
    d.text(20,318,'Two cubics · three arithmetic stages',anchor='start',color='#c43c28')
    d.box(20,330,140,70,['Top 1 bit → j','Other F−1 bits','→ residual t'])
    d.box(185,330,120,70,['2-row table','a, b, c, d'])
    d.path('M160 365 H185')
    for x,expr in [(335,'s = a·t + b'),(465,'r = s·t + c'),(595,'y = r·t + d')]:
        d.box(x,330,110,70,[expr,'round → reg.'],color='#c43c28')
    d.path('M305 365 H335');d.path('M445 365 H465');d.path('M575 365 H595')
    d.text(453,419,'carry t, c, d',size=11)
    d.text(590,419,'carry t, d',size=11)
    d.path('M90 400 V445 H390 V400')
    d.text(235,437,'t: F−1 bits',size=13)
    d.path('M705 365 H730')
    d.box(210,490,350,70,['Reconstruct 2ⁿ·y; round and pack FP32','n travels with the corresponding input'])
    d.save('polynomial-pipelines.svg')


def multiply_add():
    d=Diagram(780,485,'Fixed-point multiply-add: integer multiplication, scale alignment, rounding and register')
    d.box(20,15,145,65,['a = 3 × 2⁻⁵','stored: 11 (2 bits)'])
    d.box(195,15,145,65,['t = 3 × 2⁻²','stored: 11 (2 bits)'])
    d.box(490,15,245,65,['b = 5 × 2⁻⁴','stored: 101 (3 bits)'])
    d.path('M92 80 V100 H180 V115');d.path('M267 80 V100 H180')
    d.box(60,115,240,65,['2 × 2-bit integer multiply','3 × 3 = 9; scale 2⁻⁷'])
    d.path('M612 80 V115')
    d.box(490,115,245,65,['Align b: append three zeros','101 → 101000 = 40; scale 2⁻⁷'])
    d.path('M180 180 V210 H385 V230');d.path('M612 180 V210 H385')
    d.box(260,230,250,65,['Add at common scale 2⁻⁷','9 + 40 = 49 → 0110001'])
    d.path('M385 295 V330')
    d.box(260,330,250,90,['Keep 0110; discard 001','guard 0 · sticky 1','No increment → 0110'],color='#1460aa')
    d.path('M510 362 H565')
    d.box(565,330,185,65,['4-bit register','6 × 2⁻⁴ = 0.375'],color='#1460aa')
    d.text(390,454,'Guard: first discarded bit. Sticky: OR of all bits below guard.',size=14)
    d.save('fixed-multiply-add.svg')


def coefficient_widths():
    import json
    designs=json.loads((OUT.parents[1]/'data/design-points.json').read_text())['designs']
    quad=next(x for x in designs if x['rows']==8 and x['degree']==2)
    cubic=next(x for x in designs if x['rows']==2 and x['degree']==3)
    d=Diagram(780,385,'Stored widths of first-row coefficients at the same quantization spacing')
    d.text(390,25,'Same scale 2⁻²⁰ · unsigned integers · low bits aligned',size=15)
    for power,top in [(1,65),(2,225)]:
        q=round(quad['coefficients'][power]*2**20)
        c=round(cubic['coefficients'][power]*2**20)
        d.text(20,top,f'c{power}: '+('linear coefficient' if power==1 else 'quadratic coefficient'),anchor='start',size=16)
        for value,y,label in [(q,top+25,'8 quadratics'),(c,top+75,'2 cubics')]:
            bits=format(value,'b'); extra=max(0,len(bits)-q.bit_length())
            d.text(20,y+17,label,anchor='start')
            d.text(20,y+35,f'stored integer {value:,}',size=12,anchor='start')
            for j,bit in enumerate(bits):
                x=245+(19-len(bits)+j)*22
                highlight=j<extra
                fill='#f5ddd5' if highlight else '#e4edf3'
                stroke='#c43c28' if highlight else '#a9b9c6'
                d.parts.append(f'<rect x="{x}" y="{y}" width="21" height="30" fill="{fill}" stroke="{stroke}"/>')
                d.text(x+10.5,y+21,bit,size=15,color='#a53023' if highlight else '#1460aa')
            d.text(680,y+21,f'{len(bits)} bits',anchor='start')
    d.text(390,375,'Highlighted cells: additional high bits needed by the larger cubic coefficient',size=13)
    d.save('coefficient-widths.svg')


def booth_multiply_add():
    d=Diagram(780,205,'A fused radix-4 Booth multiply-add')
    d.text(125,30,'Recode the narrower operand',size=14)
    d.path('M125 40 V70')
    d.box(15,70,220,95,['Radix-4 Booth recoding','Select 0, ±A or ±2A','Include sign corrections'])
    d.path('M235 118 H280')
    d.text(390,30,'Aligned coefficient',size=14)
    d.path('M390 40 V70')
    d.box(280,70,220,95,['Compress all rows','and the coefficient','to two rows'])
    d.path('M500 118 H545')
    d.box(545,70,220,95,['Final carry-propagate addition','Guard/sticky → rounding','Result register'])
    d.save('booth-multiply-add.svg')


if __name__=='__main__':
    pipeline();multiply_add();coefficient_widths();booth_multiply_add()
