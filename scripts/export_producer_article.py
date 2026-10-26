"""Export the recorded producer experiments; rendering uses only saved assets."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

ARTICLE = Path(__file__).resolve().parents[1]
CODE = ARTICLE.parent / 'code'
ROOT = CODE / 'rtl/producer'
RESULTS = ROOT / 'results'
NAMES = ['narrow_local', 'residual_local', 'residual_carried',
         'column_local', 'prefix_local', 'whole_rows', 'early_cut',
         'column_residual_local', 'column_residual_carried', 'column_prefix']
LABELS = ['Generated seed', 'Recode t locally',
          'Carry decoded t', 'Column compression', 'Prefix carry completion',
          'Store full rows', 'Earlier compression cut',
          'Columns + local t decode', 'Columns + carried t decode',
          'Columns + prefix completion']
# IDs follow the experiment order; diagrams identify ancestry by these IDs.
IDS = dict(zip(NAMES, [1, 3, 4, 2, 5, 6, 7, 8, 9, 10]))

def digest(data):
    return hashlib.sha256(data).hexdigest()

runs = [p for p in (RESULTS / 'runs').iterdir()
        if (p / 'experiment.textproto').exists()
        and (p / 'experiment.textproto').read_bytes() == (RESULTS / 'experiment.textproto').read_bytes()]
run = max(runs, key=lambda p: int(p.name))
records = []
files = {}
inputs = {}
for name, label in zip(NAMES, LABELS):
    report_bytes = (run / f'{name}.json').read_bytes()
    report = json.loads(report_bytes)
    base = run / name
    stats = json.loads((base / 'statistics.json').read_text())['design']
    assert abs(stats['area'] - report['cell_area_um2']) < 1e-8
    assert 'PASS:' in (base / 'simulation.log').read_text()
    assert 'PASS:' in (base / 'gate_simulation.log').read_text()
    for filename, sha in report['rtl_sha256'].items():
        assert digest((base / filename).read_bytes()) == sha, (name, filename)
    ff = sum(count for cell, count in stats['num_cells_by_type'].items() if 'DFF' in cell)
    counts = []
    if name != 'reference':
        svg = (base / 'pipeline.svg').read_text()
        counts = [int(x) for x in re.findall(r'>(\d+) register bits', svg)]
        assert len(counts) == 5
    records.append(dict(id=IDS[name], name=name, label=label,
                        area_um2=report['cell_area_um2'], slack_ps=report['worst_setup_slack_ps'],
                        power_mw=report['power']['Total']['total'] * 1000,
                        flip_flops=ff, graph_register_bits_by_stage=counts,
                        measurement=report))
    inputs[str((run / f'{name}.json').relative_to(CODE))] = digest(report_bytes)
    files[f'measurements/{name}.json'] = report_bytes
    for source in base.iterdir():
        if source.is_file():
            files[f'circuits/{name}/{source.name}'] = source.read_bytes()

for record in records[1:]:
    for field in ['library_sha256', 'sdc_sha256', 'eda_bundle_id', 'testbench_sha256',
                  'clock_period_ps', 'conda_environment']:
        assert record['measurement'][field] == records[0]['measurement'][field], field

# Include the typed inputs and producer source without requiring the research
# checkout when the article is rendered or the download is inspected.
for path in ROOT.iterdir():
    if path.is_file() and path.suffix in ['.cc', '.h', '.proto', '.bzl', '.bazel', '.md', '.sdc']:
        files[f'producer/{path.name}'] = path.read_bytes()
for path in (ROOT / 'fixtures').glob('*.textproto'):
    files[f'producer/fixtures/{path.name}'] = path.read_bytes()
files['experiment.textproto'] = (run / 'experiment.textproto').read_bytes()
files['sfu/fixed.h'] = (CODE / 'sfu/fixed.h').read_bytes()
files['toolchain.lock.json'] = (CODE / 'rtl/toolchain.lock.json').read_bytes()
files['README.txt'] = b'''Part 4: recorded polynomial implementation experiments

producer/: C++ producer, protobuf schemas, implementation configurations.
circuits/: generated/reference RTL, exact-model benches, mapped netlists,
           diagrams, circuit protobufs and checked simulation logs.
measurements/: mapped area, timing and activity-based power with source hashes.
experiment.textproto: the numerical design and all implementation choices.

Build in the code/ workspace using producer/README.md. The producer's Bazel
rules use the code workspace's pinned source dependencies and published EDA
bundle. Compile one sfu_poly top at a time when inspecting the circuit folders.
The measurements cover coefficient lookup and polynomial arithmetic at 1 ns,
ASAP7 RVT TT, with four register stages and one input per cycle.
'''
archive = ARTICLE / 'docs/artifacts/rtl-producer-experiments.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as output:
    for name, data in sorted(files.items()):
        info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        output.writestr(info, data)

circuit_path = CODE / 'bazel-bin/rtl/producer/narrow_local_generated/circuit.textproto'
circuit_text = circuit_path.read_text()
heap_block = re.findall(r'(?ms)^heaps \{.*?^\}', circuit_text)[0]
heap_rows = [[int(x) for x in re.findall(r'bits: (\d+)', row)]
             for row in re.findall(r'(?ms)^  rows \{.*?^  \}', heap_block)]
assert len(heap_rows) == 8 and all(len(row) == 36 for row in heap_rows)
heap_support = [[min(bit, 2) for bit in row] for row in heap_rows]
inputs[str(circuit_path.relative_to(CODE))] = digest(circuit_path.read_bytes())

result = dict(first_heap=heap_support, records=sorted(records, key=lambda r: r['id']),
              numerical_design=dict(rows=256, a_bits=8, b_bits=13, c_bits=23,
                                    residual_bits=18, first_result_bits=15,
                                    final_result_bits=25, first_rounding='truncate',
                                    second_rounding='truncate', register_stages=4),
              provenance=dict(run=run.name, input_sha256=inputs,
                              producer_sha256={str(p.relative_to(CODE)): digest(p.read_bytes())
                                for p in ROOT.iterdir() if p.suffix in ['.cc', '.h', '.proto', '.bzl', '.bazel']},
                              download_sha256=digest(archive.read_bytes())))
(ARTICLE / 'data/rtl-producer.json').write_text(json.dumps(result, indent=2) + '\n')
print(f'Exported {len(records)} checked circuits and {len(files)} download entries.')
