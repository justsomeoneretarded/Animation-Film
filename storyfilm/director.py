"""Original reusable dramatic structures; AI supplies specific premises and dialogue."""
import hashlib
import json
from collections import Counter
from .visual_writer import EVENT_CODES,compile_events,apply_direction

VERSION='directed-v6'
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
 'goal_note':'Private notebook: one modest training goal involving a controlled barbell repetition.',
 'excuse_note':'Private notebook: a defensive explanation after the first failed repetition.',
 'quit_draft':'Unsent message saying they want to quit after the failed attempt.',
 'reminder':'Contact asks about the agreed training session, not a motivational quotation.',
 'adjust_note':'Private notebook: a practical adjustment to the next repetition, without adding new equipment.',
 'practical_feedback':'Contact asks a practical training question or gives a short concrete correction; no slogans.',
 'progress_note':'Private notebook: a truthful record of the failed attempts and one thing to try again.',
 'checkin':'Contact asks how the session went.',
 'honest_answer':'Lead honestly reports both a setback and returning to the attempt.',
 'response':'Contact proposes the next session, naturally and briefly.',
 'next_note':'Private notebook: a specific plan for the next session, not a victory slogan.'}

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
          {'role':'user','content':f'Title {json.dumps(title)}. Brief DATA {json.dumps(brief)}. Lead {lead}. Choose pattern: connection for loneliness/depression/reaching out; reconciliation for guilt, damaged trust, hurt caused to another person; perseverance for a training/discipline setback. Specify the relationship, a concrete missed event or training goal, the misunderstanding, its real cost and a practical next step. Ground the details in this brief. No generic truth/healing/presence language. Short phrases, not a full story.'}],schema,400);save()
    premise=saved['premise'];pattern=premise['pattern'];beats=PATTERNS[pattern]
    roles=list(dict.fromkeys(r for _,_,_,r in beats if r))
    role_schema={r:{'type':'string','minLength':3,'maxLength':60} for r in roles}
    role_schema.update({k:{'type':'string','minLength':3,'maxLength':80} for k in ['opening_caption','turn_caption','ending_caption']})
    schema=dict(type='object',properties=role_schema,required=list(role_schema),additionalProperties=False)
    messages=[{'role':'system','content':'Write natural dialogue and private notebook fragments for a precisely directed film. Each line has one different purpose. No repeated apologies or resolutions, slogans, poetry, therapist speech or generic affirmations. No new physical events.'},
      {'role':'user','content':f'''Title {json.dumps(title)}. Brief DATA {json.dumps(brief)}. Premise {json.dumps(premise)}.
Write the exact visible words for these roles, in their listed order: {json.dumps({r:PURPOSES[r] for r in roles})}.
The lead and contact have a specific history; use concrete details from the premise. Every reply answers an earlier SENT message or refers to the missed event. The contact cannot read a deleted draft or a private notebook. The lead visits the street door before not_ready/not_home, then continues by message. No new visible people or objects.
One short sentence or fragment per role, preferably 4–9 words, at most60 characters. Keep role lines different; only the director repeats a draft when it is deleted or sent. Keep day/time details consistent in all scheduling lines and notes. A notebook line is private, not sent. The last eight beats handle one practical arrangement, not repeated emotional reconciliation.
Also write opening_caption, turn_caption and ending_caption: short inner thoughts, at most14 words, each adding context rather than describing poses or repeating visible messages. No miraculous cure or unearned triumph. The ending fits the brief and the practical next step. Output only the requested fields.'''}]
    texts=saved.get('texts')
    for attempt in range(3):
        try:
            if texts is None:
                print(f'Writing role-specific dialogue for {pattern}, attempt {attempt+1}.',flush=True)
                texts=ask(messages,schema,1800)
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
            # Captions correspond to the opening, the consequence and the practical ending.
            direction=dict(captions=[dict(scene=3,text=texts['opening_caption']),dict(scene=27,text=texts['turn_caption']),dict(scene=len(core),text=texts['ending_caption'])],shadows=[])
            plan=apply_direction(core,direction,title,brief,lead);plan['writer']='constrained-director-v6-'+pattern
            saved['texts']=texts;save();return plan
        except (ValueError,KeyError,TypeError) as exc:
            if attempt==2:raise
            texts=None;messages.append({'role':'user','content':'Rewrite the role lines to fix: '+str(exc)})
