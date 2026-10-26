"""Lay out the recorded search and mapping results; no numerical fitting."""
import json
from pathlib import Path
from draw_cost_diagrams import Diagram

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/hardware-search.json').read_text())
NARROW=json.loads((ROOT/'data/narrow256-study.json').read_text()) if (ROOT/'data/narrow256-study.json').exists() else {'records':[]}
MEASURED=json.loads((ROOT/'data/rounding-measurements.json').read_text())['results']
QUALITY={r['profile_sha256']:r for r in json.loads((ROOT/'data/numerical-quality.json').read_text())['records']}
BLUE,RUST,SLATE='#1460aa','#b65322','#747d86'

def feedback():
    history=next(r['history'] for r in NARROW['records'] if r['name']=='narrow256-s15-rne')
    d=Diagram(850,210,'The same 256-row RNE hardware passes after counterexamples refine its coefficients')
    for i,record in enumerate(history):
        x=15+285*i
        color=BLUE if record['accepted'] else RUST
        count=f"{record['failures']:,} failing inputs"
        d.box(x,30,250,90,[f'Fit {i+1}',count,'Same widths and rounding'],color)
        if i<2: d.path(f'M{x+250} 75 H{x+285}')
    d.text(425,155,'Retain the failures and nearby inputs; change the coefficient words.',size=16)
    d.text(425,185,'Each check covers all 2³² FP32 encodings.',size=14,color=SLATE)
    d.save('counterexample-refitting.svg')

def resolution():
    names=['rows32-wide-rne','rows64-wide-rne','stage17-11','narrow256-s15-rne']
    records={r['name']:r for r in DATA['records']+NARROW['records']}
    colors=dict(zip(names,[SLATE,RUST,'#97826c',BLUE]))
    phases=[('Before fitting','Dimensions only','architecture'),
            ('After fitting','Fitted ROM patterns','proxy'),
            ('Synthesis','Mapped ROM and pipeline','mapped')]
    orders=[sorted(names,key=lambda n:records[n][phase]['normalized_cost' if phase=='mapped' else 'cost']) for _,_,phase in phases]
    d=Diagram(850,445,'Candidate ordering changes as coefficient contents and mapped logic become known')
    xs=[10,320,630]
    for phase,order in enumerate(orders[:-1]):
        for name in names:
            y1=108+80*order.index(name);y2=108+80*orders[phase+1].index(name)
            d.parts.append(f'<path d="M{xs[phase]+210} {y1} L{xs[phase+1]} {y2}" fill="none" stroke="{colors[name]}" stroke-width="{3 if name=="narrow256-s15-rne" else 1.6}"/>')
    for j,(title,subtitle,phase) in enumerate(phases):
        d.text(xs[j]+105,25,title,size=18)
        d.text(xs[j]+105,48,subtitle,size=13,color=SLATE)
        for i,name in enumerate(orders[j]):
            r=records[name];cost=r[phase]['normalized_cost' if phase=='mapped' else 'cost']
            d.box(xs[j],80+80*i,210,56,[f"{1<<r['table_bits']} rows · first {r['shape'][4]} bits",f'{cost:.2f}'],colors[name])
    d.text(425,410,'Lowest cost at the top of each column',size=15)
    d.text(425,435,'Costs in data-register-bit units; line height shows rank, not cost distance.',size=13,color=SLATE)
    d.save('table-resolution-search.svg')

def formats():
    records=DATA['records']+NARROW['records']
    groups=[('Wide','12/16/26','22/28', [12,16,26,22,22,28]),
            ('Medium','11/14/24','19/26',[11,14,24,20,19,26]),
            ('Compact, 18-bit first','10/13/23','18/25',[10,13,23,20,18,25]),
            ('Compact, 17-bit first','10/13/23','17/25',[10,13,23,20,17,25]),
            ('Narrower, 16-bit first','8/13/23','16/25',[8,13,23,18,16,25]),
            ('Narrower, 15-bit first','8/13/23','15/25',[8,13,23,18,15,25]),
            ('Narrower, 14-bit first','8/13/23','14/25',[8,13,23,18,14,25])]
    d=Diagram(850,415+65*(len(groups)-4),'Recorded RNE coefficient fits across table sizes and physical precision profiles')
    d.text(15,25,'Coefficient bits a/b/c · residual · first/result bits',anchor='start',size=15)
    xs=[370,500,630,760]
    for x,n in zip(xs,[32,64,128,256]):d.text(x,65,f'{n} rows',size=16)
    for i,(name,coefficients,retained,shape) in enumerate(groups):
        y=108+65*i
        d.text(15,y,name,anchor='start',size=15)
        d.text(15,y+21,f'{coefficients} · {shape[3]} · {retained}',anchor='start',size=13,color=SLATE)
        for x,n in zip(xs,[32,64,128,256]):
            match=[r for r in records if r['first_rne'] and r['final_rne'] and r['shape']==shape and (1<<r['table_bits'])==n]
            if match:
                passed=match[0]['exhaustive']['accepted']
                counts=QUALITY[match[0]['exhaustive']['profile_sha256']]['exhaustive']['quality']['negative_approximation']
                if passed:
                    labels=[f"{i} ULP: {100*counts['ulp'][i]/counts['count']:.2f}%" for i in [0,1]]
                else:
                    labels=['Fit failed',f">2 ULP: {100*counts['ulp'][3]/counts['count']:.2f}%"]
                d.box(x-58,y-22,116,52,labels,BLUE if passed else RUST)
            else:d.text(x,y+5,'—',size=18,color=SLATE)
    d.text(425,377+65*(len(groups)-4),'RNE at both narrowing points; all cells use the same negative input range.',size=14)
    d.text(425,403+65*(len(groups)-4),'Negative inputs · blue: remainder is 2 ULP · rust: fit failed · —: not compared',size=13,color=SLATE)
    d.save('format-search-grid.svg')

def rounding():
    d=Diagram(850,380,'Truncation is a bit slice; RNE adds guard/sticky logic and an increment')
    d.text(200,25,'Truncate',size=18)
    d.text(635,25,'Round to nearest, ties to even',size=18)
    for x in [15,445]:
        d.box(x,48,375,45,['Exact sum: high bits | guard | lower bits'])
    d.path('M200 93 V320')
    d.text(210,158,'High bits',anchor='start',color=BLUE)
    d.text(35,233,'Discard guard',anchor='start',size=14,color=SLATE)
    d.text(35,253,'and lower bits',anchor='start',size=14,color=SLATE)
    d.text(200,352,'Retained word',size=16,color=BLUE)
    d.box(445,110,125,40,['High bits'],BLUE)
    d.box(600,110,45,40,['G'])
    d.box(690,110,125,40,['Lower bits'])
    d.path('M505 93 V110');d.path('M622 93 V110');d.path('M752 93 V110')
    d.path('M752 150 V173')
    d.box(722,173,60,35,['OR'])
    d.text(808,225,'sticky',anchor='end',size=11)
    d.path('M752 208 V223 H710 V235')
    d.box(660,235,60,35,['OR'])
    d.path('M505 150 V290')
    d.parts.append(f'<circle cx="505" cy="192" r="3" fill="{SLATE}"/>')
    d.path('M505 192 H615 V252 H660')
    d.text(562,183,'Retained LSB',size=12)
    d.box(660,290,70,35,['AND'])
    d.path('M690 270 V290')
    d.path('M622 150 V280 H710 V290')
    d.box(445,290,125,35,['+ increment'],RUST)
    d.path('M660 307 H570')
    d.text(609,298,'0 or 1',size=12)
    d.path('M505 325 V338')
    d.text(505,360,'Retained word',size=16,color=RUST)
    d.save('truncate-versus-rne.svg')

feedback();resolution();formats();rounding()
