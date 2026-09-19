import json
import os
import time

import requests

from etl.extract import listing


def run(links_path, out_path, failed_path, limit=None, delay=0.6):
    links = _load_links(links_path)
    skip = _already_done(out_path) | _already_failed(failed_path)
    todo = {k: v for k, v in links.items() if k not in skip}

    if limit:
        todo = dict(list(todo.items())[:limit])

    print(f"{len(links)} total, {len(skip)} done, {len(todo)} to fetch")

    session = requests.Session()

    ok = failed = 0
    with open(out_path, "a", encoding="utf-8") as out, \
         open(failed_path, "a", encoding="utf-8") as bad:
        for i, (codigo, url) in enumerate(todo.items(), 1):
            data = _fetch_with_retry(url, session=session)

            if data is None:
                bad.write(f"{codigo}\t{url}\n")
                bad.flush()
                failed += 1
            else:
                out.write(json.dumps(data, ensure_ascii=False) + "\n")
                out.flush()
                ok += 1

            if i % 100 == 0:
                print(f"{i}/{len(todo)}  ok={ok} failed={failed}")

            time.sleep(delay)

    print(f"done: ok={ok} failed={failed}")


def _load_links(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found — build it with --harvest, or supply --links")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _already_done(path):
    done = set()
    if not os.path.exists(path):
        return done

    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                done.add(json.loads(line)["propertyId"])
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def _fetch_with_retry(url, session=None, attempts=4):
    for n in range(attempts):
        try:
            return listing.scrape(url, session=session)
        except requests.HTTPError as e:
            if e.response.status_code in (429, 500, 502, 503, 504):
                time.sleep(30 * (n + 1))
                continue
            return None
        except requests.RequestException:
            time.sleep(10 * (n + 1))
    return None

def _already_failed(path):
    failed = set()

    if not os.path.exists(path):
        return failed

    with open(path, encoding= 'utf-8') as f:
        for line in f:
            codigo = line.split("\t",1)[0].strip()

            if codigo:
                failed.add(codigo)

    return failed