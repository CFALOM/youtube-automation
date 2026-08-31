#!/usr/bin/env python3
import json, os, re, shutil, subprocess, sys, math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'work'
SCENES = WORK / 'scenes'
SCENES.mkdir(exist_ok=True)

FPS = 30
W, H = 1920, 1080


def run(cmd):
    print('[FFMPEG]', ' '.join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def duration(path):
    p = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)], capture_output=True, text=True)
    return float(p.stdout.strip()) if p.stdout.strip() else 0.0


def words(s):
    return re.findall(r"\b[\w'’-]+\b", s)


def build_scenes():
    script = json.loads((WORK/'script.json').read_text(encoding='utf-8'))
    assets = json.loads((WORK/'assets.json').read_text(encoding='utf-8')).get('assets', [])
    narration = WORK/'narration.wav'
    total = duration(narration)
    text = script['script']
    chunks = re.split(r'(?<=[.!?])\s+', text)
    chunks = [x.strip() for x in chunks if x.strip()]

    # Group sentences into ~7–10 sec scenes using word counts.
    target_seconds = 8.0
    wpm = max(115, min(170, len(words(text)) / max(total, 1) * 60))
    target_words = max(15, round(target_seconds * wpm / 60))
    grouped, cur, count = [], [], 0
    for sentence in chunks:
        wc = len(words(sentence))
        cur.append(sentence); count += wc
        if count >= target_words:
            grouped.append(' '.join(cur)); cur=[]; count=0
    if cur: grouped.append(' '.join(cur))

    scenes=[]; cursor=0.0
    for i, chunk in enumerate(grouped):
        dur = total * (len(words(chunk)) / max(len(words(text)),1))
        dur = max(3.2, dur)
        asset = assets[i % len(assets)] if assets else None
        scenes.append({'index':i,'start':cursor,'end':cursor+dur,'duration':dur,'narration':chunk,'asset':asset})
        cursor += dur

    (WORK/'scenes.json').write_text(json.dumps({'scenes':scenes,'duration':total}, indent=2, ensure_ascii=False), encoding='utf-8')
    return scenes


def render_scene(scene):
    idx = scene['index']
    out = SCENES / f'scene_{idx:03d}.mp4'
    dur = scene['duration']
    asset = scene.get('asset')
    if not asset:
        # Fallback dark background with title text.
        title = json.loads((WORK/'script.json').read_text())['title'].replace(':','\\:').replace("'", "\\'")
        vf = f"color=c=0x111111:s={W}x{H}:r={FPS},drawtext=text='{title}':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2"
        run(['ffmpeg','-y','-f','lavfi','-i',vf,'-t',str(dur),'-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p',str(out)])
        return out
    img = asset['path']
    # Ken Burns. Use only fast filters; captions are handled globally by ffmpeg.
    frames = max(1, int(dur*FPS))
    zoom = "zoompan=z='min(zoom+0.0007,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1"
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},{zoom}:s={W}x{H}:fps={FPS},setsar=1"
    run(['ffmpeg','-y','-loop','1','-i',img,'-vf',vf,'-frames:v',str(frames),'-an','-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p',str(out)])
    return out


def make_concat(scenes):
    concat = WORK/'concat.txt'
    with concat.open('w', encoding='utf-8') as f:
        for s in scenes:
            f.write("file '" + str(SCENES/f"scene_{s['index']:03d}.mp4").replace("'", "'\\''") + "'\n")
    joined = WORK/'visuals.mp4'
    run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(joined)])
    return joined


def caption_file(scenes):
    ass = WORK/'captions.ass'
    def esc(t):
        return t.replace('\\','\\\\').replace('{','\\{').replace('}','\\}')
    def ts(sec):
        h=int(sec//3600); m=int((sec%3600)//60); s=sec%60
        return f'{h}:{m:02d}:{s:05.2f}'
    with ass.open('w', encoding='utf-8') as f:
        f.write('[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n')
        f.write('[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Alignment, MarginL, MarginR, MarginV, Encoding\n')
        f.write('Style: Default,Arial,54,&H00FFFFFF,&H00FFFFFF,&H00101010,&H50000000,1,0,2,80,80,70,1\n\n')
        f.write('[Events]\nFormat: Layer, Start, End, Style, Text\n')
        for s in scenes:
            text=s['narration'].strip()
            # Split long narration into compact caption phrases.
            ws=words(text); parts=[]
            for i in range(0,len(ws),7): parts.append(' '.join(ws[i:i+7]))
            span=s['duration']/max(1,len(parts))
            for j,p in enumerate(parts):
                a=s['start']+j*span; b=min(s['end'],a+span)
                f.write(f'Dialogue: 0,{ts(a)},{ts(b)},Default,{esc(p)}\\N\n')
    return ass


def final_render(visuals, ass):
    out = WORK / 'final.mp4'
    narration = WORK/'narration.wav'
    music = WORK/'music.wav'
    vf = f"ass={ass}"
    if music.exists():
        run(['ffmpeg','-y','-i',str(visuals),'-i',str(narration),'-i',str(music),'-filter_complex',
             '[1:a]volume=1.0[n];[2:a]volume=0.08[m];[m][n]amix=inputs=2:duration=first:dropout_transition=2[a]',
             '-vf',vf,'-map','0:v:0','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','20','-c:a','aac','-b:a','160k','-shortest',str(out)])
    else:
        run(['ffmpeg','-y','-i',str(visuals),'-i',str(narration),'-vf',vf,'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','20','-c:a','aac','-b:a','160k','-shortest',str(out)])
    return out


def main():
    scenes=build_scenes()
    for s in scenes:
        render_scene(s)
    visuals=make_concat(scenes)
    ass=caption_file(scenes)
    out=final_render(visuals,ass)
    report={'output':str(out),'duration':duration(out),'scenes':len(scenes)}
    (WORK/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':
    main()
