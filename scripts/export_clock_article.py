"""Freeze the directed clock-target experiments for independent rendering."""
import hashlib
import json
import re
from pathlib import Path
import zipfile
from rtl_viewer_blocks import load

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT.parent / 'code'
STUDY = CODE / 'rtl/producer/clock_search'
report = json.loads((STUDY/'results/comparison.json').read_text())
old = json.loads((ROOT/'data/rtl-producer.json').read_text())
old_archive = zipfile.ZipFile(ROOT/'docs/artifacts/rtl-producer-experiments.zip')
sha = lambda b: hashlib.sha256(b).hexdigest()
records=[]; files={}; inputs={}
LABELS={
 't1000_c4_ripple':'Four cycles · column compression',
 't800_c4_ripple':'Four cycles · ripple',
 't800_c4_first_prefix':'Four cycles · separate prefix sums',
 't800_c4_unified_prefix':'Four cycles · unified prefix',
 't800_c4_unified_hybrid':'Four cycles · unified hybrid',
 't800_c5_ripple':'Five cycles · ripple',
 't700_c5_ripple':'Five cycles · column compression',
 't700_c5_rows':'Five cycles · whole-row compression',
 't700_c5_cut15':'Five cycles · cut at column 15',
 't700_c5_cut13':'Five cycles · cut at column 13',
 't700_c6_product_cut':'Six cycles · store product rows',
 't700_c6_compress3':'Six cycles · compress before storage',
 't700_c6_compress4':'Six cycles · four layers before storage',
 't700_c6_compress5':'Six cycles · five layers before storage',
 't700_c6_full_compress':'Six cycles · finish compression before storage',
}
SUMMARIES={
 't1000_c4_ripple':'Column compression reduces storage and logic while the four-cycle ripple pipeline meets 1 ns.',
 't800_c4_ripple':'At 800 ps, the complete first multiply-add misses timing; both second-MAC stages meet.',
 't800_c4_unified_prefix':'A single prefix network spans the first sum. It narrowly misses the 800 ps target.',
 't800_c4_unified_hybrid':'Eight low columns ripple; the upper suffix uses prefix completion. Four cycles now meet 800 ps.',
 't800_c5_ripple':'Splitting the first multiply-add also meets 800 ps, with another 61 register bits and a fifth cycle.',
 't700_c5_ripple':'After splitting the first MAC, the second compression and low-column addition miss 700 ps.',
 't700_c5_rows':'Whole-row grouping changes the dependency paths and meets 700 ps, with a larger cut bank.',
 't700_c5_cut13':'Moving four unresolved columns across the second cut helps, but this five-cycle fit still misses timing.',
 't700_c6_product_cut':'A new register separates second-MAC product selection from compression. It closes timing but stores 189 signals in that bank.',
 't700_c6_compress3':'Three compressor layers run before the extra register, shrinking its bank from 189 to 87 bits while retaining positive slack.',
 't700_c6_full_compress':'Compression finishes before the extra register. Its bank holds 55 signals instead of 189, and the circuit meets 700 ps.',
}
for i,t in enumerate(report['trials'],1):
    name=t['name']; base=STUDY/'results'/name; m=t['measurement']
    for fn,digest in m['rtl_sha256'].items():assert sha((base/'generated'/fn).read_bytes())==digest
    assert sha((base/'clock.sdc').read_bytes())==m['sdc_sha256']
    for fn in ['simulation.log','gate_simulation.log']:assert b'PASS:' in (base/fn).read_bytes()
    gates,_,_,_=load((base/'generated/circuit.pb').read_bytes(),(base/'generated/sfu_poly.sv').read_text())
    counts=[sum(g['live'] and g['op']==7 and g['stage']==stage for g in gates.values()) for stage in range(t['cycles']+1)]
    records.append(dict(id=i,name=name,label=LABELS.get(name,name),period_ps=m['clock_period_ps'],
        cycles=t['cycles'],area_um2=m['cell_area_um2'],slack_ps=m['worst_setup_slack_ps'],
        power_mw=m['power']['Total']['total']*1000,flip_flops=t['flip_flops'],
        graph_register_bits_by_stage=counts,measurement=m,summary=SUMMARIES.get(name,t['hypothesis'])))
    pathlog=(base/'audit/stage_paths.log').read_text()
    stages=[]
    for section in pathlog.split('SEQUENTIAL_DEPTH ')[1:]:
        stages.append(float(re.search(r'([-\d.]+)\s+slack',section)[1]))
    assert len(stages)==t['cycles']
    assert abs(min(stages)-m['worst_setup_slack_ps'])<.011
    records[-1]['stage_slack_ps']=stages
    files[f'producer/fixtures/{name}.textproto']=(STUDY/f'{name}.impl.textproto').read_bytes()
    for fn in ['sfu_poly.sv','circuit.pb','circuit.textproto','bench.cc','fixture.h']:
        files[f'circuits/{name}/{fn}']=(base/'generated'/fn).read_bytes()
    files[f'measurements/{name}.json']=(base/'reports/summary.json').read_bytes()
    inputs[name]=sha(files[f'measurements/{name}.json'])

# Keep the four-cycle starting circuit and Booth comparisons at 1 ns from the
# previous checked run. They use the same table, clock, library and stimulus.
seed=next(r for r in old['records'] if r['name']=='narrow_local').copy()
seed.update(id=101,period_ps=1000,cycles=4,label='Four cycles · whole-row starting circuit',
            summary='Start with local narrow-operand Booth recoding, whole-row compression and ripple carry completion.')
records.append(seed)
for fn in ['sfu_poly.sv','circuit.pb','circuit.textproto','bench.cc','fixture.h']:
    path=f'circuits/{seed["name"]}/{fn}'
    if path in old_archive.namelist():files[path]=old_archive.read(path)
files['producer/fixtures/narrow_local.textproto']=old_archive.read('producer/fixtures/narrow_local.textproto')
for r in records:
    for field in ['library_sha256','eda_bundle_id','conda_environment']:
        assert r['measurement'][field]==records[0]['measurement'][field]

viewer=['narrow_local','t1000_c4_ripple',
        't800_c4_ripple','t800_c4_unified_prefix','t800_c4_unified_hybrid','t800_c5_ripple',
        't700_c5_ripple','t700_c5_rows','t700_c5_cut13','t700_c6_product_cut','t700_c6_full_compress']
viewer=[n for n in viewer if any(r['name']==n for r in records)]
for r in records:r['is_baseline']=r['name'] in ['narrow_local','t800_c4_ripple','t700_c5_ripple']
files['plan.json']=(STUDY/'results/plan.json').read_bytes()
for p in (STUDY/'results/sources').iterdir():files[f'producer/{p.name}']=p.read_bytes()
archive=ROOT/'docs/artifacts/rtl-clock-experiments.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for name,b in sorted(files.items()):
        info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o644<<16
        z.writestr(info,b)
result=dict(records=records,viewer=viewer,
    activity_clocks=json.loads((STUDY/'results/activity-clocks.json').read_text()),
    booth_comparison=[r for r in old['records'] if r['name'] in ['column_local','column_residual_local','column_residual_carried']],
    provenance=dict(measurement_sha256=inputs,archive_sha256=sha(archive.read_bytes())))
(ROOT/'data/rtl-clocks.json').write_text(json.dumps(result,indent=2)+'\n')
print(f'Exported {len(records)} measurements; {len(viewer)} curated circuit views.')
