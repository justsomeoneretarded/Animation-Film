"""Original rounded vector artwork rasterized directly at 1920 x 1080.

Geometry is authored in 960x540 logical units; every path and stroke is drawn at
2x, not enlarged from an existing low-resolution frame. No reference assets.
"""
import math
import random
from .motion import text_count, send_time, text_finished, prop_count, PHONE_BOUNDS, PHONE_ZOOM
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W,H=1920,1080
S=2
INK='#202534'

@lru_cache(maxsize=64)
def font(size):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','C:/Windows/Fonts/arial.ttf']:
        try:return ImageFont.truetype(p,int(size))
        except OSError:pass
    return ImageFont.load_default(size=int(size))

def wrapped(text,width,size):
    d=ImageDraw.Draw(Image.new('RGB',(1,1)));lines=[];line=''
    for word in text.split():
        test=(line+' '+word).strip()
        if line and d.textlength(test,font=font(size))>width:lines.append(line);line=word
        else:line=test
    return lines+([line] if line else [])

class Draw:
    def __init__(self,im,dy=0,scale=S):self.d=ImageDraw.Draw(im);self.dy=dy;self.scale=scale
    def box(self,b,fill,outline=None,width=1,r=0):
        b=tuple(round((v+(self.dy if i%2 else 0))*self.scale) for i,v in enumerate(b))
        if r:self.d.rounded_rectangle(b,round(r*self.scale),fill=fill,outline=outline,width=max(1,round(width*self.scale)))
        else:self.d.rectangle(b,fill=fill,outline=outline,width=max(1,round(width*self.scale)))
    def ellipse(self,b,fill,outline=None,width=1):self.d.ellipse(tuple(round((v+(self.dy if i%2 else 0))*self.scale) for i,v in enumerate(b)),fill=fill,outline=outline,width=max(1,round(width*self.scale)))
    def line(self,p,fill,width=1):self.d.line([(round(x*self.scale),round((y+self.dy)*self.scale)) for x,y in p],fill=fill,width=max(1,round(width*self.scale)),joint='curve')
    def polygon(self,p,fill):self.d.polygon([(round(x*self.scale),round((y+self.dy)*self.scale)) for x,y in p],fill=fill)
    def text(self,p,text,size=14,fill='#dce5ee',stroke=0):self.d.text((round(p[0]*self.scale),round((p[1]+self.dy)*self.scale)),text,font=font(size*self.scale),fill=fill,stroke_width=round(stroke*self.scale),stroke_fill=INK)
    def path(self,commands,fill,outline=None,width=1):
        pts=[];cur=(0,0)
        for c in commands:
            if c[0]=='M':cur=tuple(c[1:]);pts.append(cur)
            elif c[0]=='L':cur=tuple(c[1:]);pts.append(cur)
            elif c[0]=='C':
                a=cur;b=c[1:3];cc=c[3:5];end=c[5:7]
                for j in range(1,19):
                    t=j/18;v=1-t;pts.append((v**3*a[0]+3*v*v*t*b[0]+3*v*t*t*cc[0]+t**3*end[0],v**3*a[1]+3*v*v*t*b[1]+3*v*t*t*cc[1]+t**3*end[1]))
                cur=tuple(end)
        if fill:self.polygon(pts,fill)
        if outline:self.line(pts+[pts[0]] if fill else pts,outline,width)

def capsule(d,a,b,width,fill,outline=INK):
    if outline:
        d.line([a,b],outline,width+4)
        for x,y in (a,b):d.ellipse((x-width/2-2,y-width/2-2,x+width/2+2,y+width/2+2),outline)
    d.line([a,b],fill,width)
    for x,y in (a,b):d.ellipse((x-width/2,y-width/2,x+width/2,y+width/2),fill)

def jointed(d,points,width,fill):
    # One continuous silhouette eliminates mechanical rings at elbows/knees.
    for color,w in [(INK,width+4),(fill,width)]:
        d.line(points,color,w)
        for x,y in points:d.ellipse((x-w/2,y-w/2,x+w/2,y+w/2),color)


def glow(im,xy,color,radius=80,strength=80):
    layer=Image.new('RGBA',im.size);d=Draw(layer);x,y=xy
    d.ellipse((x-radius,y-radius,x+radius,y+radius),(*color,strength))
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius*S*.38)))

def smooth(a,b,t):
    t=max(0,min(1,t));return a+(b-a)*t*t*(3-2*t)

def gradient(size,top,bottom):
    im=Image.new('RGBA',size);d=ImageDraw.Draw(im)
    for y in range(size[1]):
        f=y/max(1,size[1]-1);d.line((0,y,size[0],y),fill=tuple(round(a+(b-a)*f) for a,b in zip(top,bottom))+(255,))
    return im

def insert_shot(im,scene,gender,t,progress):
    """Hand-and-object inserts communicate an action, not a decorative zoom."""
    im=im.filter(ImageFilter.GaussianBlur(18));veil=Image.new('RGBA',im.size,(12,22,33,70));im.alpha_composite(veil)
    zoom=PHONE_ZOOM if scene['action'] in {'phone','send','receive','dismiss'} else 1.
    if zoom!=1:im=im.resize((round(W*zoom),round(H*zoom)),Image.Resampling.LANCZOS)
    d=Draw(im,scale=S*zoom);skin='#e5d7bf';sleeve='#7f8d93' if gender=='male' else '#a18e98'
    text=scene.get('prop_text','')
    if scene['action'] in {'phone','send','receive','dismiss'}:
        capsule(d,(320,558),(375,370),51,sleeve)
        capsule(d,(640,552),(586,365),51,sleeve)
        d.ellipse((355,289,405,413),skin,INK,3);d.ellipse((551,284,604,417),skin,INK,3)
        d.box(PHONE_BOUNDS,'#182029','#899397',3,r=22)
        d.box((399,78,561,442),'#e9e9e1',r=16)
        d.box((455,84,505,92),'#20272c',r=4)
        received=scene['action']=='receive';sent=scene['action']=='send' and t>=send_time(text,scene.get('pretyped',False))
        status='RECEIVED' if received else 'DELETED' if scene['action']=='dismiss' and t>=.55 else 'DRAFT' if not sent else 'MESSAGE'
        d.text((413,111 if scene.get('contact') else 116),scene.get('contact') or status,13,'#526367')
        if scene.get('contact'):d.text((413,132),status,9,'#677775')
        d.line([(410,148),(550,148)],'#bbc6c2',1)
        chars=prop_count(scene,t);typed=text[:chars].replace('|',' ')
        if scene['action']=='dismiss' and t>.55:typed=''
        lines=wrapped(typed,272,32)
        if typed:
            bottom=min(365,195+len(lines)*23)
            d.box((408,175,552,bottom),'#bdcfc6',r=9)
            for j,line in enumerate(lines[:7]):d.text((417,187+j*23),line,16,'#253c43')
        if not received:
            d.box((477,397,550,427),'#4f7c79' if chars or sent else '#aab4b0',r=9)
            d.text((488,404),'SENT' if sent else 'SEND',13,'#f1f3e6')
            if not sent and ((scene['action']=='dismiss' and t<.65) or (scene['action']!='dismiss' and chars<len(text))):
                for row in range(2):
                    for key in range(7):d.box((411+key*20,340+row*21,426+key*20,355+row*21),'#c6cbc6',r=3)
        tap=max(0,1-abs(t-(.55 if scene['action']=='dismiss' else send_time(text,scene.get('pretyped',False))))/.20) if scene['action'] in {'send','dismiss'} else 0
        typing=math.sin(t*17)*3 if chars<len(text) and t>.35 and not received else 0
        thumb_x=566-(25 if scene['action']=='dismiss' else 49)*tap;thumb_y=358+(9 if scene['action']=='dismiss' else 53)*tap+typing
        capsule(d,(586,388),(thumb_x,thumb_y),24,skin)
        capsule(d,(375,373),(404,323),23,skin)
    else:
        d.box((169,149,791,459),'#b89d7f','#394755',3,r=16)
        d.path([('M',237,181),('L',696,166),('L',731,437),('L',214,442),('L',237,181)],'#f1e7ce','#8b877a',2)
        for yy in range(218,419,28):d.line([(247,yy),(690,yy-8)],'#c5c8b4',1)
        chars=text_count(text,t,'write')
        chunks=text[:chars].split('|')
        for j,line in enumerate(chunks):
            for k,wrapped_line in enumerate(wrapped(line,810,34)):
                d.text((268,229+j*65+k*25),wrapped_line,17,'#48545a')
        if not text:
            # Unspecified handwriting stays abstract; never invent a quoted goal.
            for j in range(4):
                amount=max(0,min(1,progress*5-j))
                if amount:d.line([(269,233+j*28),(269+amount*(220-j*19),230+j*28)],'#69726c',2)
        written=text[:chars].replace('|',' ')
        pen_lines=wrapped(written,810,34)
        last=pen_lines[-1] if pen_lines else ''
        measured=ImageDraw.Draw(im).textlength(last,font=font(34))/S
        retreat=smooth(0,1,(t-text_finished(text,'write')-.2)/.5) if text else 0
        tipx=min(690,268+measured)+retreat*35;tipy=247+max(0,len(pen_lines)-1)*25+retreat*95
        px=tipx+13;py=tipy-49
        capsule(d,(744,542),(px+79,py+50),54,sleeve)
        d.ellipse((px-9,py-5,px+83,py+67),skin,INK,3)
        d.line([(px+26,py-42),(px-8,py+39)],'#e0ad69',8)
        d.line([(px-8,py+39),(tipx,tipy)],'#33404b',3)
        capsule(d,(px+48,py+30),(px+9,py+5),22,skin)
        capsule(d,(218,550),(265,399),52,sleeve)
        d.ellipse((243,363,309,439),skin,INK,3)
    if zoom!=1:
        left=round((im.width-W)/2);top=round(520*zoom-H/2)
        im=im.crop((left,top,left+W,top+H))
    return im


# Public rendering entry points always use the shared v4 staging engine.
def character(*args,**kwargs):
    from .staging import actor
    return actor(*args,**kwargs)

def frame(*args,**kwargs):
    from .staging import stage
    return stage(*args,**kwargs)

def background(location,day="night"):
    from .staging import set_design
    return set_design(location,day)
