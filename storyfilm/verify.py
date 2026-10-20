import argparse
import json
import subprocess
from pathlib import Path

def verify(path,height=1080,fps=None,min_seconds=None,max_seconds=None):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
    video=next(s for s in data['streams'] if s['codec_type']=='video')
    audio=next(s for s in data['streams'] if s['codec_type']=='audio')
    assert video['height']==height and video['width']==height*16//9, 'Unexpected resolution'
    assert video['codec_name']=='h264' and audio['codec_name']=='aac', 'Unexpected codecs'
    assert float(data['format']['duration'])>1, 'Empty film'
    assert abs(float(video['duration'])-float(audio['duration']))<.3, 'Audio/video durations differ'
    if fps is not None:
        a,b=map(int,video['r_frame_rate'].split('/'));assert abs(a/b-fps)<.001,'Unexpected frame rate'
    duration=float(data['format']['duration'])
    if min_seconds is not None:assert duration>=min_seconds,'Film is too short'
    if max_seconds is not None:assert duration<=max_seconds+.1,'Film is too long'
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'],check=True)
    print(f"Verified {video['width']}x{height}, {data['format']['duration']} seconds, H.264/AAC")

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('path',type=Path);p.add_argument('--height',type=int,default=1080)
    p.add_argument('--fps',type=int);p.add_argument('--min-seconds',type=float);p.add_argument('--max-seconds',type=float)
    args=p.parse_args();verify(args.path,args.height,args.fps,args.min_seconds,args.max_seconds)
