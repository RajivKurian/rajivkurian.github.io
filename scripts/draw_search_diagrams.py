"""Lay out exported C++ search results; no fitting is performed here."""
import json
from pathlib import Path
from draw_cost_diagrams import Diagram

ROOT = Path(__file__).resolve().parents[1]
BLUE, RUST, SLATE = '#1460aa', '#c43c28', '#747d86'

def line(d, x1, y1, x2, y2, color=SLATE, dash=False, width=1):
    d.parts.append(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="5 4"' if dash else '')+'/>')

def search_flow():
    d=Diagram(850,510,'Directed hardware experiments with automated coefficient fitting')
    d.box(155,15,540,65,['We fix table size, coefficient and internal formats,','and both narrowing rules'],'#b65322')
    d.box(255,105,340,45,['Initialize table from Remez'])
    d.box(255,175,340,45,['Search integer coefficient words'],BLUE)
    d.box(255,245,340,45,['Exhaustive error and monotonicity test'])
    d.box(255,325,340,65,['Record error distribution','Synthesize promising passing tables'],BLUE)
    d.box(255,425,340,60,['We compare area and numerical quality','and choose the next hardware experiment'],'#b65322')
    for y1,y2 in [(80,105),(150,175),(220,245),(290,325),(390,425)]:
        d.path(f'M425 {y1} V{y2}')
    d.text(450,313,'pass',size=12,anchor='start')
    d.path('M255 267 H160 V197 H255')
    d.text(153,230,'fail: add inputs',size=11,anchor='end',color='#b65322')
    d.path('M595 455 H790 V47 H695')
    d.text(785,411,'new point',size=12,anchor='end')
    d.path('M255 197 H65 V455 H255',True)
    d.text(75,407,'if fitting stalls',size=12,anchor='start')
    d.save('hardware-search-flow.svg')

def ulps():
    d=Diagram(850,195,'FP32 output spacing changes at one')
    x=[70,170,270,370,570,770]
    line(d,50,82,770,82)
    labels=['1 − 3·2⁻²⁴','1 − 2·2⁻²⁴','1 − 2⁻²⁴','1','1 + 2⁻²³','1 + 2·2⁻²³']
    for a,label in zip(x,labels):
        line(d,a,74,a,90,BLUE,width=2);d.text(a,114,label,size=12)
    d.text(220,46,'Spacing below 1: 2⁻²⁴',size=15,color=BLUE)
    d.text(570,46,'Spacing above 1: 2⁻²³',size=15,color=RUST)
    d.text(390,163,'Two representable steps need not cover the same numerical distance.',size=14)
    d.save('ulp-near-one.svg')

def intervals():
    p=json.loads((ROOT/'data/search-examples.json').read_text())['constant_intervals'];origin=p['c_origin']
    d=Diagram(780,240,'Constraints from three inputs share four possible constant coefficients')
    def pos(n): return 245+(n-origin+8)*32
    labels=['x = −1/128','x = −1/256','x = −1/32768']
    for i,(label,(_,lo,hi)) in enumerate(zip(labels,p['inputs'])):
        y=45+i*45;d.text(15,y+5,label,anchor='start',size=15)
        line(d,pos(lo),y,pos(hi),y,BLUE,width=5)
        for a in range(lo,hi+1):d.parts.append(f'<circle cx="{pos(a)}" cy="{y}" r="4" fill="{BLUE}"/>')
    lo,hi=p['intersection'];line(d,pos(lo),183,pos(hi),183,RUST,width=3)
    for a in range(lo,hi+1): d.parts.append(f'<circle cx="{pos(a)}" cy="183" r="5" fill="{RUST}"/>')
    d.text(15,188,'Allowed by all three',anchor='start',size=15,color=RUST)
    for a in range(-8,7,2):d.text(pos(origin+a),220,f'{a:+d}',size=12)
    d.text(755,220,'C − C₀',anchor='end',size=12)
    d.save('constant-intervals.svg')

def coupled_refit():
    p=json.loads((ROOT/'data/coupled-refit.json').read_text())
    origin=p['after'][2]
    d=Diagram(850,355,'A coupled coefficient refit changes disjoint C constraints into an overlap')
    blue,rust=BLUE,'#b65322'
    for panel,(key,coefficients,title) in enumerate([('before_interval',p['before'],'Before refitting'),('after_interval',p['after'],'After refitting')]):
        left=18+430*panel
        X=lambda c:left+85+(c-origin+2)*70
        d.text(left+190,27,title,size=18)
        d.text(left+190,53,f"A = {coefficients[0]}, B = {coefficients[1]}",size=15)
        for i,point in enumerate(p['inputs']):
            y=100+65*i
            d.text(left,y-17,f"t = {point['t']:.3f}",anchor='start',size=13)
            lo,hi=point[key]
            line(d,X(lo),y,X(hi),y,blue,width=4)
            for c in range(lo,hi+1):
                d.parts.append(f'<circle cx="{X(c)}" cy="{y}" r="5" fill="{blue}"/>')
        low=max(point[key][0] for point in p['inputs'])
        high=min(point[key][1] for point in p['inputs'])
        if low>high:
            d.text(left+190,225,'No C word satisfies both inputs',size=15,color=rust)
        else:
            line(d,X(low),213,X(high),213,rust,width=4)
            for c in range(low,high+1):
                d.parts.append(f'<circle cx="{X(c)}" cy="213" r="6" fill="{rust}"/>')
            d.text(left+190,249,'Both inputs accept C₀',size=15,color=rust)
        for offset in [-2,-1,0,1]:
            d.text(X(origin+offset),282,f'{offset:+d}' if offset else '0',size=13)
        d.text(left+190,307,'Integer coefficient offset C − C₀',size=13)
    d.text(425,344,f"C₀ = {origin:,}; the stored C word is unchanged by this refit.",size=14)
    d.save('coupled-refit.svg')

def alternation():
    frame=json.loads((ROOT/'data/remez-trace.json').read_text())['trace'][-1]
    d=Diagram(800,565,'Four alternating error peaks require three sign changes in any improving quadratic correction')
    X=lambda t:90+640*t
    Y=lambda e:155-65*e/frame['bound']
    d.text(25,28,'1. Error e(t): all four peaks must move toward zero',size=17,anchor='start')
    for value,label in [(1,'+E'),(0,'0'),(-1,'−E')]:
        y=155-65*value
        line(d,75,y,750,y,'#d8d4ca',dash=value!=0)
        d.text(58,y+5,label,anchor='end',size=14)
    curve=' '.join(('M' if i==0 else 'L')+f'{X(t):.3f} {Y(e):.3f}' for i,(t,e) in enumerate(frame['samples']))
    d.parts.append(f'<path d="{curve}" fill="none" stroke="{BLUE}" stroke-width="2.5"/>')
    points=frame['extrema']
    for i,(t,e) in enumerate(points):
        x,y=X(t),Y(e)
        positive=e>0
        d.parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{BLUE}"/>')
        d.text(x,65 if positive else 247,'lower p' if positive else 'raise p',color=RUST,size=14)
        d.path(f'M{x+13} {y} V{y+(28 if positive else -28)}')
        line(d,x,268,x,278)
        d.text(x,297,['t₀','t₁','t₂','t₃'][i],size=14)
    d.text(25,342,'2. The correction d(t) = q(t) − p(t) must have these signs',size=17,anchor='start')
    line(d,75,440,750,440,'#aeb4b8')
    d.text(58,445,'0',anchor='end',size=14)
    for i,(t,e) in enumerate(points):
        x=X(t);y=480 if e>0 else 400
        d.parts.append(f'<circle cx="{x}" cy="{y}" r="12" fill="#faf9f6" stroke="{RUST}" stroke-width="2"/>')
        d.text(x,y+6,'−' if e>0 else '+',color=RUST,size=21)
        if i:
            prev_t,prev_e=points[i-1]
            prev_y=480 if prev_e>0 else 400
            line(d,X(prev_t)+10,prev_y+( -10 if prev_e>0 else 10),x-10,y+(10 if e>0 else -10),RUST,True,width=1.5)
            mid=(X(prev_t)+x)/2
            d.parts.append(f'<circle cx="{mid}" cy="440" r="5" fill="#faf9f6" stroke="{RUST}" stroke-width="1.8"/>')
            d.text(mid,521,'one zero',color=RUST,size=14)
    d.text(410,558,'Opposite signs force a zero somewhere in each gap: at least three roots.',size=14)
    d.save('quadratic-alternation.svg')

def remez():
    trace=json.loads((ROOT/'data/remez-trace.json').read_text())['trace']
    # Separate peak-finding (same polynomial) from solving at the exchanged
    # coordinates (new polynomial). Every curve comes from an actual C++ solve.
    stages=[
        (0,False,'Initial solve','Locate peaks',
         'The four chosen points have equal alternating error. Between them, the error can be larger.'),
        (0,True,'Locate extrema · curve unchanged','Exchange and solve',
         'Locating extrema does not change the curve. The filled dots mark the actual peaks; the interior two differ from the chosen points.'),
        (1,False,'Exchange 1 · solve again','Locate new peaks',
         'Solving with those peak locations as the new constraints changes the blue curve. Gray shows the preceding fit.'),
        (1,True,'Locate extrema again · curve unchanged','Exchange and solve',
         'The new curve has new extrema. The close-up shows that the chosen point still misses the minimum, so another exchange is needed.'),
        (2,True,'Exchange 2 · solve again','Check convergence',
         'After the second exchange, the chosen points and actual extrema nearly coincide. In the close-up, the filled peak sits inside the hollow chosen point.'),
        (3,True,'Exchange 3 · converged','Replay',
         'A third exchange stabilizes the point locations and peak heights. All four alternating extrema now have the same error magnitude.')
    ]
    html=['<div class="sfu-widget" id="remez-sequence">']
    for stage,(index,show_peaks,title,button,caption) in enumerate(stages):
        frame=trace[index]
        d=Diagram(900,430,title)
        X=lambda t:65+525*t
        Y=lambda e:185-50000*e
        d.text(20,27,title,size=17,anchor='start')
        d.text(65,62,'Relative error × 10⁻³',anchor='start',size=13)
        for e in [-.002,0,.002]:
            line(d,65,Y(e),590,Y(e),'#d8d4ca')
            d.text(52,Y(e)+5,f'{e*1000:g}',anchor='end',size=13)
        for t in [0,.25,.5,.75,1]:d.text(X(t),326,f'{t:g}',size=13)
        d.text(328,355,'Local coordinate t',size=14)
        for sign in [-1,1]:line(d,65,Y(sign*frame['bound']),590,Y(sign*frame['bound']),SLATE,True)
        def plot(samples,xmap,ymap,color,width):
            points=' '.join(('M' if j==0 else 'L')+f'{xmap(x):.3f} {ymap(y):.3f}' for j,(x,y) in enumerate(samples))
            d.parts.append(f'<path d="{points}" fill="none" stroke="{color}" stroke-width="{width}"/>')
        if index:plot(trace[index-1]['samples'],X,Y,'#aeb4b8',1.5)
        plot(frame['samples'],X,Y,BLUE,2.5)
        def markers(xmap,ymap,zoom=False):
            for x,y in frame['selected']:
                if zoom and not (.18<=x<=.25):continue
                d.parts.append(f'<circle cx="{xmap(x)}" cy="{ymap(y)}" r="6" fill="#faf9f6" stroke="{RUST}" stroke-width="2"/>')
            if show_peaks:
                for x,y in frame['extrema']:
                    if zoom and not (.18<=x<=.25):continue
                    d.parts.append(f'<circle cx="{xmap(x)}" cy="{ymap(y)}" r="3.6" fill="{RUST}"/>')
        markers(X,Y)
        if stage>=3:
            # Identical inset axes make the remaining displacement comparable
            # across the second and third exchanges. No numerical rescaling
            # of errors or fitting is performed by the diagram generator.
            Zx=lambda t:695+180*(t-.18)/.07
            Zy=lambda e:100+190*(-.00169-e)/.000046
            d.text(780,62,'Close-up of minimum',size=14)
            d.text(695,85,'Error × 10⁻³',anchor='start',size=12)
            for e in [-.00169,-.00171,-.00173]:
                line(d,695,Zy(e),875,Zy(e),'#d8d4ca')
                d.text(687,Zy(e)+4,f'{e*1000:.2f}',anchor='end',size=11)
            for t in [.18,.215,.25]:d.text(Zx(t),315,f'{t:g}',size=11)
            d.text(785,340,'t',size=13)
            d.parts.append(f'<defs><clipPath id="remez-detail-{stage}"><rect x="695" y="100" width="180" height="190"/></clipPath></defs><g clip-path="url(#remez-detail-{stage})">')
            if index>1:
                plot([(x,y) for x,y in trace[index-1]['samples'] if .18<=x<=.25],Zx,Zy,'#aeb4b8',1.5)
            plot([(x,y) for x,y in frame['samples'] if .18<=x<=.25],Zx,Zy,BLUE,2.5)
            markers(Zx,Zy,True)
            d.parts.append('</g>')
        else:
            side=[
                ['Solve the four equations','at the chosen coordinates.','Only those four errors','are forced to be equal.'],
                ['Find the extrema of this','same error curve.','The interior peaks are at','t ≈ 0.204 and 0.725.'],
                ['The new chosen points','were the old extrema.','Refitting changes where','the new extrema occur.']
            ][stage]
            for j,text in enumerate(side):d.text(660,135+25*j,text,size=14,anchor='start')
        d.parts.append(f'<circle cx="90" cy="393" r="6" fill="#faf9f6" stroke="{RUST}" stroke-width="2"/>')
        d.text(104,398,'Chosen point',anchor='start',size=13)
        d.parts.append(f'<circle cx="270" cy="393" r="3.6" fill="{RUST}"/>')
        d.text(283,398,'Actual extremum',anchor='start',size=13)
        line(d,455,393,490,393,SLATE,True)
        d.text(502,398,'Equal error imposed at chosen points',anchor='start',size=13)
        svg='\n'.join(d.parts+['</svg>'])
        html.append(f'<div data-frame="{stage}"'+(' hidden' if stage else '')+'>'+svg+f'<p>{caption}</p></div>')
    html.append('<button type="button">Locate peaks</button> <span aria-live="polite">Step 1 of 6</span></div>')
    html.append('''<script>
(() => {
 const root=document.getElementById('remez-sequence');
 const frames=[...root.querySelectorAll('[data-frame]')];
 const labels=['Locate peaks','Exchange and solve','Locate new peaks','Exchange and solve','Check convergence','Replay'];
 const button=root.querySelector('button'); const status=root.querySelector('[aria-live]');let i=0;
 button.addEventListener('click',()=>{frames[i].hidden=true;i=(i+1)%frames.length;frames[i].hidden=false;button.textContent=labels[i];status.textContent=`Step ${i+1} of ${frames.length}`;});
})();
</script>''')
    (ROOT/'includes/remez-sequence.qmd').write_text('```{=html}\n'+'\n'.join(html)+'\n```\n')

search_flow();ulps();intervals();coupled_refit();alternation();remez()
