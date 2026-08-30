import pathlib, subprocess, re, wave, math, json, os
ROOT=pathlib.Path(__file__).parent; W=ROOT/'work'; W.mkdir(exist_ok=True)
audio=W/'audio.wav'
with wave.open(str(audio),'rb') as f: duration=f.getnframes()/f.getframerate()
parts=[x.strip() for x in (W/'script.txt').read_text(encoding='utf-8').splitlines() if x.strip()]
weights=[max(1,len(x.split())) for x in parts]; total=sum(weights); timeline=[]; t=0
for p,w in zip(parts,weights):
 d=duration*w/total; timeline.append((t,t+d,p)); t+=d
imgs=sorted((W/'images').glob('*.jpg'))
if not imgs: imgs=[W/'fallback.svg']
scenes=[]
for i,(a,b,text) in enumerate(timeline):
 img=imgs[i%len(imgs)]; out=W/f'scene_{i:02d}.mp4'; d=max(.8,b-a)
 # strong motion: alternating zoom and horizontal drift
 zoom="zoompan=z='min(zoom+0.0020,1.13)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30"
 if i%2: zoom="zoompan=z='min(zoom+0.0017,1.11)':x='iw/2-(iw/zoom/2)+80*sin(on/14)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30"
 vf=f"scale=1280:-2,crop=1080:1920:(iw-1080)/2:(ih-1920)/2,{zoom},format=yuv420p"
 subprocess.run(['ffmpeg','-y','-loglevel','error','-loop','1','-i',str(img),'-vf',vf,'-t',str(d),'-c:v','libx264','-preset','veryfast','-crf','25',str(out)],check=True)
 scenes.append(out)
concat=W/'concat.txt'; concat.write_text('\n'.join("file '"+str(x.resolve())+"'" for x in scenes),encoding='utf-8')
silent=W/'silent.mp4'; subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(silent)],check=True)
# Word-group captions with punchy timing.
def ts(x):
 h=int(x//3600); m=int(x%3600//60); s=x%60; return f'{h}:{m:02d}:{s:05.2f}'
ass=W/'captions.ass'; head='''[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\nStyle: Main,Arial,70,&H00FFFFFF,&H00FFFFFF,&H00000000,&HAA000000,1,0,1,6,3,5,80,80,230,1\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n'''
events=[]
for a,b,text in timeline:
 words=text.split(); n=max(1,math.ceil(len(words)/4)); step=(b-a)/n
 for j in range(n):
  ws=words[j*4:(j+1)*4]
  if ws: events.append(f'Dialogue: 0,{ts(a+j*step)},{ts(min(b,a+(j+1)*step))},Main,,0,0,0,,{" ".join(ws)}')
ass.write_text(head+'\n'.join(events),encoding='utf-8')
# Generate tiny scene-change whooshes/clicks with FFmpeg; no music license/API needed.
effects=W/'effects.wav'
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','aevalsrc=0.06*sin(2*PI*(600+900*t/0.18))*exp(-9*t):s=44100:d=0.18','-c:a','pcm_s16le',str(effects)],check=True)
# Repeat effect roughly once per scene and mix quietly.
final=W/'viral-fact-short.mp4'
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(silent),'-i',str(audio),'-i',str(effects),'-filter_complex',f"[0:v]ass={ass}[v];[1:a]volume=1[a];[2:a]volume=0.10[fx];[fx]aloop=loop=20:size=7938[fxl];[a][fxl]amix=inputs=2:duration=first:dropout_transition=2[aout]",'-map','[v]','-map','[aout]','-c:v','libx264','-preset','veryfast','-crf','24','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',str(final)],check=True)
print(final)
