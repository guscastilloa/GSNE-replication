import json
import time

import requests

from etl import config

SEARCH_URL = "https://www.metrocuadrado.com/rest-search/search"

BASE_PARAMS = {
    "realEstateTypeList": "apartamento",
    "realEstateBusinessList": "venta",
    "city": "bogota",
    "size": 50,
}

PRICE_BANDS = [
    (0,             200_000_000),
    (200_000_001,   350_000_000),
    (350_000_001,   500_000_000),
    (500_000_001,   800_000_000),
    (800_000_001, 1_500_000_000),
    (1_500_000_001, 10_000_000_000),
]

def harvest_all(out_path, bands=PRICE_BANDS):
    links = {}
    for lo, hi in bands:
        band = _harvest_band(lo, hi)
        links.update(band)
        print(f"{lo:>12,} - {hi:>12,}: {len(band):>6} -> {len(links):>6} total")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(links, f, indent=2, ensure_ascii=False)

    return links


def _harvest_band(lo, hi, step=50, ceiling=10000):
    links = {}
    frm = 0
    while frm < ceiling:
        rs = _fetch_page(lo, hi, frm)
        if not rs:
            break
        for x in rs:
            links[x["midinmueble"]] = "https://www.metrocuadrado.com" + x["link"]
        frm += step
        time.sleep(1)

    return links

def _fetch_page(lo, hi, frm):
    p = dict(BASE_PARAMS)
    p.update({"from": frm, "saleRange": [lo, hi]})
    headers = {
        "X-Api-Key": config.require("MC_API_KEY"),
        "User-Agent": "Mozilla/5.0",
    }

    r = requests.get(SEARCH_URL, params=p, headers=headers, timeout=20)
    r.raise_for_status()

    if "json" not in r.headers.get("content-type", ""):
        raise ValueError(f"non json object returned: {r.headers.get('content-type')}")

    return r.json()["results"]
