#!/usr/bin/env bash
set -e

echo "Rendering final Short..."

ffmpeg -y \
  -loglevel error \
  -i work/silent.mp4 \
  -i work/audio.wav \
  -vf "ass=work/captions.ass" \
  -map 0:v:0 \
  -map 1:a:0 \
  -c:v libx264 \
  -preset veryfast \
  -crf 23 \
  -c:a aac \
  -b:a 128k \
  -shortest \
  -movflags +faststart \
  work/viral-fact-short.mp4

echo "FINAL VIDEO CREATED:"
ls -lh work/viral-fact-short.mp4import pathlib
