import json
import math
import os
import shutil
import subprocess
import urllib.request
import wave
from pathlib import Path
import numpy as np

VOICE_BASE = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ljspeech/medium/'
VOICE_NAME = 'en_US-ljspeech-medium.onnx'


def voice_files(cache):
    cache = Path(cache); cache.mkdir(parents=True, exist_ok=True)
    for name in [VOICE_NAME, VOICE_NAME+'.json', 'MODEL_CARD']:
        target = cache/name
        if not target.exists():
            tmp = target.with_suffix(target.suffix+'.part')
            try:
                with urllib.request.urlopen(VOICE_BASE+name, timeout=120) as response, tmp.open('wb') as out:
                    shutil.copyfileobj(response, out)
                tmp.replace(target)
            finally:
                tmp.unlink(missing_ok=True)
    return cache/VOICE_NAME


def read_wave(path):
    with wave.open(str(path), 'rb') as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 1:
            raise ValueError('Narration must be mono signed 16-bit PCM')
        return np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float32)/32768, w.getframerate()


def write_wave(path, samples, sr=24000):
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(samples, -.98, .98)*32767).astype('<i2').tobytes())


def synthesize(plan, out, engine='piper', cache='.cache/voices', duration_scale=1., fps=24):
    out=Path(out)
    voice=None
    if engine=='piper':
        from piper import PiperVoice, SynthesisConfig
        voice=PiperVoice.load(str(voice_files(cache)))
    elif engine=='espeak' and not (shutil.which('espeak-ng') or shutil.which('espeak')):
        raise RuntimeError('Install espeak-ng or use --voice piper')
    sr=24000
    all_audio=[]; timings=[]; cursor=0
    for i, scene in enumerate(plan['scenes']):
        dest=out/f'narration-{i:02d}.wav'
        if engine=='piper':
            with wave.open(str(dest),'wb') as wav:
                voice.synthesize_wav(scene['narration'],wav,syn_config=SynthesisConfig(length_scale=1.06))
            samples, rate=read_wave(dest)
        elif engine=='espeak':
            subprocess.run([shutil.which('espeak-ng') or shutil.which('espeak'), '-s','145','-v','en-us','-w',str(dest),'--',scene['narration']],check=True)
            samples,rate=read_wave(dest)
        else:
            rate=sr
            samples=np.zeros(int(sr*max(3,len(scene['narration'].split())/2.4)),np.float32)
        if rate != sr:
            samples=np.interp(np.arange(round(len(samples)*sr/rate))*rate/sr,np.arange(len(samples)),samples).astype(np.float32)
        lead=int(.65*sr); tail=int(.9*sr)
        duration=round(max(5,(len(samples)+lead+tail)/sr)*duration_scale*fps)/fps
        # Preview scaling deliberately shortens scenes and omits the cut-off narration.
        sound=np.zeros(round(duration*sr),np.float32)
        if duration_scale==1:
            sound[lead:lead+len(samples)]=samples[:max(0,len(sound)-lead)]
        all_audio.append(sound)
        timings.append({'start':cursor,'duration':duration,'speech_start':cursor+.65,
                        'speech_duration':len(samples)/sr,'scene':i})
        cursor+=duration
        print(f'Narration ready: scene {i+1}/{len(plan["scenes"])}',flush=True)
    narration=np.concatenate(all_audio)
    # Original restrained ambient score: slowly moving sine chords, no downloaded music.
    mix=narration*.84
    chords=[(130.81,155.56,196.),(103.83,130.81,155.56),(116.54,146.83,174.61),(98.,123.47,146.83)]
    for start in range(0,len(mix),sr*2):
        stop=min(len(mix),start+sr*2)
        t=np.arange(start,stop)/sr
        chord=chords[int(t[0]//12)%len(chords)]
        pad=np.zeros(len(t))
        for freq in chord:
            pad+=np.sin(2*np.pi*freq*t+.3*np.sin(t*.17))*.009
            pad+=np.sin(2*np.pi*freq*.5*t)*.005
        pad*=.75+.25*np.sin(t*.4)
        # Duck the score under narration, using a smooth block envelope.
        energy=float(np.sqrt(np.mean(narration[start:stop]**2)))
        mix[start:stop]+=pad*(.5 if energy>.015 else 1)
    # Soft transition chimes act as restrained sound effects.
    for timing in timings[1:]:
        start=round(timing['start']*sr); length=min(sr,len(mix)-start)
        tt=np.arange(length)/sr
        mix[start:start+length]+=.017*np.sin(2*np.pi*523.25*tt)*np.exp(-tt*7)
    ramp=min(sr*2,len(mix)//2)
    mix[:ramp]*=np.linspace(0,1,ramp);mix[-ramp:]*=np.linspace(1,0,ramp)
    write_wave(out/'soundtrack.wav',mix,sr)
    write_wave(out/'narration.wav',narration,sr)
    return timings
