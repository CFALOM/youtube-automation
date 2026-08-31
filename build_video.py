```python
#!/usr/bin/env python3

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# The project data is still stored here.
WORK = ROOT / "viral_facts_long_v1" / "work"
SCENES = WORK / "scenes"

WORK.mkdir(parents=True, exist_ok=True)
SCENES.mkdir(parents=True, exist_ok=True)

FPS = 30
W = 1920
H = 1080


def run(cmd):
    print("[FFMPEG]", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True)


def duration(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    try:
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def words(text):
    return re.findall(r"\b[\w'’-]+\b", text)


def build_scenes():
    script_path = WORK / "script.json"
    assets_path = WORK / "assets.json"
    narration_path = WORK / "narration.wav"

    script = json.loads(script_path.read_text(encoding="utf-8"))

    assets = []
    if assets_path.exists():
        assets = json.loads(
            assets_path.read_text(encoding="utf-8")
        ).get("assets", [])

    total = duration(narration_path)

    if total <= 0:
        raise RuntimeError("Could not determine narration duration.")

    text = script.get("script", "").strip()

    if not text:
        raise RuntimeError("script.json contains no script.")

    sentence_list = re.split(r"(?<=[.!?])\s+", text)
    sentence_list = [s.strip() for s in sentence_list if s.strip()]

    target_seconds = 7.5

    script_word_count = len(words(text))
    wpm = (script_word_count / total) * 60

    wpm = max(115.0, min(175.0, wpm))
    target_words = max(12, round(target_seconds * wpm / 60))

    grouped = []
    current = []
    count = 0

    for sentence in sentence_list:
        sentence_words = len(words(sentence))

        current.append(sentence)
        count += sentence_words

        if count >= target_words:
            grouped.append(" ".join(current))
            current = []
            count = 0

    if current:
        grouped.append(" ".join(current))

    total_script_words = max(len(words(text)), 1)

    scenes = []
    cursor = 0.0

    for index, chunk in enumerate(grouped):
        chunk_words = len(words(chunk))

        scene_duration = total * (
            chunk_words / total_script_words
        )

        scene_duration = max(3.0, scene_duration)

        asset = None

        if assets:
            asset = assets[index % len(assets)]

        scene = {
            "index": index,
            "start": cursor,
            "end": cursor + scene_duration,
            "duration": scene_duration,
            "narration": chunk,
            "asset": asset,
        }

        scenes.append(scene)

        cursor += scene_duration

    scene_data = {
        "duration": total,
        "scenes": scenes,
    }

    (WORK / "scenes.json").write_text(
        json.dumps(
            scene_data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return scenes


def render_scene(scene):
    index = scene["index"]

    output = SCENES / f"scene_{index:03d}.mp4"

    scene_duration = float(scene["duration"])

    asset = scene.get("asset")

    if not asset or not asset.get("path"):
        filter_graph = (
            f"color=c=0x111111:s={W}x{H}:r={FPS},"
            "format=yuv420p"
        )

        run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                filter_graph,
                "-t",
                str(scene_duration),
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-pix_fmt",
                "yuv420p",
                str(output),
            ]
        )

        return output

    image_path = Path(asset["path"])

    if not image_path.exists():
        print(
            f"[WARN] Missing image: {image_path}. "
            "Using fallback."
        )

        filter_graph = (
            f"color=c=0x111111:s={W}x{H}:r={FPS},"
            "format=yuv420p"
        )

        run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                filter_graph,
                "-t",
                str(scene_duration),
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-pix_fmt",
                "yuv420p",
                str(output),
            ]
        )

        return output

    frames = max(1, int(scene_duration * FPS))

    zoom = (
        "zoompan="
        "z='min(zoom+0.0007,1.10)':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        f"d=1:s={W}x{H}:fps={FPS}"
    )

    filter_graph = (
        f"scale={W}:{H}:"
        "force_original_aspect_ratio=increase,"
        f"crop={W}:{H},"
        f"{zoom},"
        "setsar=1"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(image_path),
            "-vf",
            filter_graph,
            "-frames:v",
            str(frames),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            str(output),
        ]
    )

    return output


def make_concat(scenes):
    concat_file = WORK / "concat.txt"
    visuals = WORK / "visuals.mp4"

    with concat_file.open("w", encoding="utf-8") as file:
        for scene in scenes:
            scene_file = (
                SCENES /
                f"scene_{scene['index']:03d}.mp4"
            )

            escaped = str(scene_file).replace(
                "'", "'\\''"
            )

            file.write(
                f"file '{escaped}'\n"
            )

    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(visuals),
        ]
    )

    return visuals


def timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    return (
        f"{hours}:"
        f"{minutes:02d}:"
        f"{secs:05.2f}"
    )


def caption_file(scenes):
    output = WORK / "captions.ass"

    def escape(text):
        return (
            text
            .replace("\\", "\\\\")
            .replace("{", "\\{")
            .replace("}", "\\}")
        )

    with output.open("w", encoding="utf-8") as file:
        file.write(
            "[Script Info]\n"
            "ScriptType: v4.00+\n"
            "PlayResX: 1920\n"
            "PlayResY: 1080\n\n"
        )

        file.write(
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, "
            "PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        )

        file.write(
            "Style: Default,Arial,54,"
            "&H00FFFFFF,&H00FFFFFF,&H00101010,"
            "&H50000000,1,0,2,80,80,70,1\n\n"
        )

        file.write(
            "[Events]\n"
            "Format: Layer, Start, End, Style, Text\n"
        )

        for scene in scenes:
            text = scene["narration"].strip()

            token_list = words(text)

            parts = [
                " ".join(token_list[i:i + 7])
                for i in range(
                    0,
                    len(token_list),
                    7
                )
            ]

            span = scene["duration"] / max(
                len(parts),
                1
            )

            for part_index, part in enumerate(parts):
                start = (
                    scene["start"]
                    + part_index * span
                )

                end = min(
                    scene["end"],
                    start + span
                )

                file.write(
                    "Dialogue: 0,"
                    f"{timestamp(start)},"
                    f"{timestamp(end)},"
                    f"Default,"
                    f"{escape(part)}"
                    "\\N\n"
                )

    return output


def final_render(visuals, captions):
    output = WORK / "final.mp4"

    narration = WORK / "narration.wav"
    music = WORK / "music.wav"

    if not narration.exists():
        raise RuntimeError(
            "narration.wav does not exist."
        )

    caption_filter = f"ass={captions}"

    if music.exists():
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(visuals),
                "-i",
                str(narration),
                "-i",
                str(music),
                "-filter_complex",
                (
                    "[1:a]volume=1.0[n];"
                    "[2:a]volume=0.08[m];"
                    "[m][n]"
                    "amix=inputs=2:"
                    "duration=first:"
                    "dropout_transition=2[a]"
                ),
                "-vf",
                caption_filter,
                "-map",
                "0:v:0",
                "-map",
                "[a]",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-shortest",
                str(output),
            ]
        )
    else:
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(visuals),
                "-i",
                str(narration),
                "-vf",
                caption_filter,
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-shortest",
                str(output),
            ]
        )

    return output


def main():
    print(
        f"[INFO] Work directory: {WORK}",
        flush=True
    )

    scenes = build_scenes()

    print(
        f"[INFO] Rendering {len(scenes)} scenes...",
        flush=True
    )

    for number, scene in enumerate(
        scenes,
        start=1
    ):
        print(
            f"[SCENE {number}/{len(scenes)}] "
            f"{scene['duration']:.1f}s",
            flush=True
        )

        render_scene(scene)

    visuals = make_concat(scenes)
    captions = caption_file(scenes)

    output = final_render(
        visuals,
        captions
    )

    report = {
        "output": str(output),
        "duration": duration(output),
        "scenes": len(scenes),
    }

    (WORK / "report.json").write_text(
        json.dumps(
            report,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        json.dumps(report),
        flush=True
    )


if __name__ == "__main__":
    main()
```
