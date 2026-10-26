#!/usr/bin/env python3
"""Check explanatory math and the provenance of embedded MPFR examples."""
import hashlib
import json
from pathlib import Path
import subprocess
import importlib.util

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('article_tools', root / 'scripts/site.py')
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)
prefix, lock, identity = tools.environment()
tools.verify(prefix, lock, identity)
subprocess.run([str(prefix / 'bin/deno'), 'run', '--allow-read',
                str(root / 'scripts/check_sfu_models.js')], check=True)
data_path = root / 'data/base-conversion.json'
data = json.loads(data_path.read_text())
metadata = json.loads((root / 'data/base-conversion.provenance.json').read_text())
assert hashlib.sha256(data_path.read_bytes()).hexdigest() == metadata['data_sha256']
assert len(data['rows']) == 641
assert data['rows'][0][4:] == [0x3f800000] * 3
assert all(row[0] == -i/8 for i, row in enumerate(data['rows']))
embedded = '<script id="conversion-data" type="application/json">\n' + data_path.read_text() + '</script>\n'
assert (root / 'data/base-conversion.html').read_text() == embedded
print('Checked MPFR dataset hash, input grid, exact zero and embedded copy.')

# Independently reconstruct the real-coefficient design curves from the export.
from decimal import Decimal, localcontext
fit_path = root / 'data/design-points.json'
fit_metadata = json.loads((root / 'data/design-points.provenance.json').read_text())
assert hashlib.sha256(fit_path.read_bytes()).hexdigest() == fit_metadata['data_sha256']
fits = json.loads(fit_path.read_text(), parse_float=Decimal)
assert {(d['rows'], d['degree']) for d in fits['designs']} == {(n,d) for n in [1,2,4,8] for d in [1,2,3]}
with localcontext() as context:
    context.prec = 60
    for design in fits['designs']:
        assert design['extrema_spread'] < Decimal('1e-7')
        q = Decimal(2).ln() / design['rows']
        for t, exported_error in design['samples']:
            p = Decimal(0)
            for coefficient in reversed(design['coefficients']):
                p = p*t + coefficient
            error = p/((q*t).exp())-1
            assert abs(error-exported_error) < Decimal('2e-15')
            assert abs(error) <= design['max_relative_error']*(1+Decimal('1e-7'))+Decimal('2e-15')
print('Checked 12 relative-minimax exports against independent 60-digit polynomial/error evaluation.')

# A copied table must remain bound to the exhaustive report for those exact
# coefficient words, widths and modes. Sampling metadata cannot satisfy this.
accepted = json.loads((root / 'data/rounding-accepted.json').read_text())['rounding_search']
measurements = json.loads((root / 'data/rounding-measurements.json').read_text())
for i, candidate in enumerate(accepted):
    report = candidate['exhaustive']
    assert report['accepted'] and report['exhaustive_fp32'] and report['complete_range']
    assert report['begin'] == 0 and report['end'] == report['tested'] == 2**32
    assert all(report[key] == 0 for key in ['failures', 'special_failures', 'exceptions', 'monotonicity_violations'])
    assert report['max_ulp'] <= 2
    canonical = '7 ' + ' '.join(map(str, candidate['shape'] + [int(candidate['first_rne']), int(candidate['final_rne'])])) + '\n'
    canonical += '\n'.join(' '.join(map(str, row)) for row in candidate['coefficients']) + '\n'
    assert hashlib.sha256(canonical.encode()).hexdigest() == report['profile_sha256']
    measured = measurements['results'][i]
    assert measured['profile'] == i
    assert all(measured[key] == candidate[key] for key in ['shape', 'first_rne', 'final_rne'])
assert measurements['selected_profile'] == min(measurements['results'], key=lambda r:r['normalized_cost'])['profile']
trace = json.loads((root / 'data/remez-trace.json').read_text())['trace']
assert max(abs(y) for _, y in trace[0]['extrema']) > 1.5 * trace[0]['bound']
for frame in trace:
    assert all(abs(abs(y)-frame['bound']) < 1e-15 for _, y in frame['selected'])
last = [y for _, y in trace[-1]['extrema']]
assert all(a*b < 0 for a,b in zip(last,last[1:]))
assert max(abs(y) for y in last)-min(abs(y) for y in last) < 1e-14
print('Checked exhaustive table/report hashes, mapped-profile bindings and Remez exchange data.')
provenance = json.loads((root / 'data/part3.provenance.json').read_text())
for name, digest in provenance['data_sha256'].items():
    assert hashlib.sha256((root / 'data'/name).read_bytes()).hexdigest() == digest
print('Checked Part 3 exported-dataset hashes.')

study = json.loads((root / 'data/hardware-search.json').read_text())
records = {r['name']: r for r in study['records']}
for candidate in records.values():
    report = candidate['exhaustive']
    canonical = str(candidate['table_bits']) + ' ' + ' '.join(map(str, candidate['shape'] + [int(candidate['first_rne']), int(candidate['final_rne'])])) + '\n'
    canonical += '\n'.join(' '.join(map(str, row)) for row in candidate['coefficients']) + '\n'
    assert hashlib.sha256(canonical.encode()).hexdigest() == report['profile_sha256']
    assert len(candidate['coefficients']) == 1 << candidate['table_bits']
    assert report['complete_range'] and report['tested'] == 2**32
    if candidate['mapped']:
        assert report['accepted'] and report['max_ulp'] <= 2
        assert all(report[k] == 0 for k in ['failures','special_failures','exceptions','monotonicity_violations'])
        assert candidate['mapped']['slack_ps'] >= 0
    else:
        assert not report['accepted'] and report['failures'] > 0
    proxy = candidate['proxy']
    assert abs(proxy['cost'] - sum(proxy[k] for k in ['lookup','arithmetic','registers'])) < 1e-8
resolution = [records[k] for k in ['rows32-wide-rne','rows64-wide-rne','stage17-11','rows256-rne']]
assert min(resolution,key=lambda r:r['mapped']['normalized_cost'])['name'] == 'stage17-11'
assert min(resolution,key=lambda r:r['proxy']['cost'])['name'] == 'rows64-wide-rne'
assert [r['failures'] for r in study['refit_histories']['stage17-11']] == [16813,7417,0]
assert all(r['tested'] == 2**32 for history in study['refit_histories'].values() for r in history)
print('Checked resolution/precision study snapshots, complete acceptance, proxy accounting and refit trace.')

for candidate in study['records']:
    assert candidate['architecture']['phase'] == 'before_fit'
    assert candidate['proxy']['phase'] == 'after_fit'
    assert candidate['architecture']['arithmetic'] == candidate['proxy']['arithmetic']
    assert candidate['architecture']['registers'] == candidate['proxy']['registers']
print('Checked separate architecture-only and after-fit cost records.')

method = json.loads((root / 'data/methodology-check.json').read_text())
replay = method['replay']
assert replay['seed_words'] == 9
assert replay['before_fit']['phase'] == 'before_fit'
assert replay['after_fit']['phase'] == 'after_fit'
assert replay['after_fit']['profile_sha256'] == replay['exhaustive']['profile_sha256']
for profile, report in [(replay['profile'], replay['exhaustive']), (method['neighbor'], method['neighbor']['exhaustive'])]:
    canonical = str(profile['table_bits']) + ' ' + ' '.join(map(str, profile['shape'] + [int(profile['first_rne']), int(profile['final_rne'])])) + '\n'
    canonical += '\n'.join(' '.join(map(str, row)) for row in profile['coefficients']) + '\n'
    assert hashlib.sha256(canonical.encode()).hexdigest() == report['profile_sha256']
    assert report['accepted'] and report['complete_range'] and report['tested'] == 2**32
    assert all(report[k] == 0 for k in ['failures','special_failures','exceptions','monotonicity_violations'])
    assert report['max_ulp'] <= 2
neighbor = method['neighbor']
assert neighbor['table_bits'] == 6 and not neighbor['first_rne'] and not neighbor['final_rne']
assert abs(neighbor['mapped_cost'] - 1282) < 1e-8
assert neighbor['setup_slack_ps'] >= 0 and neighbor['latency_cycles'] == 6 and neighbor['initiation_interval_cycles'] == 1
assert [r['name'] for r in sorted(resolution, key=lambda r:r['architecture']['cost'])] == ['rows32-wide-rne','rows64-wide-rne','stage17-11','rows256-rne']
print('Checked staged-cost replay and exhaustive/mapped neighboring truncation design.')

# Repeated exhaustive runs add distributions to the same frozen fits. Check
# raw counts, common domains and the frontier independently of the exporter.
quality = json.loads((root/'data/numerical-quality.json').read_text())
known = {c['exhaustive']['profile_sha256']: c for c in accepted}
known.update({c['exhaustive']['profile_sha256']: c for c in study['records']})
known[neighbor['exhaustive']['profile_sha256']] = neighbor
narrow_study=json.loads((root/'data/narrow256-study.json').read_text()) if (root/'data/narrow256-study.json').exists() else {'records':[]}
narrow_records={r['name']:r for r in narrow_study['records']}
known.update({r['exhaustive']['profile_sha256']:r for r in narrow_records.values()})
expected_domains = {
    'all_finite': 2**32-2**24,
    'approximation': (0x43000000-0x32800000-1)+(0x43160000-0x32800000-1),
    'negative_approximation': 0x43160000-0x32800000-1,
    'near_zero': 0x3f800000-0x32800000,
}
expected_domains['exact_bypass'] = expected_domains['all_finite']-expected_domains['approximation']
assert len(quality['records']) == len(known) == 18+len(narrow_records)
for r in quality['records']:
    original = known[r['profile_sha256']]
    report = r['exhaustive']
    assert report['tested']==report['end']==2**32 and report['begin']==0
    assert report['exhaustive_fp32'] and report['complete_range']
    assert report['accepted']==original['exhaustive']['accepted']
    assert report['max_ulp']==original['exhaustive']['max_ulp']
    assert r['shape']==original['shape']
    for domain, denominator in expected_domains.items():
        c=report['quality'][domain]
        assert c['count']==sum(c['ulp'])==denominator
        assert c['within_one']==sum(c['ulp'][:2])
        assert c['above']+c['below']==sum(c['ulp'][1:])
        if report['accepted']: assert c['ulp'][3]==0
    assert report['quality']['exact_bypass']['ulp']==[expected_domains['exact_bypass'],0,0,0]
    if r['name'].startswith('profile-'):
        cost=measurements['results'][int(r['name'].split('-')[-1])]['normalized_cost']
    elif r['name']=='rows64-medium-tt': cost=neighbor['mapped_cost']
    elif r['name'] in narrow_records: cost=narrow_records[r['name']]['mapped_cost']
    else:
        old=records[r['name']]
        cost=old['mapped']['normalized_cost'] if old['mapped'] else None
    assert r['mapped_cost']==cost

def quality_objectives(r):
    v=[-r['mapped_cost']]
    for domain in ['approximation','negative_approximation','near_zero']:
        counts=r['exhaustive']['quality'][domain]
        v += [counts['ulp'][0],counts['within_one']]
    return v
for r in quality['records']:
    if r['mapped_cost'] is None:
        assert not r['frontier']
        continue
    objectives=quality_objectives(r)
    dominating=[]
    for other in quality['records']:
        if other['mapped_cost'] is None: continue
        values=quality_objectives(other)
        if all(a>=b for a,b in zip(values,objectives)) and any(a>b for a,b in zip(values,objectives)):
            dominating.append(other['name'])
    assert r['dominated_by']==dominating
    assert r['frontier']==(not dominating)
print(f"Checked {len(quality['records'])} full FP32 quality censuses, common-domain counts, mapped bindings and accuracy/area frontier.")

delta=json.loads((root/'data/rounding-area-delta.json').read_text())
assert delta['coefficient_change']==dict(rne_a_min=249,rne_a_max=510,truncate_a_max=512,high_bit_rows=[127])
assert delta['rne']['top_booth_zero'] and not delta['rne']['coefficient_bit_register']
assert not delta['truncate-refit']['top_booth_zero'] and delta['truncate-refit']['coefficient_bit_register']
assert abs(delta['rne']['normalized_cost']-measurements['results'][8]['normalized_cost'])<1e-8
assert abs(delta['truncate-refit']['normalized_cost']-measurements['results'][10]['normalized_cost'])<1e-8
assert abs(delta['rne']['normalized_cost']-delta['truncate-unrefitted']['normalized_cost']-40.70)<1e-8
assert abs(delta['truncate-refit']['normalized_cost']-delta['truncate-high-bit-zero']['normalized_cost']-40.15)<1e-8
assert delta['truncate-unrefitted']['structural_probe'] and delta['truncate-high-bit-zero']['structural_probe']
print('Checked the revived coefficient-bit path and the two controlled mapped-area comparisons.')

for record in narrow_records.values():
    report=record['exhaustive']
    canonical=str(record['table_bits'])+' '+' '.join(map(str,record['shape']+[int(record['first_rne']),int(record['final_rne'])]))+'\n'
    canonical+='\n'.join(' '.join(map(str,row)) for row in record['coefficients'])+'\n'
    assert hashlib.sha256(canonical.encode()).hexdigest()==report['profile_sha256']
    assert report['tested']==2**32 and report['complete_range']
    if report['accepted']:
        assert record['mapped_cost'] is not None and record['mapped']['slack_ps']>=0
        assert record['mapped_cost']==record['mapped']['normalized_cost']
    else: assert record['mapped_cost'] is None
    if record['first_rne'] and record['final_rne']:
        assert record['architecture']['phase']=='before_fit'
        assert record['proxy']['phase']=='after_fit'
        assert record['proxy']['profile_sha256']==report['profile_sha256']
print('Checked narrower 256-row fits, staged-cost records, and exhaustive/mapped bindings.')

# The displayed staged-cost comparison uses the narrower 256-row design,
# rather than the obsolete equal-width comparison's mapped-area winner.
if narrow_records:
    shown=[records[n] for n in ['rows32-wide-rne','rows64-wide-rne','stage17-11']]+[narrow_records['narrow256-s15-rne']]
    assert min(shown,key=lambda r:r['mapped']['normalized_cost'])['name']=='narrow256-s15-rne'
    assert min(shown,key=lambda r:r['proxy']['cost'])['name']=='rows64-wide-rne'
    figure=(root/'assets/figures/table-resolution-search.svg').read_text()
    for candidate in shown:
        for phase in ['architecture','proxy','mapped']:
            cost=candidate[phase]['normalized_cost' if phase=='mapped' else 'cost']
            assert f'{cost:.2f}' in figure
    print('Checked the current 256-row-led staged-cost diagram against recorded costs.')

if narrow_records:
    feedback=narrow_records['narrow256-s15-rne']['history']
    assert [r['failures'] for r in feedback]==[75704,7973,0]
    assert all(r['tested']==2**32 and r['complete_range'] for r in feedback)
    assert feedback[-1]['accepted']
    feedback_figure=(root/'assets/figures/counterexample-refitting.svg').read_text()
    assert all(label in feedback_figure for label in ['75,704 failing inputs','7,973 failing inputs','0 failing inputs','256-row'])
    print('Checked the published 256-row counterexample sequence against its exhaustive reports.')


example = json.loads((root / 'data/coupled-refit.json').read_text())
record = narrow_records['narrow256-s15-rne']
inputs = example['provenance']['input_sha256']
assert inputs['rtl/audits/rounding/narrow256-s15-rne/fit-0.txt'] == record['history'][0]['profile_sha256']
assert inputs['rtl/audits/rounding/narrow256-s15-rne/fit-2.txt'] == record['exhaustive']['profile_sha256']
assert example['shape'] == record['shape']
assert example['after'] == record['coefficients'][example['row']]
assert example['before'][2] == example['after'][2]
constant = example['after'][2]
for phase in ['before', 'after']:
    intervals = [sample[phase + '_interval'] for sample in example['inputs']]
    lower = max(interval[0] for interval in intervals)
    upper = min(interval[1] for interval in intervals)
    if phase == 'before':
        assert lower > upper
        assert any(sample['before_ulp'] > 2 for sample in example['inputs'])
    else:
        assert lower <= constant <= upper
        assert all(sample['after_ulp'] <= 2 for sample in example['inputs'])
print('Checked the coupled-refit example against frozen profiles and its conflicting/overlapping C intervals.')


# Published area ratios cancel the common cell-area normalization. They must
# remain tied to the measured mapped costs, not the archived proxy scores.
accepted_quality = [r for r in quality['records'] if r['exhaustive']['accepted']]
area_reference = min(r['mapped_cost'] for r in accepted_quality)
rendered = (root / 'includes/design-quality-results.qmd').read_text()
main_table = rendered.split('<details>')[0]
for candidate in accepted_quality:
    assert f"{candidate['mapped_cost']/area_reference:.3f}×" in main_table
assert main_table.count('× |') == len(accepted_quality)
assert 'register-bit units' not in main_table
print('Checked published mapped-area ratios against the measured accepted designs.')
