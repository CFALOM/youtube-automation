import json
import pathlib
import random
import time
import requests

ROOT = pathlib.Path(__file__).parent
WORK = ROOT / "work"

IMAGES = WORK / "images"
VIDEOS = WORK / "videos"

IMAGES.mkdir(parents=True, exist_ok=True)
VIDEOS.mkdir(parents=True, exist_ok=True)

# Remove old visuals
for file in IMAGES.glob("*"):
    file.unlink()

for file in VIDEOS.glob("*"):
    file.unlink()

selected = json.loads(
    (WORK / "selected.json").read_text(
        encoding="utf-8"
    )
)

topic = selected.get("topic", "")
title = selected.get("title", "")

# ---------------------------------------------------------
# CLEAN SEARCH TERMS
# ---------------------------------------------------------

terms = []

for value in [
    title,
    topic,
    f"{topic} image",
    title.split(":")[0] if ":" in title else ""
]:

    if not value:
        continue

    value = value.strip()

    if value not in terms:
        terms.append(value)

# Maximum 4 searches.
terms = terms[:4]

print()
print("VISUAL SEARCH TERMS:")
for term in terms:
    print("-", term)

# ---------------------------------------------------------
# WIKIMEDIA SETTINGS
# ---------------------------------------------------------

API = "https://commons.wikimedia.org/w/api.php"

HEADERS = {
    "User-Agent":
        "ViralFactsShorts/2.0 "
        "(educational automated video project)"
}

session = requests.Session()
session.headers.update(HEADERS)


# ---------------------------------------------------------
# SEARCH COMMONS WITH BACKOFF
# ---------------------------------------------------------

def search_commons(query):

    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": 12,
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "iiurlwidth": 1080,
        "format": "json"
    }

    for attempt in range(5):

        try:

            response = session.get(
                API,
                params=params,
                timeout=30
            )

            # Wikimedia is asking us to slow down.
            if response.status_code == 429:

                retry = response.headers.get(
                    "Retry-After"
                )

                try:
                    wait = int(retry)
                except Exception:
                    wait = 10 * (attempt + 1)

                wait = min(wait, 60)

                print(
                    f"Rate limited. Waiting {wait}s..."
                )

                time.sleep(wait)

                continue

            response.raise_for_status()

            data = response.json()

            pages = (
                data
                .get("query", {})
                .get("pages", {})
            )

            results = []

            for page in pages.values():

                info = page.get(
                    "imageinfo",
                    []
                )

                if not info:
                    continue

                item = info[0]

                url = item.get("url")
                mime = item.get(
                    "mime",
                    ""
                ).lower()

                if not url:
                    continue

                if not any(
                    x in mime
                    for x in [
                        "jpeg",
                        "jpg",
                        "png",
                        "webp"
                    ]
                ):
                    continue

                results.append({
                    "title":
                        page.get(
                            "title",
                            ""
                        ),
                    "url": url
                })

            return results

        except requests.RequestException as error:

            print(
                "Search error:",
                error
            )

            wait = 5 * (attempt + 1)

            time.sleep(wait)

    return []


# ---------------------------------------------------------
# FIND IMAGES
# ---------------------------------------------------------

found = []
seen = set()

for index, term in enumerate(terms):

    print()
    print(
        f"Searching {index + 1}/{len(terms)}:",
        term
    )

    results = search_commons(term)

    random.shuffle(results)

    for result in results:

        url = result["url"]

        if url in seen:
            continue

        seen.add(url)

        found.append(result)

        print(
            "Found:",
            result["title"]
        )

        if len(found) >= 8:
            break

    # VERY IMPORTANT:
    # Don't hammer Wikimedia.
    if index < len(terms) - 1:
        time.sleep(5)

    if len(found) >= 8:
        break


# ---------------------------------------------------------
# DOWNLOAD
# ---------------------------------------------------------

def download(url, path):

    response = session.get(
        url,
        timeout=45
    )

    response.raise_for_status()

    data = response.content

    if len(data) < 10000:
        raise RuntimeError(
            "Image file is suspiciously small."
        )

    path.write_bytes(data)


downloaded = 0

for result in found:

    if downloaded >= 8:
        break

    output = (
        IMAGES /
        f"image_{downloaded:02d}.jpg"
    )

    try:

        print(
            "Downloading:",
            result["title"]
        )

        download(
            result["url"],
            output
        )

        downloaded += 1

    except Exception as error:

        print(
            "Download failed:",
            error
        )


# ---------------------------------------------------------
# RESULT
# ---------------------------------------------------------

print()
print("=" * 60)
print("VISUAL SEARCH COMPLETE")
print("=" * 60)

print(
    "Images:",
    downloaded
)

print(
    "Videos:",
    0
)

print(
    "Total:",
    downloaded
)

print("=" * 60)

if downloaded < 4:

    raise RuntimeError(
        f"Only {downloaded} relevant images were downloaded. "
        "The workflow stopped instead of creating a bad Short."
    )
