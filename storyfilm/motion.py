"""Real-second choreography shared by pictures, sound and frame directions."""
import math

ACTION_SECONDS={'idle':1.2,'sit':1.1,'stand':1.25,'sleep':1.5,'phone':.75,'receive':.65,
 'send':1.0,'write':1.5,'exercise':3.2,'reach':1.0,'knock':1.25,'fall':.8,'getup':2.1,
 'lookaway':.7,'clench':.8,'wipe_tear':1.4,'dismiss':.7}
PHONE_BOUNDS=(390,65,570,455) # logical units: modern portrait handset, 0.462 aspect ratio
TYPE_RATE=11.0
WRITE_RATE=15.0

def text_count(text,t,action):
    if action=='receive':return len(text)
    if action=='dismiss':return len(text) if t<.55 else 0
    # Short pauses between bursts, never seconds spent on one letter.
    elapsed=max(0,t-.35)
    burst=int(elapsed/1.25);active=burst*1.05+min(1.05,elapsed%1.25)
    return min(len(text),int(active*(WRITE_RATE if action=='write' else TYPE_RATE)))

def text_finished(text,action):
    rate=WRITE_RATE if action=='write' else TYPE_RATE
    active=len(text)/rate
    return .35+active+int(active/1.05)*.20

def send_time(text,pretyped=False):return .7 if pretyped else text_finished(text,'send')+.35

def prop_count(scene,t):
    if scene.get('pretyped') and scene['action'] in {'phone','send'}:return len(scene.get('prop_text',''))
    return text_count(scene.get('prop_text',''),t,scene['action'])

def action_progress(action,t):return max(0,min(1,t/max(.1,ACTION_SECONDS.get(action,1.2))))

def walk_position(t):
    # Same cadence and displacement for a three-second or ten-second shot.
    return 300+min(t,4.2)*76

def natural_duration(scene):
    action=scene['action'];text=scene.get('prop_text','')
    if scene.get('shot')=='reaction':return 1.8
    if scene.get('shot')=='insert':
        read=1.0+len(text.split())/3.2
        return min(13,max(3.2,read if action=='receive' else .7+read if scene.get('pretyped') else text_finished(text,action)+read*.55+.5))
    return {'walk':4.2,'exercise':4.1,'getup':3.2,'fall':2.4,'stand':2.3,'knock':3.,
            'reach':2.5,'sleep':4.,'wipe_tear':3.2,'clench':2.6,'lookaway':2.7,'dismiss':2.8}.get(action,3.)

def frame_state(scene,t,absolute=0,duration=6):
    action=scene['action'];text=scene.get('prop_text','');ambient=scene.get('ambient_start',0)+t
    return {'character':{'action':action,'phase':round(action_progress(action,t),3),
        'emotion_from':scene.get('emotion_from',scene['emotion']),'emotion':scene['emotion'],
        'emotion_mix':round(max(0,min(1,(t-.15)/.65)),3),'intensity':scene.get('intensity',.7),
        'gaze':scene.get('gaze','phone' if action in {'phone','send','receive','dismiss'} else 'notebook' if action=='write' else 'ground'),
        'gesture':scene.get('gesture','none'),'walk_x':round(walk_position(t),2) if action=='walk' else None},
        'prop':{'visible_characters':prop_count(scene,t),'sent':action=='send' and t>=send_time(text,scene.get('pretyped',False)),
                'phone_aspect_ratio':round(180/390,4)},
        'environment':{'weather':scene.get('weather','clear'),'phase_seconds':round(ambient,3),
            'clock_seconds':round(scene.get('clock_minutes',22*60)*60+ambient,3),
            'window_rain':scene.get('weather')=='rain' and scene['location'] in {'bedroom','desk'},
            'light':scene.get('time','night')},
        'audio':{'rain':scene.get('weather')=='rain','clock_tick':scene['location'] in {'bedroom','desk','gym'} and ambient%1<1/12,'foot_contact':action=='walk' and (t%(math.pi/3.6))<1/12,'send_tap':action=='send' and 0<=t-send_time(text,scene.get('pretyped',False))<1/12},
        'camera':scene.get('shot','wide'),'time':round(absolute,3)}
