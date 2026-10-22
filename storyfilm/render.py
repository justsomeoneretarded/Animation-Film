import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from .planner import ai_plan, template_plan, validate, MODEL_ID
from .audio import synthesize
from .motion import frame_state, ACTION_SECONDS
from .art import frame, character, font, wrapped, W, H


def timestamp(seconds):
    ms=round(seconds*1000)
    h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def captions(plan,timings):
    entries=[]
    for scene,timing in zip(plan['scenes'],timings):
        if plan.get('mode')=='text-led':
            for key,begin,end in [('caption',.08,.91),('dialogue',.25,.88),('shadow_text',.18,.88)]:
                if scene.get(key):entries.append((timing['start']+timing['duration']*begin,timing['start']+timing['duration']*end,scene[key]))
            continue
        words=scene['narration'].split()
        chunks=[' '.join(words[i:i+10]) for i in range(0,len(words),10)]
        margin=min(.65,timing['duration']*.2)
        duration=min(timing['speech_duration'],timing['duration']-2*margin)
        total=sum(len(c.split()) for c in chunks)
        pos=timing['start']+margin
        for chunk in chunks:
            end=pos+duration*len(chunk.split())/total
            entries.append((pos,end,chunk));pos=end
    return entries


def storyboard(plan,out):
    count=len(plan['scenes']); rows=(count+1)//2
    sheet=Image.new('RGB',(960,rows*328),'#080b11');d=ImageDraw.Draw(sheet)
    for i,s in enumerate(plan['scenes']):
        duration=s.get('duration',6)
        im=frame(s,plan['character'],plan['title'],duration*.80,duration,i,count).resize((480,270))
        x=i%2*480;y=i//2*328;sheet.paste(im,(x,y))
        lines=wrapped(s.get('event',s['narration']),900,19)[:2]
        # Text is drawn at half storyboard width.
        description=s.get('event',s['narration']);text=description[:94]+('…' if len(description)>94 else '')
        for j,line in enumerate(wrapped(text,450,13)[:3]):
            d.text((x+12,y+278+j*16),line,font=font(13),fill='#d7d9e1')
    sheet.save(out/'storyboard.jpg',quality=93)


def character_sheet(out):
    im=Image.new('RGBA',(W,H),'#243344')
    d=ImageDraw.Draw(im)
    d.text((86,34),'STORYFILM / ORIGINAL REUSABLE LEADS',font=font(30),fill='#e8e4dc')
    character(im,280,461,1,'female','idle','neutral',.94)
    character(im,680,461,1,'male','idle','neutral',.94)
    d.text((420,974),'FEMALE LEAD',font=font(36),fill='#d0d7e4')
    d.text((1254,974),'MALE LEAD',font=font(36),fill='#d0d7e4')
    im.convert('RGB').save(out/'characters.png')


def render_video(plan,timings,out,fps=12,height=1080):
    entries=captions(plan,timings)
    (out/'captions.srt').write_text('\n\n'.join(f'{i+1}\n{timestamp(a)} --> {timestamp(b)}\n{text}' for i,(a,b,text) in enumerate(entries))+'\n')
    width=height*16//9
    # Frame counts are rounded individually, then timings are adjusted before audio muxing.
    video=out/'film.mp4'
    command=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),
             '-i','pipe:0','-i',str(out/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0',
             '-vf',f'scale={width}:{height}:flags=lanczos','-c:v','libx264','-preset','fast',
             '-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(video)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    frame_directions=(out/'frames.jsonl').open('w')
    try:
        for i,(scene,timing) in enumerate(zip(plan['scenes'],timings)):
            n=round(timing['duration']*fps)
            for j in range(n):
                t=j/fps;absolute=timing['start']+t
                subtitle='' if plan.get('mode')=='text-led' else next((s for a,b,s in entries if a<=absolute<b),'')
                im=frame(scene,plan['character'],plan['title'],t,timing['duration'],i,len(timings),subtitle)
                state=frame_state(scene,t,absolute,timing['duration']);state.update(frame=round(absolute*fps),scene=i+1)
                frame_directions.write(json.dumps(state,separators=(',',':'))+'\n')
                process.stdin.write(im.tobytes())
            print(f'Rendered scene {i+1}/{len(timings)}',flush=True)
    except BaseException:
        process.kill();process.wait();raise
    finally:
        frame_directions.close()
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
    p.add_argument('--model',default=MODEL_ID)
    p.add_argument('--voice',choices=['piper','espeak','none'],default='piper')
    p.add_argument('--plan',type=Path,help='Render a previously saved story.json instead of planning again')
    p.add_argument('--out',type=Path,default=Path('output'))
    p.add_argument('--height',type=int,choices=[540,720,1080],default=1080)
    p.add_argument('--fps',type=int,choices=[12,24,30],default=12)
    p.add_argument('--plan-only',action='store_true',help='Export the editable plan and storyboard before audio/video rendering')
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
    if plan.get('writer','').startswith('authored-'):
        source='authored'
    (args.out/'story.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False))
    print(f"Planned {len(plan['scenes'])} scenes with the {plan['character']} lead.",flush=True)
    storyboard(plan,args.out);character_sheet(args.out)
    if args.plan_only:
        print(f'Plan and storyboard ready: {args.out}',flush=True)
        return
    timings=synthesize(plan,args.out,args.voice,duration_scale=.25 if args.preview else 1,fps=args.fps)
    # Quantize every scene to frame boundaries to prevent cumulative caption drift.
    cursor=0
    for timing in timings:
        delta=cursor-timing['start']
        timing['start']=cursor;timing['speech_start']+=delta
        timing['duration']=round(timing['duration']*args.fps)/args.fps
        plan['scenes'][timing['scene']]['ambient_start']=timing['start']
        cursor+=timing['duration']
    (args.out/'story.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False))
    video=render_video(plan,timings,args.out,args.fps,args.height)
    report={'planner':source,'model':args.model if source=='ai' else None,'voice':args.voice,
            'preview':args.preview,'character':plan['character'],'duration_seconds':cursor,
            'resolution':f'{args.height*16//9}x{args.height}','fps':args.fps,'timings':timings,
            'artwork':'Original rounded vector artwork rasterized at native 1920x1080.',
            'writer':plan.get('writer',source),'target_seconds':plan.get('target_seconds'),
            'captions':'Timed screenplay text layers.' if plan.get('mode')=='text-led' else 'Phrase timing estimated from narration duration, not forced alignment.',
            'engine_version':5,'story_mode':plan.get('mode','legacy-narrated')}
    timeline=[]
    for scene,timing in zip(plan['scenes'],timings):
        timeline.append(dict(start=round(timing['start'],3),end=round(timing['start']+timing['duration'],3),**scene))
    (args.out/'timeline.json').write_text(json.dumps(timeline,indent=2,ensure_ascii=False))
    script=['# '+plan['title'],'',f"{plan['character'].title()} lead · {args.fps} FPS · {cursor:.1f} seconds",'']
    for i,row in enumerate(timeline):
        script.extend([f"## {i+1}. {row['start']:.1f}–{row['end']:.1f}s | {row['location']} | {row.get('shot','wide')}",'',row.get('event',''),'',f"Action: {row['action']}. Emotion: {row.get('emotion_from',row['emotion'])} → {row['emotion']}."])
        script.extend([f"Story change: {row.get('change','')}",f"Performance: gaze={row.get('gaze')}; gesture={row.get('gesture')}; intensity={row.get('intensity')}. Action runs on its own real-second clock, then holds.",f"Environment: {row.get('time')}, {row.get('weather')}; continuous weather phase starts at {row.get('ambient_start',0):.2f}s. Wall clock runs independently in indoor wide shots.",f"Camera: {row.get('shot')}. Frame-by-frame character, prop and environment directions: frames.jsonl."])
        for key in ['caption','dialogue','shadow_text','prop_text','voiceover']:
            if row.get(key):script.append(f"{key.replace('_',' ').title()}: {row[key]}")
        script.append('')
    (args.out/'screenplay.md').write_text('\n'.join(script))
    (args.out/'report.json').write_text(json.dumps(report,indent=2))
    print(f'Finished: {video}',flush=True)

if __name__=='__main__':
    main()
