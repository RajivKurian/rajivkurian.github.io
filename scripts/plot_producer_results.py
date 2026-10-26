"""Draw the recorded PPA measurements with their tested mutation ancestry."""
import json
from pathlib import Path
from draw_cost_diagrams import Diagram

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / 'data/rtl-producer.json').read_text())['records']
by_id = {r['id']: r for r in records}
BLUE, RUST, SLATE = '#3d6f8c', '#b75d2c', '#77878e'
d = Diagram(900,505,'Area and setup slack of ten four-cycle implementations; arrows show tested mutations')
left, right, top, bottom = 90, 865, 55, 405
amin=min(r['area_um2'] for r in records)-8
amax=max(r['area_um2'] for r in records)+8
smin=min(0,min(r['slack_ps'] for r in records))-30
smax=max(r['slack_ps'] for r in records)+35
x = lambda area: left + (area-amin)/(amax-amin)*(right-left)
y = lambda slack: bottom - (slack-smin)/(smax-smin)*(bottom-top)
for area in range(int(amin//20+1)*20,int(amax),20):
    xx=x(area)
    d.parts.append(f'<path d="M{xx} {top}V{bottom}" stroke="#dedbd3"/>')
    d.text(xx,bottom+27,str(area),size=16)
for slack in range(int(smin//50+1)*50,int(smax),50):
    yy=y(slack)
    d.parts.append(f'<path d="M{left} {yy}H{right}" stroke="#dedbd3"/>')
    d.text(left-15,yy+5,str(slack),size=16,anchor='end')
d.text((left+right)/2,465,'Mapped cell area (µm²)',size=18)
d.parts.append('<text transform="translate(24 230) rotate(-90)" text-anchor="middle" font-family="system-ui,sans-serif" font-size="17" fill="#41484b">Setup slack at a 1 ns clock (ps)</text>')
d.text(left,25,'Less area ←      More timing headroom ↑',size=16,anchor='start')
for parent,child in [(1,2),(1,3),(3,4),(1,5),(1,6),(6,7),(2,8),(8,9),(2,10)]:
    a,b=by_id[parent],by_id[child]
    color=BLUE if (parent,child)==(1,2) else RUST if child>=8 else SLATE
    # Keep arrows behind the markers; the arrowhead is visible just before
    # the destination. Each edge joins two actual recorded experiments.
    ax,ay,bx,by=x(a['area_um2']),y(a['slack_ps']),x(b['area_um2']),y(b['slack_ps'])
    dx,dy=bx-ax,by-ay
    length=(dx*dx+dy*dy)**.5
    if length>15:
        bx-=dx/length*7;by-=dy/length*7
    d.parts.append(f'<path d="M{ax} {ay}L{bx} {by}" fill="none" stroke="{color}" stroke-width="{2 if child==2 else 1.2}" opacity="{.9 if child==2 else .5}" marker-end="url(#arrow)"/>')
offsets={1:(-16,-17),2:(-20,-17),3:(-20,27),4:(14,-13),5:(-5,-18),
         6:(14,6),7:(-21,-12),8:(-20,24),9:(14,5),10:(-21,23)}
for r in records:
    i=r['id'];xx,yy=x(r['area_um2']),y(r['slack_ps'])
    color=RUST if i>=8 else BLUE
    if i>=8:
        d.parts.append(f'<path d="M{xx} {yy-6}l6 6l-6 6l-6 -6Z" fill="{color}" stroke="#faf9f6"/>')
    else:
        d.parts.append(f'<circle cx="{xx}" cy="{yy}" r="6" fill="{color}" stroke="#faf9f6"/>')
    dx,dy=offsets[i]
    d.text(xx+dx,yy+dy,str(i),size=17,color=color)
d.text(450,496,'Blue: individual changes     Rust diamonds: combined changes     Arrows: experiment ancestry',size=14)
d.save('producer-ppa-search.svg')
print('Plotted 10 measured points and recorded experiment ancestry.')
