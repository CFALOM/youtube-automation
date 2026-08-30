import os
import json
import pathlib
import requests
import random

ROOT = pathlib.Path(__file__).parent
WORK = ROOT / "work"

IMAGES = WORK / "images"
VIDEOS = WORK / "videos"

IMAGES.mkdir(parents=True, exist_ok=True)
VIDEOS.mkdir(parents=True, exist_ok=True)

for file in IMAGES.glob("*"):
    file.unlink()

for file in VIDEOS.glob("*"):
    file.unlink()

API_KEY = os.environ.get("PEXELS_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "PEXELS_API_KEY is missing. "
        "Add it under GitHub Settings → Secrets → Actions."
    )

selected = json.loads(
    (WORK / "selected.json").read_text(
        encoding="utf-8"
    )
)

terms = selected["visual_terms"]

headers = {
    "Authorization": API_KEY
}


def download(url, path):
    response = requests.get(
        url,
        timeout=45
    )

    response.raise_for_status()

    data = response.content

    if len(data) < 10000:
        raise RuntimeError("Downloaded file is suspiciously small.")

    path.write_bytes(data)


image_count = 0
video_count = 0

random.shuffle(terms)

# ---------------------------------------------------------
# VIDEO SEARCH
# ---------------------------------------------------------

for term in terms:

    if video_count >= 4:
        break

    try:

        response = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params={
                "query": term,
                "orientation": "portrait",
                "size": "medium",
                "per_page": 10,
            },
            timeout=25
        )

        response.raise_for_status()

        data = response.json()

        videos = data.get("videos", [])

        if not videos:
            continue

        random.shuffle(videos)

        for video in videos:

            files = video.get(
                "video_files",
                []
            )

            if not files:
                continue

            # Prefer files reasonably suitable for Shorts.
            files.sort(
                key=lambda f:
                abs(
                    (
                        f.get("width", 1)
                        /
                        max(f.get("height", 1), 1)
                    )
                    -
                    (9 / 16)
                )
            )

            chosen = files[0]

            url = chosen.get("link")

            if not url:
                continue

            output = (
                VIDEOS
                /
                f"video_{video_count:02d}.mp4"
            )

            try:
                download(url, output)

                video_count += 1

                print(
                    "Downloaded video:",
                    term
                )

                break

            except Exception as error:
                print(
                    "Video download failed:",
                    error
                )

    except Exception as error:
        print(
            "Video search failed:",
            term,
            error
        )


# ---------------------------------------------------------
# PHOTO SEARCH
# ---------------------------------------------------------

for term in terms:

    if image_count >= 6:
        break

    try:

        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params={
                "query": term,
                "orientation": "portrait",
                "size": "large",
                "per_page": 10,
            },
            timeout=25
        )

        response.raise_for_status()

        data = response.json()

        photos = data.get("photos", [])

        if not photos:
            continue

        random.shuffle(photos)

        for photo in photos:

            source = photo.get(
                "src",
                {}
            )

            url = (
                source.get("large2x")
                or source.get("large")
                or source.get("original")
            )

            if not url:
                continue

            output = (
                IMAGES
                /
                f"image_{image_count:02d}.jpg"
            )

            try:
                download(url, output)

                image_count += 1

                print(
                    "Downloaded image:",
                    term
                )

                break

            except Exception as error:
                print(
                    "Image download failed:",
                    error
                )

    except Exception as error:
        print(
            "Image search failed:",
            term,
            error
        )


total = image_count + video_count

print()
print("=" * 60)
print("VISUALS FOUND")
print("Photos:", image_count)
print("Videos:", video_count)
print("Total:", total)
print("=" * 60)

# Never silently make a garbage video.
if total < 4:
    raise RuntimeError(
        f"Only {total} usable visuals were found. "
        "The workflow stopped instead of creating a bad Short."
    )
