"""Archive public purchasing and library status for every selected catalog code."""
import concurrent.futures,json
from pathlib import Path
from jlc_catalog import fetch
ROOT=Path(__file__).resolve().parents[1]
codes=json.loads((ROOT/'research/selected-codes.json').read_text())
def one(c):
 try:return c,fetch(c)
 except Exception as e:return c,dict(error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for c,r in pool.map(one,codes):print(c,'ERROR '+str(r) if isinstance(r,dict) and 'error' in r else 'archived',flush=True)
