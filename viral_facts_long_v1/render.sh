#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

STEP="${1:-all}"
WORK="$(pwd)/work"

mkdir -p "$WORK/images" "$WORK/scenes"

say() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

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
    say "3/4 VIDEO EDIT + RENDER"

    if [ ! -f "$WORK/narration.wav" ]; then
      echo "ERROR: narration.wav is missing." >&2
      exit 1
    fi

    python3 build_video.py
    ;;

  all)

    say "1/4 TOPIC + SCRIPT"
    python3 generator.py

    say "2/4 VISUAL ASSETS"
    python3 make_assets.py

    say "3/4 NARRATION"

    # Install local Piper TTS if it isn't available.
    if ! command -v piper >/dev/null 2>&1; then
      echo "Installing Piper TTS..."
      python3 -m pip install --disable-pip-version-check --no-input piper-tts
    fi

    # Piper can download the selected voice model locally.
    # No paid API is used.
    MODEL_NAME="${PIPER_MODEL_NAME:-en_US-lessac-medium}"

    echo "Using local Piper voice: $MODEL_NAME"

    if ! piper --model "$MODEL_NAME" \
        --data-dir "$WORK/piper-data" \
        --output_file "$WORK/narration.wav" \
        < "$WORK/script.txt"; then

      echo "Piper failed. Trying espeak-ng fallback..."

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
      echo "ERROR: narration file was not created." >&2
      exit 1
    fi

    say "Narration ready"

    say "3/4 EDIT + RENDER"
    python3 build_video.py

    if [ ! -f "$WORK/final.mp4" ]; then
      echo "ERROR: final.mp4 was not created." >&2
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
    echo "Usage: ./render.sh [topic|assets|video|all]" >&2
    exit 2
    ;;

esac
