"""Check final ZIP contents and hashes against the saved source/evidence."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';release=OUT/'release-candidate'
def sha(data):return hashlib.sha256(data).hexdigest()
manifest=json.loads((release/'reports/verification-manifest.json').read_text())
archive_hashes=json.loads((OUT/'archives-sha256.json').read_text());counts={}
for name,info in archive_hashes.items():
 path=OUT/name;assert sha(path.read_bytes())==info['sha256'],name
 with zipfile.ZipFile(path) as z:
  names=z.namelist();assert len(names)==len(set(names)),name
  assert z.testzip() is None,name
  assert not any(Path(n).name.lower() in ['sttng_l7.zip','sttng-manual.pdf'] or '/roms/' in n.lower() or '/nvram/' in n.lower() for n in names),name
  groups=['native_files']+(['verification_files','verification_tools'] if name.endswith('-review.zip') else [])
  checked=0
  for group in groups:
   for p,h in manifest[group].items():
    assert sha((ROOT/p).read_bytes())==h,p
    assert sha(z.read('JLC-2/'+p))==h,(name,p)
    checked+=1
  if name.endswith('-review.zip'):
   files=json.loads((release/'SHA256.json').read_text())
   for p,h in files.items():
    assert sha((release/p).read_bytes())==h,p
    assert sha(z.read('JLC-2/output/release-candidate/'+p))==h,p
    checked+=1
   ready=json.loads(z.read('JLC-2/output/release-candidate/READINESS.json'))
   assert ready['revision']=='JLC-2' and ready['fab_ready'] is False and ready['all_simulation_checks_passed'] is False
  counts[name]=dict(files=len(names),bound_file_hash_checks=checked,crc_passed=True)
assert sha((ROOT/'wpc_power_driver_cost.kicad_pcb').read_bytes())==manifest['pcb_sha256']
report=dict(passed=True,revision='JLC-2',pcb_sha256=manifest['pcb_sha256'],archives=counts,rom_and_manual_not_bundled=True,scope='ZIP CRC, duplicate inventory, archive digests, native/evidence/tool/release-file hashes, and retained not-ready status. This verifies packaging consistency, not electrical readiness.')
(OUT/'archive-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
