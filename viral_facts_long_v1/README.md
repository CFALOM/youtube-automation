# Long-Form AI Video Factory — Attempt 1

This is the clean replacement for the old `viral_facts_shorts_v2` folder.

## What this version does

- Picks a different topic each run from a mixed topic pool.
- Avoids recently used topics with `work/topic_history.json`.
- Researches the topic from public Wikipedia pages without API keys.
- Builds a long-form script around 1,450 words.
- Downloads relevant Openverse images.
- Generates narration locally with Piper when available, or falls back to espeak-ng.
- Builds a 16:9 1920x1080 video.
- Uses a single scene plan for narration, visuals, and captions.
- Adds Ken Burns motion to still images.
- Generates synchronized captions.
- Adds optional music from `work/music.wav`.
- Saves intermediate files so later stages can be rerun without starting from the beginning.
- Shows clear progress in `render.sh`.

## Run

```bash
chmod +x render.sh
./render.sh all
```

Or run individual stages:

```bash
./render.sh topic
./render.sh assets
./render.sh video
```

## Natural voice

For the best voice, use a local Piper voice and set:

```bash
export PIPER_MODEL=/path/to/your/model.onnx
./render.sh all
```

The pipeline will use Piper when the command and model are available.

## Files generated

`work/script.json` — topic, research notes, script

`work/assets.json` — downloaded visual metadata

`work/narration.wav` — narration

`work/scenes.json` — timing + narration + visual mapping

`work/captions.ass` — timed captions

`work/visuals.mp4` — assembled visual timeline

`work/report.json` — final render report

`final_*.mp4` — final 16:9 video

## Important limitation of Attempt 1

This version deliberately uses a lightweight local-first pipeline. It does not pretend that a tiny offline script is the same thing as a frontier AI model. The content engine is deterministic/template-driven, with public-web research and local TTS. A real local language model can be added in Attempt 2 without rewriting the video renderer.

## Requirements

- Python 3
- FFmpeg + ffprobe
- Piper + a voice model for natural TTS, OR espeak-ng as fallback
- Internet access for public-source image downloads

No paid API key is required.
