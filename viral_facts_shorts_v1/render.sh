#!/usr/bin/env bash
set -e
mkdir -p work/png work/audio
for f in work/scenes/*.svg; do b=$(basename "$f" .svg); rsvg-convert "$f" -o "work/png/$b.png"; done
ffmpeg -y -loglevel error -loop 1 -i work/png/scene_00.png -loop 1 -i work/png/scene_01.png -loop 1 -i work/png/scene_02.png -loop 1 -i work/png/scene_03.png -loop 1 -i work/png/scene_04.png -filter_complex "[0:v]trim=duration=7,setpts=PTS-STARTPTS[v0];[1:v]trim=duration=7,setpts=PTS-STARTPTS[v1];[2:v]trim=duration=7,setpts=PTS-STARTPTS[v2];[3:v]trim=duration=7,setpts=PTS-STARTPTS[v3];[4:v]trim=duration=7,setpts=PTS-STARTPTS[v4];[v0][v1][v2][v3][v4]concat=n=5:v=1:a=0[v]" -map "[v]" -r 30 -c:v libx264 -pix_fmt yuv420p -preset veryfast -crf 28 -movflags +faststart work/video_no_audio.mp4
