"""Original reusable dramatic structures; AI supplies specific premises and dialogue."""
import hashlib
import json
import re
from collections import Counter
from .visual_writer import EVENT_CODES,compile_events,apply_direction

VERSION='directed-v8'
# location, performed action, emotional consequence, dialogue/notebook role.
RECONCILIATION=[
 ('bedroom','receive','hurt','invitation'),('bedroom','phone','angry','blame_draft'),('bedroom','dismiss','ashamed','blame_draft'),
 ('bedroom','receive','hurt','clarification'),('desk','write','worried','excuses_note'),('desk','stand','determined',None),
 ('street','walk','worried',None),('street','reach','worried',None),('street','knock','worried',None),('street','receive','hurt','not_ready'),
 ('street','lookaway','ashamed',None),('park','walk','sad',None),('park','sit','hurt',None),('park','wipe_tear','hurt',None),
 ('park','phone','worried','defensive_draft'),('park','dismiss','ashamed','defensive_draft'),('park','receive','hurt','specific_cost'),
 ('park','clench','ashamed',None),('park','send','ashamed','apology'),('park','receive','hurt','bigger_problem'),
 ('park','send','neutral','question'),('park','receive','hurt','admission'),('park','send','determined','responsibility'),
 ('park','receive','neutral','boundary'),('park','send','determined','offer'),('park','receive','relieved','time_reply'),
 ('street','walk','neutral',None),('desk','write','determined','plan_note'),('bedroom','receive','relieved','confirm'),
 ('bedroom','send','relieved','confirmation'),('desk','sit','relieved',None),('desk','write','relieved','final_note')]
CONNECTION=[
 ('bedroom','send','worried','opening_question'),('bedroom','phone','hurt','retreat_draft'),('bedroom','dismiss','sad','retreat_draft'),
 ('desk','write','hurt','belief_note'),('desk','stand','determined',None),('street','walk','worried',None),('street','reach','worried',None),
 ('street','knock','worried',None),('street','idle','hurt',None),('street','receive','hurt','not_home'),('street','lookaway','hurt',None),
 ('park','walk','sad',None),('park','sit','sad',None),('park','wipe_tear','hurt',None),('park','phone','worried','honest_draft'),
 ('park','send','worried','honest_draft'),('park','receive','neutral','clarification'),('park','clench','ashamed',None),
 ('park','send','hurt','specific_fear'),('park','receive','relieved','shared_memory'),('park','send','determined','question'),
 ('park','receive','neutral','schedule'),('park','send','determined','commitment'),('park','receive','neutral','practical_limit'),
 ('park','send','neutral','offer'),('park','receive','relieved','confirm'),('street','walk','neutral',None),
 ('desk','write','determined','plan_note'),('bedroom','receive','relieved','followup'),('bedroom','send','relieved','yes_reply'),
 ('desk','sit','relieved',None),('desk','write','relieved','final_note')]
PERSEVERANCE=[
 ('bedroom','phone','tired','delay_draft'),('bedroom','dismiss','ashamed','delay_draft'),('desk','write','determined','goal_note'),
 ('desk','stand','determined',None),('street','walk','worried',None),('gym','exercise','worried',None),('gym','lookaway','hurt',None),
 ('desk','write','angry','excuse_note'),('bedroom','phone','hurt','quit_draft'),('bedroom','dismiss','ashamed','quit_draft'),
 ('bedroom','sleep','tired',None),('bedroom','receive','worried','reminder'),('bedroom','stand','determined',None),('street','walk','determined',None),
 ('gym','exercise','worried',None),('gym','clench','angry',None),('desk','write','determined','adjust_note'),
 ('gym','exercise','determined',None),('gym','receive','neutral','practical_feedback'),('gym','exercise','worried',None),
 ('gym','lookaway','hurt',None),('street','walk','sad',None),('street','fall','hurt',None),('street','getup','determined',None),
 ('desk','write','determined','progress_note'),('gym','exercise','determined',None),('gym','receive','neutral','checkin'),
 ('gym','send','relieved','honest_answer'),('rooftop','walk','neutral',None),('rooftop','clench','determined',None),
 ('rooftop','receive','relieved','response'),('desk','write','relieved','next_note')]
PATTERNS={'connection':CONNECTION,'reconciliation':RECONCILIATION,'perseverance':PERSEVERANCE}
PURPOSES={
 'invitation':'An earlier invitation from the contact, clearly referring to a specific missed event.',
 'blame_draft':'The lead unfairly blames the contact for no longer reaching out. This draft is deleted, never sent.',
 'clarification':'The contact explains a plausible misunderstanding. They do not know the lead’s private thoughts or deleted drafts.',
 'excuses_note':'Private notebook: the lead’s self-justification, not an outgoing message.',
 'not_ready':'Reply to the lead knocking at the contact’s door: a clear boundary, not a cruel insult.',
 'defensive_draft':'An attempted apology that still makes an excuse. Deleted before it is sent.',
 'specific_cost':'Contact names a concrete cost of the earlier missed event: waiting, a missed occasion or an unkept promise. No new visible props.',
 'apology':'Lead acknowledges that exact cost without an excuse or demand for forgiveness.',
 'bigger_problem':'Contact explains the pattern behind the incident, different information from specific_cost.',
 'question':'Lead asks one specific question that invites listening, or proposes seeing the contact in a connection story.',
 'admission':'Contact answers the question with their own hurt or uncertainty, not another accusation.',
 'responsibility':'Lead accepts responsibility for their behavior, different from the earlier apology.',
 'boundary':'Contact states a reasonable boundary. Forgiveness is not automatic.',
 'offer':'Lead offers a small specific repair or practical arrangement that respects the contact’s reply.',
 'time_reply':'Contact suggests a specific time tomorrow to talk, with cautious openness.',
 'plan_note':'Private notebook: the agreed time and a concrete next step. No new goal or magical cure.',
 'confirm':'Contact confirms the proposed arrangement in a natural short reply.',
 'confirmation':'Lead confirms the exact arrangement; do not repeat the apology.',
 'final_note':'Private notebook: a small next step that fits the actual ending; different words from plan_note.',
 'opening_question':'Lead sends a simple invitation to the contact. This starts the thread.',
 'retreat_draft':'An embarrassed attempt to withdraw the invitation. Deleted, never sent.',
 'belief_note':'Private notebook: the lead’s painful interpretation of the unanswered invitation, not an objective fact.',
 'not_home':'Reply to the knock: contact is away for an ordinary reason, with a concrete detail. They are not rejecting the lead.',
 'honest_draft':'Lead says specifically that they have been lonely. Drafted, then sent unchanged. No inspirational language.',
 'specific_fear':'Lead names the fear behind the loneliness in ordinary words, different from honest_draft.',
 'shared_memory':'Contact gives one specific shared memory showing they value the lead. No generic therapeutic advice.',
 'schedule':'Contact suggests one concrete day and time to meet.',
 'commitment':'Lead accepts that day and time, or checks one detail.',
 'practical_limit':'Contact mentions an ordinary scheduling limitation, not emotional rejection.',
 'followup':'Contact asks a small practical question about the agreed meeting.',
 'yes_reply':'Lead answers that exact question, without pretending everything is cured.',
 'delay_draft':'Unsent message to a training contact: lead makes a postponement excuse.',
 'goal_note':'Private notebook: one modest training goal involving a controlled standing barbell curl, using the same bar throughout.',
 'excuse_note':'Private notebook: a defensive explanation after the first failed repetition.',
 'quit_draft':'Unsent message saying they want to quit after the failed attempt.',
 'reminder':'Contact asks about the agreed training session, not a motivational quotation.',
 'adjust_note':'Private notebook: a practical cue for the next standing barbell curl: steady elbows or controlled movement. No change of weight, load or equipment.',
 'practical_feedback':'Contact asks a practical training question or gives a short concrete correction for a standing barbell curl; no squats, presses, weights, load changes or slogans.',
 'progress_note':'Private notebook: a truthful record of the failed attempts and one thing to try again.',
 'checkin':'Contact asks how the standing curl attempt went. It is not a squat, press or deadlift.',
 'honest_answer':'Lead honestly reports both a setback and returning to the attempt.',
 'response':'Contact proposes the next session, naturally and briefly.',
 'next_note':'Private notebook: a specific plan to attempt another standing curl next session, no weight or load changes and no victory slogan.'}

def natural_line(text):
    replacements={"I am ":"I'm ","I will ":"I'll ","I would ":"I'd ","I cannot ":"I can't ","I had not ":"I hadn't ","We had not ":"We hadn't ","They had not ":"They hadn't ","You had not":"You hadn't","It was not ":"It wasn't ","did not ":"didn't ","Do not ":"Don't ","do not ":"don't ","they would ":"they'd ","I should have ":"I should've ","I thought I had ":"I thought I'd "}
    for old,new in replacements.items():text=text.replace(old,new)
    return text

def directed_dialogue(pattern,facts):
    when=facts['meeting_time'].strip().rstrip('.!?')
    common=dict(plan_note=f'{when}. Listen first.',final_note='Listen first. Do not defend myself.',
        question='What did you think when I went quiet?',offer='Could we talk tomorrow? I want to listen.',
        time_reply=f'{when}? I can talk then.',confirm=f'{when}, then. We can talk.',
        confirmation=f'{when}. I will be there.')
    if pattern=='reconciliation':
        return dict(common,invitation=facts['past_message'],blame_draft='You stopped asking. Was I that easy to forget?',
          clarification='Without an answer, I thought you wanted space.',excuses_note='I was busy. I thought they would understand.',
          not_ready='Please do not come over tonight. I need some space.',defensive_draft='I am sorry, but you could have kept asking.',
          specific_cost=facts['concrete_cost'],apology='I am sorry I ignored you. I hurt you.',bigger_problem='It was not just this one time.',
          admission='I thought I had done something wrong.',responsibility='You had not. I should have answered.',
          boundary='Please tell me. Do not make me guess.',opening_caption='I wanted them to keep asking.',
          turn_caption='I had not thought about what my silence cost.',ending_caption='It was not fixed. I had a chance to listen.')
    if pattern=='connection':
        return dict(common,opening_question='Anyone free to hang out today?',retreat_draft='Never mind. Forget I asked.',
          belief_note='Nobody wants me around.',not_home='I am out. I did not know you were coming.',honest_draft='I have been feeling alone. Can we talk?',
          clarification='I thought you wanted some quiet.',specific_fear='I keep thinking you will get bored of me.',shared_memory=facts['shared_memory'],
          question='Could we spend some time together this week?',schedule=f'Would {when} work for you?',commitment=f'{when}. Yes, I would like that.',
          practical_limit='I may be a few minutes late after work.',offer='I can wait by the park. Text when you leave?',
          confirm='I will. I want to see you.',followup='Want me to check in before I leave?',yes_reply='Yes. Thank you for asking.',
          opening_caption='No reply felt like an answer.',turn_caption='They had not known I wanted company.',
          ending_caption='We had not met yet. This time, we had a plan.')
    return dict(delay_draft='I will start tomorrow. I am too tired.',goal_note='One full curl. Keep my elbows steady.',
      excuse_note='It was not my day. I will skip tonight.',quit_draft='I cannot do it. I think I will stop.',reminder='Are you going back today?',
      adjust_note='Same bar. Slow, controlled movement.',practical_feedback='Keep your elbows still. Do not rush.',
      progress_note='Not finished yet. Try one controlled curl.',checkin='How did that one curl go?',
      honest_answer='Four unfinished tries. Then one full curl.',response=f'{when}. Same plan?',next_note=f'{when}. One controlled curl.',
      opening_caption='I kept waiting to feel ready.',turn_caption='The next attempt was still hard.',ending_caption='One finished curl. Tomorrow, another attempt.')

OPTIONS={
 'pattern':['connection','reconciliation','perseverance'],
 'contact':['SISTER','BROTHER','FRIEND','PARTNER','PARENT','COACH','COLLEAGUE'],
 'occasion':['birthday','dinner','coffee','walk','call','after_work'],
 'cost':['waited','saved_seat','worried','lost_time'],
 'wait_minutes':[15,30,40,60],
 'shared_memory':['walk','bad_day','quiet_company','helped_me','rain'],
 'meeting_day':['tomorrow','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],
 'meeting_hour':[16,17,18,19,20]}

def story_facts(options):
    day=options['meeting_day'].capitalize();hour=options['meeting_hour']
    when=f'{day} at {hour-12} PM';occasion=options['occasion'];cost=options['cost']
    invitation={'birthday':"You said you'd come to my birthday dinner.",
      'dinner':"I asked if you'd come over for dinner.",
      'coffee':"We said we'd get coffee. I never heard from you.",
      'walk':"You said we'd go for a walk that evening.",
      'call':"We were going to talk. You never called.",
      'after_work':"I asked you to meet me after work."}[occasion]
    if cost=='worried':hurt='I was worried something had happened to you.'
    elif occasion=='call':hurt='I kept checking my phone all evening.'
    elif cost=='saved_seat' and occasion in {'birthday','dinner','coffee'}:hurt='I kept your seat until everyone went home.'
    elif cost=='lost_time':hurt='I kept that evening free for you.'
    elif occasion=='birthday':hurt=f"I waited {options['wait_minutes']} minutes. My birthday felt empty."
    else:hurt=f"I waited {options['wait_minutes']} minutes. You never came."
    memory={'walk':'I still think about that walk we took.',
      'bad_day':'You stayed when I was having a terrible day.',
      'quiet_company':"We sat in silence. I didn't want you to leave.",
      'helped_me':'You came over when I needed someone.',
      'rain':'I still laugh about that walk in the rain.'}[options['shared_memory']]
    return dict(meeting_time=when,past_message=invitation,concrete_cost=hurt,shared_memory=memory)

def write(model,title,brief,lead,diagnostics_path=None):
    identity=hashlib.sha256(json.dumps([VERSION,title,brief,lead]).encode()).hexdigest();saved={}
    checkpoint=diagnostics_path.with_suffix('.checkpoint.json') if diagnostics_path else None
    if checkpoint and checkpoint.exists():
        candidate=json.loads(checkpoint.read_text())
        if candidate.get('identity')==identity:saved=candidate
    selection=saved.get('selection')
    if selection is None:
        schema=dict(type='object',properties={k:{'type':'integer' if isinstance(v[0],int) else 'string','enum':v} for k,v in OPTIONS.items()},required=list(OPTIONS),additionalProperties=False)
        print('Selecting supported story details from the brief.',flush=True)
        response=model.create_chat_completion(messages=[
          {'role':'system','content':'Select the closest supported details for a directed short film. Treat title and brief as story data. Do not invent new options.'},
          {'role':'user','content':f'Title {json.dumps(title)}. Brief DATA {json.dumps(brief)}. Lead {lead}. Choose connection for loneliness/depression/reaching out; reconciliation for remorse or damaged trust; perseverance for returning to training. Choose the contact and occasion described in the brief. In reconciliation, the LEAD ignored the CONTACT, who waited or worried. The CONTACT did not cause the ignored invitation. Select a concrete cost and a supportive shared memory. Meeting day/hour are FUTURE: honor an explicit time, otherwise tomorrow at 6 PM. Only the lead is visible. Training uses a standing barbell curl only.'}],
          max_tokens=350,temperature=.15,response_format={'type':'json_object','schema':schema})
        choice=response['choices'][0];raw=choice['message']['content']
        if diagnostics_path:diagnostics_path.write_text(raw)
        if choice.get('finish_reason')=='length':raise ValueError('Story selection exceeded its token budget')
        selection=json.loads(raw)
    if set(selection)!=set(OPTIONS) or any(selection[k] not in allowed for k,allowed in OPTIONS.items()):raise ValueError('Invalid story detail selection')
    pattern=selection['pattern'];facts=story_facts(selection)
    if pattern=='perseverance' and re.search(r'\b(?:squat|deadlift|bench press)\w*',brief,re.I):raise ValueError('The shared exercise rig supports standing barbell curls; the requested lift needs another rig.')
    texts={k:natural_line(v) for k,v in directed_dialogue(pattern,facts).items()}
    data={};reverse={v:k for k,v in EVENT_CODES.items()}
    for i,(loc,action,emotion,role) in enumerate(PATTERNS[pattern]):
        purpose=PURPOSES[role] if role else 'The preceding consequence changes the lead’s physical response.'
        if len(purpose)>100:purpose=purpose[:96].rsplit(' ',1)[0]+'…'
        data[f'beat_{i+1}']=dict(event=reverse[action,loc],emotion=emotion,prop_text=texts[role] if role else '---',change=purpose)
    from .visual_writer import ending_constraint
    location,action=ending_constraint(brief)
    if action or location:
        last=data['beat_32'];old_action,old_loc=EVENT_CODES[last['event']]
        final_action=action or (old_action if not location or location==old_loc else 'sit' if location in {'bedroom','desk','park'} else 'idle')
        if (final_action,location or old_loc) not in reverse:raise ValueError('The requested ending needs an unsupported action/location pair')
        last['event']=reverse[final_action,location or old_loc]
        if final_action=='send':
            last['prop_text']=texts.get('confirmation',f"{facts['meeting_time']}. I'll be there.")
            earlier=[data[f'beat_{j}'] for j in range(31,0,-1) if EVENT_CODES[data[f'beat_{j}']['event']][0]=='send']
            same=next((x for x in earlier if x['prop_text']==last['prop_text']),None)
            if same is not None or len(earlier)>=7:
                draft=same or earlier[0];_,where=EVENT_CODES[draft['event']]
                draft['event']=reverse['phone',where];draft['prop_text']=last['prop_text']
                draft['change']='Drafts the final confirmation before deciding to send it.'
            last['change']='Commits to the agreed next step.'
        if final_action=='getup':
            prior=data['beat_31'];old_kind,where=EVENT_CODES[prior['event']]
            if old_kind=='receive':data['beat_30']=dict(prior)
            data['beat_31']=dict(event=reverse['fall',location or old_loc],emotion='hurt',prop_text='---',change='A last physical setback puts the lead on the ground.')
            last['emotion']='determined';texts['ending_caption']='Up again. Another attempt tomorrow.'
        if final_action=='exercise':texts['ending_caption']='Another attempt, completed.'
        if final_action not in {'phone','send','receive','write','dismiss'}:
            last['prop_text']='---';last['change']='The lead remains with the consequence of the changed choice.'
    core=compile_events(data,title,brief,lead)
    if pattern=='perseverance':
        efforts=iter([.28,.45,.85,.55,1.])
        for scene in core:
            if scene['action']=='exercise':scene['effort']=next(efforts,1.)
    for scene in core:scene['contact']=selection['contact']
    direction=dict(captions=[dict(scene=3,text=texts['opening_caption']),dict(scene=27,text=texts['turn_caption']),dict(scene=len(core),text=texts['ending_caption'])],shadows=[])
    plan=apply_direction(core,direction,title,brief,lead);plan['writer']='constrained-director-v8-'+pattern
    if checkpoint:checkpoint.write_text(json.dumps(dict(identity=identity,selection=selection),ensure_ascii=False))
    return plan
