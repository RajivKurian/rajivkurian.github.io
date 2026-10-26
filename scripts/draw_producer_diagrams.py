"""Draw Part 4's design choices and measured experiment sequence."""
from pathlib import Path
import json
from draw_cost_diagrams import Diagram

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/rtl-producer.json').read_text())
RECORDS = {r['name']: r for r in DATA['records']}
BLUE, RUST, SLATE = '#3d6f8c', '#b75d2c', '#77878e'

def line(d, x1, y1, x2, y2, color=SLATE, width=1.5, dash=False):
    d.parts.append(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color}" stroke-width="{width}" fill="none"'+(' stroke-dasharray="4 4"' if dash else '')+'/>')

def box(d, x, y, w, h, lines, color=SLATE, size=17):
    d.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#f5f1e8" stroke="{color}" stroke-width="1.5"/>')
    for i, text in enumerate(lines):
        d.text(x+w/2, y+h/2+(i-(len(lines)-1)/2)*23+6, text, size=size)

def atoms():
    d = Diagram(900,240,'Coefficient table and the two fixed-format multiply-adds')
    d.text(450,26,'Polynomial and formats',size=21)
    box(d,25,55,210,80,['256-row table','a: 8 · b: 13 · c: 23 bits'],size=16)
    box(d,310,55,210,80,['s = Q₁(a·t + b)','15-bit first result'],BLUE)
    box(d,650,55,210,80,['y = Q₂(s·t + c)','25-bit result'],BLUE)
    d.path('M235 90 H310');d.path('M520 90 H650')
    d.text(585,78,'s',size=16)
    d.path('M235 120 H275 V180 H620 V110 H650')
    d.text(440,172,'carry c to the second multiply-add',size=15)
    d.path('M90 218 H755 V135');d.path('M415 218 V135')
    d.text(110,210,'t: 18 bits',size=16,anchor='start')
    d.save('producer-design-atoms.svg')

def flow():
    d=Diagram(900,495,'A fitted computation and implementation choices feed RTL generation and checked measurements')
    box(d,20,30,220,105,['Fitted computation','table words + formats','narrowing + latency'],BLUE,size=16)
    box(d,20,190,220,85,['Implementation choices','recoding · grouping · cuts'],RUST)
    box(d,300,75,240,165,['RTL generator','connect selected blocks','fold constant bits','insert chosen registers'],BLUE)
    d.path('M240 82 H270 V120 H300');d.path('M240 232 H270 V195 H300')
    box(d,605,35,275,100,['RTL + testbench','circuit diagrams'],BLUE)
    d.path('M540 120 H570 V85 H605')
    box(d,605,175,275,60,['Verilator · RTL / model check'],size=15)
    d.path('M742 135 V175')
    box(d,605,270,275,60,['Yosys + ABC','map cells · measure area'],size=15)
    d.path('M742 235 V270')
    box(d,605,370,275,60,['Verilator · gate / model check'],size=15)
    d.path('M742 330 V370')
    box(d,300,370,240,60,['OpenSTA','timing · activity power'],BLUE,size=16)
    d.path('M605 400 H540')
    box(d,20,370,220,60,['Experiment record','choices + RTL + results'],BLUE,size=15)
    d.path('M300 400 H240')
    d.path('M130 370 V275',True)
    d.text(145,323,'next experiment',size=15,anchor='start',color=RUST)
    d.text(450,478,'We choose the mutations; generation, checking and measurement run automatically.',size=15)
    d.save('producer-measurement-flow.svg')

def compression():
    d=Diagram(900,325,'The first multiply-add has eight aligned rows; column four illustrates the difference between row and column grouping')
    support=DATA['first_heap']
    d.text(450,25,'First multiply-add: eight aligned rows',size=21)
    start,step,base=90,9,85
    for bit in [35,24,12,4,0]:d.text(start+(35-bit)*step,57,str(bit),size=13)
    d.text(50,57,'bit',size=13)
    selected=start+(35-4)*step
    d.parts.append(f'<rect x="{selected-6}" y="69" width="12" height="146" fill="#e5edf1"/>')
    for row,values in enumerate(support):
        yy=base+row*18
        d.text(65,yy+5,['b','d0','d1','d2','d3','d4','corr','bias'][row],size=13,anchor='end')
        for bit,kind in enumerate(reversed(values)):
            if kind:d.parts.append(f'<circle cx="{start+bit*step}" cy="{yy}" r="3" fill="{BLUE if kind==2 else RUST}"/>')
    d.parts.append(f'<circle cx="{selected}" cy="{base}" r="4" fill="#faf9f6" stroke="{SLATE}"/>')
    box(d,470,65,405,85,['Row group: b, d0, d1','At bit 4: 0 + p + q','d2 supplies r to a later layer'],size=16)
    box(d,470,180,405,85,['Column group: d0, d1, d2','At bit 4: p + q + r','one compressor combines all three'],BLUE,size=16)
    d.text(255,247,'d0–d4: Booth product rows',size=15)
    d.text(255,272,'corr: negative-digit correction · bias: fixed constant',size=13)
    d.text(450,309,'Columns are aligned bit weights; empty positions are fixed zeros.',size=15)
    d.save('producer-column-compression.svg')

def decode():
    d=Diagram(900,475,'Local residual recoding stores 18 bits; carried recoding stores 27 distinct controls at each of two banks')
    for y,title,words,width in [(25,'Decode t at each multiplier','18-bit t',18),
                               (255,'Decode t once and carry the controls','27 controls',27)]:
        d.text(450,y,title,size=21)
        offset=y+35
        if width==18:
            d.text(25,offset+35,'t',size=17)
            d.path(f'M40 {offset+30} H95')
        else:
            box(d,15,offset+2,135,56,['decode t','one / two / sign'],BLUE,size=14)
            d.path(f'M150 {offset+30} H185')
        xs=[95,585] if width==18 else [185,625]
        for i,x in enumerate(xs):
            box(d,x,offset,155,60,[f'R{i+1}',words],BLUE,size=17)
            if i<1:d.path(f'M{x+155} {offset+30} H{xs[i+1]}')
        for i in [0,1]:
            center=xs[i]+77
            d.path(f'M{center} {offset+60} V{offset+88}')
            box(d,center-75,offset+88,150,52,
                ['decode → rows'] if width==18 else ['select product rows'],size=15)
    d.save('producer-shared-decode.svg')

def recoding_example():
    d=Diagram(900,170,'Binary and radix-4 Booth representations of 13 times 7')
    d.text(450,27,'Example: 13 × 7',size=21)
    box(d,25,55,395,90,['Binary: 7 = 1 + 2 + 4','13 × 7 = 13 + 26 + 52 = 91'],size=18)
    box(d,480,55,395,90,['Booth: 7 = −1 + 2 × 4','13 × 7 = −13 + (26 << 2) = 91'],BLUE,size=18)
    d.save('producer-booth-example.svg')

def recoding_options():
    d=Diagram(900,690,'Three Booth implementations for a times t and s times t, with local narrow-operand decoding, local residual decoding or shared residual controls')
    for option,(title,color) in enumerate([
        ('1 · Recode a and s locally','#356c92'),
        ('2 · Recode t locally at both multipliers','#a36a18'),
        ('3 · Recode t once and carry its controls','#af5137')]):
        y=option*220
        d.text(25,y+25,title,size=21,anchor='start',color=color)
        shared=option==2
        # Same two transaction banks in each option. Only t or its controls
        # are shown; the remaining operands follow the full polynomial pipeline.
        for stage,x in enumerate([150,650],1):
            box(d,x,y+50,80,36,[f'R{stage}'],color,size=16)
        if shared:
            box(d,20,y+50,110,36,['decode t'],color,size=15)
            d.path(f'M130 {y+68} H150')
            d.text(75,y+45,'t: 18 bits',size=13)
        else:
            d.text(65,y+74,'t: 18 bits',size=16)
            d.path(f'M110 {y+68} H150')
        d.path(f'M230 {y+68} H650')
        d.path(f'M730 {y+68} H835')
        d.text(450,y+59,'27 controls' if shared else '18-bit t',size=14)
        # Product selection blocks always occupy the same position.
        box(d,280,y+115,150,54,['multiples of t' if option==0 else 'multiples of a',
                              '5 Booth rows' if option==0 else '10 Booth rows'],color,size=15)
        box(d,750,y+115,130,54,['multiples of t' if option==0 else 'multiples of s',
                              '8 Booth rows' if option==0 else '10 Booth rows'],color,size=15)
        if option==0:
            box(d,95,y+115,140,54,['decode a','8 bits'],color,size=15)
            box(d,570,y+115,140,54,['decode s','15 bits'],color,size=15)
            d.text(50,y+147,'a',size=17);d.path(f'M65 {y+142} H95')
            d.text(530,y+147,'s',size=17);d.path(f'M540 {y+142} H570')
            d.path(f'M235 {y+142} H280');d.path(f'M710 {y+142} H750')
            d.path(f'M355 {y+68} V{y+115}')
            d.path(f'M815 {y+68} V{y+115}')
        elif option==1:
            box(d,95,y+115,140,54,['decode t','18 bits'],color,size=15)
            box(d,570,y+115,140,54,['decode t','18 bits'],color,size=15)
            d.path(f'M190 {y+86} V{y+100} H165 V{y+115}')
            d.path(f'M690 {y+86} V{y+100} H640 V{y+115}')
            d.path(f'M235 {y+142} H280');d.path(f'M710 {y+142} H750')
            d.text(369,y+106,'a',size=17,anchor='start');d.path(f'M355 {y+90} V{y+115}')
            d.text(829,y+106,'s',size=17,anchor='start');d.path(f'M815 {y+90} V{y+115}')
        else:
            d.path(f'M190 {y+86} V{y+142} H280')
            d.path(f'M690 {y+86} V{y+142} H750')
            d.text(369,y+106,'a',size=17,anchor='start');d.path(f'M355 {y+90} V{y+115}')
            d.text(829,y+106,'s',size=17,anchor='start');d.path(f'M815 {y+90} V{y+115}')
        d.text(355,y+193,'first product: a·t',size=15)
        d.text(815,y+193,'second product: s·t',size=15)
        if option<2:line(d,20,y+211,880,y+211,'#d9d5ca',1)
    d.text(450,681,'R1–R2 show only residual/control storage. The coefficient addends b and c are omitted.',size=15)
    d.save('producer-booth-options.svg')

def compressor_example():
    from draw_compressor_lesson import draw_all
    draw_all()

def carry_example():
    from draw_carry_lesson import carry_example as draw_carry
    draw_carry()

def register_example():
    d=Diagram(900,415,'Resolving four low columns before storage preserves the truncated sum using nine instead of sixteen bits')
    d.text(450,25,'Example: truncate four low bits after adding',size=21)
    for x,title in [(25,'Store both rows'),(480,'Resolve low columns first')]:
        d.text(x+197,60,title,size=18)
        box(d,x,78,395,65,['U = 0001 | 1110','V = 0100 | 0010'],size=18)
    box(d,480,160,395,52,['1110 + 0010 = 1 | 0000'],BLUE,size=17)
    d.path('M222 143 V232');d.path('M677 143 V160')
    line(d,45,240,400,240,RUST,5);line(d,500,240,855,240,RUST,5)
    d.text(222,224,'register: 16 bits',size=16,color=RUST)
    d.text(677,231,'register: 4 + 4 + carry = 9 bits',size=16,color=RUST)
    d.path('M222 243 V270');d.path('M677 243 V270')
    box(d,25,270,395,75,['Full sum: 0110 | 0000','Truncated result: 0110'],BLUE,size=18)
    box(d,480,270,395,75,['Upper sum: 0001 + 0100 + 1','Truncated result: 0110'],BLUE,size=17)
    d.text(450,382,'For RNE, also retain guard and sticky: both are zero here, so the rounded result is 0110.',size=15)
    d.save('producer-register-example.svg')

def four_cycle_pipeline():
    d=Diagram(900,210,'Four cycles: coefficient lookup, complete first multiply-add, second compression and final completion')
    stages=[['Cycle 1','Coefficient lookup','hold a, b, c and t'],
            ['Cycle 2','Complete a·t + b','truncate to s'],
            ['Cycle 3','Compress s·t + c','resolve low columns'],
            ['Cycle 4','Complete upper sum','truncate to output']]
    for i,lines in enumerate(stages):
        x=20+i*225
        box(d,x,40,180,105,lines,BLUE,size=15)
        if i<3:
            d.path(f'M{x+180} 92 H{x+225}')
            d.text(x+202,79,f'R{i+1}',size=14)
    d.text(880,168,'R4 · output register',size=14,anchor='end')
    d.text(450,197,'t and c travel with s until the second multiply-add uses them.',size=15)
    d.save('producer-four-cycle-pipeline.svg')

def lowering_example():
    d=Diagram(900,495,'Operand delays align transactions; a constant coefficient column bypasses registers and joins the product compression')
    d.text(450,25,'Operand stages',size=21)
    box(d,25,50,160,47,['sᵢ · stage 2'],BLUE,size=17)
    box(d,25,115,160,50,['tᵢ · stage 0'],size=17)
    box(d,705,50,170,90,['Booth product rows','sᵢ × tᵢ'],BLUE,size=15)
    d.path('M185 74 H705')
    xs=[320,515]
    for j,x in enumerate(xs):
        box(d,x,115,90,50,[f'R{j+1}'],BLUE,size=17)
        if j==0:d.path(f'M185 140 H{x}')
        else:d.path(f'M{xs[j-1]+90} 140 H{x}')
    d.path('M605 140 H650 V116 H705')
    d.text(450,193,'Delay tᵢ by two cycles to pair it with sᵢ.',size=16)
    d.text(450,227,'Constant coefficient bits',size=21)
    box(d,25,255,160,45,['c[21:0]'],size=17)
    for j,x in enumerate(xs):
        box(d,x,255,90,45,[f'R{j+1}'],size=17)
        if j==0:d.path(f'M185 278 H{x}')
        else:d.path(f'M{xs[j-1]+90} 278 H{x}')
    box(d,705,255,170,85,['product rows','+ aligned c','compress together'],BLUE,size=15)
    d.path('M605 278 H705')
    d.path('M790 140 V255')
    box(d,25,320,160,65,['c[22] in all rows','1 1 1 … 1'],size=15)
    box(d,255,330,90,45,['literal 1'],BLUE,size=15)
    d.path('M185 352 H255');d.path('M345 352 H650 V315 H705')
    d.text(500,343,'no c[22] registers',size=15)
    box(d,705,405,170,55,['carry completion'],BLUE,size=15)
    d.path('M790 340 V405')
    d.text(450,482,'The coefficient enters compression before the product is converted to an ordinary binary sum.',size=15)
    d.save('producer-lowering-example.svg')

atoms();recoding_example();recoding_options();compressor_example();carry_example();register_example()
flow();four_cycle_pipeline();lowering_example();decode()
print('Drew the pipeline, worked atoms, producer flow, constant propagation and comparisons.')
