"""Archive unauthenticated, read-only JLCPCB catalog queries."""
import argparse, concurrent.futures, csv, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/catalog-search'
API = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList/v2'

def search(keyword, basic=False, refresh=False, library='', page=1):
    OUT.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256((keyword + str(basic) + library + str(page)).encode()).hexdigest()[:16]
    path = OUT / (key + '.json')
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    payload = dict(currentPage=page, pageSize=1000, searchType=2, keyword=keyword,
                   componentLibraryType=library, preferredComponentFlag=basic,
                   stockFlag=False, componentAttributes=[], searchSource='search')
    response = requests.post(API, json=payload, headers={'User-Agent':'Mozilla/5.0',
        'Origin':'https://jlcpcb.com','Referer':'https://jlcpcb.com/parts'}, timeout=60)
    response.raise_for_status()
    raw=response.json()
    if raw.get('code') != 200: raise RuntimeError(raw)
    result=dict(source=API, request=payload, fetched_utc=datetime.now(timezone.utc).isoformat(), response=raw)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    return result

def rows(result):
    return result['response']['data']['componentPageInfo']['list'] or []

def brief(d):
    return {k:d.get(k) for k in ['componentCode','componentModelEn','componentBrandEn',
        'componentSpecificationEn','componentLibraryType','preferredComponentFlag',
        'stockCount','overseasStockCount','canPresaleNumber','preMinPurchaseNum','componentPrices','urlSuffix']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('keywords',nargs='*');p.add_argument('--bom',type=Path);p.add_argument('--basic',action='store_true');p.add_argument('--library',default='');p.add_argument('--page',type=int,default=1);a=p.parse_args()
    queries=a.keywords
    if a.bom:queries=sorted({r['MPN'] for r in csv.DictReader(a.bom.open())})
    def run(q):
        try:
            result=search(q,a.basic,library=a.library,page=a.page);return q,[brief(d) for d in rows(result)]
        except Exception as e:return q,{'error':str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for q,r in pool.map(run,queries): print(json.dumps({'query':q,'parts':r},ensure_ascii=False),flush=True)
