"""Freeze the source-checked cell-level carry explanation for Part 4."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
CODE=ROOT.parent/'code/rtl/producer'
source=CODE/'carry_audit/summary.json'
data=json.loads(source.read_text())
for r in data['comparison']:
    assert r['verification']['formal_proof_success']
    assert r['verification']['replayed_cell_topology_identical']
archive=ROOT/'docs/artifacts/rtl-carry-audit.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    def put(path,name):
        entry=zipfile.ZipInfo(name,(2026,10,23,0,0,0))
        entry.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(entry,path.read_bytes())
    put(source,'summary.json')
    put(CODE/'carry_audit/README.md','README.md')
    for r in data['comparison']:
        base=CODE/'clock_search/results'/r['name']/'carry_audit'
        for name in ['verified_trace.json','verification.json','source_carry_tags.json',
                     'carry_miter.sv','prove.ys','proof.log','observe_mapping.ys',
                     'cell_names.json','named.json']:
            put(base/name,r['name']+'/'+name)
data['provenance']={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                    'private_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
(ROOT/'data/rtl-carry-audit.json').write_text(json.dumps(data,indent=2)+'\n')
print('Exported the formally checked carry-path audit and private evidence archive.')
