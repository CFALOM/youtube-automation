```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
OLD="$ROOT/viral_facts_long_v1"
WORK="$OLD/work"

mkdir -p "$WORK/images" "$WORK/scenes"

say() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

say "LONG-FORM VIDEO FACTORY — Attempt 1"

STEP="${1:-all}"

case "$STEP" in

  topic)
    say "1/4 TOPIC + SCRIPT"
    python3 "$OLD/generator.py"
    ;;

  assets)
    say "2/4 VISUAL ASSETS"
    python3 "$OLD/make_assets.py"
    ;;

  video)
    say "3/4 EDIT + RENDER"
    python3 "$ROOT/build_video.py"
    ;;

  all)
    say "1/4 TOPIC + SCRIPT"
    python3 "$OLD/generator.py"

    say "2/4 VISUAL ASSETS"
    python3 "$OLD/make_assets.py"

    say "3/4 NARRATION"

    if ! command -v piper >/dev/null 2>&1; then
      echo "Installing Piper TTS..."
      python3 -m pip install --disable-pip-version-check --no-input piper-tts
    fi

    MODEL_NAME="${PIPER_MODEL_NAME:-en_US-lessac-medium}"

    echo "Using local Piper voice: $MODEL_NAME"

    if ! piper \
      --model "$MODEL_NAME" \
      --data-dir "$WORK/piper-data" \
      --output_file "$WORK/narration.wav" \
      < "$WORK/script.txt"; then

      echo "Piper failed. Using espeak-ng fallback..."

      if ! command -v espeak-ng >/dev/null 2>&1; then
        sudo apt-get update -qq
        sudo apt-get install -y espeak-ng
      fi

      espeak-ng \
        -s 155 \
        -v en-us \
        -f "$WORK/script.txt" \
        -w "$WORK/narration.wav"
    fi

    if [ ! -s "$WORK/narration.wav" ]; then
      echo "ERROR: narration.wav was not created."
      exit 1
    fi

    say "Narration ready"

    say "3/4 EDIT + RENDER"
    python3 "$ROOT/build_video.py"

    if [ ! -f "$WORK/final.mp4" ]; then
      echo "ERROR: $WORK/final.mp4 was not created."
      echo "Available MP4 files:"
      find "$ROOT" -type f -name "*.mp4" -print || true
      exit 1
    fi

    say "4/4 COMPLETE"

    echo
    echo "========================================"
    echo "VIDEO COMPLETE"
    echo "Output: $WORK/final.mp4"
    echo "========================================"
    ;;

  *)
    echo "Usage: ./render.sh [topic|assets|video|all]"
    exit 2
    ;;

esac
```
