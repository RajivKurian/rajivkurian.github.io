"""Prebuild the article's recorded circuits, RTL views and measurements."""
from html import escape
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'data/rtl-clocks.json').read_text())
archive = zipfile.ZipFile(ROOT / 'docs/artifacts/rtl-clock-experiments.zip')
from rtl_viewer_blocks import build as build_blocks

def config(name):
    text=archive.read(f'producer/fixtures/{name}.textproto').decode()
    return dict(re.findall(r'^(\w+): (\w+)\s*$',text,re.M))

COLORS={'fixed':'#75828a','narrow':'#356c92','residual':'#a36a18','shared':'#af5137',
 'rows':'#356c92','columns':'#af5137','ripple':'#356c92','prefix':'#a36a18',
 'resolved':'#356c92','full':'#af5137','early':'#a36a18','hybrid':'#af5137'}

def diagram(record,blocks):
    extra=(80 if 'product_cut2' in blocks else 0)-(0 if 'compress2' in blocks else 80)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 {1010+extra}" aria-label="Clickable polynomial circuit">',
      '<defs><marker id="rtl-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10" fill="#75828a"/></marker></defs>']
    def txt(x,y,s,size=13):parts.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{size}">{escape(s)}</text>')
    positions=[('rom',15),('product1',120),('compress1',200),('cut1',280),('carry1',360),('product2',500)]
    if 'product_cut2' in blocks:positions.append(('product_cut2',580))
    if 'compress2' in blocks:positions.append(('compress2',580+extra))
    positions += [('cut2',660+extra),('carry2',740+extra),('output',880+extra)]
    for n,(key,y) in enumerate(positions):
        b=blocks[key];color=COLORS[b['variant']]
        if n:
            prev=positions[n-1][1]+68
            parts.append(f'<path d="M210 {prev}V{y}" stroke="#75828a" marker-end="url(#rtl-arrow)"/>')
        if key=='product1':txt(210,110,'R1 · coefficient operands',12)
        if key=='product2':txt(210,468,f'R{2 if record["cycles"]==4 else 3} · 15-bit s + delayed t and c',12)
        if key=='output':txt(210,848+extra,f'R{record["cycles"]} · 25-bit result',12)
        parts.append(f'<g role="button" tabindex="0" class="rtl-node" data-block="{key}" aria-label="{escape(b["title"])}" style="--choice-color:{color}">')
        parts.append(f'<rect class="rtl-node-box" x="35" y="{y}" width="350" height="68" rx="4" stroke="{color}"/>')
        label={'product_cut2':b['title'],'product1':'a × t · Booth products','product2':'s × t · Booth products','compress1':'Compression + aligned b','compress2':'Compression + aligned c','cut1':'No internal register' if b['kind']=='boundary' else b['title'],'cut2':b['title'],'carry1':'First sum completion','carry2':'Second sum completion','rom':'Coefficient ROM','output':'Retained result / output'}[key]
        txt(210,y+20,label,14)
        if b['kind']=='compression':
            # Rows and columns have different grouping pictures, at word-group level.
            for j in range(3):
                parts.append(f'<rect x="{66+j*36}" y="{y+34}" width="26" height="5" fill="{color}"/>')
                if b['variant']=='rows':parts.append(f'<rect x="{66+j*36}" y="{y+43}" width="26" height="5" fill="{color}" opacity=".5"/>')
            if b['variant']=='columns':
                parts.append(f'<path d="M78 {y+31}V{y+52}M114 {y+31}V{y+52}M150 {y+31}V{y+52}" stroke="{color}" stroke-width="2"/>')
            txt(270,y+44,b['choice'],12)
        elif b['kind']=='carry':
            count=4
            for j in range(count):
                x=65+j*26;parts.append(f'<rect x="{x}" y="{y+35}" width="14" height="12" fill="none" stroke="{color}"/>')
                if j:parts.append(f'<path d="M{x} {y+41}H{x-12}" stroke="{color}"/>')
            if b['variant']=='prefix':parts.append(f'<path d="M72 {y+33}V{y+28}H150V{y+33}M98 {y+33}V{y+23}H124V{y+33}" fill="none" stroke="{color}"/>')
            if b['variant']=='hybrid':parts.append(f'<path d="M124 {y+33}V{y+26}H150V{y+33}" fill="none" stroke="{color}"/>')
            txt(270,y+45,b['choice'],12)
        else:txt(210,y+44,b['choice']+(f' · {b["bits"]} bank bits' if 'bits' in b else ''),12)
        parts.append('</g>')
    parts.append(f'<text x="210" y="{985+extra}" text-anchor="middle" font-size="12">Select a block to inspect its logic.</text></svg>')
    return ''.join(parts)

cases=[]
# Each prepared case retains its own clock, schedule and archived block ownership.
for name in data['viewer']:
    record=next(r for r in data['records'] if r['name']==name)
    k=config(record['name'])
    rtl=archive.read(f'circuits/{record["name"]}/sfu_poly.sv').decode()
    blocks=build_blocks(record,k,archive.read(f'circuits/{record["name"]}/circuit.pb'),rtl)
    for block in blocks.values():block['color']=COLORS[block['variant']]
    cases.append({**{key:record[key] for key in ['id','name','label','area_um2','slack_ps','power_mw','flip_flops','period_ps','cycles','is_baseline']},
      'summary':record['summary'], 'blocks':blocks,'svg':diagram(record,blocks)})
seed=cases[0]
for case in cases:
    for key,block in case['blocks'].items():
        baseline_case=next((c for c in cases if c['period_ps']==case['period_ps'] and c['is_baseline'] and key in c['blocks']),next(c for c in cases if c['period_ps']==case['period_ps'] and key in c['blocks']))
        baseline=baseline_case['blocks'][key]
        block['baseline']={k:baseline[k] for k in ['choice','code','variant','color']}
        block['baseline']['label']=baseline_case['label']
        # A choice change is highlighted by statement, not by incidental n IDs.
        import difflib
        base_lines=baseline['code'].splitlines();current=block['code'].splitlines()
        matching=set()
        for m in difflib.SequenceMatcher(None,base_lines,current).get_matching_blocks():matching.update(range(m.b,m.b+m.size))
        block['changed_lines']=[n for n in range(len(current)) if n not in matching] if block['changed'] else []

payload=json.dumps(cases,separators=(',',':')).replace('<','\\u003c')
options=''.join(f'<option value="{c["id"]}">{escape(c["label"])}</option>' for c in cases if c['period_ps']==1000)
html='''```{=html}
<section class="rtl-explorer" id="rtl-explorer" aria-label="Recorded RTL implementation comparison">
<div class="rtl-explorer-controls"><label for="rtl-clock">Clock target</label><select id="rtl-clock"><option value="1000">1 ns</option><option value="800">800 ps</option><option value="700">700 ps</option></select><label for="rtl-case">Recorded implementation</label><select id="rtl-case">'''+options+'''</select></div>
<p class="rtl-case-summary" aria-live="polite">'''+escape(seed['summary'])+'''</p>
<div class="rtl-metrics"></div>
<p class="rtl-comparison-note">Measurements cover lookup and polynomial arithmetic. Changes compare with the starting circuit at the selected clock target.</p>
<div class="rtl-inspection">
<div class="rtl-circuit-pane"><h4>Choose a circuit block</h4><div class="rtl-circuit">'''+seed['svg']+'''</div><p class="rtl-view-note">Bank counts include carried operands and valid/control bits, before cell mapping.</p></div>
<div class="rtl-code-pane">
<div class="rtl-tabs" role="tablist" aria-label="Implementation views"><button role="tab" id="rtl-logic-tab" aria-controls="rtl-logic-panel" aria-selected="true">Selected block</button><button role="tab" id="rtl-rom-tab" aria-controls="rtl-rom-panel" aria-selected="false" tabindex="-1">ROM contents</button></div>
<div id="rtl-logic-panel" role="tabpanel" aria-labelledby="rtl-logic-tab">
<h4 class="rtl-block-title">Compression</h4>
<div class="rtl-choice-legend"></div>
<p class="rtl-block-explanation"></p>
<div class="rtl-local-diagram"></div>
<p class="rtl-view-note">Excerpts use local aliases. Expand exact source for original identifiers and line numbers.</p>
<div class="rtl-code-label">Logic excerpt · local signal aliases</div>
<pre class="rtl-focused-code" tabindex="0" aria-label="Selected block RTL"><code></code></pre>
<p class="rtl-source-origin"></p>
<details class="rtl-baseline"><summary>Compare with the starting circuit</summary><p></p><pre tabindex="0"><code></code></pre></details>
<details class="rtl-source-details"><summary>Exact source assignments for this block</summary><pre tabindex="0"><code></code></pre></details>
</div>
<div id="rtl-rom-panel" role="tabpanel" aria-labelledby="rtl-rom-tab" hidden><h4>Coefficient ROM</h4><p class="rtl-rom-explanation"></p><pre tabindex="0"><code class="rtl-rom-interface"></code></pre><details class="rtl-rom-details"><summary>Expand the 256 coefficient rows</summary><pre tabindex="0"><code class="rtl-rom-code"></code></pre></details></div>
</div></div>
<noscript>Selecting blocks requires JavaScript. The worked diagrams and measured-results table remain available below.</noscript>
</section>
<script type="application/json" id="rtl-explorer-data">'''+payload+'''</script>
<script>
'''+(ROOT/'js/rtl-explorer.js').read_text()+'''
</script>
```
'''
# The first block and measurements also render without browser scripting.
static=seed['blocks']['compress1']
html=html.replace('<p class="rtl-block-explanation"></p>', '<p class="rtl-block-explanation">'+escape(static['explanation'])+'</p>').replace('<pre class="rtl-focused-code" tabindex="0" aria-label="Selected block RTL"><code></code></pre>', '<pre class="rtl-focused-code" tabindex="0" aria-label="Selected block RTL"><code>'+escape(static['code'])+'</code></pre>')
metrics=''.join('<div><span>'+label+'</span><strong>'+value+'</strong></div>' for label,value in [('Cell area',f"{seed['area_um2']:.3f} µm²"),('Setup slack',f"{seed['slack_ps']:.2f} ps"),('Activity power',f"{seed['power_mw']:.4f} mW"),('Flip-flops',str(seed['flip_flops']))])
html=html.replace('<div class="rtl-metrics"></div>', '<div class="rtl-metrics">'+metrics+'</div>')
(ROOT/'includes/rtl-explorer.qmd').write_text(html)
print(f'Prepared {len(cases)} circuits with {sum(len(c["blocks"]) for c in cases)} traced blocks.')
