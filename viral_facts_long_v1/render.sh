#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

STEP=${1:-all}
WORK="$(pwd)/work"
mkdir -p "$WORK/images" "$WORK/scenes"

say(){ printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"; }

say "LONG-FORM VIDEO FACTORY — Attempt 1"

case "$STEP" in
  topic)
    say "1/4 TOPIC + SCRIPT"
    python3 generator.py
    ;;
  assets)
    say "2/4 VISUAL ASSETS"
    python3 make_assets.py
    ;;
  video)
    say "3/4 VIDEO EDIT"
    python3 build_video.py
    ;;
  all)
    say "1/4 TOPIC + SCRIPT"
    python3 generator.py
    say "2/4 VISUAL ASSETS"
    python3 make_assets.py
    say "3/4 NARRATION"
    if command -v piper >/dev/null 2>&1 && [ -n "${PIPER_MODEL:-}" ] && [ -f "$PIPER_MODEL" ]; then
      cat "$WORK/script.txt" | piper --model "$PIPER_MODEL" --output_file "$WORK/narration.wav"
    elif command -v espeak-ng >/dev/null 2>&1; then
      espeak-ng -s 155 -v en-us+f3 -f "$WORK/script.txt" -w "$WORK/narration.wav"
    else
      echo "ERROR: install Piper or espeak-ng. For natural voice, set PIPER_MODEL to a local Piper model." >&2
      exit 1
    fi
    say "3/4 EDIT + RENDER"
    python3 build_video.py
    say "4/4 COMPLETE"
    ;;
  *)
    echo "Usage: ./render.sh [topic|assets|video|all]" >&2
    exit 2
    ;;
esac
