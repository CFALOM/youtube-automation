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

# Clean old files
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

HEADERS = {
    "User-Agent":
        "ViralFactsShorts/2.0 "
        "(educational project)"
}

session = requests.Session()
session.headers.update(HEADERS)


# ---------------------------------------------------------
# SEARCH WIKIPEDIA PAGES
# ---------------------------------------------------------

def wikipedia_search(query):

    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrlimit": 8,
        "prop": "pageimages",
        "piprop": "thumbnail",
        "pithumbsize": 1000,
        "format": "json"
    }

    for attempt in range(4):

        try:

            response = session.get(
                url,
                params=params,
                timeout=30
            )

            if response.status_code == 429:

                wait = 10 * (attempt + 1)

                print(
                    f"Wikipedia rate limit. "
                    f"Waiting {wait}s..."
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

                thumbnail = page.get(
                    "thumbnail"
                )

                if not thumbnail:
                    continue

                source = thumbnail.get(
                    "source"
                )

                if not source:
                    continue

                results.append({
                    "title":
                        page.get(
                            "title",
                            ""
                        ),
                    "url": source
                })

            return results

        except Exception as error:

            print(
                "Wikipedia search error:",
                error
            )

            time.sleep(
                5 * (attempt + 1)
            )

    return []


# ---------------------------------------------------------
# SEARCH TERMS
# ---------------------------------------------------------

terms = [
    title,
    topic,
    f"{topic} history"
]

# Remove duplicates
clean_terms = []

for term in terms:

    if term and term not in clean_terms:

        clean_terms.append(term)

terms = clean_terms

print()
print("=" * 60)
print("VISUAL SEARCH")
print("=" * 60)

for term in terms:

    print(
        "Search:",
        term
    )


# ---------------------------------------------------------
# COLLECT IMAGES
# ---------------------------------------------------------

found = []
seen = set()

for term in terms:

    results = wikipedia_search(term)

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

        if len(found) >= 10:
            break

    if len(found) >= 10:
        break

    # Don't hammer Wikipedia
    time.sleep(3)


# ---------------------------------------------------------
# DOWNLOAD
# ---------------------------------------------------------

def download(url, output):

    for attempt in range(4):

        try:

            response = session.get(
                url,
                timeout=45
            )

            if response.status_code == 429:

                wait = 10 * (attempt + 1)

                print(
                    f"Download rate limited. "
                    f"Waiting {wait}s..."
                )

                time.sleep(wait)

                continue

            response.raise_for_status()

            data = response.content

            if len(data) < 10000:

                raise RuntimeError(
                    "Image is too small."
                )

            output.write_bytes(data)

            return True

        except Exception as error:

            print(
                "Download attempt failed:",
                error
            )

            time.sleep(
                5 * (attempt + 1)
            )

    return False


downloaded = 0

for result in found:

    if downloaded >= 8:
        break

    output = (
        IMAGES /
        f"image_{downloaded:02d}.jpg"
    )

    print()
    print(
        "Downloading:",
        result["title"]
    )

    if download(
        result["url"],
        output
    ):

        downloaded += 1


# ---------------------------------------------------------
# REPORT
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
        f"Only {downloaded} usable visuals found. "
        "Video creation stopped."
    )
