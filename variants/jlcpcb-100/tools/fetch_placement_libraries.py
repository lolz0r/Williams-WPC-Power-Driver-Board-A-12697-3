"""Archive public LCSC/EasyEDA library data for each purchased part; no order API."""
import argparse
import concurrent.futures
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--refresh', action='store_true')
    args = p.parse_args()
    out = ROOT/'research/jlc-placement-libraries'
    out.mkdir(parents=True, exist_ok=True)
    codes = sorted({r['LCSC Part #'] for r in csv.DictReader((ROOT/'output/release-candidate/jlcpcb-assembly/BOM.csv').open())})
    def fetch(code):
        path = out/(code+'.json')
        meta = out/(code+'-source.json')
        if path.exists() and meta.exists() and not args.refresh:
            return code, json.loads(path.read_text()).get('success'), 'cached'
        url = f'https://lceda.cn/api/products/{code}/components'
        try:
            raw = urlopen(Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=40).read()
            data = json.loads(raw)
            path.write_bytes(raw)
            meta.write_text(json.dumps(dict(url=url, fetched_utc=datetime.now(timezone.utc).isoformat(),
                                            sha256=hashlib.sha256(raw).hexdigest()), indent=2)+'\n')
            return code, data.get('success'), len(raw)
        except Exception as e:
            return code, False, str(e)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(fetch, codes):
            print(*result, flush=True)


if __name__ == '__main__':
    main()
