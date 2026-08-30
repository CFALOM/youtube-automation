import json
import pathlib
import random
import re
import requests
from urllib.parse import quote

ROOT = pathlib.Path(__file__).parent
WORK = ROOT / "work"

IMAGES = WORK / "images"
VIDEOS = WORK / "videos"

IMAGES.mkdir(parents=True, exist_ok=True)
VIDEOS.mkdir(parents=True, exist_ok=True)

# Clean old visuals
for file in IMAGES.glob("*"):
    file.unlink()

for file in VIDEOS.glob("*"):
    file.unlink()

selected = json.loads(
    (WORK / "selected.json").read_text(
        encoding="utf-8"
    )
)

terms = selected.get("visual_terms", [])

if not terms:
    terms = [
        selected.get("topic", ""),
        selected.get("title", "")
    ]

USER_AGENT = (
    "ViralFactsShorts/2.0 "
    "(automated educational video project)"
)


def commons_search(query, limit=20):
    """
    Search Wikimedia Commons for real media.
    No API key required.
    """

    url = "https://commons.wikimedia.org/w/api.php"

    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
        "iiurlwidth": 1080,
        "format": "json"
    }

    response = requests.get(
        url,
        params=params,
        headers={
            "User-Agent": USER_AGENT
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    pages = (
        data
        .get("query", {})
        .get("pages", {})
    )

    results = []

    for page in pages.values():

        info = (
            page
            .get("imageinfo", [])
        )

        if not info:
            continue

        item = info[0]

        original = item.get("url")
        mime = item.get("mime", "")

        if not original:
            continue

        results.append({
            "title": page.get("title", ""),
            "url": original,
            "mime": mime
        })

    return results


def download(url, output):

    print(
        "Downloading:",
        url
    )

    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT
        },
        timeout=45
    )

    response.raise_for_status()

    data = response.content

    if len(data) < 10000:
        raise RuntimeError(
            "Downloaded file is too small."
        )

    output.write_bytes(data)


# ---------------------------------------------------------
# FIND VISUALS
# ---------------------------------------------------------

random.shuffle(terms)

found_images = []
seen_urls = set()

for term in terms:

    if not term:
        continue

    print()
    print(
        "Searching Wikimedia Commons:",
        term
    )

    try:

        results = commons_search(
            term,
            limit=20
        )

    except Exception as error:

        print(
            "Search failed:",
            error
        )

        continue

    random.shuffle(results)

    for result in results:

        url = result["url"]

        if url in seen_urls:
            continue

        seen_urls.add(url)

        mime = result["mime"].lower()

        # Only real image formats.
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

        found_images.append(result)

        print(
            "Found:",
            result["title"]
        )

        if len(found_images) >= 8:
            break

    if len(found_images) >= 8:
        break


# ---------------------------------------------------------
# DOWNLOAD IMAGES
# ---------------------------------------------------------

downloaded = 0

for result in found_images:

    if downloaded >= 8:
        break

    output = (
        IMAGES
        /
        f"image_{downloaded:02d}.jpg"
    )

    try:

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
print("WIKIMEDIA VISUAL SEARCH COMPLETE")
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
    "Total visuals:",
    downloaded
)

print("=" * 60)


# Don't create a bad Short.
if downloaded < 4:

    raise RuntimeError(
        "Could not find at least 4 relevant Wikimedia Commons "
        "images. Video creation stopped instead of producing "
        "a Short with missing or generic visuals."
    )
