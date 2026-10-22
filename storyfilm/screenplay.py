"""Shot-based screenplay contract shared by every production film."""
import json
import math
import hashlib
import re

ACTIONS={'idle','walk','sit','sleep','phone','receive','send','write','exercise','reach','knock','fall','getup','stand','lookaway','clench','wipe_tear','dismiss'}
LOCATIONS={'bedroom','desk','street','park','gym','rooftop'}
EMOTIONS={'sad','worried','tired','neutral','determined','happy','hurt','angry','ashamed','relieved'}
SHOTS={'wide','close','reaction','insert'}
SHADOWS={'none','loom','shrink','crack'}

def validate_screenplay(plan,title,brief,lead):
    if lead not in {'male','female'}:raise ValueError('Invalid lead character')
    scenes=plan.get('scenes')
    if not isinstance(scenes,list) or not 4<=len(scenes)<=48:raise ValueError('Screenplay needs 4–48 shots')
    out=[];room_states={};ambient_cursor=0
    for i,raw in enumerate(scenes):
        s={}
        for key,allowed,default in [('location',LOCATIONS,None),('action',ACTIONS,None),('emotion',EMOTIONS,None),('emotion_from',EMOTIONS,raw.get('emotion')),('shot',SHOTS,'wide'),('shadow',SHADOWS,'none'),('time',{'night','dawn','day'},'night'),('state',{'normal','clutter'},'normal')]:
            s[key]=raw.get(key,default)
            if s[key] not in allowed:raise ValueError(f'Shot {i+1}: invalid {key}={s[key]}')
        for key,limit in [('caption',120),('dialogue',100),('shadow_text',70),('prop_text',140),('hud',40),('event',500),('voiceover',120),('change',140)]:
            value=raw.get(key,'')
            if not isinstance(value,str) or len(value)>limit:raise ValueError(f'Shot {i+1}: {key} too long or not text')
            s[key]=' '.join(value.split())
        outdoors=s['location'] in {'street','park','rooftop'}
        weather='snow' if outdoors and re.search(r'\bsnow\w*|\bwinter\b|\bblizzard\b',title+' '+brief,re.I) else 'rain' if (outdoors and re.search(r'\brain\w*|\bstorm\b',brief,re.I)) or (not outdoors and s['time']=='night') else 'clear'
        s['weather']=raw.get('weather',weather)
        if s['weather'] not in {'clear','rain','snow'}:raise ValueError('Invalid weather')
        if not s['event']:raise ValueError(f'Shot {i+1} needs a concrete event')
        if len(s['caption'].split())>18:raise ValueError('Caption must be at most 18 words; let the acting carry the scene')
        s['duration']=float(raw.get('duration',7))
        if not math.isfinite(s['duration']) or not 1.25<=s['duration']<=14:raise ValueError('Each shot must last 1.25–14 seconds')
        if s['shot']=='insert' and s['action'] not in {'phone','receive','send','write','dismiss'}:raise ValueError('Insert requires an object interaction')
        if s['shot']=='insert' and not s['prop_text']:raise ValueError('Object insert needs exact readable prop_text')
        if s['action']=='write' and s['location']!='desk':raise ValueError('Writing needs the desk and notebook')
        if s['action']=='exercise' and s['location']!='gym':raise ValueError('Barbell action needs the gym')
        if s['action'] in {'sit','stand'} and s['location'] not in {'bedroom','desk','park'}:raise ValueError('Seated poses need the bed, desk chair or park bench')
        if s['action']=='sleep' and s['location']!='bedroom':raise ValueError('Sleeping needs the bed')
        if s['action']=='reach' and s['location']!='street':raise ValueError('Reaching uses the street door')
        if s['action'] in {'fall','getup','walk','knock'} and s['location'] not in {'street','park','rooftop'}:raise ValueError('Moving action needs an unobstructed outdoor floor')
        if s['action']=='knock':
            # Stage at the actual door rather than waving at empty space.
            if s['location']!='street':raise ValueError('Knock uses the street door')
        if s['location'] in {'bedroom','desk'}:
            # Clutter cannot vanish between cuts: no cleanup action exists yet.
            if room_states.get(s['location'])=='clutter':s['state']='clutter'
            room_states[s['location']]=s['state']
        if s['shadow']=='none' and s['shadow_text']:raise ValueError('Shadow dialogue requires a visible shadow')
        for key,allowed,default in [('gaze',{'phone','notebook','window','ground','camera','door'},'phone' if s['action'] in {'phone','send','receive','dismiss'} else 'notebook' if s['action']=='write' else 'ground'),('gesture',{'none','fidget','clench','wipe_tear'},'none')]:
            s[key]=raw.get(key,default)
            if s[key] not in allowed:raise ValueError('Invalid performance layer '+key)
        s['intensity']=float(raw.get('intensity',.7))
        if not math.isfinite(s['intensity']) or not 0<=s['intensity']<=1:raise ValueError('Emotion intensity must be 0–1')
        s['ambient_start']=float(raw.get('ambient_start',ambient_cursor))
        s['clock_minutes']=float(raw.get('clock_minutes',22*60 if s['time']=='night' else 6*60 if s['time']=='dawn' else 10*60))
        if not all(math.isfinite(s[k]) and s[k]>=0 for k in ('ambient_start','clock_minutes')):raise ValueError('Invalid environment timing')
        ambient_cursor+=s['duration']
        s['narration']=s['voiceover'] # compatibility only; captions are separate
        out.append(s)
    target=float(plan.get('target_seconds',210))
    if not math.isfinite(target) or not 180<=target<=240:raise ValueError('Film must last 180–240 seconds')
    if plan.get('pacing')=='natural' and abs(target-sum(s['duration'] for s in out))>.01:raise ValueError('Natural pacing cannot stretch the action plan')
    # Timing needs enough distinct material; do not turn 4 tiny shots into minutes.
    if target/sum(s['duration'] for s in out)>1.35:raise ValueError('Not enough acted material for the requested runtime')
    return dict(version=plan.get('version',4),pacing=plan.get('pacing','proportional'),mode='text-led',title=title,brief=brief,character=lead,scenes=out,target_seconds=target,writer=plan.get('writer','shot-screenplay-v4'))


def write_screenplay(model,title,brief,lead,diagnostics_path=None):
    from .visual_writer import write
    return write(model,title,brief,lead,diagnostics_path)


def depression_screenplay(title,brief,lead):
    """A testable example using exactly the same renderer and contract as AI films."""
    scenes=[]
    def add(loc,action,event,emotion='tired',caption='',prop='',shot='wide',duration=7,**kw):
        scenes.append(dict(location=loc,action=action,event=event,emotion=emotion,caption=caption,prop_text=prop,shot=shot,duration=duration,**kw))
    add('bedroom','phone','An unanswered message waits while the room stays dark.',caption='The question had been there all day.',state='clutter')
    add('bedroom','receive','Read the unanswered message.',prop='How are you doing?',shot='insert')
    add('bedroom','phone','Starts an answer, hesitates.',prop='Fine.',shot='insert',emotion='worried')
    add('bedroom','phone','Stares at the phone without sending.',emotion='sad',shadow='loom',shadow_text='Nobody needs to hear this.')
    add('desk','write','Tries to make a simple list.',prop='Shower. Breakfast. Answer.',caption='Even the small things had become negotiations.')
    add('desk','write','Pencil stops after the first line.',prop='Shower.',shot='insert')
    add('desk','sit','Looks down at the unfinished list.',emotion='sad',shot='reaction',shadow='loom',shadow_text='You did nothing again.')
    add('bedroom','sleep','Lies on the bed as the night passes.',caption='He was tired. Sleep did not fix that.',state='clutter')
    add('bedroom','receive','Another message appears the next morning.',prop='No rush. Just checking in.',shot='insert',time='dawn')
    add('bedroom','phone','Reads it; anxiety softens for a moment.',emotion_from='worried',emotion='neutral',shot='reaction',time='dawn')
    add('desk','write','Attempts to put the feeling into words.',prop='I do not feel like myself.',emotion='sad',time='dawn')
    add('desk','write','Writes one honest sentence.',prop='I do not feel like myself.',shot='insert',time='dawn')
    add('desk','sit','Reads what is written, then looks toward the window.',emotion='worried',shot='reaction',time='dawn')
    add('street','idle','Stops outside the doorway instead of retreating.',emotion='worried',shadow='loom',shadow_text='Go back inside.',time='dawn')
    add('street','walk','Takes a hesitant walk away from the door.',emotion='tired',time='dawn',caption='Outside did not make him better. It gave him somewhere to breathe.')
    add('park','sit','Sits on the empty bench with both feet on the ground.',emotion='sad',time='day')
    add('park','phone','Brings the unanswered question back up.',emotion='worried',time='day',prop='How are you doing?',shadow='loom')
    add('park','phone','Pauses with the phone held still.',emotion_from='worried',emotion='sad',shot='reaction',time='day',shadow='loom',shadow_text='You will be a burden.')
    add('park','send','Types the answer he has been avoiding.',emotion='worried',prop='I am not doing well. Can we talk?',shot='insert',time='day',duration=10)
    add('park','phone','Holds after sending, worried about the reply.',emotion='worried',shot='reaction',time='day',shadow='loom')
    add('park','receive','Reads a reply with a concrete invitation.',emotion='neutral',prop='Yes. I can call at six. You do not have to explain perfectly.',shot='insert',time='day',duration=9)
    add('park','phone','Shoulders settle; the shadow becomes smaller.',emotion_from='worried',emotion='neutral',shadow='shrink',time='day',caption='There was no perfect answer. There was an answer.')
    add('street','walk','Walks home, slower but no longer retreating.',emotion='neutral',time='day')
    add('desk','sit','Looks at the same unfinished list.',emotion='tired',time='day',caption='The list was still unfinished.')
    add('desk','write','Adds a practical next step underneath it.',emotion='determined',prop='Ask for an appointment.',time='day')
    add('desk','write','Writes the next step clearly.',emotion='determined',prop='Ask for an appointment.',shot='insert',time='day')
    add('bedroom','receive','A new message arrives at six.',emotion='neutral',prop='Ready when you are.',shot='insert',time='dawn',hud='6:00 PM')
    add('bedroom','send','Replies without pretending to be fine.',emotion='neutral',prop='Yes. Thank you for waiting.',shot='insert',time='dawn')
    add('bedroom','phone','Stays with the conversation; the shadow recedes.',emotion_from='tired',emotion='neutral',shadow='shrink',time='dawn',caption='He still felt low. This time, someone knew.')
    add('bedroom','phone','Ends on the same room and a different answer.',emotion='neutral',shot='close',time='dawn',caption='A beginning, not a cure.')
    if lead=='female':
        import re
        for s in scenes:
            for key in ('caption','event'):
                s[key]=re.sub(r'\bhe\b','she',s[key]);s[key]=re.sub(r'\bHe\b','She',s[key]);s[key]=re.sub(r'\bhim\b','her',s[key]);s[key]=re.sub(r'\bhis\b','her',s[key])
    return validate_screenplay(dict(scenes=scenes,target_seconds=210,writer='authored-visual-depression-v4'),title,brief,lead)
