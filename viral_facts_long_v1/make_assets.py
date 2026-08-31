#!/usr/bin/env python3
import json, os, re, urllib.parse, urllib.request, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'work'
IMG = WORK / 'images'
IMG.mkdir(parents=True, exist_ok=True)


def clean_query(q):
    q = re.sub(r'[^\w\s-]', ' ', q or '')
    return re.sub(r'\s+', ' ', q).strip()


def openverse_search(query, page_size=15):
    url = 'https://api.openverse.org/v1/images/?q=' + urllib.parse.quote(query) + f'&page_size={page_size}'
    req = urllib.request.Request(url, headers={'User-Agent':'LongVideoFactory/1.0'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode('utf-8'))


def download(url, out):
    req = urllib.request.Request(url, headers={'User-Agent':'LongVideoFactory/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    if len(data) < 5000:
        raise ValueError('image too small')
    out.write_bytes(data)


def main():
    script = json.loads((WORK/'script.json').read_text(encoding='utf-8'))
    # Make 1 asset request per ~45–60 seconds of narration.
    words = script.get('word_count', 1400)
    scene_count = max(14, min(26, round(words / 65)))
    keywords = script.get('keywords', [])
    title = script['title']
    queries = [title] + keywords + [f'{k} photograph' for k in keywords] + [f'{title} documentary']
    queries = [clean_query(x) for x in queries if x]

    assets = []
    idx = 1
    seen = set()
    for q in queries:
        if len(assets) >= scene_count:
            break
        try:
            result = openverse_search(q)
        except Exception as e:
            print(f'WARN search failed: {q}: {e}')
            continue
        for item in result.get('results', []):
            if len(assets) >= scene_count:
                break
            url = item.get('url') or item.get('thumbnail')
            if not url or url in seen:
                continue
            seen.add(url)
            ext = '.jpg'
            out = IMG / f'{idx:03d}{ext}'
            try:
                download(url, out)
                assets.append({
                    'path': str(out),
                    'title': html.unescape(item.get('title') or q),
                    'source': item.get('creator') or 'Openverse',
                    'license': item.get('license') or '',
                    'url': url,
                    'query': q
                })
                idx += 1
            except Exception as e:
                if out.exists(): out.unlink()
                print(f'WARN download failed: {url}: {e}')

    (WORK/'assets.json').write_text(json.dumps({'assets':assets}, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'assets': len(assets), 'needed': scene_count}))


if __name__ == '__main__':
    main()
