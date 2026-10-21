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


def synthesize(plan, out, engine='piper', cache='.cache/voices', duration_scale=1., fps=12):
    out=Path(out)
    voice=None
    has_voice=any(s.get('voiceover',s.get('narration','')) for s in plan['scenes'])
    if engine=='piper' and has_voice:
        from piper import PiperVoice, SynthesisConfig
        voice=PiperVoice.load(str(voice_files(cache)))
    elif engine=='espeak' and not (shutil.which('espeak-ng') or shutil.which('espeak')):
        raise RuntimeError('Install espeak-ng or use --voice piper')
    sr=24000
    all_audio=[]; timings=[]; cursor=0; prepared=[]
    for i, scene in enumerate(plan['scenes']):
        dest=out/f'narration-{i:02d}.wav'
        spoken=scene.get('voiceover',scene.get('narration',''))
        if not spoken:
            rate=sr;samples=np.zeros(0,np.float32)
        elif engine=='piper':
            with wave.open(str(dest),'wb') as wav:
                voice.synthesize_wav(spoken,wav,syn_config=SynthesisConfig(length_scale=1.12))
            samples, rate=read_wave(dest)
        elif engine=='espeak':
            subprocess.run([shutil.which('espeak-ng') or shutil.which('espeak'), '-s','145','-v','en-us','-w',str(dest),'--',spoken],check=True)
            samples,rate=read_wave(dest)
        else:
            rate=sr
            samples=np.zeros(int(sr*max(3,len(scene['narration'].split())/2.4)),np.float32)
        if rate != sr:
            samples=np.interp(np.arange(round(len(samples)*sr/rate))*rate/sr,np.arange(len(samples)),samples).astype(np.float32)
        prepared.append(samples)
        print(f'Speech ready: beat {i+1}/{len(plan["scenes"])}',flush=True)
    target=plan.get('target_seconds')
    text_led=plan.get('mode')=='text-led'
    if target and not text_led:
        # Preserve the spoken performance; only modest tempo changes are allowed.
        # A short script must be rewritten, not stretched into minutes of silence.
        speech_seconds=sum(len(a)/sr for a in prepared)
        body=target-len(prepared)*1.55
        tempo=speech_seconds/body
        if engine!='none' and not .72<=tempo<=1.45:
            raise ValueError(f'Script timing cannot fit 3–4 minutes naturally (tempo {tempo:.2f}); rewrite the script')
        if engine=='none':
            prepared=[np.zeros(round(len(a)/tempo),np.float32) for a in prepared]
        if engine!='none' and abs(tempo-1)>.015:
            for i,samples in enumerate(prepared):
                temp=out/f'tempo-{i:02d}.wav';write_wave(temp,samples,sr)
                dest=out/f'retimed-{i:02d}.wav'
                subprocess.run(['ffmpeg','-v','error','-y','-i',str(temp),'-af',f'atempo={tempo:.6f}',str(dest)],check=True)
                prepared[i],_=read_wave(dest);temp.unlink();dest.unlink()
    total_speech=sum(len(a) for a in prepared)
    target_frames=round(target*fps) if target else None
    used_frames=0
    for i,(scene,samples) in enumerate(zip(plan['scenes'],prepared)):
        lead=int(.65*sr)
        if text_led:
            duration=scene['duration']/sum(s['duration'] for s in plan['scenes'])*target*duration_scale
        elif target:
            # Allocate pauses proportionally; final frame absorbs rounding.
            remaining=max(0,target-total_speech/sr)
            duration=(len(samples)/sr+remaining/len(prepared))*duration_scale
        else:duration=max(5,len(samples)/sr+1.55)*duration_scale
        frames=max(1,round(duration*fps))
        if target and i==len(prepared)-1:
            frames=round(target_frames*duration_scale)-used_frames
        used_frames+=frames;duration=frames/fps
        sound=np.zeros(round(duration*sr),np.float32)
        if duration_scale==1:
            available=len(sound)-lead
            if len(samples)>available:raise ValueError('Speech does not fit allocated beat')
            sound[lead:lead+len(samples)]=samples
        all_audio.append(sound)
        timings.append({'start':cursor,'duration':duration,'speech_start':cursor+.65,
                        'speech_duration':len(samples)/sr,'scene':i})
        cursor+=duration
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
    # Deterministic scene foley: feet, pencil, phone taps, outdoor air and birds.
    rng=np.random.default_rng(42)
    for scene,timing in zip(plan['scenes'],timings):
        offset=round(timing['start']*sr);length=round(timing['duration']*sr)
        end=min(len(mix),offset+length);length=end-offset
        if scene['location'] in {'street','park','rooftop'}:
            noise=rng.normal(0,1,length)
            air=np.convolve(noise,np.ones(90)/90,mode='same')*.014
            mix[offset:end]+=air
        action=scene['action']
        step=.87 if action=='walk' else 1.3 if action=='write' else 3.1
        if action in {'walk','write','phone','send','receive','knock','fall','getup'}:
            events=(np.arange(0,timing['duration']-.2,math.pi/3.6) if action=='walk' else np.arange(timing['duration']*.28,timing['duration']*.77,.45) if action=='write' else [timing['duration']*.48] if action=='fall' else [.04] if action=='receive' else [timing['duration']*.58,timing['duration']*.66] if action=='knock' else [timing['duration']*.72] if action=='send' else [])
            for when in events:
                start=offset+round(when*sr);n=min(round(sr*.13),len(mix)-start)
                tt=np.arange(n)/sr
                if action=='walk':sound=(rng.normal(0,1,n)*.022+np.sin(2*np.pi*91*tt)*.04)*np.exp(-tt*38)
                elif action in {'fall','getup','knock'}:sound=(rng.normal(0,1,n)*.045+np.sin(2*np.pi*75*tt)*.06)*np.exp(-tt*35)
                elif action=='receive':sound=np.sin(2*np.pi*880*tt)*.024*np.exp(-tt*22)
                elif action=='write':sound=rng.normal(0,1,n)*.008*np.sin(np.pi*np.arange(n)/max(1,n))
                else:sound=np.sin(2*np.pi*740*tt)*.009*np.exp(-tt*65)
                mix[start:start+n]+=sound
        if scene['location']=='park' and scene.get('time')!='night':
            for when in np.arange(2,timing['duration']-1,6):
                start=offset+round(when*sr);n=min(round(.3*sr),len(mix)-start);tt=np.arange(n)/sr
                mix[start:start+n]+=.009*np.sin(2*np.pi*(1700*tt+900*tt**2))*np.sin(np.pi*np.arange(n)/max(1,n))**2
    ramp=min(sr*2,len(mix)//2)
    mix[:ramp]*=np.linspace(0,1,ramp);mix[-ramp:]*=np.linspace(1,0,ramp)
    write_wave(out/'soundtrack.wav',mix,sr)
    write_wave(out/'narration.wav',narration,sr)
    return timings
