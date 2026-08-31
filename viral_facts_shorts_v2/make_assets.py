import json
import pathlib
import requests
import random
import time
import re
from urllib.parse import quote

ROOT = pathlib.Path(__file__).parent
WORK = ROOT / "work"

IMAGES = WORK / "images"

IMAGES.mkdir(parents=True, exist_ok=True)

UA = "ViralFactsShortsVisuals/Final/1.0"


# ============================================================
# CLEAN OLD VISUALS
# ============================================================

for file in IMAGES.glob("*"):
    try:
        file.unlink()
    except Exception:
        pass


# ============================================================
# LOAD FACT
# ============================================================

selected = json.loads(
    (WORK / "selected.json").read_text(
        encoding="utf-8"
    )
)

topic = selected["topic"]
title = selected["title"]
terms = selected["visual_terms"]


print()
print("=" * 60)
print("VISUAL ENGINE")
print("=" * 60)

print("Topic:", topic)
print("Article:", title)

print()
print("Visual searches:")

for term in terms:
    print("-", term)


# ============================================================
# WIKIMEDIA API
# ============================================================

API = "https://commons.wikimedia.org/w/api.php"


def commons_search(term):

    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": term,
        "gsrnamespace": 6,
        "gsrlimit": 8,
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "iiurlwidth": 1400,
        "format": "json",
    }

    headers = {
        "User-Agent": UA
    }

    for attempt in range(4):

        try:

            response = requests.get(
                API,
                params=params,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 429:

                wait = 15 * (attempt + 1)

                print(
                    "Wikimedia rate limit. Waiting",
                    wait,
                    "seconds..."
                )

                time.sleep(wait)

                continue

            response.raise_for_status()

            data = response.json()

            pages = data.get(
                "query",
                {}
            ).get(
                "pages",
                {}
            )

            results = []

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

                mime = info.get(
                    "mime",
                    ""
                )

                if not url:
                    continue

                if not mime.startswith("image/"):
                    continue

                # Ignore SVG here because FFmpeg handling
                # is less reliable than JPEG/PNG.
                if mime == "image/svg+xml":
                    continue

                results.append(
                    (
                        page.get(
                            "title",
                            ""
                        ),
                        url
                    )
                )

            return results

        except Exception as error:

            print(
                "Search error:",
                error
            )

            time.sleep(
                5 * (attempt + 1)
            )

    return []


# ============================================================
# DOWNLOAD
# ============================================================

def download(url, path):

    headers = {
        "User-Agent": UA
    }

    for attempt in range(4):

        try:

            response = requests.get(
                url,
                headers=headers,
                timeout=45,
            )

            if response.status_code == 429:

                wait = 15 * (attempt + 1)

                print(
                    "Download rate limited. Waiting",
                    wait,
                    "seconds..."
                )

                time.sleep(wait)

                continue

            response.raise_for_status()

            data = response.content

            if len(data) < 15000:
                raise RuntimeError(
                    "Image is suspiciously small."
                )

            path.write_bytes(data)

            return True

        except Exception as error:

            print(
                "Download failed:",
                error
            )

            time.sleep(
                5 * (attempt + 1)
            )

    return False


# ============================================================
# IMAGE RELEVANCE
# ============================================================

def relevance(filename, search_term):

    name = filename.lower()
    query = search_term.lower()

    score = 0

    words = re.findall(
        r"[a-z0-9]+",
        query
    )

    for word in words:

        if len(word) >= 4 and word in name:
            score += 3

    # Prefer actual photographs/images over diagrams
    # when possible.
    if "diagram" in name:
        score -= 2

    if "map" in name:
        score -= 1

    if "logo" in name:
        score -= 4

    if "icon" in name:
        score -= 4

    return score


# ============================================================
# SEARCH STRATEGY
# ============================================================

# Exact article first.
searches = [
    title,
    f"{title} photo",
    f"{title} image",
    topic,
    f"{topic} photo",
    f"{topic} history",
]

# Remove duplicates.
searches = list(
    dict.fromkeys(searches)
)


found = []

seen_urls = set()


# ============================================================
# SEARCH
# ============================================================

for index, term in enumerate(searches):

    # We want several DIFFERENT visuals.
    if len(found) >= 8:
        break

    print()
    print(
        f"Searching {index + 1}/{len(searches)}:",
        term
    )

    results = commons_search(term)

    random.shuffle(results)

    for filename, url in results:

        if url in seen_urls:
            continue

        seen_urls.add(url)

        score = relevance(
            filename,
            term
        )

        found.append(
            (
                score,
                filename,
                url,
            )
        )

        if len(found) >= 8:
            break


# ============================================================
# SORT
# ============================================================

found.sort(
    key=lambda x: x[0],
    reverse=True
)


# ============================================================
# DOWNLOAD
# ============================================================

downloaded = 0

for score, filename, url in found:

    if downloaded >= 7:
        break

    output = (
        IMAGES
        /
        f"image_{downloaded:02d}.jpg"
    )

    print()
    print(
        "Downloading:",
        filename
    )

    if download(
        url,
        output
    ):

        downloaded += 1

        print(
            "Saved:",
            output.name
        )


# ============================================================
# IMPORTANT:
# IF WE HAVE FEWER THAN 4, TRY AGAIN WITH SLOWER SEARCH
# ============================================================

if downloaded < 4:

    print()
    print(
        "Only",
        downloaded,
        "visuals found."
    )

    print(
        "Trying additional searches..."
    )

    extra_terms = [
        f"{topic} Wikimedia",
        f"{title} Wikimedia",
        f"{title} historical",
        f"{topic} historical photograph",
    ]

    for term in extra_terms:

        if downloaded >= 6:
            break

        print(
            "Extra search:",
            term
        )

        results = commons_search(term)

        random.shuffle(results)

        for filename, url in results:

            if url in seen_urls:
                continue

            seen_urls.add(url)

            output = (
                IMAGES
                /
                f"image_{downloaded:02d}.jpg"
            )

            if download(
                url,
                output
            ):

                downloaded += 1

                print(
                    "Saved:",
                    output.name
                )

                if downloaded >= 6:
                    break


# ============================================================
# RESULT
# ============================================================

print()
print("=" * 60)
print("VISUAL SEARCH COMPLETE")
print("=" * 60)

print("Topic:", topic)
print("Article:", title)
print("Images:", downloaded)
print("=" * 60)


if downloaded < 4:

    raise RuntimeError(
        "Could not obtain enough relevant visuals. "
        "The workflow stopped instead of creating a bad Short."
    )
