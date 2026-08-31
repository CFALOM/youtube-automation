import json
import pathlib
import random
import re
import time
import requests
from urllib.parse import quote

ROOT = pathlib.Path(__file__).parent
WORK = ROOT / "work"

IMAGES = WORK / "images"
VIDEOS = WORK / "videos"

IMAGES.mkdir(parents=True, exist_ok=True)
VIDEOS.mkdir(parents=True, exist_ok=True)

# Clean old assets
for folder in (IMAGES, VIDEOS):
    for f in folder.iterdir():
        if f.is_file():
            try:
                f.unlink()
            except Exception:
                pass

UA = (
    "Mozilla/5.0 (compatible; ViralFactsShorts/4.0; "
    "+https://github.com/CFALOM/youtube-automation)"
)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": UA,
    "Accept": "application/json",
})


# =========================================================
# LOAD SELECTED FACT
# =========================================================

selected_path = WORK / "selected.json"

if not selected_path.exists():
    raise RuntimeError("work/selected.json does not exist.")

selected = json.loads(
    selected_path.read_text(encoding="utf-8")
)

topic = selected.get("topic", "")
title = selected.get("title", "")
fact = selected.get("fact", "")

if not topic or not fact:
    raise RuntimeError("selected.json is missing topic or fact.")


# =========================================================
# BUILD SMART VISUAL QUERIES
# =========================================================

def words(text):
    return re.findall(r"[A-Za-z0-9]+", text.lower())


def important_terms(text):
    stop = {
        "the", "and", "that", "this", "with", "from", "were",
        "was", "are", "for", "into", "about", "their", "they",
        "have", "has", "had", "which", "when", "where", "what",
        "why", "how", "than", "then", "also", "only", "more",
        "most", "some", "many", "very", "first", "part"
    }

    result = []

    for w in words(text):
        if len(w) >= 4 and w not in stop and w not in result:
            result.append(w)

    return result[:8]


key_terms = important_terms(f"{topic} {title} {fact}")

queries = []

# Most specific searches first.
if title:
    queries.append(f"{title} photo")

if title and topic:
    queries.append(f"{topic} {title}")

if key_terms:
    queries.append(" ".join(key_terms[:4]))

if topic:
    queries.append(f"{topic} real photo")

if topic:
    queries.append(f"{topic} close up")

if topic:
    queries.append(f"{topic} history")

# Remove duplicates
queries = list(dict.fromkeys(
    q.strip() for q in queries if q.strip()
))

print()
print("=" * 60)
print("SMART VISUAL ENGINE")
print("=" * 60)
print("Topic:", topic)
print("Title:", title)
print("Queries:")

for q in queries:
    print("-", q)


# =========================================================
# OPENVERSE SEARCH
# =========================================================

OPENVERSE = "https://api.openverse.org/v1/images/"

def openverse_search(query, page_size=20):
    try:
        response = SESSION.get(
            OPENVERSE,
            params={
                "q": query,
                "page_size": page_size,
            },
            timeout=25,
        )

        if response.status_code == 429:
            retry = response.headers.get("Retry-After", "10")

            try:
                retry = min(int(retry), 30)
            except Exception:
                retry = 10

            print(
                f"Openverse rate limited. Waiting {retry}s..."
            )

            time.sleep(retry)

            response = SESSION.get(
                OPENVERSE,
                params={
                    "q": query,
                    "page_size": page_size,
                },
                timeout=25,
            )

        response.raise_for_status()

        return response.json().get("results", [])

    except Exception as error:
        print("Openverse search failed:", error)
        return []


# =========================================================
# QUALITY FILTER
# =========================================================

def score_result(item, query):
    score = 0

    width = item.get("width") or 0
    height = item.get("height") or 0

    if width >= 900:
        score += 2

    if height >= 900:
        score += 2

    if width >= 1200:
        score += 1

    if height >= 1200:
        score += 1

    # Prefer portrait/square images because they work better
    # with Shorts.
    if height > width:
        score += 3

    # Avoid tiny thumbnails.
    if width < 500 or height < 500:
        score -= 5

    # Title/description relevance.
    text = (
        str(item.get("title", "")) + " " +
        str(item.get("description", ""))
    ).lower()

    for term in important_terms(query):
        if term in text:
            score += 2

    return score


def get_image_url(item):
    return (
        item.get("url")
        or item.get("thumbnail")
        or item.get("source")
    )


# =========================================================
# COLLECT VISUALS
# =========================================================

candidates = []
seen = set()

for query in queries:

    print()
    print("Searching:", query)

    results = openverse_search(query)

    print("Results:", len(results))

    ranked = []

    for item in results:

        url = get_image_url(item)

        if not url:
            continue

        if url in seen:
            continue

        score = score_result(item, query)

        if score < 0:
            continue

        ranked.append((score, item))

    ranked.sort(
        key=lambda x: x[0],
        reverse=True
    )

    for score, item in ranked[:8]:

        url = get_image_url(item)

        if url in seen:
            continue

        seen.add(url)

        candidates.append({
            "score": score,
            "url": url,
            "title": item.get("title", ""),
            "source": item.get("source", ""),
            "license": item.get("license", ""),
            "creator": item.get("creator", ""),
            "query": query,
            "width": item.get("width", 0),
            "height": item.get("height", 0),
        })

    # We don't need hundreds of images.
    if len(candidates) >= 30:
        break


# =========================================================
# SORT + RANDOMIZE TOP QUALITY
# =========================================================

candidates.sort(
    key=lambda x: x["score"],
    reverse=True
)

# Keep strong candidates but introduce some variety.
best = candidates[:20]

random.shuffle(best)


# =========================================================
# DOWNLOAD
# =========================================================

def download_image(url, output):
    response = SESSION.get(
        url,
        timeout=35,
        allow_redirects=True,
    )

    response.raise_for_status()

    data = response.content

    if len(data) < 15000:
        raise RuntimeError("Image is suspiciously small.")

    content_type = response.headers.get(
        "Content-Type",
        ""
    ).lower()

    if (
        "image" not in content_type
        and not url.lower().split("?")[0].endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        )
    ):
        raise RuntimeError(
            f"Not an image response: {content_type}"
        )

    output.write_bytes(data)


downloaded = []
attempted = 0

for item in best:

    if len(downloaded) >= 12:
        break

    attempted += 1

    output = (
        IMAGES /
        f"image_{len(downloaded):02d}.jpg"
    )

    print(
        "Downloading:",
        item["title"][:80]
    )

    try:

        download_image(
            item["url"],
            output
        )

        downloaded.append({
            **item,
            "filename": output.name,
        })

        print(
            "OK:",
            output.name
        )

    except Exception as error:

        print(
            "Download failed:",
            error
        )

        try:
            if output.exists():
                output.unlink()
        except Exception:
            pass

    # Don't hammer the API.
    time.sleep(1)


# =========================================================
# SAVE VISUAL METADATA
# =========================================================

visual_data = {
    "topic": topic,
    "title": title,
    "fact": fact,
    "images": downloaded,
}

(WORK / "visuals.json").write_text(
    json.dumps(
        visual_data,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


# =========================================================
# RESULT
# =========================================================

print()
print("=" * 60)
print("VISUAL SEARCH COMPLETE")
print("=" * 60)
print("Candidates:", len(candidates))
print("Download attempts:", attempted)
print("Images:", len(downloaded))
print("=" * 60)


# We need enough visuals to make a genuinely dynamic Short.
if len(downloaded) < 4:
    raise RuntimeError(
        f"Only {len(downloaded)} usable visuals were downloaded. "
        "The workflow stopped instead of creating a low-quality Short."
    )
