import json
import re
from pathlib import Path

LOCATIONS = {'bedroom', 'street', 'park', 'gym', 'desk', 'rooftop'}
ACTIONS = {'idle', 'walk', 'sit', 'sleep', 'phone', 'write', 'exercise', 'reach'}
EMOTIONS = {'sad', 'worried', 'tired', 'neutral', 'determined', 'happy'}


def validate(plan, title, brief, character='auto'):
    if not isinstance(plan, dict) or not isinstance(plan.get('scenes'), list):
        raise ValueError('Story must contain a scenes array')
    if not 4 <= len(plan['scenes']) <= 12:
        raise ValueError('Use between 4 and 12 scenes')
    lead = character if character != 'auto' else plan.get('character', 'male')
    if lead not in {'male', 'female'}:
        raise ValueError('Invalid lead character')
    scenes = []
    for raw in plan['scenes']:
        scene = {k: raw.get(k) for k in ('location', 'action', 'emotion', 'narration')}
        for key, allowed in [('location', LOCATIONS), ('action', ACTIONS), ('emotion', EMOTIONS)]:
            if scene[key] not in allowed:
                raise ValueError(f'Unsupported {key}: {scene[key]}')
        if not isinstance(scene['narration'], str) or not 10 <= len(scene['narration']) <= 550:
            raise ValueError('Narration must contain 10–550 characters per scene')
        scene['shadow'] = bool(raw.get('shadow', False))
        scene['narration'] = ' '.join(scene['narration'].split())
        scenes.append(scene)
    return {'title': title, 'brief': brief, 'character': lead, 'scenes': scenes}


def template_plan(title, brief, character='auto'):
    """Transparent offline fallback: preserve the user's sentences as narration."""
    parts = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+|;', brief) if s.strip()]
    if len(parts) < 4:
        parts = [f'This is where {title.lower()} begins.', *parts,
                 'The first step was small. It still counted.',
                 'There would be difficult days. There would also be another morning.']
    while len(parts) < 4:
        parts.append('One quiet choice became the beginning of something different.')
    parts = parts[:12]
    if character == 'auto':
        character = 'female' if re.search(r'\b(she|her|woman|girl|female)\b', brief, re.I) else 'male'
    scenes = []
    for i, sentence in enumerate(parts):
        low = sentence.lower()
        location, action = [('bedroom', 'sit'), ('desk', 'phone'), ('street', 'walk'),
                            ('park', 'sit'), ('gym', 'exercise'), ('rooftop', 'reach')][i % 6]
        for words, loc, act in [('sleep|bed|wake', 'bedroom', 'sleep'), ('phone|scroll', 'desk', 'phone'),
                                ('write|study|work', 'desk', 'write'), ('gym|exercise|train', 'gym', 'exercise'),
                                ('walk|outside|street', 'street', 'walk'), ('park|tree', 'park', 'sit')]:
            if re.search(words, low):
                location, action = loc, act
                break
        emotion = 'sad' if i == 0 else 'determined' if i < len(parts)-1 else 'happy'
        scenes.append(dict(location=location, action=action, emotion=emotion,
                           shadow=i < len(parts)//2, narration=sentence[:550]))
    return validate({'character': character, 'scenes': scenes}, title, brief, character)


def brief_outline(brief, character='auto'):
    """Anchor the drawable sequence to the user's ordered story events."""
    parts=[p.strip() for p in re.split(r'(?<=[.!?])\s+|\n+|;',brief) if p.strip()]
    meta=r'^(female lead|male lead|one visible|use the (female|male)|mood:|tone:|reflective[, .]|quiet[, .]|hopeful[, .])'
    events=[p for p in parts if not re.search(meta,p,re.I)] or [brief]
    if len(events)>8:
        events=[events[round(i*(len(events)-1)/7)] for i in range(8)]
    lead=character if character!='auto' else ('female' if re.search(r'\b(she|her|woman|girl|female)\b',brief,re.I) else 'male')
    scenes=[]
    for i in range(8):
        event=events[min(len(events)-1,i*len(events)//8)]
        low=event.lower()
        location='bedroom' if i<2 else 'street' if i<5 else 'park' if i<7 else 'rooftop'
        for pattern,value in [(r'bedroom|bed|wake','bedroom'),(r'desk|office','desk'),
                              (r'street|outside|neighborhood','street'),(r'park|nature','park'),
                              (r'gym','gym'),(r'rooftop|roof','rooftop')]:
            if re.search(pattern,low):location=value
        action='idle'
        for pattern,value in [(r'walk|outside|jog','walk'),(r'scroll|phone|feed','phone'),
                              (r'write|writing|journal','write'),(r'sleep|asleep','sleep'),
                              (r'exercise|workout|lift|training','exercise'),(r'\bsit|sits|sitting','sit')]:
            if re.search(pattern,low):action=value
        if action=='write' and not re.search(r'bedroom|park|roof',low):location='desk'
        if location=='rooftop' and action=='idle':action='reach'
        emotion='sad' if i<2 else 'determined' if i<7 else 'happy'
        if re.search(r'fear|afraid|almost|anxious|worr',low):emotion='worried'
        scenes.append(dict(location=location,action=action,emotion=emotion,shadow=i<3,narration=event[:550]))
    return lead,scenes


def validate_narration(text):
    if not isinstance(text,str) or not 10<=len(text)<=550:
        raise ValueError('Each narration must contain 10–550 characters')
    if re.search(r'scene[_ ]?\d|fictional character|written by the narrator|^(?:end|finish|close) on|camera|visible action|this (?:scene|shot)',text,re.I):
        raise ValueError('Write spoken story prose about the protagonist, not filmmaking instructions or scene labels')
    return text


def validate_narrations(generated):
    if not isinstance(generated,dict) or set(generated)!={f'scene_{i+1}' for i in range(8)}:
        raise ValueError('Narration must contain exactly scene_1 through scene_8')
    for text in generated.values():
        validate_narration(text)
    return generated


def ai_plan(title, brief, character='auto', model_id='Qwen/Qwen2.5-1.5B-Instruct-GGUF', diagnostics_path=None):
    import os
    import shutil
    import urllib.request
    from llama_cpp import Llama
    filename='qwen2.5-1.5b-instruct-q4_k_m.gguf'
    cache=Path('.cache/models');cache.mkdir(parents=True,exist_ok=True)
    path=cache/filename
    if not path.exists():
        print('Downloading the official CPU story model (about 1.1 GB).',flush=True)
        temporary=path.with_suffix('.part')
        try:
            with urllib.request.urlopen(f'https://huggingface.co/{model_id}/resolve/main/{filename}',timeout=180) as response,temporary.open('wb') as out:
                shutil.copyfileobj(response,out)
            if temporary.stat().st_size<100_000_000:
                raise ValueError('Model download was unexpectedly small')
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    threads=min(4,os.cpu_count() or 2)
    try:
        quota,period=Path('/sys/fs/cgroup/cpu.max').read_text().split()
        if quota!='max':threads=min(threads,max(1,int(quota)//int(period)))
    except (OSError,ValueError):
        pass
    print(f'Loading the GGUF story model on {threads} CPU threads.',flush=True)
    model=Llama(model_path=str(path),n_ctx=4096,n_batch=256,n_threads=threads,
                n_threads_batch=threads,chat_format='chatml',verbose=False,seed=42)
    lead,scenes=brief_outline(brief,character)
    beats=[{'scene':f'scene_{i+1}','event':scene['narration'],'setting':scene['location'],
            'action':scene['action']} for i,scene in enumerate(scenes)]

    spoken={}
    pronoun='she' if lead=='female' else 'he'
    raw_responses=[]
    for i,beat in enumerate(beats):
        event=re.sub(r'^(?:end|finish|close)(?: the (?:film|story))? (?:on|at) ',
                     'The protagonist is on ',beat['event'],flags=re.I)
        repeated=i>0 and beat['event']==beats[i-1]['event']
        emphasis='the small physical choice' if repeated or i==7 else 'the feeling and hesitation'
        prompt=f'''Write 20-30 words of spoken narration for ONE shot of an animated film.
Use third person ({pronoun}), no character names, no other people. Quiet, reflective, grounded.
The narration must match this event and the visible action. Focus on {emphasis}.
Do not invent a different activity, another setting, or an event that happens later.
Tell the story naturally. Do not describe camera directions, explain a scene, or say "end on".
Return only JSON: {{"narration":"two short sentences of spoken story prose"}}.
Title: {json.dumps(title)}
Event in this shot: {json.dumps(event)}
Visible setting: {beat['setting']}. Visible action: {beat['action']}.
'''
        messages=[{'role':'system','content':'You write spoken third-person narration. Follow the single event exactly.'},
                  {'role':'user','content':prompt}]
        for attempt in range(2):
            print(f'Writing narration: scene {i+1}/8, attempt {attempt+1}.',flush=True)
            schema={'type':'object','properties':{'narration':{'type':'string','minLength':30,'maxLength':300}},
                    'required':['narration'],'additionalProperties':False}
            response=model.create_chat_completion(messages=messages,max_tokens=180,temperature=.3,
                top_p=.9,repeat_penalty=1.1,response_format={'type':'json_object','schema':schema})
            raw=response['choices'][0]['message']['content'];raw_responses.append(raw)
            if diagnostics_path:Path(diagnostics_path).write_text('\n'.join(raw_responses))
            try:
                generated=json.loads(raw[raw.find('{'):raw.rfind('}')+1])
                text=generated['narration']
                validate_narration(text)
                if re.search(r'^(?:end|finish|close) on|camera|visible action|this (?:scene|shot)',text,re.I):
                    raise ValueError('Use spoken story prose, not filmmaking instructions')
                spoken[f'scene_{i+1}']=text
                scenes[i]['narration']=text
                break
            except (ValueError,TypeError,KeyError) as exc:
                if attempt:raise
                messages += [{'role':'assistant','content':raw},
                             {'role':'user','content':f'Correct this error: {exc}. Write only the spoken narration matching this one event.'}]
    validate_narrations(spoken)
    result=validate({'character':lead,'scenes':scenes},title,brief,lead)
    result['brief_beats']=beats
    result['planner_adaptations']=[]
    return result
