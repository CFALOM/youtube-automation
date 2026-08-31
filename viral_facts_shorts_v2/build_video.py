import json
import pathlib
import subprocess
import random
import math
import re

ROOT = pathlib.Path(__file__).parent
WORK = ROOT / "work"

IMAGES = WORK / "images"
AUDIO = WORK / "audio.wav"

OUTPUT = WORK / "viral-fact-short.mp4"

FPS = 30
WIDTH = 1080
HEIGHT = 1920


# =========================================================
# HELPERS
# =========================================================

def run(cmd):
    print()
    print("RUNNING:")
    print(" ".join(str(x) for x in cmd))

    subprocess.run(
        cmd,
        check=True
    )


def ffprobe_duration(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return float(result.stdout.strip())


def escape_drawtext(text):
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("'", "\\'")
    text = text.replace("%", "\\%")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace(",", "\\,")
    return text


# =========================================================
# CHECK INPUTS
# =========================================================

if not AUDIO.exists():
    raise RuntimeError(
        "work/audio.wav does not exist."
    )

image_files = sorted(
    IMAGES.glob("*")
)

if len(image_files) < 4:
    raise RuntimeError(
        f"Only {len(image_files)} images available."
    )

script_path = WORK / "script.txt"

if not script_path.exists():
    raise RuntimeError(
        "work/script.txt does not exist."
    )

script = script_path.read_text(
    encoding="utf-8"
).strip()

if not script:
    raise RuntimeError(
        "script.txt is empty."
    )


# =========================================================
# LOAD SELECTED FACT
# =========================================================

selected_path = WORK / "selected.json"

if not selected_path.exists():
    raise RuntimeError(
        "work/selected.json does not exist."
    )

selected = json.loads(
    selected_path.read_text(
        encoding="utf-8"
    )
)

title = selected.get(
    "title",
    "UNKNOWN FACT"
)

topic = selected.get(
    "topic",
    ""
)


# =========================================================
# AUDIO DURATION
# =========================================================

duration = ffprobe_duration(
    AUDIO
)

if duration <= 0:
    raise RuntimeError(
        "Audio has invalid duration."
    )

print()
print("=" * 60)
print("VIDEO BUILDER")
print("=" * 60)
print("Topic:", topic)
print("Title:", title)
print("Audio:", duration, "seconds")
print("Images:", len(image_files))
print("=" * 60)


# =========================================================
# SPLIT SCRIPT
# =========================================================

lines = [
    x.strip()
    for x in script.splitlines()
    if x.strip()
]

if not lines:
    raise RuntimeError(
        "No usable narration lines."
    )


# Don't let a single line dominate the whole video.
# Give each line a reasonable amount of screen time.
weights = []

for line in lines:

    word_count = max(
        1,
        len(line.split())
    )

    weights.append(
        max(1, word_count)
    )

total_weight = sum(weights)

durations = []

for weight in weights:

    d = duration * (
        weight / total_weight
    )

    # Prevent extremely short scenes.
    d = max(
        1.15,
        d
    )

    durations.append(d)


# Normalize durations to exact audio duration.
scale = duration / sum(durations)

durations = [
    d * scale
    for d in durations
]


# =========================================================
# CREATE SCENES
# =========================================================

scenes = WORK / "scenes"
scenes.mkdir(exist_ok=True)

for old in scenes.glob("scene_*.mp4"):
    try:
        old.unlink()
    except Exception:
        pass


scene_files = []


# Use images cyclically if narration has more scenes.
# This is much better than leaving sections static.
random.shuffle(image_files)


for index, (line, scene_duration) in enumerate(
    zip(lines, durations)
):

    image = image_files[
        index % len(image_files)
    ]

    output = (
        scenes /
        f"scene_{index:02d}.mp4"
    )

    # Slightly different movement per scene.
    zoom_start = random.choice([
        "1.00",
        "1.02",
        "1.04",
    ])

    zoom_speed = random.choice([
        "0.0009",
        "0.0012",
        "0.0015",
    ])

    # IMPORTANT:
    #
    # scale2ref + pad is used instead of a blind
    # 1080x1920 crop.
    #
    # This means the image is NEVER required to be
    # 1080x1920 before rendering.
    #
    # The important image content stays visible.

    vf = (
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"
        f"zoompan="
        f"z='min({zoom_start}+on*{zoom_speed},1.10)':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        "d=1:"
        "s=1080x1920:"
        f"fps={FPS},"
        "eq="
        "saturation=1.08:"
        "contrast=1.04,"
        "format=yuv420p"
    )

    run([
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-i",
        str(image),
        "-vf",
        vf,
        "-t",
        str(scene_duration),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        str(output),
    ])

    scene_files.append(output)


# =========================================================
# CONCAT SCENES
# =========================================================

concat_file = WORK / "concat.txt"

with concat_file.open(
    "w",
    encoding="utf-8"
) as f:

    for scene in scene_files:

        path = str(
            scene.resolve()
        ).replace(
            "'",
            "'\\''"
        )

        f.write(
            f"file '{path}'\n"
        )


joined = WORK / "joined.mp4"

run([
    "ffmpeg",
    "-y",
    "-loglevel",
    "error",
    "-f",
    "concat",
    "-safe",
    "0",
    "-i",
    str(concat_file),
    "-c",
    "copy",
    str(joined),
])


# =========================================================
# CAPTION TEXT
# =========================================================

# We intentionally keep captions inside a SAFE AREA.
#
# x=80 means 80 pixels from left.
# x=1000 means approximately 80 pixels from right.
#
# This prevents:
# MINECRAFT
# becoming
# NEC

captioned = WORK / "captioned.mp4"

# Build caption filter using ASS-style drawtext.
#
# Instead of putting the entire sentence in one tiny line,
# break it into short chunks.

caption_filters = []

current_time = 0.0

for index, (line, scene_duration) in enumerate(
    zip(lines, durations)
):

    # Break long text into manageable chunks.
    words = line.split()

    chunks = []

    current = []

    for word in words:

        current.append(word)

        if len(" ".join(current)) >= 22:
            chunks.append(
                " ".join(current)
            )
            current = []

    if current:
        chunks.append(
            " ".join(current)
        )

    if not chunks:
        continue

    chunk_duration = scene_duration / len(chunks)

    for chunk_index, chunk in enumerate(chunks):

        start = (
            current_time +
            chunk_index * chunk_duration
        )

        end = (
            start +
            chunk_duration
        )

        safe_text = escape_drawtext(
            chunk.upper()
        )

        # Large readable captions.
        #
        # Width is controlled by wrapping the text ourselves.
        #
        # Position is deliberately centered in a safe zone.

        caption_filters.append(
            "drawtext="
            "fontfile=/usr/share/fonts/truetype/dejavu/"
            "DejaVuSans-Bold.ttf:"
            f"text='{safe_text}':"
            "fontsize=76:"
            "fontcolor=white:"
            "borderw=7:"
            "bordercolor=black:"
            "shadowx=3:"
            "shadowy=3:"
            "x=(w-text_w)/2:"
            "y=h-470:"
            f"enable='between(t,{start:.3f},{end:.3f})'"
        )

    current_time += scene_duration


# =========================================================
# APPLY CAPTIONS
# =========================================================

caption_filter = ",".join(
    caption_filters
)

run([
    "ffmpeg",
    "-y",
    "-loglevel",
    "error",
    "-i",
    str(joined),
    "-vf",
    caption_filter,
    "-an",
    "-c:v",
    "libx264",
    "-preset",
    "veryfast",
    "-crf",
    "22",
    "-pix_fmt",
    "yuv420p",
    str(captioned),
])


# =========================================================
# FINAL AUDIO + VIDEO
# =========================================================

run([
    "ffmpeg",
    "-y",
    "-loglevel",
    "error",
    "-i",
    str(captioned),
    "-i",
    str(AUDIO),
    "-map",
    "0:v:0",
    "-map",
    "1:a:0",
    "-c:v",
    "copy",
    "-c:a",
    "aac",
    "-b:a",
    "128k",
    "-shortest",
    "-movflags",
    "+faststart",
    str(OUTPUT),
])


# =========================================================
# VERIFY OUTPUT
# =========================================================

if not OUTPUT.exists():
    raise RuntimeError(
        "Final video was not created."
    )

if OUTPUT.stat().st_size < 100000:
    raise RuntimeError(
        "Final video is suspiciously small."
    )

final_duration = ffprobe_duration(
    OUTPUT
)

print()
print("=" * 60)
print("FINAL SHORT CREATED")
print("=" * 60)
print("File:", OUTPUT)
print("Size:", OUTPUT.stat().st_size)
print("Duration:", final_duration)
print("Resolution: 1080x1920")
print("=" * 60)
