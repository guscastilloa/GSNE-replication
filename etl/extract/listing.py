import datetime
import json
import re

import requests


def scrape(url, session = None):

    get = session.get if session else requests.get    
    r = get(url,headers = {"User-Agent": "Mozilla/5.0"}, timeout=20)
    #print(r.status_code, len(r.text))
    r.raise_for_status()
   
    html = r.text
    pushes = re.findall(r'self\.__next_f\.push\(\[1,"(.+?)"\]\)', html, re.DOTALL) 
    if not pushes:
        return None

    #print(len(pushes), " pushes found")
    #for i,chunk in enumerate(pushes):
    #    print(i, len(chunk), "propertyId" in chunk)

    data = _best_record(pushes)
    if data is None:
        return None
    data['description'] = _get_desc(data=data, html = html)
    data['url'] = url
    data['scraped_at'] = datetime.datetime.now(datetime.UTC).isoformat()

    return data

def _unescape(chunk):
    try:
        return json.loads('"' + chunk + '"')
    except json.JSONDecodeError:
        return chunk.replace('\\', '')


def _count_refs(d):
    return sum(1 for v in d.values() if isinstance(v, str) and v.startswith("$"))

def _best_record(pushes):
    best_score, best = None, None
    for c in pushes:
        if "propertyId" not in c:
            continue
        obj = _extract_object(_unescape(c), '"propertyId"')
        if not obj:
            continue
        try:
            d = json.loads(obj)
        except json.JSONDecodeError:
            continue

        score = (_count_refs(d), -len(d))
        if best_score is None or score < best_score:
            best_score, best = score, d
    return best




def _extract_object(text, anchor):
    """
    
    anchor: a string that is known to be inside the object we want to extract
    """
    pos = text.find(anchor)
    if pos == -1:
        return None

    # walk backwards tracking depth to find the brace that ENCLOSES pos
    depth = 0
    start = -1
    for i in range(pos, -1, -1):
        if text[i] == '}':
            depth += 1
        elif text[i] == '{':
            if depth == 0:
                start = i
                break
            depth -= 1
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def _get_desc(data, html):
    comment = data.get("comment")
    if not isinstance(comment, str):
        return None

    if not comment.startswith("$"):
        return comment

    i = html.find(comment.lstrip("$") + ":T")
    if i == -1:
        return None

    header = re.search(r':T([0-9a-f]+),', html[i:i + 20])
    declared = int(header.group(1), 16) if header else None

    m = re.search(r'push\(\[1,"(.+?)"\]\)', html[i:], re.DOTALL)
    if not m:
        return None

    desc = _unescape(m.group(1))

    if declared and len(desc) < declared * 0.9:
        return None

    return desc



if __name__ == "__main__":
    url = "https://www.metrocuadrado.com/inmueble/venta-apartamento-bogota-bosque-medina-mcd-cedritos-3-habitaciones-4-banos-2-garajes/MC4976987?src_url=%2Fapartamento%2Fventa%2Fbogota%2F"
    data = scrape(url)
    print(len(data) if data else "No data found: Fail")