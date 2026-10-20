import tempfile
import unittest
from pathlib import Path
from storyfilm.planner import template_plan, validate, ACTIONS, LOCATIONS
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
    def test_timestamp_rounding(self):
        self.assertEqual(timestamp(59.9999),'00:01:00,000')
    def test_one_lead(self):
        p=template_plan('A new day',BRIEF)
        self.assertNotIn('characters',p)
        self.assertTrue(all('character' not in scene for scene in p['scenes']))
if __name__=='__main__': unittest.main()
