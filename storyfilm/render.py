import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from .planner import ai_plan, template_plan, validate
from .audio import synthesize
from .art import frame, character, font, wrapped


def timestamp(seconds):
    ms=round(seconds*1000)
    h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def captions(plan,timings):
    entries=[]
    for scene,timing in zip(plan['scenes'],timings):
        words=scene['narration'].split()
        chunks=[' '.join(words[i:i+10]) for i in range(0,len(words),10)]
        duration=min(timing['speech_duration'],timing['duration']-1.3)
        total=sum(len(c.split()) for c in chunks)
        pos=timing['start']+.65
        for chunk in chunks:
            end=pos+duration*len(chunk.split())/total
            entries.append((pos,end,chunk));pos=end
    return entries


def storyboard(plan,out):
    count=len(plan['scenes']); rows=(count+1)//2
    sheet=Image.new('RGB',(960,rows*328),'#080b11');d=ImageDraw.Draw(sheet)
    for i,s in enumerate(plan['scenes']):
        im=frame(s,plan['character'],plan['title'],2.0,6,i,count).resize((480,270))
        x=i%2*480;y=i//2*328;sheet.paste(im,(x,y))
        lines=wrapped(s['narration'],900,19)[:2]
        # Text is drawn at half storyboard width.
        text=s['narration'][:94]+('…' if len(s['narration'])>94 else '')
        for j,line in enumerate(wrapped(text,450,13)[:3]):
            d.text((x+12,y+278+j*16),line,font=font(13),fill='#d7d9e1')
    sheet.save(out/'storyboard.jpg',quality=93)


def character_sheet(out):
    im=Image.new('RGBA',(960,540),'#161c29')
    d=ImageDraw.Draw(im)
    d.text((43,33),'STORYFILM / ORIGINAL REUSABLE LEADS',font=font(22),fill='#e8e4dc')
    character(im,280,435,1,'female','idle','neutral',1.05)
    character(im,680,435,1,'male','idle','neutral',1.05)
    d.text((215,470),'FEMALE LEAD',font=font(18),fill='#d0d7e4')
    d.text((627,470),'MALE LEAD',font=font(18),fill='#d0d7e4')
    im.convert('RGB').save(out/'characters.png')


def render_video(plan,timings,out,fps=24,height=1080):
    entries=captions(plan,timings)
    (out/'captions.srt').write_text('\n\n'.join(f'{i+1}\n{timestamp(a)} --> {timestamp(b)}\n{text}' for i,(a,b,text) in enumerate(entries))+'\n')
    width=height*16//9
    # Frame counts are rounded individually, then timings are adjusted before audio muxing.
    video=out/'film.mp4'
    command=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','960x540','-r',str(fps),
             '-i','pipe:0','-i',str(out/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0',
             '-vf',f'scale={width}:{height}:flags=lanczos','-c:v','libx264','-preset','fast',
             '-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(video)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for i,(scene,timing) in enumerate(zip(plan['scenes'],timings)):
            n=round(timing['duration']*fps)
            for j in range(n):
                t=j/fps;absolute=timing['start']+t
                subtitle=next((s for a,b,s in entries if a<=absolute<b),'')
                im=frame(scene,plan['character'],plan['title'],t,timing['duration'],i,len(timings),subtitle)
                process.stdin.write(im.tobytes())
            print(f'Rendered scene {i+1}/{len(timings)}',flush=True)
    except BaseException:
        process.kill();process.wait();raise
    finally:
        if process.stdin and not process.stdin.closed:
            process.stdin.close()
    if process.wait()!=0:
        raise RuntimeError('FFmpeg failed')
    return video


def main():
    p=argparse.ArgumentParser(description='Render an original short film without paid APIs.')
    p.add_argument('--title',default=os.getenv('FILM_TITLE'))
    p.add_argument('--brief',default=os.getenv('FILM_BRIEF'))
    p.add_argument('--character',choices=['auto','male','female'],default='auto')
    p.add_argument('--planner',choices=['ai','template'],default='ai')
    p.add_argument('--model',default='Qwen/Qwen2.5-1.5B-Instruct')
    p.add_argument('--voice',choices=['piper','espeak','none'],default='piper')
    p.add_argument('--plan',type=Path,help='Render a previously saved story.json instead of planning again')
    p.add_argument('--out',type=Path,default=Path('output'))
    p.add_argument('--height',type=int,choices=[540,720,1080],default=1080)
    p.add_argument('--fps',type=int,choices=[12,24,30],default=24)
    p.add_argument('--preview',action='store_true',help='Short silent preview; cuts scene durations to 25 percent')
    p.add_argument('--allow-template-fallback',action='store_true',help='Explicitly permit basic offline planning if AI fails')
    args=p.parse_args()
    if not args.title or not args.brief:
        p.error('Provide a title and brief through arguments or FILM_TITLE/FILM_BRIEF')
    if not 1<=len(args.title)<=120 or not 20<=len(args.brief)<=4000:
        p.error('Title must be 1–120 characters; brief must be 20–4000 characters')
    if not shutil.which('ffmpeg'):
        p.error('FFmpeg is required')
    args.out.mkdir(parents=True,exist_ok=True)
    source=args.planner
    if args.plan:
        plan=validate(json.loads(args.plan.read_text()),args.title,args.brief,args.character);source='saved-plan'
    elif args.planner=='ai':
        try:
            plan=ai_plan(args.title,args.brief,args.character,args.model,diagnostics_path=args.out/'ai-response.txt')
        except Exception as exc:
            if not args.allow_template_fallback:
                raise RuntimeError('AI planning failed. Retry or explicitly choose --planner template. No misleading fallback was rendered.') from exc
            print(f'WARNING: AI planner failed ({type(exc).__name__}); using explicit template fallback.',flush=True)
            plan=template_plan(args.title,args.brief,args.character);source='template-fallback'
    else:
        plan=template_plan(args.title,args.brief,args.character)
    (args.out/'story.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False))
    print(f"Planned {len(plan['scenes'])} scenes with the {plan['character']} lead.",flush=True)
    storyboard(plan,args.out);character_sheet(args.out)
    timings=synthesize(plan,args.out,args.voice,duration_scale=.25 if args.preview else 1,fps=args.fps)
    # Quantize every scene to frame boundaries to prevent cumulative caption drift.
    cursor=0
    for timing in timings:
        delta=cursor-timing['start']
        timing['start']=cursor;timing['speech_start']+=delta
        timing['duration']=round(timing['duration']*args.fps)/args.fps
        cursor+=timing['duration']
    video=render_video(plan,timings,args.out,args.fps,args.height)
    report={'planner':source,'model':args.model if source=='ai' else None,'voice':args.voice,
            'preview':args.preview,'character':plan['character'],'duration_seconds':cursor,
            'resolution':f'{args.height*16//9}x{args.height}','fps':args.fps,'timings':timings,
            'artwork':'Original procedural 2D artwork; not extracted from the references.',
            'captions':'Phrase timing estimated from narration duration, not forced alignment.'}
    (args.out/'report.json').write_text(json.dumps(report,indent=2))
    print(f'Finished: {video}',flush=True)

if __name__=='__main__':
    main()
