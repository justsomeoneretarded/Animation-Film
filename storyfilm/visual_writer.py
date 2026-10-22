"""Compile playable events and direct sparse text with real-second choreography."""
import hashlib
import json
import re
from collections import Counter
from .screenplay import validate_screenplay,LOCATIONS,EMOTIONS
from .motion import natural_duration

COUNT=32
VERSION='visual-v5.2'
EVENTS={
 'idle':'Pauses, grounded in place.', 'sit':'Sits with both feet planted.',
 'stand':'Rises from the seat.', 'sleep':'Rests on the bed.', 'walk':'Walks across the setting.',
 'exercise':'Attempts a controlled standing barbell curl.', 'reach':'Reaches toward the street door.',
 'knock':'Knocks at the street door.', 'fall':'Falls onto hands and knees.',
 'getup':'Pushes up from hands and knees.', 'phone':'Types an unsent draft.',
 'send':'Types and sends the message.', 'receive':'Reads an incoming message.',
 'write':'Writes in the notebook.', 'dismiss':'Deletes the unsent draft.',
 'lookaway':'Turns the eyes away from what is difficult to face.',
 'clench':'Tenses the hands, holds, then releases.', 'wipe_tear':'Raises a hand and wipes a tear.'}
OBJECTS={'phone','send','receive','write','dismiss'}

def ending_constraint(brief):
    ending=re.search(r'\b(?:end|ending)\b([^.!?]{0,220})',brief,re.I)
    if not ending:return None,None
    tail=ending.group(1).lower();location=None;action=None
    for pattern,value in [(r'desk|notebook','desk'),(r'bedroom|\bbed\b','bedroom'),(r'park|bench','park'),(r'street|outside','street'),(r'roof','rooftop'),(r'gym','gym')]:
        if re.search(pattern,tail):location=value
    if re.search(r'writ',tail):action='write';location='desk'
    elif re.search(r'\bsend',tail):action='send'
    elif re.search(r'\bwalk',tail):action='walk'
    elif re.search(r'\b(?:curl|barbell)',tail):action='exercise';location='gym'
    elif re.search(r'\bknock',tail):action='knock';location='street'
    elif re.search(r'\b(?:get|gets|getting) up|rising from the ground',tail):
        action='getup';location=location if location in {'street','park','rooftop'} else 'street'
    elif re.search(r'\b(?:sit|sits|sitting|seated)\b|\bbench\b',tail):
        action='sit';location=location if location in {'bedroom','desk','park'} else 'park'
    elif re.search(r'\bsleep',tail):action='sleep';location='bedroom'
    elif re.search(r'\b(?:standing|looking)\b',tail):action='idle'
    return location,action

ALIASES={'phone':'draft_message','send':'send_message','receive':'read_message','dismiss':'delete_draft','write':'write_note','getup':'rise_from_ground','fall':'fall_to_ground','stand':'rise_from_seat'}
def event_codes():
    codes={}
    for action in EVENTS:
        locations=sorted(LOCATIONS)
        if action in {'write','exercise','sleep','reach','knock'}:locations=[{'write':'desk','exercise':'gym','sleep':'bedroom','reach':'street','knock':'street'}[action]]
        if action in {'walk','fall','getup'}:locations=['street','park','rooftop']
        if action in {'sit','stand'}:locations=['bedroom','desk','park']
        for location in locations:codes[ALIASES.get(action,action)+'__'+location]=(action,location)
    return codes
EVENT_CODES=event_codes()

def compile_events(data,title,brief,lead):
    if set(data)!={f'beat_{i+1}' for i in range(COUNT)}:raise ValueError(f'Write exactly {COUNT} events')
    scenes=[];counts=Counter();texts=Counter();previous='neutral';passive=0;draft=''
    for i in range(COUNT):
        raw=data[f'beat_{i+1}'];action,loc=EVENT_CODES[raw['event']];prop=raw['prop_text'].strip()
        if action not in EVENTS or loc not in LOCATIONS or raw['emotion'] not in EMOTIONS:raise ValueError('Unsupported event')
        counts[action]+=1
        if action in {'idle','sit','sleep','lookaway','clench','wipe_tear'}:passive+=1
        if counts[action]>({'receive':9,'send':7,'phone':5,'write':6,'walk':6,'exercise':6}.get(action,4)):
            raise ValueError(f'Too many {action} events: advance the story through different consequences')
        if action in {'write','exercise','sleep','reach','knock'}:loc={'write':'desk','exercise':'gym','sleep':'bedroom','reach':'street','knock':'street'}[action]
        if action in {'walk','fall','getup'} and loc not in {'street','park','rooftop'}:raise ValueError('Stage walking/falling/getting up outdoors')
        if action in {'sit','stand'} and loc not in {'bedroom','desk','park'}:raise ValueError('Sitting/standing needs furniture')
        pretyped=action in {'phone','send'} and prop==draft and bool(draft)
        if action=='dismiss' and draft:prop=draft
        if action in OBJECTS:
            if not prop or not prop.strip('-_. '):raise ValueError('Object actions need exact words')
            texts[prop.casefold()]+=1
            if texts[prop.casefold()]>2:raise ValueError('Repeated text without new information; change the message or event')
        else:prop=''
        if action=='phone':draft=prop
        elif action in {'send','dismiss'}:draft=''
        if not 8<=len(raw.get('change',''))<=100:raise ValueError('Every event needs a concrete change in stakes, information or behavior')
        emotion=raw['emotion'];low=emotion in {'hurt','sad','ashamed','worried'}
        s=dict(pretyped=pretyped,location=loc,action=action,emotion=emotion,emotion_from=previous,prop_text=prop,
            event=EVENTS[action]+(' Text: '+prop if prop else ''),change=raw['change'],
            shot='insert' if action in OBJECTS else 'close' if action in {'wipe_tear','clench','lookaway'} else 'wide',
            gesture=('clench' if emotion=='angry' else 'fidget' if emotion in {'worried','ashamed'} else 'none') if action not in OBJECTS else 'none',
            gaze='phone' if action in OBJECTS-{'write'} else 'notebook' if action=='write' else 'ground' if low else 'camera',
            intensity=.85 if emotion in {'hurt','angry','ashamed'} else .65,
            time=('dawn' if i>=COUNT*3//4 and re.search(r'next morning|following morning|at dawn',brief,re.I) else 'night' if re.search(r'night|evening|dark|rain',brief,re.I) else 'day'),
            caption='',shadow='none',shadow_text='',dialogue='',voiceover='',hud='')
        s['duration']=max(3. if action=='dismiss' else 5.,natural_duration(s));scenes.append(s)
        # Only consequential object events get reaction coverage; never an obligatory triplet.
        if i%2==1 and i<COUNT-1:
            pose='phone' if action in OBJECTS-{'write'} else 'sit' if action=='write' or action=='sit' else 'idle'
            if action in {'fall','sleep'}:pose=action
            reaction={**s,'action':pose,'shot':'reaction','prop_text':'','pretyped':False,'event':'Reacts to the preceding event.',
                'duration':1.8,'hold_at':.8 if action=='fall' else 1.5 if action=='sleep' else None,'emotion_from':emotion,'gaze':'ground' if low else 'camera','change':'The preceding consequence registers in the face and posture.'}
            scenes.append(reaction)
        previous=emotion
    if passive>9:raise ValueError('Too many passive events; at least 23 events must advance physical attempts or object interactions')
    if len(counts)<5:raise ValueError('Use at least five distinct playable actions')
    for pattern,action in [(r'\bsend\w*\b','send'),(r'\bwrit\w*\b','write'),(r'\bwalk\w*\b','walk')]:
        if re.search(pattern,brief,re.I) and not counts[action]:raise ValueError(f'Brief requires {action}')
    location,action=ending_constraint(brief)
    if location and scenes[-1]['location']!=location or action and scenes[-1]['action']!=action:raise ValueError('Respect the requested ending')
    runtime=sum(s['duration'] for s in scenes)
    if not 180<=runtime<=240:raise ValueError(f'Natural runtime {runtime:.0f}s: use shorter messages if over 240, more specific readable messages if under 180. Never pad with repeated poses.')
    return validate_screenplay(dict(version=5,scenes=scenes,target_seconds=runtime,pacing='natural'),title,brief,lead)['scenes']

def direction_schema(count=48):
    cue=dict(type='object',properties={'scene':{'type':'integer','minimum':1,'maximum':count},'text':{'type':'string','minLength':3,'maxLength':85}},required=['scene','text'],additionalProperties=False)
    return dict(type='object',properties={'captions':{'type':'array','minItems':3,'maxItems':5,'items':cue},'shadows':{'type':'array','minItems':0,'maxItems':2,'items':cue}},required=['captions','shadows'],additionalProperties=False)

def apply_direction(core,direction,title,brief,lead):
    scenes=json.loads(json.dumps(core));seen=set()
    for group,field in [('captions','caption'),('shadows','shadow_text')]:
        if len(direction[group])>(5 if group=='captions' else 2):raise ValueError('Keep text sparse')
        for cue in direction[group]:
            index=cue['scene']-1;text=' '.join(cue['text'].split())
            if not 0<=index<len(scenes) or len(text.split())>18:raise ValueError('Invalid text cue')
            if text.casefold() in seen:raise ValueError('Do not repeat text')
            if field=='caption' and re.search(r'^(?:she|he) (?:sits?|stands?|writes?|walks?|looks?|breathes?)(?: (?:in|on|at|across|to|down|up|slowly|quietly|outside|inside)\b[^.!?]*)?[.!?]?$|lamp glows|rain taps',text,re.I):raise ValueError('Caption merely describes a pose')
            if field=='shadow_text' and len(text)>70:raise ValueError('Shorten shadow line')
            scenes[index][field]=text;seen.add(text.casefold())
            if field=='shadow_text':scenes[index]['shadow']='loom'
    return validate_screenplay(dict(version=5,scenes=scenes,target_seconds=sum(s['duration'] for s in scenes),pacing='natural',writer='causal-event-screenplay-v5'),title,brief,lead)

def write(model,title,brief,lead,diagnostics_path=None):
    from .director import write as direct
    return direct(model,title,brief,lead,diagnostics_path)
