"""Write a complete visual arc, then direct text over the actual playable actions."""
import hashlib
import json
import re
from collections import Counter
from .screenplay import validate_screenplay, LOCATIONS, EMOTIONS

COUNT=36
VERSION='visual-v4.3'
EVENTS={
 'idle':'Stands and holds the reaction.', 'sit':'Sits with both feet planted.',
 'stand':'Rises from the seat and pauses.', 'sleep':'Lies on the bed with eyes closed.',
 'walk':'Walks across the setting.', 'exercise':'Raises the barbell once, holds, then lowers it.',
 'reach':'Extends a hand toward the street door.', 'knock':'Raises a hand and knocks at the street door.',
 'fall':'Falls onto hands and knees, then holds.', 'getup':'Pushes up from hands and knees to standing.',
 'phone':'Holds the phone and pauses before responding.',
 'send':'Types and sends the message.', 'receive':'Reads an incoming message.',
 'write':'Writes in the notebook at the desk.'}


def shot_variants():
    """Action comes first so the model chooses the event before its setting."""
    base=dict(action={},location={},shot={},emotion={'type':'string','enum':sorted(EMOTIONS)},prop_text={})
    def variant(actions,locations,shots,object_text=False):
        props={**base,'action':{'type':'string','enum':actions},'location':{'type':'string','enum':locations},
               'shot':{'type':'string','enum':shots},'prop_text':{'type':'string','minLength':3,'maxLength':110} if object_text else {'const':''}}
        required=list(props)
        props['time']={'type':'string','enum':['night','dawn','day']}
        props['weather']={'type':'string','enum':['clear','rain','snow']}
        return dict(type='object',properties=props,required=required,additionalProperties=False)
    ordinary=['wide','close','reaction'];all_locations=sorted(LOCATIONS)
    return [variant(['idle'],all_locations,ordinary),
            variant(['phone'],all_locations,ordinary),
            variant(['phone','send','receive'],all_locations,['insert'],True),
            variant(['sit','stand'],['bedroom','desk','park'],ordinary),
            variant(['sleep'],['bedroom'],ordinary),
            variant(['walk','fall','getup'],['street','park','rooftop'],ordinary),
            variant(['knock','reach'],['street'],ordinary),
            variant(['write'],['desk'],ordinary+['insert'],True),
            variant(['exercise'],['gym'],ordinary)]


def ending_constraint(brief):
    ending=re.search(r'\b(?:end|ending)\b([^.!?]{0,220})',brief,re.I)
    if not ending:return None,None
    tail=ending.group(1).lower();location=None;action=None
    for pattern,value in [(r'desk|notebook','desk'),(r'bedroom|\bbed\b','bedroom'),(r'park|bench','park'),(r'street|outside','street'),(r'roof','rooftop'),(r'gym','gym')]:
        if re.search(pattern,tail):location=value
    if re.search(r'writ',tail):action='write';location='desk'
    elif re.search(r'\bsend',tail):action='send'
    elif re.search(r'\bwalk',tail):action='walk'
    return location,action


def core_schema(brief):
    variants=shot_variants();properties={f'scene_{i+1}':{'oneOf':variants} for i in range(COUNT)}
    location,action=ending_constraint(brief)
    if location or action:
        restricted=[]
        for source in variants:
            v=json.loads(json.dumps(source));p=v['properties']
            if action:
                if action not in p['action']['enum']:continue
                p['action']['enum']=[action]
            if location:
                if location not in p['location']['enum']:continue
                p['location']['enum']=[location]
            restricted.append(v)
        if not restricted:raise ValueError('The requested ending needs an unsupported action/location combination')
        properties[f'scene_{COUNT}']={'oneOf':restricted}
    return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)


def compile_core(data,title,brief,lead):
    if set(data)!={f'scene_{i+1}' for i in range(COUNT)}:raise ValueError(f'Write exactly {COUNT} numbered shots')
    scenes=[];previous='tired'
    for i in range(COUNT):
        raw=data[f'scene_{i+1}'];s=dict(raw)
        action=s['action'];prop=s.get('prop_text','')
        if action not in EVENTS:raise ValueError('Unsupported action')
        if action not in {'phone','send','receive','write'} and prop:raise ValueError('This action has no phone or notebook text')
        if action=='phone' and s.get('shot')!='insert' and prop:raise ValueError('Use an insert to display draft text')
        if action in {'send','receive'} and s.get('shot')!='insert':raise ValueError('Sending/receiving requires a readable insert')
        if action=='write' and not prop.strip():raise ValueError('Writing requires exact notebook words')
        duration={'walk':7,'fall':4,'getup':7,'exercise':8,'stand':4,'knock':5,'reach':5,'sleep':7}.get(action,6)
        if s['shot']=='insert':duration=max(6,min(12,3+len(prop.split())/2))
        # Clock changes happen at act boundaries, not arbitrarily between cuts.
        time=s.get('time','night' if i<COUNT//3 else 'dawn' if i<COUNT*2//3 else 'day')
        s.update(duration=duration,event=EVENTS[action]+(' Text: '+prop if prop else ''),emotion_from=previous,
                 time=time,shadow='none',caption='',dialogue='',shadow_text='',voiceover='',hud='')
        previous=s['emotion'];scenes.append(s)
    actions=[s['action'] for s in scenes]
    if actions.count('stand')>4:raise ValueError('Too much repeated rising/sitting; use at most four stand shots and advance the object interactions or journey')
    for pattern,action in [(r'\bsend\w*\b','send'),(r'\bwrit\w*\b','write'),(r'\bwalk\w*\b','walk')]:
        if re.search(pattern,brief,re.I) and action not in actions:raise ValueError(f'The brief needs a visible {action} action')
    if len(set(actions))<4:raise ValueError('Use at least four distinct playable actions; do not repeat holding/sitting throughout')
    if sum(a in {'write','send','receive','walk','exercise','reach','knock','fall','getup','stand'} for a in actions)<12:
        raise ValueError('Too few acted events; at least twelve shots need a specific performed action')
    if len({s['emotion'] for s in scenes})<2:raise ValueError('The story needs a visible emotional change')
    # A message or written phrase can be revisited, but cannot fill the whole film.
    counts=Counter(s['prop_text'].casefold().strip() for s in scenes if s['shot']=='insert' and s['prop_text'])
    if any(n>4 for n in counts.values()):raise ValueError('Repeated object inserts: advance the story instead of rereading the same text')
    location,action=ending_constraint(brief)
    if location and scenes[-1]['location']!=location:raise ValueError('Keep the requested final location')
    if action and scenes[-1]['action']!=action:raise ValueError('Perform the requested final action')
    return validate_screenplay(dict(scenes=scenes,target_seconds=210),title,brief,lead)['scenes']


def direction_schema():
    cue={'type':'object','properties':{'scene':{'type':'integer','minimum':1,'maximum':COUNT},
          'text':{'type':'string','minLength':3,'maxLength':100}},'required':['scene','text'],'additionalProperties':False}
    return {'type':'object','properties':{'captions':{'type':'array','minItems':4,'maxItems':6,'items':cue},
            'shadows':{'type':'array','minItems':0,'maxItems':4,'items':cue}},'required':['captions','shadows'],'additionalProperties':False}


def apply_direction(core,direction,title,brief,lead):
    scenes=json.loads(json.dumps(core));seen=set()
    if not 4<=len(direction['captions'])<=6 or len(direction['shadows'])>4:raise ValueError('Use 4–6 story captions and at most four shadow lines')
    for group,field in [('captions','caption'),('shadows','shadow_text')]:
        used=set()
        for cue in direction[group]:
            index=cue['scene']-1;text=' '.join(cue['text'].split());identity=text.casefold()
            if not 0<=index<COUNT:raise ValueError('Text cue points outside the film')
            if index in used:raise ValueError('Use separate shots for separate cues of the same type')
            if identity in seen:raise ValueError('Do not repeat captions or shadow lines')
            if len(text.split())>18:raise ValueError('Keep text under 18 words')
            if field=='caption' and re.search(r'\b(?:she|he) (?:sits?|stands?|writes?|walks?|looks?|breathes?)\b|lamp glows|rain taps',text,re.I):
                raise ValueError('Captions must add story meaning, not describe poses, breathing, lamps or rain')
            if field=='shadow_text' and len(text)>70:raise ValueError('Shorten the shadow line')
            scenes[index][field]=text;used.add(index);seen.add(identity)
            if field=='shadow_text':scenes[index]['shadow']='loom'
    if direction['shadows']:
        choices=[i for i,s in enumerate(scenes) if i>=COUNT*2//3 and s['action'] in {'send','write','getup'}]
        if choices:
            choice=choices[-1]
            visible=next((i for i in range(choice,COUNT) if scenes[i]['shot']!='insert'),None)
            if visible is not None and not scenes[visible]['shadow_text']:scenes[visible]['shadow']='shrink'
    return validate_screenplay(dict(scenes=scenes,target_seconds=210,writer='connected-visual-screenplay-qwen4b-v43'),title,brief,lead)


def write(model,title,brief,lead,diagnostics_path=None):
    identity=hashlib.sha256(json.dumps([VERSION,title,brief,lead]).encode()).hexdigest()
    checkpoint=diagnostics_path.with_suffix('.checkpoint.json') if diagnostics_path else None
    saved={};raws=[]
    if checkpoint and checkpoint.exists():
        try:
            candidate=json.loads(checkpoint.read_text())
            if candidate.get('identity')==identity:saved=candidate;raws=candidate.get('raws',[])
        except (ValueError,TypeError):pass
    def save():
        if checkpoint:checkpoint.write_text(json.dumps({**saved,'identity':identity,'raws':raws},ensure_ascii=False))
    def ask(messages,schema,tokens):
        response=model.create_chat_completion(messages=messages,max_tokens=tokens,temperature=.55,response_format={'type':'json_object','schema':schema})
        raw=response['choices'][0]['message']['content'];raws.append(raw)
        if diagnostics_path:diagnostics_path.write_text('\n\n'.join(raws))
        return json.loads(raw)
    fields=['opening','desire','obstacle','setback','decision','payoff']
    outline=saved.get('outline')
    if not isinstance(outline,dict) or set(outline)!=set(fields):
        print('Planning the complete story arc.',flush=True)
        schema={'type':'object','properties':{k:{'type':'string','maxLength':140} for k in fields},'required':fields,'additionalProperties':False}
        outline=ask([{'role':'system','content':'Write specific visual stories with cause and effect, an honest setback and an earned ending. No instant cure or motivational slogans.'},
                     {'role':'user','content':f'Title: {json.dumps(title)}. Brief data: {json.dumps(brief)}. One adult {lead} lead only. Plan opening, desire, obstacle, setback, decision and payoff. Each is one concise sentence. Respect the requested ending.'}],schema,550)
        if set(outline)!=set(fields):raise ValueError('Incomplete outline')
        saved['outline']=outline;save()
    core=saved.get('core')
    if core is not None:
        try:core=compile_core({f'scene_{i+1}':{k:s[k] for k in ('action','location','shot','emotion','prop_text','time','weather')} for i,s in enumerate(core)},title,brief,lead)
        except (ValueError,KeyError,TypeError):core=None;saved.pop('direction',None)
    if core is None:
        prompt=f'''Stage the WHOLE film as {COUNT} numbered shots, scene_1 through scene_{COUNT}, one complete connected arc.
Title: {json.dumps(title)}. Lead: {lead}. Brief DATA: {json.dumps(brief)}.
Story arc: {json.dumps(outline)}.
Shots 1–12 establish the pattern, the desire and a failed attempt. Shots 13–24 show its consequence, a difficult step and a real setback. Shots 25–36 make a different consequential choice and fulfill the requested ending. Never restart or repeat an earlier act.
Use only the supported action/location pairs in the schema. Choose the ACTION first, then its setting. Change indoor settings with a cut. Walking/falling/getting up are outdoors. Writing uses the desk. Sleeping uses the bed. Sitting/rising needs the bed, desk chair or park bench. Reaching/knocking uses the street door. Exercise is one barbell rep in the gym.
One human only. Do not invent objects, folding pages, opening books, eating, calls, extra people, or invisible physical actions. This is a performed story, not a slideshow of poses. Include purposeful movement, the failed attempt, a response, a pause and a new choice. Use at most four stand shots; do not fill acts with repeated sitting and rising.
shot=wide establishes place; close/reaction shows an emotional change; insert shows an object interaction. Every send and receive MUST be an insert with the exact message in prop_text. Phone wide/close means holding the phone, not sending. Phone insert is an unsent draft. Write uses the exact notebook words in prop_text. A send is a committed choice; show it if the brief asks for it. Empty prop_text on other actions.
Use brief, natural message/notebook wording that advances the story. Do not repeat the same message insert more than four times. Revisit a place with changed behavior rather than repeating events. Use different expressions as the story develops. End exactly as the brief requests. No captions or prose descriptions in this pass: the actions themselves are the screenplay.'''
        messages=[{'role':'system','content':'You are a visual dramatist. Plan literal playable actions across ONE continuous complete story.'},{'role':'user','content':prompt}]
        schema=core_schema(brief)
        for attempt in range(3):
            print(f'Writing the complete {COUNT}-shot action story, attempt {attempt+1}.',flush=True)
            try:
                data=ask(messages,schema,4000)
                core=compile_core(data,title,brief,lead);break
            except (ValueError,KeyError,TypeError) as exc:
                if attempt==2:raise
                messages[1]['content']=prompt+f'\nRewrite the WHOLE story and fix this validation problem: {exc}'
        saved['core']=core;save()
    compact=[dict(scene=i+1,action=s['action'],location=s['location'],emotion=s['emotion'],text=s['prop_text']) for i,s in enumerate(core)]
    direction=saved.get('direction')
    if direction:
        try:return apply_direction(core,direction,title,brief,lead)
        except (ValueError,KeyError,TypeError):pass
    messages=[{'role':'system','content':'Direct economical text over a performed film. Never describe an action that is absent.'},
              {'role':'user','content':f'''Title {json.dumps(title)}. Brief DATA: {json.dumps(brief)}. Arc: {json.dumps(outline)}.
ACTUAL performed shots: {json.dumps(compact)}.
Choose 4–6 short white story captions across the WHOLE film. Add meaning, stakes or a change in understanding; do not describe sitting, standing, walking, looking, writing, breathing, lamps or rain. No generic advice or slogans. The visible messages already carry dialogue. Avoid explaining every beat.
Optionally choose 0–4 short red shadow lines at specific moments of doubt. Each line must be different and tied to this story. Never repeat a line. Give each cue its actual numbered scene and text, at most 18 words. No new people, objects, physical events, miraculous cure or unearned victory. The last caption must fit the actual ending. Output captions and shadows arrays only.'''}]
    for attempt in range(3):
        print(f'Directing sparse story text, attempt {attempt+1}.',flush=True)
        try:
            data=ask(messages,direction_schema(),900)
            plan=apply_direction(core,data,title,brief,lead);saved['direction']=data;save();return plan
        except (ValueError,KeyError,TypeError) as exc:
            if attempt==2:raise
            messages.append({'role':'user','content':f'Rewrite the text cues and fix: {exc}'})
