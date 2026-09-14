"""Read-only public inventory research; no cart or order operations."""
import argparse,json,time,concurrent.futures
from pathlib import Path
from catalog_search import search,rows
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('queries',type=Path);p.add_argument('--refresh',action='store_true');a=p.parse_args()
 queries=json.loads(a.queries.read_text());result=[]
 def run(q):
  for attempt in range(3):
   try:
    d=search(q['keyword'],library=q.get('library',''),refresh=a.refresh)
    return dict(query=q,parts=rows(d),fetched_utc=d['fetched_utc'])
   except Exception as e:
    if attempt==2:return dict(query=q,error=str(e))
    time.sleep(3*(attempt+1))
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for r in pool.map(run,queries):
   result.append(r);print(r['query'],'results',len(r.get('parts',[])),r.get('error',''),flush=True)
 out=ROOT/'research'/(a.queries.stem+'-results.json');out.write_text(json.dumps(result,indent=2)+'\n');print(out,flush=True)
if __name__=='__main__':main()
