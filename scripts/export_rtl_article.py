"""Freeze existing RTL measurements and source excerpts for Part 4.

This is an explicit research export; site rendering only reads its saved output.
"""
import hashlib
import json
from pathlib import Path
import zipfile

article = Path(__file__).resolve().parents[1]
code = article.parent / 'code'
inputs = {}
def read(relative):
    path = code / relative
    inputs[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text())

study = json.loads((article / 'data/narrow256-study.json').read_text())
designs = []
sources = {}
archive_files = {}
for name, label in [('narrow256-s15-tt', '15-bit first result · truncate/truncate'),
                    ('narrow256-combined-rne', '16-bit first result · RNE/RNE')]:
    frozen = next(r for r in study['records'] if r['name'] == name)
    report = read(f'rtl/audits/rounding/{name}/mapped.json')
    assert report['rtl_sha256'] == frozen['mapped']['rtl_sha256']
    assert abs(report['cell_area_um2'] / .2916 - frozen['mapped_cost']) < 1e-7
    target = name.replace('-', '_')
    base = code / 'bazel-bin/rtl/rounding' / target
    for log in ['simulation.log', 'gate_simulation.log']:
        assert 'PASS:' in (base / log).read_text()
    stats = json.loads((base / 'mapped/statistics.json').read_text())['design']
    assert abs(stats['area'] - report['cell_area_um2']) < 1e-8
    for filename, digest in report['rtl_sha256'].items():
        source = code / ('rtl/rounding/' + target + '/' + filename if filename == 'sfu_poly.sv'
                         else ('rtl/examples/' if filename in ['booth_rows.sv', 'carry_save_layer.sv'] else 'rtl/rounding/') + filename)
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
        destination = target + '/sfu_poly.sv' if filename == 'sfu_poly.sv' else 'common/' + filename
        archive_files[destination] = source.read_bytes()
        sources[str(source.relative_to(code))] = digest
    archive_files[target + '/measurement.json'] = json.dumps(report, indent=2).encode() + b'\n'
    designs.append(dict(name=name, label=label, shape=frozen['shape'], target=target,
                        profile_sha256=frozen['exhaustive']['profile_sha256'], report=report,
                        flip_flops=sum(n for cell, n in stats['num_cells_by_type'].items() if 'DFF' in cell)))
optimization = read('rtl/audits/booth/optimization.json')
constants = read('rtl/audits/rounding/constant-bits/summary.json')
delta = read('rtl/audits/rounding/first-rounding-delta/summary.json')
archive_files['common/polynomial.sdc'] = (code / 'rtl/rounding/polynomial.sdc').read_bytes()
archive_files['README.txt'] = b'''Part 4 RTL and frozen measurements

Each design folder contains a separate top named sfu_poly; compile one at a time
with common/*.sv. Both use common/polynomial.sdc. Cell libraries and tools come
from the pinned research checkout.

From code/ with its pinned environment active:
  ./scripts/bazel.py build //rtl/rounding:narrow256_s15_tt //rtl/rounding:narrow256_combined_rne
  ./scripts/bazel.py test //rtl/rounding:narrow256_s15_tt_test //rtl/rounding:narrow256_s15_tt_gate_test
  ./scripts/bazel.py test //rtl/rounding:narrow256_combined_rne_test //rtl/rounding:narrow256_combined_rne_gate_test

Reports cover mapped coefficient lookup and polynomial arithmetic. Numerical
FP32 reconstruction and range reduction are evaluated by the full reference model.
'''
archive_files['source-sha256.json'] = json.dumps(sources, indent=2).encode() + b'\n'
archive = article / 'assets/downloads/exp2-rtl.zip'
archive.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as out:
    for name, content in sorted(archive_files.items()):
        info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        out.writestr(info, content)
result = dict(designs=designs, architecture_experiment=optimization,
              constant_audit=constants, rounding_delta=delta,
              provenance=dict(input_sha256=inputs, rtl_sha256=sources,
                              narrow256_study_sha256=hashlib.sha256((article / 'data/narrow256-study.json').read_bytes()).hexdigest(),
                              download_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                              download_entries={n:hashlib.sha256(c).hexdigest() for n,c in archive_files.items()}))
(article / 'data/rtl-implementation.json').write_text(json.dumps(result, indent=2) + '\n')
print('Exported two fitted circuits, optimization records, constant-bit audits and RTL archive.')
