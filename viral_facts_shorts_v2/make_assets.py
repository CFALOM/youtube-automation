import json
import pathlib
import requests
import random
import time
import re

ROOT = pathlib.Path(__file__).parent
WORK = ROOT / "work"
IMAGES = WORK / "images"

WORK.mkdir(exist_ok=True)
IMAGES.mkdir(exist_ok=True)

# =========================================================
# CLEAN OLD VISUALS
# =========================================================

for f in IMAGES.glob("*"):
    try:
        f.unlink()
    except Exception:
        pass

# =========================================================
# LOAD FACT
# =========================================================

selected = json.loads(
    (WORK / "selected.json").read_text(
        encoding="utf-8"
    )
)

topic = selected.get("topic", "")
title = selected.get("title", "")
fact = selected.get("fact", "")

print("=" * 60)
print("SMART VISUAL ENGINE")
print("=" * 60)
print("Topic:", topic)
print("Title:", title)

# =========================================================
# SEARCH TERMS
# =========================================================

terms = [
    title,
    topic,
    f"{title} photo",
    f"{topic} photo",
]

# remove duplicates
terms = list(dict.fromkeys(
    x.strip()
    for x in terms
    if x.strip()
))

random.shuffle(terms)

print()
print("Visual searches:")

for term in terms:
    print("-", term)

# =========================================================
# SOURCE 1:
# WIKIMEDIA COMMONS
#
# Only ONE request.
# If rate limited, continue immediately.
# =========================================================

def commons_search(term):

    url = "https://commons.wikimedia.org/w/api.php"

    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": term,
        "gsrnamespace": 6,
        "gsrlimit": 8,
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "iiurlwidth": 1200,
        "format": "json",
    }

    try:

        r = requests.get(
            url,
            params=params,
            headers={
                "User-Agent":
                "ViralFactsShorts/2.0 contact"
            },
            timeout=8
        )

        if r.status_code == 429:
            print("Wikimedia rate limited.")
            return []

        r.raise_for_status()

        data = r.json()

        pages = (
            data
            .get("query", {})
            .get("pages", {})
        )

        results = []

        for page in pages.values():

            info = (
                page.get("imageinfo")
                or []
            )

            if not info:
                continue

            item = info[0]

            url = (
                item.get("thumburl")
                or item.get("url")
            )

            if not url:
                continue

            mime = item.get(
                "mime",
                ""
            )

            if not mime.startswith(
                "image/"
            ):
                continue

            if re.search(
                r"\.(svg|gif|tif|tiff)$",
                url,
                re.I
            ):
                continue

            results.append(url)

        return results

    except Exception as e:

        print(
            "Wikimedia unavailable:",
            str(e)[:120]
        )

        return []


# =========================================================
# SOURCE 2:
# WIKIPEDIA PAGE IMAGE
#
# This is different from Commons search.
# =========================================================

def wikipedia_image(term):

    try:

        url = (
            "https://en.wikipedia.org/w/api.php"
        )

        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": term,
            "gsrnamespace": 0,
            "gsrlimit": 3,
            "prop": "pageimages",
            "piprop": "original",
            "format": "json",
        }

        r = requests.get(
            url,
            params=params,
            headers={
                "User-Agent":
                "ViralFactsShorts/2.0"
            },
            timeout=8
        )

        if r.status_code == 429:
            print("Wikipedia rate limited.")
            return []

        r.raise_for_status()

        data = r.json()

        pages = (
            data
            .get("query", {})
            .get("pages", {})
        )

        results = []

        for page in pages.values():

            image = page.get(
                "original"
            )

            if not image:
                continue

            img = image.get("source")

            if img:
                results.append(img)

        return results

    except Exception as e:

        print(
            "Wikipedia image search failed:",
            str(e)[:120]
        )

        return []


# =========================================================
# COLLECT URLS
# =========================================================

urls = []

# Try only the best term first.
# This prevents huge numbers of requests.

best_term = terms[0]

print()
print(
    "Searching best visual term:",
    best_term
)

urls.extend(
    commons_search(best_term)
)

# If Commons is blocked, try Wikipedia.
if len(urls) < 4:

    print(
        "Trying Wikipedia visual source..."
    )

    urls.extend(
        wikipedia_image(best_term)
    )

# Remove duplicates
urls = list(dict.fromkeys(urls))

print()
print(
    "Visual URLs found:",
    len(urls)
)

# =========================================================
# DOWNLOAD
# =========================================================

session = requests.Session()

session.headers.update({
    "User-Agent":
    "Mozilla/5.0 ViralFactsShorts/2.0"
})

downloaded = 0

for url in urls:

    if downloaded >= 8:
        break

    output = (
        IMAGES /
        f"image_{downloaded:02d}.jpg"
    )

    print()
    print(
        "Downloading visual",
        downloaded + 1
    )

    try:

        r = session.get(
            url,
            timeout=10
        )

        if r.status_code == 429:

            print(
                "Download rate limited."
            )

            continue

        r.raise_for_status()

        data = r.content

        # Don't accept tiny garbage files.
        if len(data) < 15000:

            print(
                "Skipped tiny file."
            )

            continue

        output.write_bytes(
            data
        )

        downloaded += 1

        print(
            "Saved:",
            output.name,
            f"({len(data)//1024} KB)"
        )

        time.sleep(0.5)

    except Exception as e:

        print(
            "Download failed:",
            str(e)[:120]
        )

# =========================================================
# RESULT
# =========================================================

print()
print("=" * 60)
print("VISUAL SEARCH COMPLETE")
print("=" * 60)
print("Images:", downloaded)
print("=" * 60)

# IMPORTANT:
# Don't create a generic fake visual.
# But don't fail if only a few real images exist.
if downloaded == 0:

    raise RuntimeError(
        "No real visual could be downloaded. "
        "The visual source is unavailable."
    )
