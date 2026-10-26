"""Draw recorded row supports and the specific changes in the clock study."""
from pathlib import Path
import zipfile
from draw_cost_diagrams import Diagram
from rtl_viewer_blocks import load, replay

BLUE,RUST,SLATE='#356c92','#af5137','#75828a'
ROOT=Path(__file__).resolve().parents[1]
archive=zipfile.ZipFile(ROOT/'docs/artifacts/rtl-clock-experiments.zip')

def box(d,x,y,w,h,lines,color=BLUE,size=16):
    d.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#f5f1e8" stroke="{color}" stroke-width="1.5"/>')
    for j,s in enumerate(lines):d.text(x+w/2,y+h/2+(j-(len(lines)-1)/2)*22+5,s,size=size)

def circuit(name):
    return load(archive.read(f'circuits/{name}/circuit.pb'),archive.read(f'circuits/{name}/sfu_poly.sv').decode())

def dot(d,x,y,bit,color,r=4):
    if bit==0:
        d.parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="#d8d4ca"/>')
    elif bit==1:d.text(x,y+max(2,r),'1',size=2*r+4 if r>=4 else 6,color=RUST)
    else:d.parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')

# A concrete input configuration and the stages the producer constructs.
d=Diagram(900,465,'Fitted words and implementation choices generate a scheduled polynomial circuit')
box(d,20,28,390,80,['Numerical design from Part 3','256 rows · a/b/c: 8/13/23 bits','t: 18 · s: 15 · y: 25 · two truncations'],BLUE,15)
box(d,20,132,390,104,['Implementation choices for this example','local a/s recoding · column compression','first MAC: hybrid, no internal cut','second MAC: ripple, low-column cut'],RUST,15)
d.path('M410 65 H457 V140 H500');d.path('M410 184 H457 V140')
box(d,500,72,375,135,['Generator','select Booth rows and compressors','build carry networks · fold constants','insert cuts and matching operand delays'],BLUE,16)
d.path('M685 207 V266')
d.text(22,281,'Generated four-cycle circuit',size=19,anchor='start')
for x,w,label in [(25,125,['ROM + R1']),(185,235,['First MAC → R2','one hybrid-completed sum']),(455,200,['Second MAC → R3','compression + low carry']),(690,185,['Completion → R4','truncate to 25 bits'])]:
    box(d,x,305,w,65,label,BLUE,14)
for a,b in [(150,185),(420,455),(655,690)]:d.path(f'M{a} 337 H{b}')
d.path('M150 365 V402 H550 V370');d.text(365,426,'t and c delayed to the same transaction as s',size=15)
d.text(450,458,'Changing a cut regenerates its row storage, downstream logic and operand delays.',size=16)
d.save('producer-generator-inputs.svg')

# Exact upper-row supports in the measured one-ns row/column pair.
d=Diagram(900,350,'Actual compressed row bits stored at R3: whole-row grouping versus column packing')
for offset,name,title,color,total in [(0,'narrow_local','Whole-row grouping',BLUE,50),(455,'t1000_c4_ripple','Column packing',RUST,35)]:
    gates,_,heaps,_=circuit(name)
    _,_,rows=replay(gates,heaps[1],name!='narrow_local')
    upper=[row[17:] for row in rows]
    count=len({b for row in upper for b in row if b>1})
    regs=[g for g in gates.values() if g['live'] and g['op']==7 and g['stage']==3]
    assert len(regs)==total and count==total-2
    d.text(offset+220,30,title,size=20,color=color)
    d.text(offset+220,65,'Upper columns after resolving columns 0–16',size=14)
    for j in [41,33,25,17]:d.text(offset+100+(41-j)*12,96,str(j),size=12)
    for r,row in enumerate(upper):
        d.text(offset+64,125+r*38,f'row {r}',size=13)
        for j,b in enumerate(reversed(row)):dot(d,offset+100+j*12,120+r*38,b,color)
    d.text(offset+220,205,f'{count} variable row bits + low carry + valid',size=16)
    box(d,offset+95,228,280,48,[f'R3 bank: {total} signals'],color,18)
d.text(450,309,'Filled dot: variable bit → storage. Hollow dot: fixed zero. “1”: fixed one.',size=15)
d.text(450,337,'Same bit weights and same sum; column packing leaves many carry-row positions constant.',size=16)
d.save('producer-clock-grouping.svg')

# Carry completion includes the recorded upstream dependency profile.
from draw_carry_lesson import measured_example
measured_example()

# Move four exact columns across the existing bank, not the rounding point.
d=Diagram(900,335,'Moving the cut from seventeen resolved columns to thirteen stores four more unresolved columns in each row')
for y,cut,title,color in [(30,17,'Resolve 17 low columns before R4',BLUE),(181,13,'Resolve 13 low columns before R4',RUST)]:
    d.text(25,y,title,size=18,anchor='start',color=color)
    for j in [0,12,16,25,41]:d.text(110+(41-j)*17,y+31,str(j),size=11)
    for r in range(2):
        for j in range(42):
            fill='#e7e3da' if j<cut else '#e7bda9' if j<17 else color
            d.parts.append(f'<rect x="{103+(41-j)*17}" y="{y+43+r*17}" width="13" height="12" fill="{fill}"/>')
    d.text(65,y+54,'row 0',size=12);d.text(65,y+71,'row 1',size=12)
    d.text(110+(41-(cut-1)/2)*17,y+101,f'complete low sum → c{cut}',size=14)
    d.text(110+(41-cut)*17/2,y+101,'store unresolved upper row bits',size=14,color=color)
d.text(450,326,'Columns 13–16 move across R4. The final numerical truncation still removes columns 0–16.',size=15)
d.save('producer-clock-low-cut.svg')

# Complete schedules, with the common lookup and first MAC muted.
d=Diagram(1200,410,'Complete five- and six-cycle pipelines; the lookup and first MAC through R3 are unchanged')
common=[['Coefficient','lookup'],['First MAC','row selection','compression','low-column sum'],['First MAC','carry completion','15-bit s']]
schedules=[(32,BLUE,'Five cycles · original column-compression cut',common+[
    ['Second MAC','row selection','compression','low-column sum'],['Second MAC','carry completion','25-bit result']]),
    (220,RUST,'Six cycles · register selected rows before compression',common+[
    ['Second MAC','row selection'],['Second MAC','compression +','low-column sum'],['Second MAC','carry completion','25-bit result']])]
for title_y,color,title,stages in schedules:
    d.text(20,title_y,title,size=21,anchor='start',color=color)
    y=title_y+35
    for index,labels in enumerate(stages):
        x=25+194*index
        muted=index<3
        if muted:d.parts.append('<g opacity="0.5">')
        box(d,x,y,160,92,labels,SLATE if muted else color,15)
        # The bank at the right of each stage holds that cycle's result.
        d.path(f'M{x+160} {y+46} H{x+176}')
        d.parts.append(f'<path d="M{x+176} {y+14} V{y+78}" stroke="{SLATE if muted else color}" stroke-width="4"/>')
        d.text(x+176,y+116,f'R{index+1}',size=15)
        if index+1<len(stages):d.path(f'M{x+176} {y+46} H{x+194}')
        if muted:d.parts.append('</g>')
d.text(600,402,'Grey: unchanged lookup and first MAC. Colour: the second MAC and its register cuts.',size=17)
d.save('producer-clock-schedules.svg')

# Actual selected/partially compressed/full row patterns entering an extra bank.
d=Diagram(900,410,'The second MAC extra bank stores eleven selected rows, three partially compressed rows, or two fully compressed rows')
for x,name,layers,title,color,count in [(18,'t700_c6_product_cut',None,'Selected rows',BLUE,189),(315,'t700_c6_compress5',5,'After 5 layers',RUST,66),(612,'t700_c6_full_compress',0,'After full compression',RUST,55)]:
    g,_,heaps,_=circuit(name);rows=heaps[1]
    if layers is not None:_,_,rows=replay(g,rows,True,layers)
    bits={b for row in rows for b in row if b>1}
    assert len(bits)+1==count
    d.text(x+132,28,title,size=18,color=color)
    d.text(x+132,57,f'{len(rows)} rows · same weighted sum',size=14)
    for j in [41,20,0]:d.text(x+22+(41-j)*5.4,84,str(j),size=11)
    for r,row in enumerate(rows):
        for j,b in enumerate(reversed(row)):dot(d,x+22+j*5.4,101+r*14,b,color,2)
    bottom=101+(len(rows)-1)*14
    d.path(f'M{x+132} {bottom+10} V293')
    box(d,x+20,300,245,48,[f'R4: {count-1} row bits + valid'],color,15)
d.text(450,377,'Compression moves before R4; it preserves every bit weight and the eventual truncation.',size=15)
d.text(450,402,'R5 still holds the low carry and upper pair; carry completion follows it in the final cycle.',size=15)
d.save('producer-clock-cuts.svg')
print('Drew generator inputs, traced row banks, carry networks and register-cut changes.')
