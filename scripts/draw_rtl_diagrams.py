"""Draw Part 4's circuit explanations from the recorded RTL structure."""
from draw_cost_diagrams import Diagram

BLUE, RUST, SLATE = '#1460aa', '#b65322', '#747d86'

def rule(d, x1,y1,x2,y2,color=SLATE,width=1.5):
    d.parts.append(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color}" stroke-width="{width}" fill="none"/>')

def flow():
    d=Diagram(850,235,'RTL synthesis, cell mapping, checked simulation and timing/power analysis')
    for x,w,title,detail in [(15,155,'Yosys','lower + simplify RTL'),(205,155,'ABC','map + size gates'),(395,155,'Mapped netlist','cells + connections'),(615,220,'OpenSTA','timing + activity power')]:
        d.box(x,55,w,65,[title,detail])
    for a,b in [(170,205),(360,395),(550,615)]:d.path(f'M{a} 87 H{b}')
    d.text(92,30,'SystemVerilog',size=14,color=BLUE)
    d.text(520,30,'ASAP7 Liberty: cell functions, area, delay and power',size=13)
    d.box(395,160,155,55,['Verilator','checked gate activity'],BLUE)
    d.path('M472 120 V160');d.path('M550 188 H725 V120')
    d.text(627,207,'VCD transitions',size=13,color=BLUE)
    d.save('rtl-tool-flow.svg')

def pipeline():
    d=Diagram(850,565,'Six register stages for coefficient lookup and the two polynomial multiply-adds')
    d.text(425,24,'Input: table address j and 18-bit local coordinate t',size=16)
    stages=[('Coefficient lookup','register a, b, c and t'),
            ('First Booth rows + b; compression; low-column addition','register two upper rows, carry/rounding information, t and c'),
            ('Complete first sum; apply its narrowing rule','register s: 15 or 16 bits; carry t and c'),
            ('Second Booth rows + c; compression; low-column addition','register two upper rows and carry/rounding information'),
            ('Complete second sum','register retained word and rounding information'),
            ('Apply final internal narrowing rule','register y: 25 bits and valid')]
    for i,lines in enumerate(stages):
        y=45+i*82
        d.box(135,y,580,58,lines,BLUE if i in [0,2,5] else '#d8d4ca')
        d.text(100,y+34,f'R{i+1}',size=15,color=SLATE)
        if i<5:d.path(f'M425 {y+58} V{y+82}')
    d.text(425,555,'One new input per cycle · FP32 reconstruction follows this block',size=14)
    d.save('rtl-six-stage-pipeline.svg')

def multiply_add():
    d=Diagram(850,300,'Booth product rows and the aligned addend share one carry-save reduction network')
    d.box(15,65,210,135,['Select 0, ±t, ±2t','shift each Booth digit','add sign corrections','include aligned b'],BLUE)
    d.path('M225 132 H270')
    d.box(270,80,185,105,['3:2 compressors','reduce to two rows','local sum/carry bits'])
    d.path('M455 132 H505')
    for y in [111,144]:rule(d,505,y,600,y,BLUE,4)
    d.text(552,76,'two upper rows',size=13)
    rule(d,610,83,610,175,RUST,5)
    d.text(610,202,'register cut',size=13,color=RUST)
    d.path('M615 132 H660')
    d.box(660,80,175,105,['Carry completion','+ narrowing','first result s'],BLUE)
    d.text(425,250,'Each compressor preserves value: three rows → sum row + shifted carry row.',size=15)
    d.text(425,279,'The low-column carry and rounding information cross the register cut too.',size=13)
    d.save('rtl-fused-multiply-add.svg')

def constants():
    d=Diagram(850,380,'Traced constant coefficient bits simplify lookup, register banks and consuming arithmetic')
    d.text(425,24,'Traced 128-row table: c[22] = 1 and a[9] = 0 in every row',size=16)
    d.box(15,60,165,80,['ROM column c[22]','1  1  1  …  1'],BLUE)
    d.path('M180 100 H230')
    d.box(230,60,220,80,['c0[22], c1[22], c2[22]','all become literal 1'],BLUE)
    d.path('M450 100 H500')
    d.box(500,60,335,80,['Compressor inputs (1, 0, 0)','sum = 1, carry = 0'],BLUE)
    d.text(425,164,'Three carried c bits need no flip-flops; this compressor becomes constants.',size=14)
    d.box(15,205,165,75,['ROM column a[9]','0  0  0  …  0'],BLUE)
    d.path('M180 242 H230')
    d.box(230,205,220,75,['Top Booth triple: 000','magnitude = 0'],BLUE)
    d.path('M450 242 H500')
    d.box(500,205,335,75,['No variable top-digit multiple','to select or compress'],BLUE)
    d.text(425,322,'A refit with A = 512 makes a[9] variable in one row.',size=15,color=RUST)
    d.text(425,350,'That restores a carried bit and a live top-digit arithmetic path.',size=14,color=RUST)
    d.save('rtl-coefficient-constants.svg')

def low_columns():
    d=Diagram(850,425,'Resolve the low columns before storage while preserving carry and rounding information')
    d.text(425,25,'Example: discard four low columns from the final two rows',size=16)
    d.text(215,65,'Store both full rows',size=17,color=SLATE)
    d.text(650,65,'Resolve the low columns first',size=17,color=BLUE)
    d.box(40,90,350,100,['U = 0010 | 1101','V = 0001 | 1111','register 16 bits'])
    d.box(460,90,350,100,['1101 + 1111 = 1 | 1100','carry = 1 · guard = 1 · sticky = 1','register upper rows + these 3 bits'],BLUE)
    d.path('M215 190 V235');d.path('M635 190 V235')
    d.box(40,235,350,75,['After register: add full rows','0100 | 1100 → RNE → 0101'])
    d.box(460,235,350,75,['After register: 0010 + 0001 + carry','0100 → RNE increment → 0101'],BLUE)
    d.text(215,350,'16 stored bits',size=15)
    d.text(635,350,'4 + 4 + 3 = 11 stored bits',size=15,color=BLUE)
    d.text(425,393,'Same rounded result; low-column work moved across the register boundary.',size=15)
    d.save('rtl-low-column-cut.svg')

flow();pipeline();multiply_add();constants();low_columns()
