import json
import tempfile
import unittest
from pathlib import Path
from storyfilm.planner import template_plan, validate, brief_outline, validate_narrations, ACTIONS, LOCATIONS
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
    def test_rejects_scene_metadata_as_narration(self):
        values={f'scene_{i+1}':'She takes one small step and chooses to try again tomorrow.' for i in range(8)}
        self.assertEqual(validate_narrations(values),values)
        values['scene_1']='scene_1 is a fictional character who appears in the story.'
        with self.assertRaises(ValueError):validate_narrations(values)
        with self.assertRaises(ValueError):validate_narrations({'scene_1':'A brief narration.'})
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
