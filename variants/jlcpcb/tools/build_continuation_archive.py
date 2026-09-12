"""Package verification addendum without replacing the JLC-2 review snapshot."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


summary_path = OUT / 'verification/continuation/summary.json'
summary = json.loads(summary_path.read_text())
assert not summary['pcb_changed'] and not summary['fab_ready']
assert not summary['pending_bounded_runs'], 'Do not archive pending simulations as a finished review round'
for name, expected in json.loads((OUT/'archives-sha256.json').read_text()).items():
    assert digest(OUT/name) == expected['sha256'], 'Original JLC-2 archive changed'
files = set(summary['evidence_sha256']) | set(summary['sources_sha256'])
for name, expected in (summary['evidence_sha256'] | summary['sources_sha256']).items():
    assert digest(ROOT/name) == expected, name
files.update(['output/verification/continuation/summary.json',
              'docs/CONTINUED_ANALOG_REVIEW.md', 'tools/build_continuation_archive.py',
              'research/sttng-manual-source.json', 'research/runtime-versions.json'])
manifest = dict(fab_ready=False, pcb_changed=False, native_pcb_sha256=summary['pcb_sha256'],
                files={name: digest(ROOT/name) for name in sorted(files)},
                original_archives=json.loads((OUT/'archives-sha256.json').read_text()),
                scope='Verification addendum; use with the unchanged JLC-2 CAD/review archives. No ROM, vendor model or manual PDF included.')
target = OUT/'JLC-2-verification-addendum.zip'
with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for name in sorted(files):
        archive.write(ROOT/name, name)
    archive.writestr('ADDENDUM-MANIFEST.json', json.dumps(manifest, indent=2)+'\n')
    archive.writestr('README.txt',
        'JLC-2 verification addendum. Start with docs/CONTINUED_ANALOG_REVIEW.md.\n'
        'The native PCB and original JLC-2 archives are unchanged; fabrication readiness remains false.\n'
        'Use tools from the complete project workspace. KiCad Flatpak supplies libngspice.\n'
        'Vendor model URLs and hashes are in research/vendor-model-sources.json; obtain models into the documented .scratch paths.\n'
        'ROM and manufacturer manual/model PDFs are not distributed here.\n')
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    names = archive.namelist()
    assert len(names) == len(set(names))
    assert not any(n.endswith('sttng_l7.zip') or n.endswith('sttng-manual.pdf') for n in names)
    for name, expected in manifest['files'].items():
        assert hashlib.sha256(archive.read(name)).hexdigest() == expected, name
report = dict(passed=True, archive=target.name, sha256=digest(target), bytes=target.stat().st_size,
              files=len(names), bound_file_checks=len(files), crc_passed=True,
              original_JLC2_archives_unchanged=True, fab_ready=False)
(OUT/'verification-addendum-check.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
