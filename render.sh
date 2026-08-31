
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$ROOT/viral_facts_long_v1"
WORK="$PROJECT/work"

GENERATOR="$PROJECT/generator.py"
ASSETS="$PROJECT/make_assets.py"
VIDEO="$ROOT/build_video.py"

mkdir -p "$WORK/images" "$WORK/scenes"

log() {
    echo "[$(date '+%H:%M:%S')] $1"
}

fail() {
    echo
    echo "ERROR: $1"
    exit 1
}

MODE="${1:-all}"

echo "========================================"
echo "LONG-FORM VIDEO FACTORY — Attempt 1"
echo "========================================"

case "$MODE" in

    topic)
        log "1/4 TOPIC + SCRIPT"
        python3 "$GENERATOR"
        ;;

    assets)
        log "2/4 VISUAL ASSETS"
        python3 "$ASSETS"
        ;;

    video)
        log "4/4 EDIT + RENDER"

        [ -f "$WORK/narration.wav" ] || fail "narration.wav not found."

        python3 "$VIDEO"

        [ -f "$WORK/final.mp4" ] || fail "final.mp4 was not created."

        log "COMPLETE"
        ;;

    all)

        log "1/4 TOPIC + SCRIPT"
        python3 "$GENERATOR"

        log "2/4 VISUAL ASSETS"
        python3 "$ASSETS"

        log "3/4 NARRATION"

        python3 -m pip install \
            --disable-pip-version-check \
            --no-input \
            -q \
            piper-tts

        PIPER_DATA="$WORK/piper-data"
        PIPER_VOICE="${PIPER_MODEL_NAME:-en_US-lessac-medium}"

        mkdir -p "$PIPER_DATA"

        echo "Checking Piper voice: $PIPER_VOICE"

        python3 -m piper.download_voices \
            --data-dir "$PIPER_DATA" \
            "$PIPER_VOICE"

        echo "Generating narration..."

        python3 -m piper \
            --model "$PIPER_VOICE" \
            --data-dir "$PIPER_DATA" \
            --input-file "$WORK/script.txt" \
            --output-file "$WORK/narration.wav"

        [ -s "$WORK/narration.wav" ] || fail "Narration was not created."

        log "Narration ready"

        log "4/4 EDIT + RENDER"

        python3 "$VIDEO"

        [ -f "$WORK/final.mp4" ] || fail "final.mp4 was not created."

        echo
        echo "========================================"
        echo "VIDEO COMPLETE"
        echo "========================================"
        echo "File: $WORK/final.mp4"
        echo "========================================"

        ;;

    *)
        echo "Usage:"
        echo "  ./render.sh all"
        echo "  ./render.sh topic"
        echo "  ./render.sh assets"
        echo "  ./render.sh video"
        exit 2
        ;;

esac

