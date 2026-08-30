import pathlib
import subprocess
import wave
import math

ROOT = pathlib.Path(__file__).parent
WORK = ROOT / "work"

AUDIO = WORK / "audio.wav"

if not AUDIO.exists():
    raise RuntimeError(
        "work/audio.wav does not exist."
    )


# ---------------------------------------------------------
# AUDIO DURATION
# ---------------------------------------------------------

with wave.open(str(AUDIO), "rb") as audio:

    duration = (
        audio.getnframes()
        /
        audio.getframerate()
    )


# ---------------------------------------------------------
# SCRIPT
# ---------------------------------------------------------

lines = [
    line.strip()
    for line
    in (WORK / "script.txt")
    .read_text(
        encoding="utf-8"
    )
    .splitlines()
    if line.strip()
]

if not lines:
    raise RuntimeError("Script is empty.")


weights = [
    max(1, len(line.split()))
    for line in lines
]

total_words = sum(weights)

timeline = []

current = 0

for line, weight in zip(lines, weights):

    segment = (
        duration
        *
        weight
        /
        total_words
    )

    timeline.append(
        (
            current,
            current + segment,
            line
        )
    )

    current += segment


# ---------------------------------------------------------
# VISUALS
# ---------------------------------------------------------

visuals = sorted(
    list(
        (WORK / "images").glob("*.jpg")
    )
    +
    list(
        (WORK / "videos").glob("*.mp4")
    )
)

if len(visuals) < 4:
    raise RuntimeError(
        "Not enough visuals."
    )


# ---------------------------------------------------------
# TIMESTAMP
# ---------------------------------------------------------

def timestamp(seconds):

    hours = int(seconds // 3600)

    minutes = int(
        seconds % 3600 // 60
    )

    secs = seconds % 60

    return (
        f"{hours}:"
        f"{minutes:02d}:"
        f"{secs:05.2f}"
    )


# ---------------------------------------------------------
# CREATE SCENES
# ---------------------------------------------------------

scenes = []

for index, (start, end, text) in enumerate(timeline):

    visual = visuals[
        index % len(visuals)
    ]

    output = (
        WORK
        /
        f"scene_{index:02d}.mp4"
    )

    scene_duration = max(
        0.9,
        end - start
    )

    if visual.suffix.lower() == ".mp4":

        video_filter = (
            "scale=1080:1920:"
            "force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "eq=saturation=1.08:contrast=1.04,"
            "format=yuv420p"
        )

        command = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",

            "-stream_loop",
            "-1",

            "-i",
            str(visual),

            "-vf",
            video_filter,

            "-t",
            str(scene_duration),

            "-an",

            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-crf",
            "23",

            str(output)
        ]

    else:

        # Stronger camera motion.
        if index % 3 == 0:

            motion = (
                "zoompan="
                "z='min(zoom+0.0035,1.18)':"
                "x='iw/2-(iw/zoom/2)':"
                "y='ih/2-(ih/zoom/2)':"
                "d=1:"
                "s=1080x1920:"
                "fps=30"
            )

        elif index % 3 == 1:

            motion = (
                "zoompan="
                "z='min(zoom+0.0028,1.15)':"
                "x='iw/2-(iw/zoom/2)+"
                "110*sin(on/10)':"
                "y='ih/2-(ih/zoom/2)':"
                "d=1:"
                "s=1080x1920:"
                "fps=30"
            )

        else:

            motion = (
                "zoompan="
                "z='min(zoom+0.003,1.16)':"
                "x='iw/2-(iw/zoom/2)':"
                "y='ih/2-(ih/zoom/2)+"
                "70*sin(on/12)':"
                "d=1:"
                "s=1080x1920:"
                "fps=30"
            )

        video_filter = (
            "scale=1280:-2,"
            "crop=1080:1920:"
            "(iw-1080)/2:"
            "(ih-1920)/2,"
            + motion +
            ",eq=saturation=1.10:"
            "contrast=1.05,"
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
            str(visual),

            "-vf",
            video_filter,

            "-t",
            str(scene_duration),

            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-crf",
            "23",

            str(output)
        ]

    subprocess.run(
        command,
        check=True
    )

    scenes.append(output)


# ---------------------------------------------------------
# CONCAT
# ---------------------------------------------------------

concat_file = (
    WORK / "concat.txt"
)

concat_file.write_text(
    "\n".join(
        f"file '{scene.resolve()}'"
        for scene in scenes
    ),
    encoding="utf-8"
)

silent = WORK / "silent.mp4"

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

        str(silent)
    ],
    check=True
)


# ---------------------------------------------------------
# CAPTIONS
# ---------------------------------------------------------

def ass_time(seconds):

    hours = int(seconds // 3600)

    minutes = int(
        seconds % 3600 // 60
    )

    secs = seconds % 60

    centiseconds = int(
        (secs - int(secs)) * 100
    )

    return (
        f"{hours}:"
        f"{minutes:02d}:"
        f"{int(secs):02d}."
        f"{centiseconds:02d}"
    )


caption_events = []

for start, end, text in timeline:

    words = text.split()

    # 3 words per caption group for faster movement.
    groups = [
        words[i:i + 3]
        for i in range(
            0,
            len(words),
            3
        )
    ]

    step = (
        end - start
    ) / max(
        1,
        len(groups)
    )

    for index, group in enumerate(groups):

        if not group:
            continue

        caption_start = (
            start
            +
            index * step
        )

        caption_end = min(
            end,
            caption_start + step
        )

        caption = " ".join(group)

        # Highlight key words by making the whole group bold.
        caption_events.append(
            "Dialogue: 0,"
            f"{ass_time(caption_start)},"
            f"{ass_time(caption_end)},"
            "Main,,0,0,0,,"
            f"{caption}"
        )


ass_file = WORK / "captions.ass"

ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Main,Arial,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&HAA000000,1,0,1,7,3,5,70,70,300,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

ass_file.write_text(
    ass_header
    +
    "\n".join(caption_events),
    encoding="utf-8"
)


# ---------------------------------------------------------
# SOUND EFFECT
# ---------------------------------------------------------

effect = WORK / "whoosh.wav"

subprocess.run(
    [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",

        "-f",
        "lavfi",

        "-i",
        "aevalsrc="
        "0.10*sin("
        "2*PI*(500+1400*t/0.18)"
        ")*exp(-10*t):"
        "s=44100:"
        "d=0.18",

        "-c:a",
        "pcm_s16le",

        str(effect)
    ],
    check=True
)


# ---------------------------------------------------------
# FINAL VIDEO
# ---------------------------------------------------------

final = (
    WORK /
    "viral-fact-short.mp4"
)

filter_complex = (
    f"[0:v]ass={ass_file}[video];"
    f"[2:a]volume=0.08,"
    f"aloop=loop=30:size=7938[fx];"
    f"[1:a]volume=1.0[voice];"
    f"[voice][fx]"
    f"amix=inputs=2:"
    f"duration=first:"
    f"dropout_transition=1"
    f"[audio]"
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
        str(effect),

        "-filter_complex",
        filter_complex,

        "-map",
        "[video]",

        "-map",
        "[audio]",

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

        "-shortest",

        "-movflags",
        "+faststart",

        str(final)
    ],
    check=True
)

print()
print("=" * 60)
print("FINAL SHORT CREATED")
print(final)
print("=" * 60)
