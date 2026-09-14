"""Fetch manufacturer/catalog PDFs into the isolated inventory variant."""
from pathlib import Path
import argparse,json,requests,hashlib,time
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);a=p.parse_args();out=ROOT/'research/datasheets';out.mkdir(exist_ok=True)
results=[]
for name,url in json.loads(a.manifest.read_text()).items():
 dest=out/(name+'.pdf')
 try:
  if not dest.exists():
   r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=45);r.raise_for_status();assert r.content.startswith(b'%PDF'),r.text[:80];dest.write_bytes(r.content)
  results.append(dict(name=name,url=url,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()));print(name,dest.stat().st_size,flush=True)
 except Exception as e:results.append(dict(name=name,url=url,error=str(e)));print(name,'ERROR',str(e),flush=True)
(out/(a.manifest.stem+'-downloads.json')).write_text(json.dumps(results,indent=2)+'\n')
