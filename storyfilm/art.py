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
    def __init__(self,im):self.d=ImageDraw.Draw(im)
    def box(self,b,fill,outline=None,width=1,r=0):
        b=tuple(round(v*S) for v in b)
        if r:self.d.rounded_rectangle(b,round(r*S),fill=fill,outline=outline,width=max(1,round(width*S)))
        else:self.d.rectangle(b,fill=fill,outline=outline,width=max(1,round(width*S)))
    def ellipse(self,b,fill,outline=None,width=1):self.d.ellipse(tuple(round(v*S) for v in b),fill=fill,outline=outline,width=max(1,round(width*S)))
    def line(self,p,fill,width=1):self.d.line([(round(x*S),round(y*S)) for x,y in p],fill=fill,width=max(1,round(width*S)),joint='curve')
    def polygon(self,p,fill):self.d.polygon([(round(x*S),round(y*S)) for x,y in p],fill=fill)
    def text(self,p,text,size=14,fill='#dce5ee',stroke=0):self.d.text((round(p[0]*S),round(p[1]*S)),text,font=font(size*S),fill=fill,stroke_width=round(stroke*S),stroke_fill=INK)
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

@lru_cache(maxsize=18)
def background(location,day='night'):
    dawn=day in {'dawn','day'}
    im=gradient((W,H),(30,44,67) if dawn else (12,20,35),(155,135,121) if dawn else (35,48,66))
    d=Draw(im);rng=random.Random(34)
    if location in {'bedroom','desk','gym'}:
        d.box((0,0,960,410),'#354352' if dawn else '#253344')
        d.polygon([(0,0),(105,55),(105,410),(0,475)],'#2b3949' if dawn else '#1a293b')
        d.box((105,57,920,410),None,'#4b5865',2)
        for x in range(140,920,95):d.line([(x,59),(x,409)],'#3d4a58' if dawn else '#2b3b4d')
        d.box((0,410,960,540),'#3e3c42' if dawn else '#262b36')
        for y in (428,461,501):d.line([(0,y),(960,y)],'#55505a' if dawn else '#353944')
        for x in range(-200,1300,130):d.line([(480+(x-480)*.55,410),(x,540)],'#4a4650' if dawn else '#323744')
        # Deep window reveal, city, curtains and sill.
        d.box((145,83,337,284),'#172232','#657184',3,r=7)
        d.box((156,94,326,273),'#9cabb7' if dawn else '#152c49',r=3)
        for x in range(160,320,25):
            top=rng.randint(180,230);d.box((x,top,x+21,270),'#687b8e' if dawn else '#233f5a')
            for y in range(top+7,265,17):d.box((x+5,y,x+9,y+6),'#bdaf87' if dawn else '#798582')
        d.ellipse((281,115,304,138),'#ffe2a9' if dawn else '#b9d7e7')
        d.line([(241,94),(241,273)],'#687785',4);d.line([(155,183),(325,183)],'#687785',3)
        for xx in (130,329):
            d.path([('M',xx,75),('C',xx+16,115,xx+11,215,xx+22,280),('L',xx-8,284),('C',xx-12,201,xx-17,123,xx-10,75)],'#536174', '#202b3b',2)
            d.line([(xx,87),(xx+4,265)],'#748091',2)
        d.box((137,280,346,289),'#8a8c91',r=3)
        # Framed print and shelves give rooms depth.
        d.box((744,99,832,192),'#1b293a','#7e7f83',4,r=3)
        d.ellipse((763,117,810,164),'#b09c87');d.polygon([(750,185),(785,141),(826,185)],'#4c686c')
        d.box((510,132,685,141),'#8a7164',r=3)
        for j in range(7):
            x=518+j*19;hh=rng.randint(24,48);d.box((x,132-hh,x+13,131),['#9e7774','#79958f','#b5a486'][j%3],r=2)
        # Potted plant.
        d.path([('M',850,390),('C',858,345,845,315,867,279)],None,'#739188',4)
        for x,y,sg in [(854,354,-1),(856,333,1),(855,313,-1),(864,296,1)]:
            d.path([('M',x,y),('C',x+sg*36,y-30,x+sg*39,y+4,x,y+6)],'#759789','#294d4b',1)
        d.path([('M',832,382),('L',878,382),('L',872,418),('L',839,418),('L',832,382)],'#a17e6d','#4c4445',2)
        if location=='bedroom':
            d.ellipse((352,390,858,460),'#1e2734')
            d.box((405,273,842,404),'#4c5365','#1e2837',3,r=24)
            d.box((416,310,836,392),'#80939c','#243544',3,r=20)
            d.box((423,307,548,348),'#d8d4ca','#8e969b',2,r=20)
            d.path([('M',529,323),('C',620,311,755,316,836,329),('L',836,397),('C',740,414,625,395,535,397),('L',529,323)],'#64798c','#344959',2)
            for x in (563,622,681,740,799):d.path([('M',x,326),('C',x-10,355,x+6,378,x-4,396)],None,'#8193a1',1)
            for x in (423,816):d.box((x,399,x+10,433),'#775e54',r=2)
            d.box((300,355,374,422),'#66594f','#292e38',2,r=5)
            d.box((297,348,378,359),'#96816b',r=3)
            d.box((313,324,363,346),'#182533','#66798a',2,r=5)
            d.text((320,331),'02:17',10,'#b8c9ce')
            glow(im,(590,260),(106,163,204),140,35)
        elif location=='desk':
            d.box((450,294,535,449),'#586877','#253444',3,r=18)
            d.box((427,370,562,387),'#687782','#253444',2,r=10)
            for x in (443,549):d.line([(x,385),(x,461)],'#283342',7)
            # The desktop foreground is drawn after the body so it occludes legs.
            d.line([(737,359),(746,271),(790,243)],'#9d9b90',5)
            d.path([('M',771,226),('C',796,213,818,237,816,255),('L',765,255),('C',759,244,761,233,771,226)],'#c0a47b','#433e3d',2)
            glow(im,(731,334),(255,200,124),132,65)
        else:
            d.box((619,106,871,391),'#364c5c','#a0b0b8',4,r=8)
            d.line([(745,108),(745,388)],'#6f8799',3)
            for x in (164,321):
                d.line([(x,205),(x,430)],'#a0a7aa',8)
                d.box((x-16,426,x+27,435),'#71818d',r=4)
            for x in (106,346):d.ellipse((x,264,x+48,312),'#172632','#647784',4)
            d.line([(115,288),(385,288)],'#a7b4bd',6)
            d.box((346,416,697,460),'#293d4b',r=12)
    else:
        # Layered skyline with lit windows, deliberate foreground silhouette.
        for layer,base,col in [(0,354,'#5f7184' if dawn else '#23374d'),(1,400,'#475b70' if dawn else '#1b2c40')]:
            for x in range(-30,1000,68):
                top=rng.randint(160+layer*40,285+layer*30);d.box((x,top,x+63,base),col)
                for xx in range(x+10,x+54,17):
                    for yy in range(top+13,base-10,24):
                        if rng.random()>.45:d.box((xx,yy,xx+6,yy+10),'#cfb78d' if dawn else '#667570')
        d.ellipse((750,87,795,132),'#f6d5ad' if dawn else '#c9dce4')
        glow(im,(773,109),(255,188,120) if dawn else (137,191,222),110,65)
        d.box((0,403,960,540),'#6f777a' if dawn else '#354554')
        d.polygon([(0,435),(960,435),(960,540),(0,540)],'#4c5963' if dawn else '#263544')
        d.line([(0,435),(960,435)],'#a1a3a0' if dawn else '#586978',3)
        for x in range(-100,1100,180):d.line([(x,436),(x-90,540)],'#566570' if dawn else '#344858',1)
        if location in {'street','park'}:
            for x in (128,830):
                d.box((x-6,166,x+6,434),'#2f424f','#74858a',1,r=5)
                d.path([('M',x-24,171),('L',x-19,139),('L',x+19,139),('L',x+24,171),('L',x-24,171)],'#ffe3ad','#394b58',3)
                glow(im,(x,182),(255,201,133),92,45 if dawn else 80)
        if location=='street':
            d.box((365,248,657,403),'#314758','#829094',2,r=4)
            d.box((385,268,510,368),'#879391' if dawn else '#597378','#a3a9a0',3,r=3)
            d.box((528,268,638,403),'#182f41','#9b9e96',3,r=3)
            d.ellipse((618,333,624,339),'#d5bf93')
            d.box((358,235,665,256),'#b3967e',r=4)
            d.text((417,238),'SLOW MORNINGS',12,'#273b48')
            d.box((0,482,960,540),'#34434f' if dawn else '#1d2b3a')
            for x in range(20,1000,180):d.box((x,511,x+93,514),'#9ca5a3' if dawn else '#627582',r=1)
        elif location=='park':
            for x in (32,890):
                d.path([('M',x-14,435),('C',x-8,365,x-7,304,x-3,241),('L',x+13,241),('C',x+15,315,x+20,375,x+24,435)],'#4f514b','#293d40',2)
                for dx,dy,r in [(-35,0,66),(25,-40,76),(4,-90,61),(60,9,55)]:
                    d.ellipse((x+dx-r,235+dy-r,x+dx+r,235+dy+r),'#54766c' if dawn else '#284c49','#294b48',2)
            for yy in (291,314,337):d.box((321,yy,668,yy+16),'#a8886c','#4b4d4c',2,r=5)
            d.box((311,355,678,375),'#b29678','#4d514e',3,r=7)
            for xx in (341,645):
                d.line([(xx,374),(xx-8,440)],'#354d53',9)
                d.line([(xx,289),(xx,365)],'#354d53',6)
            d.path([('M',0,439),('C',180,407,212,415,303,436),('L',303,460),('L',0,473)],'#3c6358' if dawn else '#274b46')
        else:
            d.box((0,377,960,426),'#7c858c' if dawn else '#546576','#293a4a',2)
            d.box((0,373,960,385),'#bac1be' if dawn else '#8b9ba5',r=3)
            d.box((0,426,960,540),'#61666b' if dawn else '#3c4b5b')
            for x in range(-100,1200,155):d.line([(480+(x-480)*.6,426),(x,540)],'#7a7d7b' if dawn else '#536273',1)
            d.box((76,245,220,376),'#485b6a','#87979f',3,r=5)
            for y in range(264,348,14):d.line([(92,y),(202,y)],'#2d414f',3)
    return im


def character(im,x,floor,t,gender='male',action='idle',emotion='neutral',scale=1.,shadow=False,progress=.5):
    """Rounded clothed rig: articulated thick limbs, shaded head and independent face.

    Local floor anchor is (180,432), so seated feet and planted walk cycles share
    exact scene contact coordinates. t is animation time, progress is shot action.
    """
    layer=Image.new('RGBA',(720,940));d=Draw(layer)
    sad=emotion in {'sad','tired','worried'}
    breathe=math.sin(t*1.8)*1.8
    sitting=action in {'sit','phone','write'}
    hip=304 if sitting else 310
    bob=math.sin(t*1.8)*1.2
    if action=='walk':bob=-abs(math.sin(t*3.6))*5
    top=194+bob+breathe
    hoodie='#7e9aab' if gender=='male' else '#ac8f91'
    shade='#567488' if gender=='male' else '#806b7b'
    light='#aec2c7' if gender=='male' else '#d4b0ac'
    pants='#344758' if gender=='male' else '#4e485e'
    skin='#e5d7bf';skinshade='#bca78f';edge='#293340'
    # Feet move on stance arcs rather than sliding as rigid sticks.
    feet=[]
    for j in range(2):
        if sitting:
            knee=(180+j*35,345);foot=(174+j*43,425)
        elif action=='walk':
            phase=t*3.6+j*math.pi;ankle=math.sin(phase)*38
            foot=(161+j*38+ankle,425-max(0,math.cos(phase))*24)
            knee=(161+j*38+ankle*.45,363-max(0,math.cos(phase))*12)
        else:
            knee=(157+j*47,365);foot=(151+j*57,426)
        capsule(d,(157+j*46,hip),knee,29,pants)
        capsule(d,knee,foot,27,pants)
        fx,fy=foot;d.box((fx-18,fy-10,fx+26,fy+9),'#23323e',edge,2,r=12)
        d.line([(fx-15,fy+5),(fx+23,fy+5)],'#a3adb0',3);feet.append(foot)
    # A rounded neck joins the head to the hoodie.
    d.box((158,top-39,203,top+6),skin,edge,2,r=17)
    # Rounded hoodie silhouette, shoulders, waist and soft cloth folds.
    d.path([('M',146,top-12),('C',130,top-5,116,top+4,116,top+30),('C',118,top+65,123,hip-22,125,hip),('C',149,hip+18,202,hip+18,231,hip),('C',235,hip-30,238,top+51,241,top+30),('C',243,top+5,222,top-8,208,top-12),('L',146,top-12)],hoodie,edge,3)
    d.path([('M',126,top+30),('C',137,top+53,135,hip-5,146,hip+5),('C',171,hip+14,213,hip+10,231,hip),('L',233,hip-18),('C',193,hip-6,153,hip-9,146,top+27)],shade)
    d.path([('M',142,top+2),('C',150,top-14,201,top-15,217,top+2),('C',211,top+25,151,top+26,142,top+2)],shade,edge,2)
    d.path([('M',150,top-4),('C',159,top+6,197,top+7,208,top-4)],None,light,3)
    for xx in (167,192):d.line([(xx,top+15),(xx-2,top+41)],light,2);d.ellipse((xx-4,top+38,xx,top+44),'#d3d5cb')
    d.path([('M',150,hip-30),('C',160,hip-42,196,hip-42,209,hip-30),('L',206,hip-12),('L',151,hip-12),('L',150,hip-30)],shade,None)
    d.line([(148,hip-30),(157,hip-18)],edge,1);d.line([(209,hip-30),(201,hip-18)],edge,1)
    # Arms and palms are independent; gesture curves follow the current action.
    swing=math.sin(t*3.6)*23 if action=='walk' else math.sin(t*1.7)*2
    if action=='phone':
        lift=smooth(12,0,progress*4)
        left=[(126,top+19),(112,top+66),(166,top+58+lift)]
        right=[(229,top+19),(247,top+65),(206,top+51+lift)]
    elif action=='write':
        left=[(126,top+20),(119,top+70),(167,top+81)]
        right=[(229,top+18),(249,top+63),(221+math.sin(t*5)*5,top+79)]
    elif action=='reach':
        lift=smooth(0,1,progress*2)
        left=[(126,top+20),(109-18*lift,top+69-50*lift),(112-20*lift,top+96-105*lift)]
        right=[(229,top+20),(250+9*lift,top+63-55*lift),(246+22*lift,top+91-120*lift)]
    elif action=='exercise':
        lift=(math.sin(t*1.7)+1)*26
        left=[(126,top+20),(102,top+40-lift),(93,top+10-lift)]
        right=[(229,top+20),(253,top+40-lift),(264,top+10-lift)]
    elif sitting:
        left=[(126,top+20),(113,top+73),(167,hip+18)]
        right=[(229,top+20),(246,top+73),(204,hip+18)]
    else:
        left=[(126,top+20),(112+swing*.5,top+69),(116+swing,top+110)]
        right=[(229,top+20),(246-swing*.5,top+69),(241-swing,top+110)]
    for arm in (left,right):
        capsule(d,arm[0],arm[1],27,hoodie)
        capsule(d,arm[1],arm[2],25,hoodie)
        ax,ay=arm[2];d.ellipse((ax-14,ay-5,ax+14,ay+21),skin,edge,2)
        d.path([('M',ax-8,ay+7),('C',ax-4,ay+11,ax+3,ay+11,ax+7,ay+6)],None,skinshade,1)
    # Props match palms; animated thumb and pen movement gives readable contact.
    if action=='phone':
        py=top+25+smooth(12,0,progress*4)
        d.box((169,py,209,py+64),'#1e2d40','#a2b1b7',2,r=7)
        d.box((174,py+6,204,py+55),'#82aec0',r=3)
        d.box((183,py+3,196,py+5),'#172c3e',r=1)
        for j in range(3):
            yy=py+13+j*13+(t*7)%9;d.box((178,yy,200,yy+7),'#b6d1d4' if j%2 else '#60899f',r=2)
        d.ellipse((196+math.sin(t*4)*2,py+37,211+math.sin(t*4)*2,py+51),skin,edge,1)
    if action=='write':
        d.path([('M',156,top+87),('L',238,top+87),('L',252,top+100),('L',153,top+100),('L',156,top+87)],'#f0e4c9','#7d827d',1)
        for yy in range(3):d.line([(165,top+91+yy*3),(229,top+91+yy*3)],'#a0a9a0',.6)
        px,py=right[-1];d.line([(px-4,py-16),(px+7,py+16)],'#f4bf75',4);d.ellipse((px-9,py-2,px+9,py+14),skin,edge,1)
    if action=='exercise':
        y=left[-1][1]+9;d.line([(62,y),(295,y)],'#bcc9cc',6)
        for xx in (62,277):d.box((xx,y-22,xx+20,y+22),'#324b5d','#899ba5',2,r=6)
    # Expressive head is shaded separately, so it can tilt over the shoulders.
    head=Image.new('RGBA',(400,400));hd=Draw(head)
    hx,hy=100,96
    if gender=='female':
        hd.path([('M',29,86),('C',19,25,55,5,103,8),('C',161,7,186,44,177,103),('C',180,135,187,157,175,170),('C',144,184,60,181,24,166),('C',15,149,27,115,29,86)],'#34313d',edge,3)
        hd.path([('M',36,59),('C',47,24,74,18,108,19),('C',144,22,165,43,166,78)],None,'#6d5960',8)
    hd.ellipse((29,24,172,171),skinshade,edge,3)
    hd.ellipse((32,25,166,162),skin)
    hd.ellipse((43,29,146,141),'#eadfc9')
    hd.path([('M',45,53),('C',58,30,98,29,116,35)],None,'#f4e9d5',5)
    # Eyelid openness, pupil direction and eyebrows communicate different states.
    blink=(t%4.15)<.16 or (t%7.1)<.12
    if action=='sleep':blink=True
    ey=105 if sad else 99
    gaze_x=math.sin(t*.7)*2+(3 if action in {'phone','write'} else 0)
    gaze_y=5 if action in {'phone','write'} or sad else 0
    for ex in (70,130):
        if sad:
            hd.ellipse((ex-24,ey-14,ex+23,ey+30),'#baa7a1')
            hd.path([('M',ex-22,ey+20),('C',ex-13,ey+32,ex+14,ey+33,ex+23,ey+16)],None,'#8a7c80',2)
        if blink:
            hd.path([('M',ex-22,ey),('C',ex-9,ey+9,ex+10,ey+9,ex+22,ey-1)],None,edge,3)
        else:
            hd.ellipse((ex-23,ey-23,ex+23,ey+25),'#faf3df',edge,2)
            if emotion=='tired':hd.path([('M',ex-23,ey-8),('C',ex-10,ey-20,ex+9,ey-20,ex+22,ey-10),('L',ex+21,ey-21),('L',ex-20,ey-22)],skinshade)
            hd.ellipse((ex-7+gaze_x,ey-5+gaze_y,ex+8+gaze_x,ey+13+gaze_y),edge)
            hd.ellipse((ex-3+gaze_x,ey-4+gaze_y,ex+1+gaze_x,ey+gaze_y),'#ffffff')
            if emotion=='worried':hd.line([(ex-18,ey+15),(ex-13,ey+18)],'#bba2a0',1)
        if gender=='female':
            side=-1 if ex<100 else 1
            for j in range(2):hd.line([(ex+side*(20-j*2),ey-13-j*4),(ex+side*(28-j*2),ey-19-j*4)],edge,2)
    if emotion in {'sad','worried'}:
        hd.path([('M',47,74),('C',58,76,73,68,86,64)],None,edge,4)
        hd.path([('M',113,64),('C',125,68,141,76,153,74)],None,edge,4)
    elif emotion=='determined':
        hd.line([(49,70),(86,81)],edge,4);hd.line([(113,81),(150,70)],edge,4)
    elif emotion=='happy':
        hd.path([('M',48,72),('C',60,63,74,63,87,70)],None,edge,3)
        hd.path([('M',113,70),('C',125,63,141,63,153,72)],None,edge,3)
    else:
        hd.line([(49,73),(86,75)],edge,3);hd.line([(113,75),(151,73)],edge,3)
    hd.path([('M',98,115),('C',94,121,95,125,102,125)],None,skinshade,2)
    if emotion=='happy':hd.path([('M',83,141),('C',94,151,108,151,120,138)],None,edge,3)
    elif emotion=='worried':hd.ellipse((92,139,109,150),edge)
    elif sad:hd.path([('M',85,147),('C',96,139,108,140,118,146)],None,edge,3)
    else:hd.path([('M',85,143),('C',96,145,109,145,119,142)],None,edge,2)
    if emotion=='sad' and progress>.32 and progress<.72:
        tear=smooth(0,24,(progress-.32)/.4);hd.ellipse((144,120+tear,148,129+tear),'#9ac1d0')
    if gender=='female':
        hd.path([('M',27,82),('C',25,37,45,15,91,13),('C',116,12,158,24,170,60),('L',170,96),('C',150,83,136,66,128,42),('C',97,66,56,47,27,82)],'#3e3541',edge,2)
        hd.path([('M',39,54),('C',65,29,102,25,129,34)],None,'#7c6167',3)
        hd.path([('M',163,83),('C',165,123,170,149,159,166)],None,'#6c545f',5)
    tilt=(-7 if sad else 2)+math.sin(t*1.2)*2.5+math.sin(progress*math.pi*2)*3
    if action in {'phone','write'}:tilt=-10+math.sin(t*.9)*2
    if action=='reach':tilt=smooth(-6,6,progress)
    head=head.rotate(tilt,resample=Image.Resampling.BICUBIC,expand=False)
    layer.alpha_composite(head,(160,round((top-187)*S)))
    if action=='sleep':layer=layer.rotate(81,resample=Image.Resampling.BICUBIC,expand=True)
    if scale!=1:layer=layer.resize((round(layer.width*scale),round(layer.height*scale)),Image.Resampling.LANCZOS)
    dest=(round(x*S-layer.width/2),round(floor*S-432*S*scale))
    if action=='sleep':dest=(round(x*S-layer.width/2),round(floor*S-layer.height*.62))
    im.alpha_composite(layer,dest)


def foreground(im,location):
    d=Draw(im)
    if location=='desk':
        d.path([('M',306,378),('L',810,378),('L',867,400),('L',290,400),('L',306,378)],'#ba9978','#393e43',2)
        d.box((290,399,867,411),'#7a6558','#343b42',2,r=3)
        for x in (320,827):d.path([('M',x,411),('L',x+12,411),('L',x+5,487),('L',x-8,487),('L',x,411)],'#65564e','#333c44',2)
        d.box((681,354,715,380),'#ccd1c7','#435663',2,r=5)
        d.path([('M',714,359),('C',734,352,734,376,714,374)],None,'#cbd1c6',4)
        d.path([('M',692,348),('C',682,338,702,333,692,320)],None,'#98a8aa',1)

def insert_shot(im,scene,gender,t,progress):
    """Hand-and-object inserts communicate an action, not a decorative zoom."""
    im=im.filter(ImageFilter.GaussianBlur(18));veil=Image.new('RGBA',im.size,(12,22,33,70));im.alpha_composite(veil)
    d=Draw(im);skin='#e5d7bf';sleeve='#7e9aab' if gender=='male' else '#ac8f91'
    text=scene.get('prop_text','')
    if scene['action']=='phone':
        # A held phone, a moving thumb, and progressive message entry.
        capsule(d,(310,558),(364,369),57,sleeve)
        capsule(d,(654,552),(610,360),57,sleeve)
        d.ellipse((349,285,409,409),skin,INK,3);d.ellipse((565,280,628,413),skin,INK,3)
        d.box((375,90,598,450),'#17283b','#9dabb4',4,r=24)
        d.box((388,109,585,429),'#e4e7df' if text else '#496a85',r=15)
        d.box((451,100,521,108),'#263a50',r=3)
        d.text((409,139),'MESSAGE' if text else 'FOR YOU',14,'#476473' if text else '#e0ece9')
        if text:
            d.line([(402,171),(572,171)],'#adbbb8',1)
            chars=round(len(text)*smooth(0,1,progress*1.8))
            typed=text[:chars].replace('|',' ')
            lines=wrapped(typed,285,28)
            d.box((402,211,572,238+len(lines)*21),'#bacfc8',r=11)
            for j,line in enumerate(lines):d.text((412,223+j*21),line,14,'#263e4d')
            if progress>.72:
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
        if not text:text='One thing at a time.'
        chars=round(len(text)*smooth(0,1,progress*1.4))
        chunks=text[:chars].split('|')
        for j,line in enumerate(chunks):
            for k,wrapped_line in enumerate(wrapped(line,810,34)):
                d.text((268,229+j*65+k*25),wrapped_line,17,'#48545a')
        px=420+min(195,progress*220);py=287+math.sin(t*3)*3
        capsule(d,(744,542),(px+79,py+50),54,sleeve)
        d.ellipse((px-9,py-5,px+83,py+67),skin,INK,3)
        d.line([(px+26,py-42),(px-8,py+39)],'#e0ad69',8)
        d.line([(px-8,py+39),(px-13,py+49)],'#33404b',3)
        capsule(d,(px+48,py+30),(px+9,py+5),22,skin)
        capsule(d,(218,550),(265,399),52,sleeve)
        d.ellipse((243,363,309,439),skin,INK,3)
    return im


def frame(scene,gender,title,t,duration,index,total,subtitle=''):
    progress=t/max(.01,duration)
    day=scene.get('time','dawn' if index>=total*.65 else 'night')
    im=background(scene['location'],day).copy();d=Draw(im)
    act=scene['action'];location=scene['location']
    # Three actual compositions per beat; each cut has its own acting interval.
    cut=min(2,int(progress*3));local=(progress*3)%1
    if act=='walk':
        # Full cycle advances ~60 units / step; horizontal progression is bounded
        # to the street while background movement supplies the longer walk.
        x=350+min(t*24,270);floor=463;scale=.84
    elif location=='park' and act in {'sit','phone'}:x=493;floor=474;scale=.90
    elif location=='desk':x=505;floor=520;scale=.94
    elif location=='bedroom' and act in {'sit','phone'}:x=584;floor=476;scale=.87
    elif act=='sleep':x=620;floor=362;scale=.76
    else:x=495;floor=468;scale=.88
    # Contact shadow is soft, anchored to the feet or furniture.
    shadow=Image.new('RGBA',im.size);sd=Draw(shadow)
    sd.ellipse((x-64,floor-8,x+65,floor+12),(9,18,27,105));im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(9)))
    character(im,x,floor,t,gender,act,scene['emotion'],scale,False,progress)
    foreground(im,location)
    # Window rain early in the story; leaves and light later, never over faces.
    d=Draw(im)
    if location in {'bedroom','desk'} and day=='night':
        for k in range(13):
            xx=161+(k*29)%160;yy=101+(k*31+t*29)%164
            d.line([(xx,yy),(xx-2,yy+10)],'#7191a5',.7)
    if location=='park':
        for k in range(6):
            xx=(k*181+t*11)%960;yy=220+(k*59+t*5)%210
            d.ellipse((xx,yy,xx+4,yy+2),'#b7a37c')
    # Establishing, medium and face/action close-up shots. Full native-resolution
    # paths make these crops clean. Crop target follows the protagonist.
    order=scene.get('shot','wide')
    zooms=(1.0,1.47,1.95) if order!='close' else (1.8,1.25,1.55)
    z=zooms[cut]+.035*local
    focus_x=x if cut else 480
    head_y=floor-315*scale
    focus_y=273 if cut==0 else head_y+75 if cut==1 else head_y+36
    if act=='sleep':focus_y=320
    cw,ch=W/z,H/z
    left=max(0,min(W-cw,focus_x*S-cw/2));top=max(0,min(H-ch,focus_y*S-ch/2))
    im=im.crop((round(left),round(top),round(left+cw),round(top+ch))).resize((W,H),Image.Resampling.LANCZOS)
    if cut==2 and act in {'phone','write'}:
        im=insert_shot(im,scene,gender,t,local)
    # Captions retain fixed display resolution and sit on a translucent panel.
    d=Draw(im);d.box((0,0,960,24),'#111c2a');d.box((0,516,960,540),'#111c2a')
    if subtitle:
        lines=wrapped(subtitle,1600,36)[:2]
        panel=Image.new('RGBA',im.size);pd=Draw(panel)
        pd.box((65,471-len(lines)*13,895,510),(12,22,33,220),r=9)
        im.alpha_composite(panel);dd=ImageDraw.Draw(im)
        for j,line in enumerate(lines):
            tw=dd.textlength(line,font=font(36));dd.text(((W-tw)/2,(476-len(lines)*13+j*23)*S),line,font=font(36),fill='#faf5e7',stroke_width=1,stroke_fill='#152334')
    # Fast dissolves only at beat boundaries; internal cuts remain readable.
    fade=min(1,t/.25,(duration-t)/.3)
    if fade<1:im=Image.blend(Image.new('RGBA',im.size,'#111c2a'),im,max(0,fade))
    return im.convert('RGB')
