"""Original reusable dramatic structures; AI supplies specific premises and dialogue."""
import hashlib
import json
import re
from collections import Counter
from .visual_writer import EVENT_CODES,compile_events,apply_direction

VERSION='directed-v7'
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

def directed_dialogue(pattern,facts):
    when=facts['meeting_time'].strip().rstrip('.!?')
    common=dict(plan_note=f'{when}. Listen first.',final_note='Ask how they felt. Listen before explaining.',
        question='What did you think when I went quiet?',offer='Could we talk tomorrow? I want to listen.',
        time_reply=f'Could we do {when}?',confirm=f'{when}, then. We can talk.',
        confirmation=f'{when}. I will be there.')
    if pattern=='reconciliation':
        return dict(common,invitation=facts['past_message'],blame_draft='You stopped asking. Was I that easy to forget?',
          clarification='Without an answer, I thought you wanted space.',excuses_note='I was busy. I thought they would understand.',
          not_ready='Please do not come over tonight. I need some space.',defensive_draft='I am sorry, but you could have kept asking.',
          specific_cost=facts['concrete_cost'],apology='I am sorry I ignored you. That hurt you.',bigger_problem='It was not only the missed plan.',
          admission='I thought I had done something wrong.',responsibility='You had not. I should have answered.',
          boundary='I need you to tell me, not make me guess.',opening_caption='I wanted them to keep asking.',
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
      excuse_note='It was not my day. I will skip tonight.',quit_draft='I cannot do it. I think I will stop.',reminder=facts['context_line'],
      adjust_note='Same bar. Slow, controlled movement.',practical_feedback='Keep your elbows still. Do not rush.',
      progress_note='Not finished yet. Try one controlled curl.',checkin='How did that one curl go?',
      honest_answer='Four unfinished tries. Then one full curl.',response=f'{when}. Same plan?',next_note=f'{when}. One controlled curl.',
      opening_caption='I kept waiting to feel ready.',turn_caption='The next attempt was still hard.',ending_caption='One finished curl. Tomorrow, another attempt.')

def write(model,title,brief,lead,diagnostics_path=None):
    identity=hashlib.sha256(json.dumps([VERSION,title,brief,lead]).encode()).hexdigest();saved={};raws=[]
    checkpoint=diagnostics_path.with_suffix('.checkpoint.json') if diagnostics_path else None
    if checkpoint and checkpoint.exists():
        candidate=json.loads(checkpoint.read_text())
        if candidate.get('identity')==identity:saved=candidate;raws=candidate.get('raws',[])
    def save():
        if checkpoint:checkpoint.write_text(json.dumps({**saved,'identity':identity,'raws':raws},ensure_ascii=False))
    def ask(messages,schema,tokens):
        result=model.create_chat_completion(messages=messages,max_tokens=tokens,temperature=.65,response_format={'type':'json_object','schema':schema})
        choice=result['choices'][0];raw=choice['message']['content'];raws.append(raw)
        if diagnostics_path:diagnostics_path.write_text('\n\n'.join(raws))
        if choice.get('finish_reason')=='length':raise ValueError('Director output exceeded its token budget')
        return json.loads(raw)
    if 'premise' not in saved:
        fields={k:{'type':'string','maxLength':100} for k in ['relationship','missed_event_or_goal','misunderstanding','real_cost','practical_plan']}
        fields['pattern']={'type':'string','enum':list(PATTERNS)}
        schema=dict(type='object',properties=fields,required=list(fields),additionalProperties=False)
        saved['premise']=ask([{'role':'system','content':'Adapt the given brief into concrete, restrained drama. One visible adult; other people only through phone messages. No other visible people, food, kitchen, car, extra props, spoken calls or new actions.'},
          {'role':'user','content':f'Title {json.dumps(title)}. Brief DATA {json.dumps(brief)}. Lead {lead}. Choose pattern: connection for loneliness/depression/reaching out; reconciliation for guilt, damaged trust, hurt caused to another person; perseverance for a training/discipline setback. The only supported exercise is a STANDING BARBELL CURL, not a squat, press, deadlift or weight change. Specify the relationship, a concrete missed event or training goal, the misunderstanding, its real cost and a practical next step. Ground the details in this brief. No generic truth/healing/presence language. Short phrases, not a full story.'}],schema,400);save()
    premise=saved['premise'];pattern=premise['pattern'];beats=PATTERNS[pattern]
    unsupported=r'\b(?:squats?|press(?:es)?|deadlifts?|bench|lbs?|kg|pounds?|kilos?|load|lighter|heavier)\b|\b\d+(?:\.\d+)?\s*(?:lbs?|kg|pounds?|kilos?)\b'
    if pattern=='perseverance':
        if re.search(r'\b(?:squat|deadlift|bench press)\w*',brief,re.I):raise ValueError('The shared exercise rig supports standing barbell curls; the requested lift needs another rig.')
        defaults=dict(missed_event_or_goal='One controlled standing barbell curl with the same bar throughout.',misunderstanding='An unfinished attempt feels like proof that trying is pointless.',real_cost='The lead has avoided returning after the unsuccessful attempts.',practical_plan='Return next session and attempt one controlled standing curl again.')
        for key,value in defaults.items():
            if re.search(unsupported,premise.get(key,''),re.I):premise[key]=value
    fact_fields=['meeting_time']+(['past_message','concrete_cost'] if pattern=='reconciliation' else ['shared_memory'] if pattern=='connection' else ['context_line'])
    schema=dict(type='object',properties={k:{'type':'string','minLength':3,'maxLength':50 if k!='meeting_time' else 24} for k in fact_fields},required=fact_fields,additionalProperties=False)
    messages=[{'role':'system','content':'Write specific details for a fixed causal screenplay. Only the CONTACT speaks in quoted lines. The lead is a different person. Never swap their roles. No new future actions, objects or exercise types.'},
      {'role':'user','content':f'''Title {json.dumps(title)}. Brief DATA {json.dumps(brief)}. Premise {json.dumps(premise)}.
meeting_time: one short FUTURE day/time phrase, such as "Tomorrow at 6 PM". Respect a time requested in the brief. It is copied consistently into the arrangement and notebook.
If requested, past_message: CONTACT recalls their earlier invitation that the LEAD ignored. CONTACT invited; LEAD failed to answer. Use a specific missed occasion. CONTACT is not apologizing.
If requested, concrete_cost: CONTACT explains how waiting or being ignored affected THEM. First person "I" means CONTACT. At most nine words. No apology or advice. This must concern the same missed occasion.
If requested, shared_memory: CONTACT recalls one specific shared moment showing they value the LEAD. A natural short text, not therapist speech or a slogan.
If requested, context_line: CONTACT asks about the lead returning after a failed standing barbell curl. No squats, presses, weight measurements, load changes or exact pause durations.
Do not invent cards, deliveries, gifts, cooking, phone calls, extra on-screen people or offscreen actions by the lead. All quoted details are short plain messages, at most50 characters. Output only the requested fields.'''}]
    facts=saved.get('facts')
    for attempt in range(3):
        try:
            if facts is None:
                print(f'Writing grounded contact details for {pattern}, attempt {attempt+1}.',flush=True)
                facts=ask(messages,schema,450)
            texts=directed_dialogue(pattern,facts)
            if pattern=='perseverance' and any(re.search(unsupported,text,re.I) for text in texts.values()):raise ValueError('Only standing barbell CURLS are shown. Remove squats, presses, weight measurements, load changes and other unsupported exercise references.')
            data={};reverse={v:k for k,v in EVENT_CODES.items()}
            for i,(loc,action,emotion,role) in enumerate(beats):
                prop=texts[role] if role else '---'
                data[f'beat_{i+1}']=dict(event=reverse[action,loc],emotion=emotion,prop_text=prop,change=PURPOSES[role][:100] if role else 'The preceding consequence changes the lead’s physical response.')
            from .visual_writer import ending_constraint
            location,action=ending_constraint(brief)
            if action or location:
                last=data['beat_32'];old_action,old_loc=EVENT_CODES[last['event']]
                last['event']=reverse[action or old_action,location or old_loc]
                if (action or old_action) not in {'phone','send','receive','write','dismiss'}:last['prop_text']='---'
            core=compile_events(data,title,brief,lead)
            if pattern=='perseverance':
                efforts=iter([.28,.45,.85,.55,1.])
                for scene in core:
                    if scene['action']=='exercise':scene['effort']=next(efforts)
            contact=re.search(r'\b(sister|brother|mother|father|mum|mom|dad|friend|coach|partner|colleague)',premise.get('relationship',''),re.I)
            for scene in core:scene['contact']=contact.group(1).upper() if contact else 'COACH' if pattern=='perseverance' else 'CONTACT'
            # Captions correspond to the opening, the consequence and the practical ending.
            direction=dict(captions=[dict(scene=3,text=texts['opening_caption']),dict(scene=27,text=texts['turn_caption']),dict(scene=len(core),text=texts['ending_caption'])],shadows=[])
            plan=apply_direction(core,direction,title,brief,lead);plan['writer']='constrained-director-v7-'+pattern
            saved['facts']=facts;save();return plan
        except (ValueError,KeyError,TypeError) as exc:
            if attempt==2:raise
            facts=None;messages.append({'role':'user','content':'Rewrite the role lines to fix: '+str(exc)})
