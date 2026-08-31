import json
import pathlib
import requests
import time
import re

ROOT = pathlib.Path(__file__).parent
WORK = ROOT / "work"
IMAGES = WORK / "images"

WORK.mkdir(exist_ok=True)
IMAGES.mkdir(exist_ok=True)

# Remove old visuals
for f in IMAGES.glob("*"):
    try:
        f.unlink()
    except:
        pass

UA = "Mozilla/5.0 (compatible; ViralFactsShorts/2.0)"

selected = json.loads(
    (WORK / "selected.json").read_text(encoding="utf-8")
)

topic = selected.get("topic", "")
title = selected.get("title", "")

# =========================================================
# BUILD ONE GOOD SEARCH QUERY
# =========================================================

query = title if title else topic

print("=" * 60)
print("VISUAL SEARCH")
print("=" * 60)
print("Topic:", topic)
print("Title:", title)
print("Query:", query)

# =========================================================
# WIKIMEDIA COMMONS SEARCH
# ONE REQUEST ONLY
# =========================================================

API = "https://commons.wikimedia.org/w/api.php"

params = {
    "action": "query",
    "generator": "search",
    "gsrsearch": query,
    "gsrnamespace": 6,
    "gsrlimit": 12,
    "prop": "imageinfo",
    "iiprop": "url|mime",
    "iiurlwidth": 1200,
    "format": "json",
}

try:

    response = requests.get(
        API,
        params=params,
        headers={
            "User-Agent": UA
        },
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

except Exception as error:

    print("Wikimedia search failed:", error)

    data = {}

pages = (
    data
    .get("query", {})
    .get("pages", {})
)

print("Search results:", len(pages))

# =========================================================
# COLLECT IMAGE URLS
# =========================================================

urls = []

for page in pages.values():

    info_list = page.get(
        "imageinfo",
        []
    )

    if not info_list:
        continue

    info = info_list[0]

    url = (
        info.get("thumburl")
        or info.get("url")
    )

    if not url:
        continue

    mime = info.get(
        "mime",
        ""
    )

    if not mime.startswith("image/"):
        continue

    # Avoid obvious SVGs and weird formats
    if re.search(
        r"\.(svg|gif|tiff?)($|\?)",
        url,
        re.I
    ):
        continue

    if url not in urls:
        urls.append(url)

# =========================================================
# DOWNLOAD MAX 8
# =========================================================

print("Usable image URLs:", len(urls))

downloaded = 0

session = requests.Session()

session.headers.update({
    "User-Agent": UA
})

for index, url in enumerate(urls):

    if downloaded >= 8:
        break

    output = (
        IMAGES /
        f"image_{downloaded:02d}.jpg"
    )

    print(
        f"Downloading {downloaded + 1}:",
        url[:120]
    )

    try:

        response = session.get(
            url,
            timeout=12
        )

        response.raise_for_status()

        content = response.content

        if len(content) < 10000:
            print("Skipped: file too small")
            continue

        output.write_bytes(content)

        downloaded += 1

        print(
            "Downloaded:",
            output.name
        )

        # Small delay to be polite to Wikimedia
        time.sleep(1)

    except Exception as error:

        print(
            "Download failed:",
            error
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

# We only require ONE real image here.
# build_video.py can reuse/animate the available visuals.

if downloaded == 0:

    raise RuntimeError(
        "No real visuals could be downloaded."
    )
