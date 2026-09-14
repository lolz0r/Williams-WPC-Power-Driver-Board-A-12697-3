#!/usr/bin/env python3
"""Archive public JLCPCB product pages and extract their server-rendered data.

No account, shopping cart, or purchase API is used. Prices/stock are snapshots.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/jlcpcb/catalog'


def flight_objects(html):
    chunks = [json.loads(s) for s in re.findall(r'self\.__next_f\.push\((.*?)\)</script>', html)]
    stream = ''.join(c[1] for c in chunks if c[0] == 1).encode()
    objects = {}
    pos = 0
    while pos < len(stream):
        end = stream.index(b':', pos)
        key = stream[pos:end].decode()
        pos = end + 1
        if stream[pos:pos+1] == b'T':
            end = stream.index(b',', pos)
            size = int(stream[pos+1:end], 16)
            pos = end + 1
            objects[key] = stream[pos:pos+size].decode()
            pos += size
            continue
        end = stream.find(b'\n', pos)
        if end == -1:
            end = len(stream)
        value = stream[pos:end]
        pos = end + 1
        try:
            objects[key] = json.loads(value)
        except (ValueError, TypeError):
            pass
    return objects


def walk(value):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk(v)


def extract(html, code):
    objects = flight_objects(html)
    def resolve(v):
        if isinstance(v, str) and re.fullmatch(r'\$[0-9a-f]+', v):
            return resolve(objects.get(v[1:], v)) if v[1:] in objects else v
        if isinstance(v, dict):
            return {k: resolve(x) for k, x in v.items()}
        if isinstance(v, list):
            return [resolve(x) for x in v]
        return v
    matches = [d for x in objects.values() for d in walk(x)
               if d.get('componentCode') == code and 'overseasStockCount' in d]
    if not matches:
        raise ValueError('No current JLCPCB product data found for ' + code)
    data = resolve(max(matches, key=lambda d: 'componentLibraryType' in d))
    attrs = next((d.get('attributes') for x in objects.values() for d in walk(x)
                  if d.get('componentCode') == code and isinstance(d.get('attributes'), list)), [])
    keep = ['componentCode', 'componentModelEn', 'componentBrandEn', 'componentSpecificationEn',
            'dataManualUrl', 'isBuyComponent', 'allowPostFlag', 'componentAlternativesCode',
            'replaceUrlSuffix', 'preMinPurchaseNum', 'encapsulationNumber', 'canPresaleNumber',
            'overseasStockCount', 'prices', 'buyPrices', 'componentLibraryType',
            'assemblyComponentFlag', 'lossNumber', 'leastPatchNumber']
    return {**{k: data.get(k) for k in keep}, 'attributes': attrs}


def fetch(code, refresh=False):
    assert re.fullmatch(r'C[0-9]+', code)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (code + '.html')
    meta = OUT / (code + '.json')
    if path.exists() and meta.exists() and not refresh:
        return json.loads(meta.read_text())
    url = 'https://jlcpcb.com/partdetail/' + code
    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40) as response:
        raw = response.read()
        final_url = response.url
    data = extract(raw.decode(), code)
    data.update(url=final_url, fetched_utc=datetime.now(timezone.utc).isoformat(),
                page_sha256=hashlib.sha256(raw).hexdigest())
    path.write_bytes(raw)
    meta.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    return data


def price(data, qty):
    tiers = data.get('prices') or []
    assert isinstance(tiers, list) and all(isinstance(p, dict) for p in tiers), 'Unresolved price data'
    valid = [p for p in tiers if p['startNumber'] <= qty and
             (p['endNumber'] == -1 or p['endNumber'] >= qty)]
    return max(valid, key=lambda p: p['startNumber'])['productPrice'] if valid else None


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('codes', nargs='+')
    p.add_argument('--refresh', action='store_true')
    p.add_argument('--quantity', type=int, default=105)
    args = p.parse_args()
    for code in args.codes:
        d = fetch(code, args.refresh)
        print(code, d['componentModelEn'], d['componentBrandEn'], d['componentSpecificationEn'],
              'stock=', d['overseasStockCount'], 'orderable=', d['canPresaleNumber'],
              'USD@'+str(args.quantity)+'=', price(d, args.quantity), d['componentLibraryType'], flush=True)
