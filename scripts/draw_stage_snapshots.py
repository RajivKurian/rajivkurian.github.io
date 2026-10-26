"""Render each recorded clock experiment with its measured stage margins."""
from pathlib import Path
import json
import zipfile
from draw_cost_diagrams import Diagram
from rtl_viewer_blocks import fields, load, replay

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/rtl-clocks.json').read_text())
ARCHIVE=zipfile.ZipFile(ROOT/'docs/artifacts/rtl-clock-experiments.zip')
BLUE,RUST,SLATE,AMBER='#356c92','#af5137','#75828a','#9a681c'
get=lambda d,n,default=0:d.get(n,[default])[0]
sub=lambda d,n:fields(get(d,n,b''))
LABELS={
 't800_c4_ripple':'800 ps · four-cycle ripple',
 't800_c4_first_prefix':'800 ps · separate prefix networks in the first MAC',
 't800_c4_unified_prefix':'800 ps · unified prefix in the first MAC',
 't800_c4_unified_hybrid':'800 ps · unified hybrid in the first MAC',
 't800_c5_ripple':'800 ps · split the first MAC, retain ripple',
 't700_c4_ripple':'700 ps · four-cycle ripple',
 't700_c4_prefix':'700 ps · four cycles, prefix in both MACs',
 't700_c5_ripple':'700 ps · split the first MAC, retain ripple',
 't700_c5_low_block8':'700 ps · block lookahead in the second low sum',
 't700_c5_cut15':'700 ps · resolve 15 columns before the second cut',
 't700_c5_cut13':'700 ps · resolve 13 columns before the second cut',
 't700_c5_rows':'700 ps · five cycles with whole-row grouping',
 't700_c6_product_cut':'700 ps · register the second MAC’s selected rows',
 't700_c6_compress3':'700 ps · three compression layers before R4',
 't700_c6_compress4':'700 ps · four compression layers before R4',
 't700_c6_compress5':'700 ps · five compression layers before R4',
 't700_c6_full_compress':'700 ps · finish compression before R4',
}

def stages(record):
    name=record['name']
    blob=ARCHIVE.read(f'circuits/{name}/circuit.pb')
    circuit=fields(blob);impl=sub(circuit,2);design=sub(circuit,1)
    first,second=sub(impl,9),sub(impl,10)
    global_kind=get(impl,6,1)
    def carry(mac,which):
        plan=sub(mac,which)
        kind=get(plan,1,global_kind)
        return {1:'ripple',2:'prefix',3:f'hybrid, low {get(plan,2)}',4:f'block-{get(plan,3)}'}[kind]
    def drop(a,b,out):return get(sub(design,a),2)+get(sub(design,b),2)-get(sub(design,out),2)
    second_cut=get(second,3,drop(7,6,8))
    grouping='row' if get(impl,5)==1 else 'column'
    result=[['Coefficient','lookup']]
    if record['cycles']==4:
        mode=('unified ' if get(first,6) else '')+carry(first,2)
        result += [['First MAC','complete sum',mode]]
    else:
        result += [['First MAC',f'{grouping} compression','+ low sum'],['First MAC','carry completion',carry(first,2)]]
    if record['cycles']==6:
        if 8 in second:
            limit=get(second,8)
            g,_,heaps,_=load(blob,ARCHIVE.read(f'circuits/{name}/sfu_poly.sv').decode())
            layers,_,_=replay(g,heaps[1],grouping=='column',limit)
            count=len(layers)
            done=limit==0
        else:count=0;done=False
        result += [['Second MAC','row selection',f'+ {count} layers' if count and not done else '+ full compression' if done else 'raw rows stored']]
        result += [['Second MAC','low-column sum' if done else 'remaining compression',carry(second,1) if done else '+ low sum']]
    else:
        result += [['Second MAC',f'{grouping} compression',f'low {second_cut}: {carry(second,1)}']]
    result += [['Second MAC','carry completion',carry(second,2)]]
    assert len(result)==record['cycles']==len(record['stage_slack_ps'])
    return result

for record in DATA['records']:
    name=record['name']
    if name not in LABELS:continue
    labels=stages(record);slacks=record['stage_slack_ps'];worst=min(slacks)
    d=Diagram(1200,235,LABELS[name]+'; minimum setup slack at every stage')
    d.text(20,28,LABELS[name],size=22,anchor='start')
    d.text(20,56,'Setup slack at each register stage · ps',size=16,anchor='start')
    d.text(1180,56,'Timing fails' if worst<0 else 'Meets target',size=17,anchor='end',color=RUST if worst<0 else BLUE)
    step=1160/len(labels)
    for index,(lines,slack) in enumerate(zip(labels,slacks)):
        x=20+index*step;w=step-38;y=77
        bad=slack<0;limiting=slack==worst
        color=RUST if bad else AMBER if limiting else SLATE
        fill='#f6e9e1' if bad else '#f5eddb' if limiting else '#f1f0eb'
        d.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="114" rx="4" fill="{fill}" stroke="{color}" stroke-width="{2.5 if limiting else 1.2}"/>')
        for j,line in enumerate(lines):d.text(x+w/2,y+23+j*21,line,size=14 if len(labels)==6 else 16)
        signed=f'{slack:+.2f}'.replace('-','−')
        d.text(x+w/2,y+98,signed+' ps',size=19,color=color if bad or limiting else '#41484b')
        bank=x+w+15
        d.path(f'M{x+w} {y+57} H{bank}')
        d.parts.append(f'<path d="M{bank} {y+21} V{y+93}" stroke="{color}" stroke-width="3"/>')
        d.text(bank,218,f'R{index+1}',size=15)
        if index+1<len(labels):d.path(f'M{bank} {y+57} H{x+step}')
    filename=f'producer-stages-{name}.svg'
    d.save(filename)
print(f'Drew {len(LABELS)} complete pipelines from recorded per-stage timing.')
