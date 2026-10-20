import json
import tempfile
import unittest
from pathlib import Path
from storyfilm.planner import template_plan, validate, adapt_model_plan, story_schema, brief_outline, narration_schema, ACTIONS, LOCATIONS
from storyfilm.render import captions, timestamp
from storyfilm.art import frame
from storyfilm.audio import synthesize,read_wave
BRIEF='She wakes up feeling stuck. She writes down her goal. She walks outside. She finally feels hopeful.'
class PipelineTests(unittest.TestCase):
    def test_lead_selection_and_override(self):
        self.assertEqual(template_plan('A new day',BRIEF)['character'],'female')
        self.assertEqual(template_plan('A new day',BRIEF,'male')['character'],'male')
    def test_brief_is_data(self):
        p=template_plan('Title `uname`','She writes $(touch /tmp/never-create-this); then walks outside. She smiles. She rests.')
        self.assertIn('$(touch',p['scenes'][0]['narration'])
        self.assertEqual(p['title'],'Title `uname`')
    def test_generation_grammar_rejects_unsupported_emotions(self):
        try:
            from lmformatenforcer import JsonSchemaParser
        except ImportError:
            self.skipTest('AI dependencies are not installed')
        plan=template_plan('A new day',BRIEF)
        plan['scenes']*=2
        text=json.dumps({'character':plan['character'],'scenes':plan['scenes']})
        parser=JsonSchemaParser(story_schema())
        for char in text:
            self.assertIn(char,parser.get_allowed_characters())
            parser=parser.add_character(char)
        self.assertTrue(parser.can_end())
        invalid=text.replace('"sad"','"worrying"',1)
        parser=JsonSchemaParser(story_schema())
        rejected=False
        for char in invalid:
            if char not in parser.get_allowed_characters():
                rejected=True
                break
            parser=parser.add_character(char)
        self.assertTrue(rejected)
    def test_model_synonyms_preserve_the_story(self):
        plan=template_plan('A new day',BRIEF)
        narration=plan['scenes'][0]['narration']
        plan['scenes'][0]['emotion']='reflective'
        plan['scenes'][1]['emotion']='hopeful'
        mapped,changes=adapt_model_plan(plan)
        result=validate(mapped,'A new day',BRIEF)
        self.assertEqual(result['scenes'][0]['emotion'],'neutral')
        self.assertEqual(result['scenes'][1]['emotion'],'happy')
        self.assertEqual(result['scenes'][0]['narration'],narration)
        self.assertEqual(len(changes),2)
    def test_outline_preserves_brief_actions_and_ending(self):
        brief='She scrolls in her bedroom. She writes a goal at her desk. She walks outside. She sits in the park. End on the rooftop with her trying again tomorrow. Reflective, quiet, hopeful. Female lead.'
        lead,scenes=brief_outline(brief)
        self.assertEqual(lead,'female')
        self.assertEqual(len(scenes),8)
        self.assertEqual((scenes[0]['location'],scenes[0]['action']),('bedroom','phone'))
        self.assertEqual(scenes[-1]['location'],'rooftop')
        self.assertIn('trying again tomorrow',scenes[-1]['narration'])
        self.assertTrue(any(s['action']=='write' and s['location']=='desk' for s in scenes))
        self.assertTrue(any(s['action']=='sit' and s['location']=='park' for s in scenes))
        for scene in scenes:
            self.assertIn(scene['location'],LOCATIONS)
            self.assertIn(scene['action'],ACTIONS)
    def test_narration_grammar_accepts_all_eight_scenes(self):
        try:
            from lmformatenforcer import JsonSchemaParser
        except ImportError:
            self.skipTest('AI dependencies are not installed')
        parser=JsonSchemaParser(narration_schema())
        value={f'scene_{i+1}':'She makes one small choice and tries again tomorrow.' for i in range(8)}
        for char in json.dumps(value):
            self.assertIn(char,parser.get_allowed_characters())
            parser=parser.add_character(char)
        self.assertTrue(parser.can_end())
    def test_invalid_model_output(self):
        plan=template_plan('A new day',BRIEF);plan['scenes'][1]['location']='castle'
        with self.assertRaises(ValueError): validate(plan,'Title',BRIEF)
        with self.assertRaises(ValueError): validate({'scenes':[]},'Title',BRIEF)
    def test_actions_and_leads_render(self):
        for gender in ('female','male'):
            for action in ACTIONS:
                for location in LOCATIONS:
                    scene=dict(location=location,action=action,emotion='worried',shadow=True)
                    image=frame(scene,gender,'A new day',1.2,5,0,4,'A small beginning.')
                    self.assertEqual(image.size,(960,540))
                    self.assertGreater(sum(image.getextrema()[0]),10)
    def test_caption_timing_and_audio(self):
        plan=template_plan('A new day',BRIEF)
        with tempfile.TemporaryDirectory() as directory:
            timings=synthesize(plan,Path(directory),'none')
            samples,sr=read_wave(Path(directory)/'soundtrack.wav')
            self.assertGreater(float(abs(samples).max()),.001)
            self.assertAlmostEqual(len(samples)/sr,sum(t['duration'] for t in timings),places=3)
            caps=captions(plan,timings)
            self.assertTrue(all(a<b for a,b,_ in caps))
            self.assertTrue(all(caps[i][1]<=caps[i+1][0] for i in range(len(caps)-1)))
    def test_audio_scene_lengths_match_frame_boundaries(self):
        plan=template_plan('A new day',BRIEF)
        with tempfile.TemporaryDirectory() as directory:
            timings=synthesize(plan,Path(directory),'none',duration_scale=.25,fps=12)
            for timing in timings:
                self.assertAlmostEqual(timing['duration']*12,round(timing['duration']*12),places=7)
            samples,sr=read_wave(Path(directory)/'soundtrack.wav')
            self.assertAlmostEqual(len(samples)/sr,sum(t['duration'] for t in timings),places=4)
            caps=captions(plan,timings)
            self.assertTrue(all(a<b for a,b,_ in caps))
            self.assertLessEqual(caps[-1][1],sum(t['duration'] for t in timings))
    def test_timestamp_rounding(self):
        self.assertEqual(timestamp(59.9999),'00:01:00,000')
    def test_one_lead(self):
        p=template_plan('A new day',BRIEF)
        self.assertNotIn('characters',p)
        self.assertTrue(all('character' not in scene for scene in p['scenes']))
if __name__=='__main__': unittest.main()
