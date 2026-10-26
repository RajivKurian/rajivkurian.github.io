"""Check Part 4's published numbers and download against its frozen dataset."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'data/rtl-producer.json').read_text())
records = data['records']
assert [r['id'] for r in records] == list(range(1, 11))
assert data['numerical_design']['register_stages'] == 4
assert all(len(r['graph_register_bits_by_stage']) == 5 for r in records)
text = (ROOT / 'posts/rtl-producer.qmd').read_text().replace('**', '')
for r in records:
    assert r['slack_ps'] > 0
    for field in ['library_sha256','sdc_sha256','testbench_sha256','eda_bundle_id','clock_period_ps']:
        assert r['measurement'][field] == records[0]['measurement'][field]
selected = records[1]
assert round(100*(1-selected['area_um2']/records[0]['area_um2']),2) == 7.10
assert round(100*(1-selected['power_mw']/records[0]['power_mw']),2) == 4.89
assert records[0]['flip_flops']-selected['flip_flops'] == 16
archive = ROOT / 'docs/artifacts/rtl-producer-experiments.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest() == data['provenance']['download_sha256']
with zipfile.ZipFile(archive) as bundle:
    for r in records:
        report = json.loads(bundle.read(f"measurements/{r['name']}.json"))
        for name, digest in report['rtl_sha256'].items():
            assert hashlib.sha256(bundle.read(f"circuits/{r['name']}/{name}")).hexdigest() == digest
        for log in ['simulation.log','gate_simulation.log']:
            assert b'PASS:' in bundle.read(f"circuits/{r['name']}/{log}")
print('Archived four-cycle comparisons: common constraints, RTL hashes and checked logs verified.')

# Worked bit examples used in the four design-atom diagrams.
assert 13 * 7 == 13 + 26 + 52 == -13 + (26 << 2) == 91
assert (8 + 2)//2 == 5 and (18 + 2)//2 == 10
full = 30 + 66
low = 14 + 2
upper = 1 + 4 + (low >> 4)
assert full == 96 and low == 16 and full >> 4 == upper == 6
assert low & 15 == 0  # Exact discarded low sum: guard/sticky both zero.
widget = (ROOT / 'includes/rtl-explorer.qmd').read_text()
assert 'id="rtl-clock"' in widget
assert 'Show generated RTL' not in widget
assert 'Structural RTL outline' not in widget
assert 'Exact source assignments for this block' in widget
payload=re.search(r'<script type="application/json" id="rtl-explorer-data">(.*?)</script>',widget,re.S).group(1)
cases=json.loads(payload)
assert len(cases)==11 and sum(len(c['blocks']) for c in cases)==111
for c in cases:
    assert c['svg'].count('data-block=')==len(c['blocks'])
    assert 'reg [' in c['blocks']['rom']['full'] and "8'd255" in c['blocks']['rom']['full']
    assert all(b['code'] and b['full'] and b['origin'] for b in c['blocks'].values())
seed=cases[0]['blocks']['compress1']
columns=cases[1]['blocks']['compress1']
assert 'd2_aligned[4]' not in seed['code']
assert 'd2_aligned[4]' in columns['code']
assert len(columns['code'].splitlines())==5
assert columns['changed_lines']
assert seed['color']!=columns['color']
for c in cases:
    if c['cycles']==4:
        assert c['blocks']['cut1']['choice'] == 'No internal register'
        assert '<=' not in c['blocks']['cut1']['code']
    else:
        assert c['blocks']['cut1']['kind']=='cut'
    assert f"R{c['cycles']}" in c['blocks']['output']['choice']
assert 'producer-four-cycle-pipeline.svg' in text
assert 'downloads/' not in text
assert 'C++' not in text and 'protobuf' not in text
print('Checked worked arithmetic, recorded viewer cases and publication scope.')

booth=(ROOT/'assets/figures/producer-booth-options.svg').read_text()
for label in ['1 · Recode a and s locally','2 · Recode t locally at both multipliers','3 · Recode t once and carry its controls','5 Booth rows','8 Booth rows','10 Booth rows','27 controls']:
    assert label in booth, label
assert (8+2)//2==5 and (15+2)//2==8 and (18+2)//2==10
assert 'producer-booth-options.svg' in text
assert 'producer-shared-decode.svg' not in text
print('Checked all three Booth alternatives and their unsigned row counts.')

for name in ['producer-booth-options.svg','producer-shared-decode.svg','producer-column-compression.svg']:
    diagram=(ROOT/'assets/figures'/name).read_text()
    assert 'µm' not in diagram and 'slack' not in diagram and 'mapped flip-flops' not in diagram
print('Checked design-choice diagrams contain no measured PPA results.')

from draw_compressor_lesson import verify as verify_compressor_lesson
verify_compressor_lesson()
section=text.split('### How to compress the rows')[1].split('### How to complete the sum')[0]
for name in ['producer-compressor-unit.svg','producer-compressor-inputs.svg','producer-compressor-circuits.svg']:
    assert name in section
assert 'producer-compressor-example.svg' not in section
assert 'producer-column-compression.svg' not in section
assert 'three FAs and three HAs' in section
print('Checked both complete compressor circuits over all 128 input combinations.')

clocks=json.loads((ROOT/'data/rtl-clocks.json').read_text())
by_name={r['name']:r for r in clocks['records']}
assert len(clocks['records'])==19
for r in clocks['records']:
    if 'stage_slack_ps' in r:
        assert abs(min(r['stage_slack_ps'])-r['slack_ps'])<.011
    assert len(r['graph_register_bits_by_stage'])==r['cycles']+1
for a in clocks['activity_clocks']:
    assert a['first_timestamps_ps']==[0,a['period_ps']//2,a['period_ps']]
    assert 'PASS:' in a['simulation']
for name in ['t800_c4_ripple','t800_c4_unified_hybrid','t800_c5_ripple',
             't700_c5_ripple','t700_c5_rows','t700_c6_compress5','t700_c6_full_compress']:
    r=by_name[name]
    assert f"{r['area_um2']:.3f}" in text
    assert f"{r['slack_ps']:.2f}".replace('-','−') in text
    assert f"{r['power_mw']:.4f}" in text
assert by_name['t700_c6_product_cut']['flip_flops']-by_name['t700_c6_compress3']['flip_flops']==102
assert by_name['t700_c6_compress3']['graph_register_bits_by_stage'][4]==87
archive=ROOT/'docs/artifacts/rtl-clock-experiments.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==clocks['provenance']['archive_sha256']
with zipfile.ZipFile(archive) as bundle:
    for r in clocks['records']:
        assert hashlib.sha256(bundle.read(f"circuits/{r['name']}/sfu_poly.sv")).hexdigest()==r['measurement']['rtl_sha256']['sfu_poly.sv']
assert 'producer-ppa-search.svg' not in text
assert next(c for c in cases if c['name']=='t800_c4_unified_hybrid')['blocks']['carry1']['variant']=='hybrid'
assert next(c for c in cases if c['name']=='t700_c6_full_compress')['blocks']['product_cut2']['bits']==55
print('Clock targets: measured tables, stage paths, clock activity, pipeline views and frozen RTL verified.')

# Every clock-study step closes with its own complete measured stage snapshot.
import xml.etree.ElementTree as ET
ns={'svg':'http://www.w3.org/2000/svg'}
for r in clocks['records']:
    if r['period_ps']>=1000:continue
    name=f"producer-stages-{r['name']}.svg"
    assert name in text, f"Missing pipeline snapshot for {r['name']}"
    svg=ET.parse(ROOT/'assets/figures'/name)
    labels=[e.text for e in svg.findall('.//svg:text',ns)]
    margins=[v for v in labels if v and re.fullmatch(r'[+−]\d+\.\d{2} ps',v)]
    assert margins==[f"{v:+.2f} ps".replace('-','−') for v in r['stage_slack_ps']]
    assert [v for v in labels if v and re.fullmatch(r'R\d+',v)]==[f'R{i+1}' for i in range(r['cycles'])]
    failures=svg.findall('.//svg:rect[@fill="#f6e9e1"]',ns)
    assert len(failures)==sum(v<0 for v in r['stage_slack_ps'])
print('Checked all 17 pipeline snapshots: stage counts, margins and failure highlights match recorded timing.')

# Compression and carry completion share bit direction and incoming dependencies.
assert text.index('#### Separate and unified carry networks') < text.index('## Exploring the choices')
assert 'producer-unified-example.svg' in text
carry=(ROOT/'assets/figures/producer-carry-example.svg').read_text()
assert 'high bits left' in carry and 'compressor path' in carry
measured=(ROOT/'assets/figures/producer-clock-carry.svg').read_text()
assert 'P₂₂' in measured and 's[14]' in measured
cell=json.loads((ROOT/'data/rtl-carry-audit.json').read_text())
a,b=cell['comparison']
assert a['launch']==b['launch']=='a[3]' and a['capture']==b['capture']=='s[14]'
for r in [a,b]:
    assert r['verification']['formal_proof_success']
    assert r['verification']['replayed_cell_topology_identical']
    for v in [r['p22_arrival_ps'],r['p22_to_c30_ps'],r['p22_to_c30_ps']+r['c30_to_sum_ps']]:
        assert f'{v:.2f}' in measured
proof_archive=ROOT/'docs/artifacts/rtl-carry-audit.zip'
assert hashlib.sha256(proof_archive.read_bytes()).hexdigest()==cell['provenance']['private_archive_sha256']
with zipfile.ZipFile(proof_archive) as z:
    assert hashlib.sha256(z.read('summary.json')).hexdigest()==cell['provenance']['source_sha256']
    for r in [a,b]:assert 'SUCCESS' in z.read(r['name']+'/proof.log').decode()
print('Checked unified completion, consistent carry orientation, and the formally traced cell-delay explanation.')

for figure in ['producer-prefix-node.svg','producer-register-cuts.svg']:
    assert figure in text
assert 'short ticks' in carry.lower()
for case in cases:
    for key,block in case['blocks'].items():
        if key.startswith('carry'):
            assert len(block['code'].splitlines())<=18
            assert 'logic_' not in block['code']
print('Checked prefix/cut explanations and focused source-backed carry excerpts.')
