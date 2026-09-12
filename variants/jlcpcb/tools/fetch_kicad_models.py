"""Vendor the exact official KiCad STEP files needed by this variant."""
import concurrent.futures,hashlib,json,urllib.parse
from datetime import datetime,timezone
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1];dest=ROOT/'models/kicad';dest.mkdir(exist_ok=True)
models=json.loads((ROOT/'research/standard-models.json').read_text())
def fetch(raw):
 rel=raw.split('}/',1)[1];p=dest/rel;p.parent.mkdir(exist_ok=True)
 url='https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/master/'+urllib.parse.quote(rel)
 if not p.exists():
  r=requests.get(url,timeout=90);r.raise_for_status();assert r.content.startswith(b'ISO-10303-21;'),url;p.write_bytes(r.content)
 return dict(path=rel,url=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),fetched_utc=datetime.now(timezone.utc).isoformat())
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(fetch,models))
(ROOT/'research/kicad-model-sources.json').write_text(json.dumps(rows,indent=2)+'\n');print('Archived',len(rows),'official STEP models')
