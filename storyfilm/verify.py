import argparse
import json
import subprocess
from pathlib import Path

def verify(path,height=1080):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
    video=next(s for s in data['streams'] if s['codec_type']=='video')
    audio=next(s for s in data['streams'] if s['codec_type']=='audio')
    assert video['height']==height and video['width']==height*16//9, 'Unexpected resolution'
    assert video['codec_name']=='h264' and audio['codec_name']=='aac', 'Unexpected codecs'
    assert float(data['format']['duration'])>1, 'Empty film'
    assert abs(float(video['duration'])-float(audio['duration']))<.3, 'Audio/video durations differ'
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'],check=True)
    print(f"Verified {video['width']}x{height}, {data['format']['duration']} seconds, H.264/AAC")

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('path',type=Path);p.add_argument('--height',type=int,default=1080)
    args=p.parse_args();verify(args.path,args.height)
