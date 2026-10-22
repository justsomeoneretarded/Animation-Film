"""Continuity-first screenplay planning, with a fully authored depression story."""
import json
import re
from pathlib import Path

LOCATIONS={'bedroom','street','park','gym','desk','rooftop'}
from .screenplay import ACTIONS
EMOTIONS={'sad','worried','tired','neutral','determined','happy'}
BEATS=12
MODEL_ID='unsloth/Qwen3-4B-Instruct-2507-GGUF'
MODEL_FILE='Qwen3-4B-Instruct-2507-Q4_K_M.gguf'


def validate(plan,title,brief,character='auto'):
    if isinstance(plan,dict) and plan.get('mode')=='text-led':
        from .screenplay import validate_screenplay
        return validate_screenplay(plan,title,brief,select_lead(brief,character) if character!='auto' else plan.get('character','male'))
    if not isinstance(plan,dict) or not isinstance(plan.get('scenes'),list):raise ValueError('Story must contain a scenes array')
    if not 4<=len(plan['scenes'])<=24:raise ValueError('Use between 4 and 24 scenes')
    lead=character if character!='auto' else plan.get('character','male')
    if lead not in {'male','female'}:raise ValueError('Invalid lead character')
    scenes=[]
    for raw in plan['scenes']:
        s={k:raw.get(k) for k in ('location','action','emotion','narration')}
        for key,allowed in [('location',LOCATIONS),('action',ACTIONS),('emotion',EMOTIONS)]:
            if s[key] not in allowed:raise ValueError(f'Unsupported {key}: {s[key]}')
        validate_narration(s['narration'])
        s['narration']=' '.join(s['narration'].split());s['shadow']=False
        for key,allowed,default in [('time',{'night','dawn','day'},'night'),('shot',{'wide','close'},'wide')]:
            s[key]=raw.get(key,default)
            if s[key] not in allowed:raise ValueError(f'Invalid {key}')
        s['event']=str(raw.get('event',''))[:1000]
        s['prop_text']=str(raw.get('prop_text',''))[:150]
        scenes.append(s)
    result={'title':title,'brief':brief,'character':lead,'scenes':scenes}
    if plan.get('target_seconds') is not None:
        target=float(plan['target_seconds'])
        if not 180<=target<=240:raise ValueError('Production films must be 180–240 seconds')
        result['target_seconds']=target
    if 'writer' in plan:result['writer']=plan['writer']
    return result


def select_lead(brief,character='auto'):
    if character!='auto':return character
    explicit=re.search(r'\b(female|male)\s+(?:lead|protagonist)\b',brief,re.I)
    if explicit:return explicit.group(1).lower()
    return 'female' if re.search(r'\b(she|her|woman|girl|female)\b',brief,re.I) else 'male'


def validate_narration(text):
    if not isinstance(text,str) or not 10<=len(text)<=1000:raise ValueError('Narration must contain 10–1000 characters')
    if re.search(r'scene[_ ]?\d|fictional character|written by the narrator|^(?:end|finish|close) on|camera|visible action|this (?:scene|shot)',text,re.I):
        raise ValueError('Narration must be spoken story prose, without filmmaking metadata')
    return text


def validate_narrations(generated,count=BEATS):
    if not isinstance(generated,dict) or set(generated)!={f'scene_{i+1}' for i in range(count)}:raise ValueError(f'Expected exactly {count} narration beats')
    for text in generated.values():validate_narration(text)
    return generated


def brief_outline(brief,character='auto'):
    parts=[p.strip() for p in re.split(r'(?<=[.!?])\s+|\n+|;',brief) if p.strip()]
    meta=r'^(female lead|male lead|one visible|use the (female|male)|mood:|tone:|quiet[, .]|reflective[, .]|hopeful[, .]|present depression|the ending is|no other|do not|avoid )'
    events=[p for p in parts if not re.search(meta,p,re.I)] or [brief]
    scenes=[]
    for i in range(BEATS):
        event=events[min(len(events)-1,i*len(events)//BEATS)];low=event.lower()
        location='bedroom' if i<3 else 'desk' if i<5 else 'street' if i<8 else 'park' if i<11 else 'rooftop'
        for pattern,value in [(r'bedroom|\bbed\b|wake','bedroom'),(r'desk|office','desk'),(r'street|outside|neighborhood','street'),(r'park|nature|bench','park'),(r'gym','gym'),(r'rooftop|roof','rooftop')]:
            if re.search(pattern,low):location=value
        action='idle'
        for pattern,value in [(r'walk|outside|jog','walk'),(r'scroll|phone|feed','phone'),(r'write|writing|journal','write'),(r'sleep|asleep','sleep'),(r'exercise|workout|lift|training','exercise'),(r'\bsit|sits|sitting|bench','sit')]:
            if re.search(pattern,low):action=value
        if action=='write':location='desk'
        emotion='tired' if i<3 else 'worried' if i<7 else 'neutral'
        if re.search(r'sad|cry|alone|heavy|depress',low):emotion='sad'
        if re.search(r'fear|afraid|almost|anxious|worr',low):emotion='worried'
        scenes.append(dict(location=location,action=action,emotion=emotion,shadow=False,narration=event[:900],event=event,
                           time='night' if i<5 else 'dawn',shot='close' if i in {1,4,7,10} else 'wide'))
    return select_lead(brief,character),scenes


def template_plan(title,brief,character='auto'):
    """Explicit debug path; user sentences remain verbatim, never claimed as AI."""
    parts=[s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+|;',brief) if s.strip()]
    while len(parts)<4:parts.append('One quiet choice became the beginning of something different.')
    lead,scenes=brief_outline(brief,character);scenes=scenes[:len(parts[:12])]
    for s,p in zip(scenes,parts):s['narration']=p[:1000]
    return validate({'character':lead,'scenes':scenes},title,brief,lead)


def depression_plan(title,brief,character='auto'):
    """An authored screenplay, not keyword-spliced motivational fragments.

    Selected transparently only for a depression title and the supported single-
    protagonist recovery arc. General briefs still use the local story model.
    """
    from .screenplay import depression_screenplay
    return depression_screenplay(title,brief,select_lead(brief,character))


def narration_issues(text,scene):
    """Catch concrete visual contradictions before an unrenderable story ships."""
    issues=[];action=scene['action']
    if action not in {'sit','phone','write'} and re.search(r'\b(?:he|she) (?:sits|sat|is sitting)\b',text,re.I):
        issues.append('The lead must not sit in this shot; the rig is '+action)
    if action!='write' and re.search(r'\b(?:he|she) (?:writes|wrote|is writing)\b|then (?:he |she )?writes',text,re.I):
        issues.append('No writing in this shot; the rig is '+action)
    if re.search(r'sit(?:s|ting)? without touching|hand on the sidewalk',text,re.I):
        issues.append('Use physically plausible contact: feet on pavement, hands on a real object')
    return issues


def ai_plan(title,brief,character='auto',model_id=MODEL_ID,diagnostics_path=None):
    # The approved depression arc gets the authored script supplied with the
    # project; explicit alternate plots use the general writer.
    if re.search(r'authored depression story|sample: depressed',brief,re.I):
        result=depression_plan(title,brief,character)
        if diagnostics_path:Path(diagnostics_path).write_text('Selected authored-visual-depression-v4. Other briefs use the connected AI writer.\n')
        print('Using the authored 3m30s depression screenplay. Brief selects the lead. Other briefs use the connected AI writer.',flush=True)
        return result
    import os,shutil,urllib.request
    from llama_cpp import Llama
    cache=Path('.cache/models');cache.mkdir(parents=True,exist_ok=True);path=cache/MODEL_FILE
    if not path.exists():
        print('Downloading the Apache-licensed 4B CPU writing model (about 2.5 GB).',flush=True)
        temp=path.with_suffix('.part')
        try:
            with urllib.request.urlopen(f'https://huggingface.co/{model_id}/resolve/main/{MODEL_FILE}',timeout=180) as response,temp.open('wb') as out:shutil.copyfileobj(response,out)
            if temp.stat().st_size<500_000_000:raise ValueError('Incomplete model download')
            temp.replace(path)
        finally:temp.unlink(missing_ok=True)
    threads=min(4,os.cpu_count() or 2)
    try:
        quota,period=Path('/sys/fs/cgroup/cpu.max').read_text().split()
        if quota!='max':threads=min(threads,max(1,int(quota)//int(period)))
    except (OSError,ValueError):pass
    model=Llama(model_path=str(path),n_ctx=12288,n_batch=256,n_threads=threads,n_threads_batch=threads,chat_format='chatml',verbose=False,seed=42)
    from .screenplay import write_screenplay
    return write_screenplay(model,title,brief,select_lead(brief,character),Path(diagnostics_path) if diagnostics_path else None)
