import pathlib
import subprocess
import wave
import math
import re
import json

ROOT = pathlib.Path(__file__).parent
W = ROOT / "work"

AUDIO = W / "audio.wav"
SCRIPT = W / "script.txt"
IMAGES = W / "images"

W.mkdir(exist_ok=True)

# ---------------------------------------------------------
# AUDIO DURATION
# ---------------------------------------------------------

if not AUDIO.exists():
    raise RuntimeError(
        "work/audio.wav was not found."
    )

with wave.open(str(AUDIO), "rb") as f:
    duration = (
        f.getnframes()
        /
        f.getframerate()
    )

# ---------------------------------------------------------
# SCRIPT
# ---------------------------------------------------------

parts = [
    x.strip()
    for x in SCRIPT.read_text(
        encoding="utf-8"
    ).splitlines()
    if x.strip()
]

if not parts:
    raise RuntimeError(
        "work/script.txt is empty."
    )

# ---------------------------------------------------------
# TIMELINE
# ---------------------------------------------------------

weights = [
    max(1, len(x.split()))
    for x in parts
]

total = sum(weights)

timeline = []

current = 0.0

for text, weight in zip(parts, weights):

    scene_duration = (
        duration
        *
        weight
        /
        total
    )

    timeline.append(
        (
            current,
            current + scene_duration,
            text
        )
    )

    current += scene_duration

# ---------------------------------------------------------
# VISUALS
# ---------------------------------------------------------

images = sorted(
    IMAGES.glob("*.jpg")
)

if not images:

    images = sorted(
        IMAGES.glob("*.jpeg")
    )

if not images:

    images = sorted(
        IMAGES.glob("*.png")
    )

if not images:

    raise RuntimeError(
        "No visual images were found."
    )

print()
print(
    "Found",
    len(images),
    "visuals."
)

# ---------------------------------------------------------
# TIMESTAMP
# ---------------------------------------------------------

def timestamp(seconds):

    hours = int(
        seconds // 3600
    )

    minutes = int(
        (seconds % 3600)
        // 60
    )

    secs = (
        seconds
        %
        60
    )

    return (
        f"{hours}:"
        f"{minutes:02d}:"
        f"{secs:05.2f}"
    )


# ---------------------------------------------------------
# CREATE SCENES
# ---------------------------------------------------------

scenes = []

for i, (start, end, text) in enumerate(
    timeline
):

    image = images[
        i % len(images)
    ]

    output = (
        W /
        f"scene_{i:02d}.mp4"
    )

    scene_duration = max(
        0.8,
        end - start
    )

    print()
    print(
        f"Scene {i + 1}/{len(timeline)}"
    )

    print(
        "Visual:",
        image.name
    )

    print(
        "Text:",
        text
    )

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # Scale the image proportionally so that it completely
    # covers a 1080x1920 canvas.
    #
    # This works for BOTH landscape and portrait images.
    # -----------------------------------------------------

    if i % 3 == 0:

        motion = (
            "zoompan="
            "z='min(zoom+0.0028,1.16)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=1:"
            "s=1080x1920:"
            "fps=30"
        )

    elif i % 3 == 1:

        motion = (
            "zoompan="
            "z='min(zoom+0.0032,1.18)':"
            "x='iw/2-(iw/zoom/2)+"
            "45*sin(on/12)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=1:"
            "s=1080x1920:"
            "fps=30"
        )

    else:

        motion = (
            "zoompan="
            "z='min(zoom+0.0025,1.14)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)+"
            "35*sin(on/10)':"
            "d=1:"
            "s=1080x1920:"
            "fps=30"
        )

    # -----------------------------------------------------
    # THE IMPORTANT FIX
    #
    # force_original_aspect_ratio=increase makes the image
    # large enough to cover the entire 1080x1920 canvas.
    #
    # THEN crop it safely.
    # -----------------------------------------------------

    vf = (
        "scale="
        "1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "setsar=1,"
        f"{motion},"
        "eq="
        "saturation=1.12:"
        "contrast=1.06:"
        "brightness=0.01,"
        "format=yuv420p"
    )

    command = [
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

        "-r",
        "30",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        str(output)
    ]

    subprocess.run(
        command,
        check=True
    )

    scenes.append(output)


# ---------------------------------------------------------
# CONCATENATE
# ---------------------------------------------------------

concat = W / "concat.txt"

concat.write_text(
    "\n".join(
        f"file '{scene.resolve()}'"
        for scene in scenes
    ),
    encoding="utf-8"
)

silent = W / "silent.mp4"

subprocess.run(
    [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat),
        "-c",
        "copy",
        str(silent)
    ],
    check=True
)


# ---------------------------------------------------------
# CAPTIONS
# ---------------------------------------------------------

ass = W / "captions.ass"

header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Main,Arial,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&HAA000000,1,0,1,7,3,5,70,70,300,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

events = []

for start, end, text in timeline:

    words = text.split()

    # 3-word groups = faster visual rhythm
    group_size = 3

    groups = [
        words[x:x + group_size]
        for x in range(
            0,
            len(words),
            group_size
        )
    ]

    groups = [
        group
        for group in groups
        if group
    ]

    if not groups:
        continue

    step = (
        end - start
    ) / len(groups)

    for j, group in enumerate(
        groups
    ):

        a = (
            start
            +
            j * step
        )

        b = min(
            end,
            start
            +
            (j + 1) * step
        )

        caption = " ".join(
            group
        )

        # ASS escape
        caption = (
            caption
            .replace(
                "\\",
                "\\\\"
            )
            .replace(
                "{",
                "\\{"
            )
            .replace(
                "}",
                "\\}"
            )
        )

        events.append(
            "Dialogue: 0,"
            f"{timestamp(a)},"
            f"{timestamp(b)},"
            "Main,,0,0,0,,"
            f"{caption}"
        )

ass.write_text(
    header
    +
    "\n".join(events),
    encoding="utf-8"
)


# ---------------------------------------------------------
# FINAL VIDEO
# ---------------------------------------------------------

final = (
    W /
    "viral-fact-short.mp4"
)

# ---------------------------------------------------------
# SOUND EFFECT
# ---------------------------------------------------------

effects = (
    W /
    "effects.wav"
)

subprocess.run(
    [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",

        "-f",
        "lavfi",

        "-i",
        (
            "aevalsrc="
            "0.035*sin("
            "2*PI*(500+1200*t/0.16)"
            ")*exp(-12*t)"
            ":s=44100:d=0.16"
        ),

        "-c:a",
        "pcm_s16le",

        str(effects)
    ],
    check=True
)

# ---------------------------------------------------------
# MIX
# ---------------------------------------------------------

filter_complex = (
    f"[0:v]ass={ass}[v];"
    "[2:a]volume=0.07[fx];"
    "[fx]aloop=loop=30:size=7056[fxloop];"
    "[1:a]volume=1[a];"
    "[a][fxloop]"
    "amix="
    "inputs=2:"
    "duration=first:"
    "dropout_transition=2"
    "[aout]"
)

subprocess.run(
    [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",

        "-i",
        str(silent),

        "-i",
        str(AUDIO),

        "-i",
        str(effects),

        "-filter_complex",
        filter_complex,

        "-map",
        "[v]",

        "-map",
        "[aout]",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-pix_fmt",
        "yuv420p",

        "-shortest",

        "-movflags",
        "+faststart",

        str(final)
    ],
    check=True
)

print()
print("=" * 60)
print("VIDEO CREATED SUCCESSFULLY")
print("=" * 60)
print(final)
print("=" * 60)
