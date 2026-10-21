"""Original rounded vector artwork rasterized directly at 1920 x 1080.

Geometry is authored in 960x540 logical units; every path and stroke is drawn at
2x, not enlarged from an existing low-resolution frame. No reference assets.
"""
import math
import random
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
    def __init__(self,im,dy=0):self.d=ImageDraw.Draw(im);self.dy=dy
    def box(self,b,fill,outline=None,width=1,r=0):
        b=tuple(round((v+(self.dy if i%2 else 0))*S) for i,v in enumerate(b))
        if r:self.d.rounded_rectangle(b,round(r*S),fill=fill,outline=outline,width=max(1,round(width*S)))
        else:self.d.rectangle(b,fill=fill,outline=outline,width=max(1,round(width*S)))
    def ellipse(self,b,fill,outline=None,width=1):self.d.ellipse(tuple(round((v+(self.dy if i%2 else 0))*S) for i,v in enumerate(b)),fill=fill,outline=outline,width=max(1,round(width*S)))
    def line(self,p,fill,width=1):self.d.line([(round(x*S),round((y+self.dy)*S)) for x,y in p],fill=fill,width=max(1,round(width*S)),joint='curve')
    def polygon(self,p,fill):self.d.polygon([(round(x*S),round((y+self.dy)*S)) for x,y in p],fill=fill)
    def text(self,p,text,size=14,fill='#dce5ee',stroke=0):self.d.text((round(p[0]*S),round((p[1]+self.dy)*S)),text,font=font(size*S),fill=fill,stroke_width=round(stroke*S),stroke_fill=INK)
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
    d=Draw(im);skin='#e5d7bf';sleeve='#7f8d93' if gender=='male' else '#a18e98'
    text=scene.get('prop_text','')
    if scene['action'] in {'phone','send','receive'}:
        # A held phone, a moving thumb, and progressive message entry.
        capsule(d,(310,558),(364,369),57,sleeve)
        capsule(d,(654,552),(610,360),57,sleeve)
        d.ellipse((349,285,409,409),skin,INK,3);d.ellipse((565,280,628,413),skin,INK,3)
        d.box((375,90,598,450),'#17283b','#9dabb4',4,r=24)
        d.box((388,109,585,429),'#e4e7df' if text else '#496a85',r=15)
        d.box((451,100,521,108),'#263a50',r=3)
        d.text((409,139),('RECEIVED' if scene.get('action')=='receive' else 'MESSAGE') if text else 'FOR YOU',14,'#476473' if text else '#e0ece9')
        if text:
            d.line([(402,171),(572,171)],'#adbbb8',1)
            chars=len(text) if scene.get('action')=='receive' else round(len(text)*smooth(0,1,progress*1.8))
            typed=text[:chars].replace('|',' ')
            lines=wrapped(typed,285,28)
            d.box((402,211,572,238+len(lines)*21),'#bacfc8',r=11)
            for j,line in enumerate(lines):d.text((412,223+j*21),line,14,'#263e4d')
            if progress>.72 and scene.get('action')=='send':
                d.box((485,373,567,405),'#4f7c79',r=11);d.text((501,380),'SENT',13,'#f1f3e6')
        else:
            for k in range(3):
                y=186+k*91-(t*15)%65
                d.box((402,y,570,y+69),['#7996a1','#a5b5b4','#b9a893'][k%3],r=8)
                d.ellipse((420,y+13,448,y+41),'#dce3d7')
                d.line([(462,y+23),(551,y+23)],'#e2e7da',3)
                d.line([(419,y+53),(544,y+53)],'#e2e7da',2)
        thumb_x=574+math.sin(t*2)*3;thumb_y=348-smooth(0,48,progress)
        capsule(d,(605,383),(thumb_x,thumb_y),27,skin)
        capsule(d,(369,369),(397,319),25,skin)
    else:
        d.box((169,149,791,459),'#b89d7f','#394755',3,r=16)
        d.path([('M',237,181),('L',696,166),('L',731,437),('L',214,442),('L',237,181)],'#f1e7ce','#8b877a',2)
        for yy in range(218,419,28):d.line([(247,yy),(690,yy-8)],'#c5c8b4',1)
        chars=round(len(text)*smooth(0,1,progress*1.4))
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
        tipx=min(690,268+measured);tipy=247+max(0,len(pen_lines)-1)*25
        px=tipx+13;py=tipy-49
        capsule(d,(744,542),(px+79,py+50),54,sleeve)
        d.ellipse((px-9,py-5,px+83,py+67),skin,INK,3)
        d.line([(px+26,py-42),(px-8,py+39)],'#e0ad69',8)
        d.line([(px-8,py+39),(tipx,tipy)],'#33404b',3)
        capsule(d,(px+48,py+30),(px+9,py+5),22,skin)
        capsule(d,(218,550),(265,399),52,sleeve)
        d.ellipse((243,363,309,439),skin,INK,3)
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
