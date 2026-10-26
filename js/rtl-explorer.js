(() => {
  const root = document.getElementById('rtl-explorer');
  if (!root) return;
  const cases = JSON.parse(document.getElementById('rtl-explorer-data').textContent);
  const selector = root.querySelector('#rtl-case');
  const clock = root.querySelector('#rtl-clock');
  let selected = 'compress1';
  const q = sel => root.querySelector(sel);
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function highlight(source) {
    const tokens = /\/\/[^\n]*|\/\*[\s\S]*?\*\/|"(?:\\.|[^"\\])*"|\b\d+'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+|\b\d+(?:\.\d+)?\b|\b(?:module|endmodule|input|output|wire|logic|reg|localparam|parameter|int|assign|always|always_ff|posedge|negedge|begin|end|if|else|case|endcase|default|generate|endgenerate|genvar|for|signed|unsigned)\b/g;
    let result = '', start = 0;
    for (const match of source.matchAll(tokens)) {
      result += escape(source.slice(start, match.index));
      const token = match[0], kind = token.startsWith('//') || token.startsWith('/*') ? 'comment' : token.startsWith('"') ? 'string' : /^\d/.test(token) ? 'number' : 'keyword';
      result += `<span class="rtl-${kind}">${escape(token)}</span>`;
      start = match.index + token.length;
    }
    return result + escape(source.slice(start));
  }
  function code(target, source, changed = []) {
    target.innerHTML = source.split('\n').map((line, i) => `<span class="rtl-code-line${changed.includes(i) ? ' rtl-line-changed' : ''}">${highlight(line) || ' '}</span>`).join('');
    target.parentElement.scrollTop = 0; target.parentElement.scrollLeft = 0;
  }
  function tab(name, focus = false) {
    for (const value of ['logic','rom']) {
      const button = q(`#rtl-${value}-tab`), active = name === value;
      button.setAttribute('aria-selected', String(active)); button.tabIndex = active ? 0 : -1;
      q(`#rtl-${value}-panel`).hidden = !active;
      if (active && focus) button.focus();
    }
    root.querySelectorAll('.rtl-node').forEach(node=>{const active=node.dataset.block===(name==='rom'?'rom':selected);node.classList.toggle('rtl-node-selected',active);node.setAttribute('aria-pressed',String(active));});
  }
  function detailDiagram(block) {
    const color = block.color;
    const text = (x,y,s) => `<text x="${x}" y="${y}" text-anchor="middle">${escape(s)}</text>`;
    const box = (x,y,w,h,label) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="3" fill="#faf9f6" stroke="${color}"/>${text(x+w/2,y+h/2+4,label)}`;
    const path = d => `<path d="${d}" fill="none" stroke="${color}" marker-end="url(#rtl-detail-arrow)"/>`;
    let body='',height=140;
    if(block.kind==='compression') {
      body=block.inputs.map((s,i)=>box(8,8+i*34,94,26,s)+path(`M102 ${21+i*34}H${125+i*14}V${42+i*14}H169`)).join('');
      const column=block.column ?? 4;
      body+=box(170,32,108,48,'compress')+path('M278 45H322V27H345')+path('M278 67H322V92H345')+text(401,31,`sum · weight ${column}`)+text(401,96,`carry · weight ${column+1}`);
      body+=text(245,132,`Three equal-weight bits at column ${column}`);
    } else if(block.kind==='product') {
      body=box(8,8,140,32,block.variant==='shared'?'carried controls':block.choice.split(' · ')[0])+path('M148 24H183')+box(184,8,134,32,block.variant==='shared'?'controls arrive': 'local decoder')+path('M251 40V73')+box(184,74,134,32,'select 0, ±u, ±2u')+box(8,74,140,32,'other operand')+path('M148 90H183')+path('M318 90H346')+text(405,94,`${block.rows} rows`);
    } else if(block.kind==='boundary') {
      body=box(8,35,150,36,'compressed rows')+path('M158 53H210')+box(212,35,190,36,'carry completion');
      body+=text(245,112,'Combinational signals · no register bank');
    } else if(block.kind==='cut') {
      if(block.variant==='resolved')body=box(8,12,150,32,'two full rows')+path('M158 28H190')+box(191,12,125,32,'low-column sum')+path('M255 44V75')+box(175,77,160,36,'upper pair + carry');
      else body=box(8,12,160,38,block.complete_compression?'compressed pair':block.variant==='early'?'unfinished heap':'full row pair')+path('M168 31H210')+box(212,12,180,38,'store live positions');
      body+=`<path d="M7 121H484" stroke="${color}" stroke-width="3"/>`+text(245,138,`${block.bits} bits at this bank`);height=150;
    } else if(block.kind==='carry') {
      if(block.variant==='hybrid') {
        body=box(12,45,240,40,'prefix · upper columns')+path('M322 65H252')+box(322,45,150,40,'ripple · low 8');
        body+=text(132,20,'upper row bits')+path('M132 25V45')+text(397,20,'low row bits')+path('M397 25V45');
        body+=text(245,120,'High bits left · low carry travels left');
      } else if(block.variant==='ripple') {
        for(let i=0;i<4;i++){body+=box(12+i*120,42,92,35,i===0?'high':i===3?'low':'carry group');body+=path(`M${58+i*120} 15V42`);if(i)body+=path(`M${12+i*120} 60H${i*120-16}`);}
        body+=text(245,112,'Row bits enter above; carries travel left');
      }else{
        const xs=[418,298,178,58];
        for(const x of xs)body+=path(`M${x} 12V35`)+`<circle cx="${x}" cy="40" r="4" fill="${color}"/>`;
        for(let level=0;level<2;level++){const stride=1<<level,y=75+level*35;for(let i=0;i<4;i++){body+=path(`M${xs[i]} ${y-30}V${y-5}`);if(i>=stride)body+=path(`M${xs[i-stride]} ${y-30}L${xs[i]} ${y-5}`);body+=`<circle cx="${xs[i]}" cy="${y}" r="4" fill="${color}"/>`;}}
        body+=text(245,140,'High bits left · combine from low toward high');height=155;
      }
    } else { const r=block.choice.match(/R\d+/)?.[0] ?? 'R4';body=box(20,35,180,36,'completed result')+path('M200 53H270')+box(272,35,170,36,`${r} · output`); }
    return `<svg viewBox="0 0 490 ${height}" role="img" aria-label="${escape(block.choice)} detail"><defs><marker id="rtl-detail-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10" fill="${color}"/></marker></defs>${body}</svg>`;
  }
  function renderBlock() {
    const item = cases.find(c => c.id === Number(selector.value));
    const block=item.blocks[selected];
    q('.rtl-code-pane').style.setProperty('--choice-color',block.color);
    root.querySelectorAll('.rtl-node').forEach(node=>{const active=node.dataset.block===(q('#rtl-rom-tab').getAttribute('aria-selected')==='true'?'rom':selected);node.classList.toggle('rtl-node-selected',active);node.setAttribute('aria-pressed',String(active));});
    q('.rtl-block-title').textContent=block.title;
    const alternatives=new Map();
    for(const entry of cases.filter(c=>c.period_ps===item.period_ps)){const b=entry.blocks[selected];if(b)alternatives.set(b.variant,{choice:b.choice,color:b.color});}
    q('.rtl-choice-legend').innerHTML=[...alternatives].map(([variant,b])=>`<span class="${variant===block.variant?'rtl-choice-selected':''}" style="--choice-color:${b.color}"><i></i>${escape(b.choice)}</span>`).join('');
    q('.rtl-block-explanation').textContent=block.explanation;
    q('.rtl-local-diagram').innerHTML=detailDiagram(block);
    q('.rtl-code-label').textContent=block.kind==='boundary'?'RTL excerpt · generated assignments':'RTL excerpt · local signal aliases';
    code(q('.rtl-focused-code code'),block.code,block.changed_lines);
    q('.rtl-source-origin').textContent=block.origin+(block.changed_lines.length?' · shaded lines differ from the comparison excerpt':'');
    q('.rtl-baseline summary').textContent=`Compare with ${block.baseline.label}`;
    q('.rtl-baseline').hidden=!block.changed;
    q('.rtl-baseline p').textContent=block.baseline.choice;
    q('.rtl-baseline').style.setProperty('--baseline-color',block.baseline.color);
    code(q('.rtl-baseline code'),block.baseline.code);
    code(q('.rtl-source-details code'),block.full);
    q('.rtl-source-details').open=false;
    q('.rtl-baseline').open=false;
  }
  function render() {
    const item=cases.find(c=>c.id===Number(selector.value));
    const seed=cases.find(c=>c.period_ps===item.period_ps&&c.is_baseline);
    if(!item.blocks[selected])selected='compress1';
    q('.rtl-case-summary').textContent=item.summary;
    const delta=(v,n,u)=>`${v>0?'+':''}${v.toFixed(n)}${u}`;
    const metrics=[['Cell area',`${item.area_um2.toFixed(3)} µm²`,delta(100*(item.area_um2/seed.area_um2-1),2,'%')],['Setup slack',`${item.slack_ps.toFixed(2)} ps`,delta(item.slack_ps-seed.slack_ps,2,' ps')],['Activity power',`${item.power_mw.toFixed(4)} mW`,delta(100*(item.power_mw/seed.power_mw-1),2,'%')],['Flip-flops',item.flip_flops,delta(item.flip_flops-seed.flip_flops,0,'')]];
    q('.rtl-metrics').innerHTML=metrics.map(([label,value,change])=>`<div><span>${label}</span><strong>${value}</strong><small>${change} vs starting circuit</small></div>`).join('');
    q('.rtl-comparison-note').textContent=`${item.cycles} cycles, one input per cycle. ${item.slack_ps>=0?'Meets':'Misses'} the ${item.period_ps} ps target. Changes compare with the starting circuit at this target.`;
    q('.rtl-circuit').innerHTML=item.svg;
    const rom=item.blocks.rom;
    q('.rtl-rom-explanation').textContent=rom.explanation;
    code(q('.rtl-rom-interface'),rom.code);code(q('.rtl-rom-code'),rom.full);
    q('.rtl-rom-details').open=false;
    renderBlock();
  }
  q('.rtl-circuit').addEventListener('click',event=>{const node=event.target.closest('[data-block]');if(!node)return;if(node.dataset.block==='rom'){tab('rom');return;} selected=node.dataset.block;tab('logic');renderBlock();});
  q('.rtl-circuit').addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();event.target.closest('[data-block]')?.dispatchEvent(new MouseEvent('click',{bubbles:true}));}});
  for(const name of ['logic','rom']) {
    q(`#rtl-${name}-tab`).addEventListener('click',()=>tab(name));
    q(`#rtl-${name}-tab`).addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();tab(e.key==='Home'?'logic':e.key==='End'?'rom':name==='logic'?'rom':'logic',true);}});
  }
  selector.addEventListener('change',render);
  clock.addEventListener('change',()=>{
    selector.innerHTML=cases.filter(c=>c.period_ps===Number(clock.value)).map(c=>`<option value="${c.id}">${escape(c.label)}</option>`).join('');
    render();
  });
  render();
})();
