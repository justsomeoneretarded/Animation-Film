import json
import tempfile
import unittest
from pathlib import Path
from PIL import ImageChops,ImageStat
from storyfilm.planner import template_plan,validate,brief_outline,validate_narrations,depression_plan,BEATS,ACTIONS,narration_issues
from storyfilm.render import captions,timestamp
from storyfilm.art import frame,character,background
from storyfilm.audio import synthesize,read_wave
BRIEF='She wakes up feeling stuck. She writes down her goal. She walks outside. She finally feels hopeful.'
class PipelineTests(unittest.TestCase):
    def test_lead_selection_and_override(self):
        self.assertEqual(template_plan('A new day',BRIEF)['character'],'female')
        self.assertEqual(template_plan('A new day',BRIEF,'male')['character'],'male')
        from storyfilm.planner import select_lead
        self.assertEqual(select_lead('Male lead. He rereads her message.'),'male')
        self.assertEqual(select_lead('Female protagonist. She rereads his message.'),'female')
    def test_brief_is_data(self):
        p=template_plan('Title `uname`','She writes $(touch /tmp/never-create-this); then walks outside. She smiles. She rests.')
        self.assertIn('$(touch',p['scenes'][0]['narration'])
        self.assertEqual(p['title'],'Title `uname`')
    def test_ordered_outline(self):
        brief='She scrolls in her bedroom. She writes a goal at her desk. She walks outside. She sits in the park. End on the rooftop with her trying again tomorrow. Reflective, quiet, hopeful. Female lead.'
        lead,scenes=brief_outline(brief)
        self.assertEqual(lead,'female');self.assertEqual(len(scenes),BEATS)
        self.assertEqual((scenes[0]['location'],scenes[0]['action']),('bedroom','phone'))
        self.assertEqual(scenes[-1]['location'],'rooftop')
        self.assertIn('trying again tomorrow',scenes[-1]['narration'])
        self.assertTrue(any(s['action']=='write' and s['location']=='desk' for s in scenes))
    def test_authored_script_continuity_and_length(self):
        p=depression_plan('Depressed','Male lead.')
        self.assertEqual(p['target_seconds'],210)
        self.assertEqual(p['mode'],'text-led')
        self.assertEqual(len(p['scenes']),30)
        texts=' '.join(s['prop_text'] for s in p['scenes'])
        self.assertIn('Can we talk?',texts)
        self.assertIn('appointment',texts)
        self.assertFalse(any(s['voiceover'] for s in p['scenes']))
        female=depression_plan('Depressed','Female lead.')
        self.assertNotIn(' he ',' '.join(s['caption'] for s in female['scenes']))
        self.assertEqual(female['character'],'female')
    def test_rejects_scene_metadata(self):
        values={f'scene_{i+1}':'She takes one small step and chooses to try again tomorrow.' for i in range(BEATS)}
        self.assertEqual(validate_narrations(values),values)
        values['scene_1']='scene_1 is a fictional character who appears in the story.'
        with self.assertRaises(ValueError):validate_narrations(values)
    def test_invalid_plan(self):
        p=template_plan('Title',BRIEF);p['scenes'][1]['location']='castle'
        with self.assertRaises(ValueError):validate(p,'Title',BRIEF)
        with self.assertRaises(ValueError):validate({'scenes':[]},'Title',BRIEF)
        p=depression_plan('Depressed','Male lead.');p['target_seconds']=60
        with self.assertRaises(ValueError):validate(p,'Title',BRIEF)
    def test_all_actions_native_resolution(self):
        for gender in ('female','male'):
            for i,action in enumerate(sorted(ACTIONS)):
                s=dict(location=['bedroom','desk','street','park','gym','rooftop'][i%6],action=action,emotion='worried',shadow=False)
                im=frame(s,gender,'Title',2,8,0,12,'A small beginning.')
                self.assertEqual(im.size,(1920,1080))
                self.assertGreater(ImageStat.Stat(im).stddev[0],15)
    def test_expression_and_motion_are_visible(self):
        s=dict(location='park',action='sit',emotion='sad',shadow=False)
        a=frame(s,'male','Title',4,12,0,12)
        b=frame(dict(s,emotion='happy'),'male','Title',4,12,0,12)
        self.assertGreater(sum(ImageStat.Stat(ImageChops.difference(a,b)).mean),.5)
        # Keep the camera and scene fixed: rig itself must move.
        from PIL import Image
        a=Image.new('RGBA',(1920,1080));b=a.copy()
        character(a,480,470,0,'female','walk','worried')
        character(b,480,470,.4,'female','walk','worried')
        self.assertGreater(sum(ImageStat.Stat(ImageChops.difference(a,b)).mean),1)
    def test_day_and_night_are_distinct(self):
        self.assertGreater(sum(ImageStat.Stat(ImageChops.difference(background('park','night'),background('park','dawn'))).mean),20)
    def test_object_inserts_render(self):
        for action in ('phone','write'):
            s=dict(location='desk',action=action,emotion='worried',prop_text='Ask for help.|One step.',shadow=False)
            im=frame(s,'female','Title',10,12,2,12)
            self.assertEqual(im.size,(1920,1080))
    def test_production_timing_and_captions(self):
        plan=depression_plan('Depressed','Male lead.')
        with tempfile.TemporaryDirectory() as directory:
            t=synthesize(plan,Path(directory),'none',fps=12)
            samples,sr=read_wave(Path(directory)/'soundtrack.wav')
            self.assertAlmostEqual(sum(v['duration'] for v in t),210,places=5)
            self.assertAlmostEqual(len(samples)/sr,210,places=5)
            self.assertGreater(float(abs(samples).max()),.01)
            self.assertTrue(all(abs(v['duration']*12-round(v['duration']*12))<1e-6 for v in t))
            caps=captions(plan,t)
            self.assertTrue(all(a<b for a,b,_ in caps));self.assertLessEqual(caps[-1][1],210)
            self.assertTrue(all(caps[i][1]<=caps[i+1][0] for i in range(len(caps)-1)))
    def test_preview_audio_lengths(self):
        with tempfile.TemporaryDirectory() as directory:
            t=synthesize(template_plan('Title',BRIEF),Path(directory),'none',duration_scale=.25,fps=12)
            samples,sr=read_wave(Path(directory)/'soundtrack.wav')
            self.assertAlmostEqual(len(samples)/sr,sum(v['duration'] for v in t),places=4)
    def test_neck_remains_visible_below_jaw(self):
        from PIL import Image
        for gender in ('male','female'):
            for action,emotion in [('idle','neutral'),('phone','sad')]:
                im=Image.new('RGBA',(1920,1080))
                character(im,480,470,1,gender,action,emotion)
                # Sample below the jaw, above the collar, in each actual pose.
                region=(952,438,974,450) if action=='idle' else (984,492,1000,496)
                neck=im.crop(region)
                pixels=list(neck.getdata())
                skin=sum(r>150 and g>130 and b>90 and a==255 for r,g,b,a in pixels)
                self.assertGreater(skin/len(pixels),.9)
    def test_locked_camera_does_not_drift(self):
        s=dict(location='desk',action='idle',emotion='neutral',time='day')
        a=frame(s,'male','Title',1,18,0,12)
        b=frame(s,'male','Title',4,18,0,12)
        self.assertIsNone(ImageChops.difference(a.crop((20,70,550,260)),b.crop((20,70,550,260))).getbbox())
    def test_visual_continuity_rejects_impossible_contact(self):
        self.assertTrue(narration_issues('She sits without touching it, and she writes another line.',{'action':'walk'}))
        self.assertFalse(narration_issues('She walks slowly along the pavement, then pauses at the curb.',{'action':'walk'}))
    def test_timestamp_rounding(self):self.assertEqual(timestamp(59.9999),'00:01:00,000')

class VisualScreenplayTests(unittest.TestCase):
    def test_saved_plan_preserves_the_render_contract(self):
        p=depression_plan('Another title','Female lead.')
        checked=validate(json.loads(json.dumps(p)),'Another title','Female lead.')
        self.assertEqual(checked,p)
        self.assertEqual(checked['scenes'][18]['action'],'send')
        self.assertEqual(checked['scenes'][20]['action'],'receive')
        self.assertEqual(checked['scenes'][18]['prop_text'],'I am not doing well. Can we talk?')
    def test_impossible_object_shots_are_rejected(self):
        import copy
        for mutation in [{'action':'walk','shot':'insert'},{'action':'write','location':'park'}, {'duration':float('nan')},{'shadow':'none','shadow_text':'Stay home.'}]:
            p=copy.deepcopy(depression_plan('Title','Male lead.'))
            p['scenes'][0].update(mutation)
            with self.assertRaises(ValueError):validate(p,'Title','Male lead.')
    def test_fall_and_recovery_have_different_body_levels(self):
        from PIL import Image
        images=[]
        for action,p in [('idle',.8),('fall',.8),('getup',1.)]:
            im=Image.new('RGBA',(1920,1080));character(im,480,475,1,'male',action,'neutral',progress=p)
            images.append(im.getchannel('A').getbbox())
        self.assertGreater(images[1][1],images[0][1]+100)
        self.assertEqual(images[2][1],images[0][1])
        self.assertEqual(images[2][3],images[0][3])
    def test_phone_insert_keeps_send_and_receive_semantics(self):
        from unittest.mock import patch
        from storyfilm.staging import stage
        from PIL import Image
        for action in ('send','receive'):
            scene=dict(location='park',action=action,emotion='worried',shot='insert',prop_text='A specific answer.')
            with patch('storyfilm.art.insert_shot',return_value=Image.new('RGBA',(1920,1080))) as insert:
                stage(scene,'female','Unrelated title',4,7,1,4)
                self.assertEqual(insert.call_args.args[1]['action'],action)
    def test_text_led_audio_does_not_download_an_unused_voice(self):
        from unittest.mock import patch
        p=depression_plan('Title','Female lead.')
        with tempfile.TemporaryDirectory() as directory,patch('storyfilm.audio.voice_files',side_effect=AssertionError('Unnecessary voice download')):
            timings=synthesize(p,Path(directory),'piper',duration_scale=.1,fps=12)
            samples,sr=read_wave(Path(directory)/'narration.wav')
            self.assertFalse(samples.any())
            self.assertAlmostEqual(sum(t['duration'] for t in timings),21)

class GeneralWriterContractTests(unittest.TestCase):
    def test_complete_arc_action_binding_sparse_text_and_checkpoint(self):
        from storyfilm.visual_writer import write,COUNT
        class Model:
            def __init__(self):self.calls=[]
            def create_chat_completion(self,**request):
                self.calls.append(request)
                required=request['response_format']['schema']['required']
                if 'opening' in required:
                    data={k:'A specific cause and consequence.' for k in required}
                elif 'beat_1' in required:
                    data={}
                    for i in range(12):
                        action,location,emotion,prop=[('receive','bedroom','worried',f'Can we talk {i}?'),('phone','bedroom','tired',f'Draft {i}'),('walk','street','worried',''),('write','desk','worried',f'The truth {i}'),('send','park','determined',f'An honest answer {i}'),('sit','park','neutral','')][i%6]
                        if i==11:action,location,prop='write','desk','Keep writing.'
                        data[f'beat_{i+1}']=dict(action=action,location=location,emotion=emotion,prop_text=prop)
                    if len(self.calls)==2:data.pop('beat_12')
                else:
                    data=dict(captions=[dict(scene=i,text=t) for i,t in [(1,'The question had waited all night.'),(10,'An easy answer would have been another lie.'),(24,'Perfect was no longer the point.'),(36,'There was room for another sentence.')]],shadows=[dict(scene=2,text='Leave it unanswered.'),dict(scene=20,text='They will misunderstand.')])
                return {'choices':[{'message':{'content':json.dumps(data)}}]}
        model=Model();brief='She walks outside and sends an honest answer. End at the desk, writing again.'
        with tempfile.TemporaryDirectory() as directory:
            diagnostic=Path(directory)/'writer.txt'
            p=write(model,'A completely different title',brief,'female',diagnostic)
            reused=write(model,'A completely different title',brief,'female',diagnostic)
            self.assertEqual(reused,p)
        self.assertEqual(len(model.calls),4);self.assertEqual(len(p['scenes']),36)
        self.assertEqual(p['scenes'][-1]['action'],'write');self.assertEqual(p['scenes'][-1]['location'],'desk')
        self.assertEqual(sum(bool(s['caption']) for s in p['scenes']),4)
        self.assertEqual(sum(bool(s['shadow_text']) for s in p['scenes']),2)
        self.assertTrue(all('Writes' in s['event'] for s in p['scenes'] if s['action']=='write'))
        self.assertTrue(all(not s['voiceover'] for s in p['scenes']))
        from storyfilm.visual_writer import shot_variants,beat_schema
        variants=shot_variants()
        required=beat_schema(brief)['properties']
        self.assertEqual(required['beat_10']['properties']['action']['enum'],['send'])
        self.assertEqual(required['beat_12']['properties']['action']['enum'],['write'])
        for location,action in [('bedroom','walk'),('gym','write'),('rooftop','sleep'),('street','sit'),('park','knock'),('desk','exercise')]:
            self.assertFalse(any(location in v['properties']['location']['enum'] and action in v['properties']['action']['enum'] for v in variants))
        for v in variants:
            if v['properties']['shot']['enum']==['insert']:self.assertEqual(v['properties']['prop_text']['minLength'],3)
    def test_director_rejects_pose_captions_and_repeated_shadow_lines(self):
        from storyfilm.visual_writer import apply_direction
        core=depression_plan('Title','Male lead.')['scenes']
        core=(core+core)[:36]
        captions=[dict(scene=i,text='A distinct story meaning '+str(i)) for i in (1,10,20,36)]
        captions[0]['text']='She writes in her notebook.'
        with self.assertRaises(ValueError):apply_direction(core,dict(captions=captions,shadows=[]),'Title','Male lead.','male')
        captions[0]['text']='The question had waited all night.'
        shadows=[dict(scene=2,text='Do not answer.'),dict(scene=3,text='Do not answer.')]
        with self.assertRaises(ValueError):apply_direction(core,dict(captions=captions,shadows=shadows),'Title','Male lead.','male')


class EnvironmentContactTests(unittest.TestCase):
    def test_phone_pose_uses_furniture_only_where_available(self):
        from unittest.mock import patch
        from storyfilm.staging import stage
        for location,seated in [('street',False),('gym',False),('rooftop',False),('park',True),('bedroom',True),('desk',True)]:
            with patch('storyfilm.staging.actor') as actor:
                stage(dict(location=location,action='phone',emotion='worried'),'male','Any title',2,8,0,4)
                self.assertEqual(actor.call_args.kwargs['seated'],seated)
    def test_clutter_does_not_disappear_between_room_visits(self):
        p=depression_plan('Another title','Male lead.')
        bedroom=[s for s in p['scenes'] if s['location']=='bedroom']
        self.assertTrue(all(s['state']=='clutter' for s in bedroom))

class WeatherTests(unittest.TestCase):
    def test_winter_brief_defaults_to_visible_outdoor_snow(self):
        p=depression_plan('Winter Arc','Male lead. A snowy winter walk.')
        self.assertTrue(all(s['weather']=='snow' for s in p['scenes'] if s['location'] in {'street','park'}))
        scene=dict(location='street',action='idle',emotion='worried',time='night',weather='clear')
        clear=frame(scene,'male','Title',2,8,0,4)
        snow=frame(dict(scene,weather='snow'),'male','Title',2,8,0,4)
        self.assertGreater(sum(ImageStat.Stat(ImageChops.difference(clear,snow)).mean),.5)
        p['scenes'][0]['weather']='hail'
        with self.assertRaises(ValueError):validate(p,'Title','Male lead.')

class TextPlacementTests(unittest.TestCase):
    def test_shadow_dialogue_does_not_cover_the_leads_face(self):
        scene=dict(location='desk',action='sit',emotion='sad',shot='close',shadow='loom')
        a=frame(scene,'female','Title',4,8,0,4)
        b=frame(dict(scene,shadow_text='You did nothing again.'),'female','Title',4,8,0,4)
        self.assertIsNone(ImageChops.difference(a.crop((700,400,1200,900)),b.crop((700,400,1200,900))).getbbox())
        self.assertIsNotNone(ImageChops.difference(a,b).getbbox())

class DeskContactTests(unittest.TestCase):
    def test_writing_pencil_reaches_the_visible_notebook_plane(self):
        for gender in ('male','female'):
            scene=dict(location='desk',action='write',emotion='neutral',time='day',weather='clear',shot='wide')
            im=frame(scene,gender,'Title',3,6,1,4)
            pixels=im.crop((990,752,1090,762)).getdata()
            pencil=sum(abs(r-191)<4 and abs(g-162)<4 and abs(b-120)<4 for r,g,b in pixels)
            self.assertGreater(pencil,4)


if __name__=='__main__':unittest.main()
