import pathlib
import subprocess
import wave
import math
import re

ROOT = pathlib.Path(__file__).parent
WORK = ROOT / "work"

AUDIO = WORK / "audio.wav"
SCRIPT = WORK / "script.txt"
IMAGES = WORK / "images"

W = 1080
H = 1920
FPS = 30


# ============================================================
# AUDIO DURATION
# ============================================================

if not AUDIO.exists():

    raise RuntimeError(
        "work/audio.wav does not exist."
    )


with wave.open(
    str(AUDIO),
    "rb"
) as f:

    duration = (
        f.getnframes()
        /
        f.getframerate()
    )


# ============================================================
# SCRIPT
# ============================================================

parts = [
    x.strip()
    for x in SCRIPT.read_text(
        encoding="utf-8"
    ).splitlines()
    if x.strip()
]


if not parts:

    raise RuntimeError(
        "script.txt is empty."
    )


# ============================================================
# WEIGHT TIMELINE
# ============================================================

weights = []

for text in parts:

    words = len(
        text.split()
    )

    weights.append(
        max(
            1,
            words
        )
    )


total = sum(
    weights
)


timeline = []

current = 0.0

for text, weight in zip(
    parts,
    weights
):

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


# ============================================================
# IMAGES
# ============================================================

images = sorted(
    IMAGES.glob(
        "*.jpg"
    )
)


if len(images) < 4:

    raise RuntimeError(
        "Not enough visuals."
    )


# ============================================================
# MAKE SCENES
# ============================================================

scenes = []


for i, (
    start,
    end,
    text
) in enumerate(timeline):

    scene_duration = max(
        0.7,
        end - start
    )

    image = images[
        i % len(images)
    ]

    output = (
        WORK
        /
        f"scene_{i:02d}.mp4"
    )


    # ========================================================
    # SAFE VERTICAL IMAGE FIT
    # ========================================================
    #
    # The image is enlarged until it completely covers
    # 1080x1920, then cropped safely.
    #
    # This prevents the previous:
    # "Invalid too big or non positive crop size" error.
    #

    if i % 3 == 0:

        motion = (
            "zoompan="
            "z='min(zoom+0.0018,1.14)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=1:"
            "s=1080x1920:"
            "fps=30"
        )

    elif i % 3 == 1:

        motion = (
            "zoompan="
            "z='min(zoom+0.0015,1.12)':"
            "x='iw/2-(iw/zoom/2)+"
            "35*sin(on/18)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=1:"
            "s=1080x1920:"
            "fps=30"
        )

    else:

        motion = (
            "zoompan="
            "z='min(zoom+0.0020,1.16)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)+"
            "25*sin(on/16)':"
            "d=1:"
            "s=1080x1920:"
            "fps=30"
        )


    vf = (
        "scale="
        "1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        + motion
        + ","
        "eq=saturation=1.08:"
        "contrast=1.04,"
        "format=yuv420p"
    )


    subprocess.run(
        [
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
        ],
        check=True
    )


    scenes.append(
        output
    )


# ============================================================
# CONCAT
# ============================================================

concat_file = (
    WORK /
    "concat.txt"
)


concat_file.write_text(
    "\n".join(
        "file '"
        +
        str(scene.resolve())
        +
        "'"
        for scene in scenes
    ),
    encoding="utf-8"
)


silent = (
    WORK /
    "silent.mp4"
)


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
        str(concat_file),

        "-c",
        "copy",

        str(silent),
    ],
    check=True
)


# ============================================================
# ASS CAPTIONS
# ============================================================

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
        % 60
    )

    return (
        f"{hours}:"
        f"{minutes:02d}:"
        f"{secs:05.2f}"
    )


# ============================================================
# CAPTION HEADER
# ============================================================

ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Main,Arial,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&HCC000000,1,0,1,5,2,5,100,100,400,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""


events = []


# ============================================================
# WORD GROUP CAPTIONS
# ============================================================

for start, end, text in timeline:

    words = text.split()

    if not words:
        continue


    # 3 words per caption.
    group_size = 3

    groups = []

    for i in range(
        0,
        len(words),
        group_size
    ):

        group = words[
            i:i + group_size
        ]

        groups.append(
            " ".join(group)
        )


    group_duration = (
        end - start
    ) / max(
        1,
        len(groups)
    )


    for index, group in enumerate(groups):

        a = (
            start
            +
            index
            *
            group_duration
        )

        b = (
            start
            +
            (index + 1)
            *
            group_duration
        )


        # ----------------------------------------------------
        # IMPORTANT:
        # ASS can interpret long words strangely if they
        # aren't escaped properly.
        # ----------------------------------------------------

        group = (
            group
            .replace(
                "\\",
                ""
            )
            .replace(
                "{",
                ""
            )
            .replace(
                "}",
                ""
            )
        )


        events.append(
            "Dialogue: 0,"
            + timestamp(a)
            + ","
            + timestamp(b)
            + ",Main,,0,0,0,,"
            + group
        )


captions = (
    WORK /
    "captions.ass"
)


captions.write_text(
    ass_header
    +
    "\n".join(events),
    encoding="utf-8"
)


# ============================================================
# OUTPUT
# ============================================================

print()
print("=" * 60)
print("VIDEO SCENES CREATED")
print("=" * 60)

print(
    "Duration:",
    round(duration, 2),
    "seconds"
)

print(
    "Scenes:",
    len(scenes)
)

print(
    "Images:",
    len(images)
)

print("=" * 60)
