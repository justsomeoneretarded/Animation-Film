"""Reusable, text-led acting and staging. Coordinates are authored at 1080p."""
import math
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter
from .art import Draw, capsule, jointed, smooth, glow, gradient, wrapped, font, W, H, S

SKIN='#e9dfcb'; SHADE='#b8aa96'; EDGE='#171c24'

def envelope(p,a,b):return smooth(0,1,(p-a)/max(.001,b-a))


def actor(im,x,floor,t,gender='male',action='idle',emotion='neutral',scale=1.,shadow=False,progress=.5,walk_speed=24,emotion_from=None,seated=None):
    """A round silhouette, integrated short neck and contact-aware pose phases.

    Feet are planted except during explicit walk/fall/recovery actions. Local
    origin is the midpoint of the feet; drawing above it cannot clip the scalp.
    """
    p=max(0,min(1,progress)); q=envelope(p,.18,.68)
    layer=Image.new('RGBA',(800,1080));d=Draw(layer)
    # Center x=200, foot y=490. All joints follow the pelvis/shoulders.
    sitting=action in {'sit','phone','receive','send','write'} if seated is None else seated
    crouch=0;lean=0;lift=0
    if action=='fall':
        q=envelope(p,.18,.48);crouch=84*q;lean=57*q
    if action=='getup':
        q=envelope(p,.26,.88);crouch=84*(1-q);lean=57*(1-q)
    if action=='stand':
        q=envelope(p,.26,.78);crouch=40*(1-q);lean=10*(1-q)
    if action=='exercise':
        # Prepare, attempt one rep, hold the effort, then lower under control.
        lift=envelope(p,.18,.46)*(1-envelope(p,.7,.94));crouch=12*(1-lift)
    walk=action=='walk';phase=t*3.6
    bob=-abs(math.sin(phase))*3 if walk else 0
    # Emotional posture changes once per shot, with a restrained breath between actions.
    mood=envelope(p,.22,.58)
    start_low=emotion_from in {'sad','tired','worried'} if emotion_from else emotion in {'sad','tired','worried'}
    end_low=emotion in {'sad','tired','worried'}
    hunch=(float(start_low)*(1-mood)+float(end_low)*mood)
    lean+=hunch*7
    bob+=math.sin(t*1.7)*.65
    hip=(200+lean*.36,352+crouch+(20 if sitting else 0)+bob)
    shoulder=(200+lean,250+crouch+(20 if sitting else 0)+bob)
    head=(shoulder[0]+8*hunch,177+6*hunch+crouch+(20 if sitting else 0)+bob)
    if action in {'phone','write','send','receive'}:head=(head[0]+7,head[1]+6)
    cloth='#7f8d93' if gender=='male' else '#a18e98';pants='#44494f'
    # Shoes and curved substantial legs. Linear stance cancels world movement.
    for j in range(2):
        side=-1 if j==0 else 1;ax=200+side*25;fy=490
        if sitting:
            knee=(ax+34,423);foot=(ax+35,490)
        elif walk:
            ph=(phase+j*math.pi)%(2*math.pi);span=walk_speed*math.pi/7.2
            if ph<math.pi:dx=span*(1-2*ph/math.pi);dy=0
            else:
                z=(ph-math.pi)/math.pi;dx=smooth(-span,span,z);dy=math.sin(z*math.pi)*26
            foot=(ax+dx,fy-dy);knee=(ax+dx*.48,421-dy*.7)
        elif action in {'fall','getup'}:
            amt=crouch/84;knee=(ax+side*45*amt,423+40*amt);foot=(ax+side*35*amt,490)
        else:knee=(ax,422+crouch*.12);foot=(ax,490)
        jointed(d,[(hip[0]+side*21,hip[1]-4),knee,foot],35,pants)
        fx,fy=foot;d.box((fx-24,fy-9,fx+29,fy+18),'#24292f',EDGE,2,r=11)
    sx,sy=shoulder;hx,hy=head
    # Hair sits behind the head and above the shoulders.
    if gender=='female':
        d.path([('M',hx-65,hy),('C',hx-78,hy-91,hx+75,hy-99,hx+68,hy+14),('L',hx+76,hy+78),('C',hx+25,hy+94,hx-33,hy+89,hx-75,hy+72),('L',hx-65,hy)],'#423c40',EDGE,3)
    # Neck is short, visible and flares smoothly into the shoulders.
    d.path([('M',hx-17,hy+55),('L',hx+17,hy+55),('L',sx+18,sy-10),('C',sx+30,sy-2,sx+24,sy+8,sx,sy+9),('C',sx-25,sy+8,sx-29,sy-2,sx-18,sy-10),('L',hx-17,hy+55)],SKIN,EDGE,2)
    d.path([('M',hx+5,hy+60),('L',hx+17,hy+55),('L',sx+18,sy-10),('L',sx+5,sy-7)],SHADE)
    # Rounded pear-like torso rather than a stick or a rectangular hoodie.
    px,py=hip
    d.path([('M',sx-29,sy-9),('C',sx-67,sy-3,sx-60,sy+44,px-63,py-7),('C',px-65,py+31,px+64,py+31,px+63,py-7),('C',sx+60,sy+44,sx+67,sy-3,sx+29,sy-9),('C',sx+10,sy+3,sx-10,sy+3,sx-29,sy-9)],cloth,EDGE,3)
    d.path([('M',sx+42,sy+16),('C',sx+50,sy+59,px+55,py,px+42,py+13),('C',px+10,py+26,px-25,py+17,px-39,py+15)],None,'#646b72',3)
    # Arms use event phases, never an unrelated idle waving cycle.
    swing=math.sin(phase)*19 if walk else 0
    left=[(sx-45,sy+8),(sx-59,sy+65),(sx-55+swing,sy+113)]
    right=[(sx+45,sy+8),(sx+59,sy+65),(sx+55-swing,sy+113)]
    if sitting:
        left=[(sx-45,sy+8),(sx-65,sy+60),(sx-5,sy+79)]
        right=[(sx+45,sy+8),(sx+62,sy+61),(sx+31,sy+72)]
    if action in {'phone','send','receive'}:
        raise_hand=envelope(p,.08,.30)
        left[-1]=(sx-5,sy+87-raise_hand*31);right[-1]=(sx+30,sy+79-raise_hand*29)
    if action=='write':
        stroke=math.sin(t*8)*4 if .28<p<.78 else 0
        left[-1]=(sx-8,sy+90);right[-1]=(sx+46+stroke,sy+91)
    if action in {'reach','knock'}:
        reach=envelope(p,.18,.48);tap=math.sin((p-.56)*math.pi*24)*3 if action=='knock' and .56<p<.78 else 0
        right=[(sx+45,sy+8),(sx+60+reach*30,sy+57-reach*34),(sx+55+reach*76+tap,sy+107-reach*93)]
    if action=='exercise':
        left=[(sx-45,sy+8),(sx-77,sy+38),(sx-89,sy+57-lift*77)]
        right=[(sx+45,sy+8),(sx+77,sy+38),(sx+89,sy+57-lift*77)]
    if action in {'fall','getup'}:
        amt=crouch/84
        left=[(sx-45,sy+8),(sx-65,sy+75),(sx-70,sy+115+amt*35)]
        right=[(sx+45,sy+8),(sx+55,sy+74),(sx+62,sy+115+amt*35)]
    for arm in (left,right):
        jointed(d,arm,29,cloth);ax,ay=arm[-1]
        d.ellipse((ax-16,ay-7,ax+16,ay+21),SKIN,EDGE,2)
    if action in {'phone','send','receive'}:
        ax,ay=left[-1];d.box((ax+1,ay-34,ax+37,ay+24),'#202932','#87949c',2,r=6)
        d.box((ax+6,ay-27,ax+32,ay+13),'#82a9b4',r=3)
        if action=='send' and .65<p<.83:d.ellipse((ax+23,ay+4,ax+38,ay+18),SKIN,EDGE,1)
    if action=='write':
        ax,ay=right[-1];d.line([(ax+7,ay-21),(ax-9,ay+26)],'#bfa278',4)
    if action=='exercise':
        yy=left[-1][1]+8;d.line([(sx-119,yy),(sx+119,yy)],'#bac2c7',5)
        for xx in (sx-120,sx+102):d.box((xx,yy-27,xx+18,yy+27),'#222830','#737f88',2,r=5)
    d.ellipse((hx-65,hy-69,hx+66,hy+65),SHADE,EDGE,3)
    d.ellipse((hx-63,hy-68,hx+60,hy+59),SKIN)
    d.path([('M',hx-48,hy-41),('C',hx-35,hy-58,hx-8,hy-62,hx+12,hy-57)],None,'#f6eedc',4)
    current=emotion_from if emotion_from and p<.38 else emotion
    tired=current in {'sad','tired'}; worried=current=='worried'
    eyes_y=hy+7+(4 if tired else 0)
    gaze=(2+4*envelope(p,.08,.3)) if action in {'phone','receive','send','write','reach','knock'} else 2
    blink=(t%4.7)>.0 and (t%4.7)<.12
    if action=='sleep':blink=True
    for ex in (hx-25,hx+25):
        if blink:d.line([(ex-7,eyes_y+1),(ex+7,eyes_y+1)],EDGE,2)
        else:d.ellipse((ex-5+gaze,eyes_y-7,ex+5+gaze,eyes_y+(4 if tired else 7)),EDGE)
        if tired:d.path([('M',ex-11,eyes_y+11),('C',ex-4,eyes_y+16,ex+7,eyes_y+17,ex+12,eyes_y+10)],None,'#b4a395',1.5)
    if current in {'sad','worried','tired'}:
        d.line([(hx-40,hy-9),(hx-12,hy-17)],EDGE,3);d.line([(hx+12,hy-17),(hx+40,hy-9)],EDGE,3)
    elif current=='determined':
        d.line([(hx-40,hy-18),(hx-12,hy-9)],EDGE,3);d.line([(hx+12,hy-9),(hx+40,hy-18)],EDGE,3)
    else:
        d.line([(hx-39,hy-15),(hx-13,hy-16)],EDGE,2);d.line([(hx+13,hy-16),(hx+39,hy-15)],EDGE,2)
    if current=='happy':d.path([('M',hx-13,hy+35),('C',hx,hy+47,hx+10,hy+42,hx+19,hy+32)],None,EDGE,3)
    elif worried:d.ellipse((hx-5,hy+34,hx+9,hy+43),EDGE)
    elif tired:d.path([('M',hx-15,hy+40),('C',hx-3,hy+32,hx+10,hy+33,hx+18,hy+39)],None,EDGE,2.5)
    else:d.line([(hx-13,hy+37),(hx+16,hy+37)],EDGE,2.5)
    if gender=='female':
        d.path([('M',hx-66,hy-7),('C',hx-74,hy-72,hx-17,hy-91,hx+29,hy-68),('C',hx+63,hy-55,hx+68,hy-24,hx+62,hy+3),('C',hx+37,hy-5,hx+23,hy-26,hx+20,hy-47),('C',hx-8,hy-26,hx-37,hy-39,hx-66,hy-7)],'#453d42',EDGE,2)
    if action=='sleep':
        layer=layer.rotate(83,resample=Image.Resampling.BICUBIC,expand=True)
    if scale!=1:layer=layer.resize((round(layer.width*scale),round(layer.height*scale)),Image.Resampling.LANCZOS)
    dest=(round(x*S-400*scale),round(floor*S-490*S*scale))
    if action=='sleep':dest=(round(x*S-layer.width*.5),round(floor*S-layer.height*.65))
    im.alpha_composite(layer,dest)


@lru_cache(maxsize=24)
def set_design(location,day='night',state='normal'):
    warm=day!='night';im=gradient((W,H),(24,29,38),(49,54,61) if not warm else (115,106,92));d=Draw(im)
    floor=463
    if location in {'bedroom','desk','gym'}:
        d.box((0,0,960,floor),'#272d35' if not warm else '#706c65')
        d.box((0,floor,960,540),'#1e242c' if not warm else '#47494b')
        d.line([(0,floor),(960,floor)],'#919087' if warm else '#4d5660',2)
        d.box((115,106,289,315),'#121923','#6e7378',4,r=3)
        d.box((123,114,281,307),'#142b43' if not warm else '#b7b2a0')
        d.line([(202,114),(202,306)],'#686e72',4)
        d.line([(123,213),(281,213)],'#686e72',4)
        if not warm:d.ellipse((241,137,258,154),'#d1d8d3')
        glow(im,(228,280),(130,170,207) if not warm else (255,221,155),200,35)
        if location=='bedroom':
            d.box((360,365,756,458),'#4c5962',EDGE,3,r=22)
            d.box((374,361,489,401),'#b3b2a5',EDGE,2,r=17)
            d.path([('M',475,381),('C',551,366,672,371,756,390),('L',756,464),('L',481,464),('L',475,381)],'#5a6f7a',EDGE,3)
            d.box((791,382,878,464),'#514a43',EDGE,2,r=4)
            d.box((805,355,866,382),'#151a21','#656e77',2,r=5);d.text((810,361),'02:17',13,'#e1a092')
        elif location=='desk':
            d.box((408,321,518,442),'#424b54',EDGE,3,r=22)
            d.line([(754,353),(758,255),(714,234)],'#93958f',5)
            d.path([('M',688,227),('C',707,204,738,220,739,243),('L',682,243),('L',688,227)],'#ac9875',EDGE,2)
            glow(im,(657,343),(255,206,129),150,80)
        else:
            d.box((643,133,848,418),'#34404b','#89949b',3,r=5)
            for xx in (138,322):d.line([(xx,230),(xx,460)],'#939b9f',8)
            d.line([(132,270),(331,270)],'#c1c5c1',5)
        if state=='clutter':
            for xx,yy in [(330,457),(770,460),(824,445),(299,474)]:
                d.box((xx,yy-23,xx+16,yy),'#8d7970',EDGE,1,r=4)
    else:
        # Sparse silhouettes and one clear pool of light leave room for acting.
        d.box((0,390,960,540),'#303c47' if not warm else '#777a74')
        d.line([(0,463),(960,463)],'#74808a',2)
        for xx in (50,840):
            d.path([('M',xx,463),('C',xx+7,330,xx+7,230,xx+1,149)],None,'#202a33',16)
            for dx,dy in [(-60,20),(40,-10),(0,-60)]:d.ellipse((xx+dx-60,dy+130,xx+dx+65,dy+250),'#293a3d' if not warm else '#59695a')
        if location=='park':
            for yy in (316,342):d.box((330,yy,665,yy+18),'#9d876c',EDGE,2,r=4)
            d.box((319,377,677,396),'#9d876c',EDGE,2,r=5)
            for xx in (350,641):d.line([(xx,394),(xx,463)],'#28323b',8)
        elif location=='street':
            d.box((697,151,709,463),'#26323d');d.box((675,142,732,168),'#ecd5a6',EDGE,2,r=5)
            glow(im,(702,262),(255,209,137),190,50)
            d.box((361,142,493,462),'#252d35','#6c7780',3,r=4)
            d.ellipse((472,314,480,322),'#c2ad84')
        else:
            d.box((0,389,960,430),'#63717b','#29333e',3)
            for xx,hh in [(100,100),(215,70),(690,115),(770,90)]:d.box((xx,390-hh,xx+65,389),'#253440')
    return im


def shadow_actor(im,x,floor,t,p,mode='loom',size=1.):
    if mode=='none':return
    layer=Image.new('RGBA',im.size);d=Draw(layer)
    shrink=1-envelope(p,.25,.8)*.8 if mode=='shrink' else 1
    a=size*shrink;cx=x;cy=floor
    d.path([('M',cx-60*a,cy),('C',cx-120*a,cy-80*a,cx-72*a,cy-180*a,cx-66*a,cy-270*a),('C',cx-59*a,cy-353*a,cx+63*a,cy-362*a,cx+72*a,cy-278*a),('C',cx+93*a,cy-190*a,cx+92*a,cy-65*a,cx+65*a,cy),('L',cx-60*a,cy)],'#10131a')
    eye_y=cy-275*a
    for ex in (cx-23*a,cx+24*a):d.ellipse((ex-5*a,eye_y-3*a,ex+5*a,eye_y+4*a),'#da655e')
    if mode=='crack':
        crack=envelope(p,.3,.8)
        if crack>0:d.line([(cx,cy-336*a),(cx-17*a,cy-280*a),(cx+12*a,cy-245*a),(cx-13*a,cy-180*a),(cx,cy-80*a)],'#f1d69b',max(1,crack*5))
        if p>.8:layer.putalpha(layer.getchannel('A').point(lambda v:round(v*(1-envelope(p,.8,1)))))
    im.alpha_composite(layer)


def label(im,text,y=70,color='#f4f1e5',size=36,width=1540,bubble=False):
    if not text:return
    lines=wrapped(text,width,size);dd=ImageDraw.Draw(im)
    lineheight=round(size*1.4)
    if bubble:
        tw=max(dd.textlength(line,font=font(size)) for line in lines)
        dd.rounded_rectangle(((W-tw)/2-25,y-16,(W+tw)/2+25,y+len(lines)*lineheight+12),radius=20,fill=(15,20,28,240),outline=color,width=2)
    for j,line in enumerate(lines):
        tw=dd.textlength(line,font=font(size));dd.text(((W-tw)/2,y+j*lineheight),line,font=font(size),fill=color,stroke_width=2,stroke_fill='#141a22')


def stage(scene,gender,title,t,duration,index,total,subtitle=''):
    p=t/max(.001,duration);loc=scene['location'];act=scene['action'];day=scene.get('time','night')
    im=set_design(loc,day,scene.get('state','normal')).copy()
    shot=scene.get('shot','wide');scale=.83;x=490;floor=473
    if act=='walk':x=350+p*260;scale=.8
    if act in {'knock','reach'}:x=252;scale=.83
    if loc=='desk':x=480;floor=501;scale=.82
    if loc=='park' and act in {'sit','phone','send','receive'}:floor=475;scale=.88
    if act=='sleep':x=576;floor=370;scale=.72
    sh=scene.get('shadow','none');sh='loom' if sh is True else 'none' if sh is False else sh
    shadow_actor(im,x+151,floor,t,p,sh,scene.get('shadow_size',1.))
    d=Draw(im);d.ellipse((x-67,floor-4,x+70,floor+12),'#19212a')
    seated=act in {'sit','phone','send','receive','write'} and loc in {'park','bedroom','desk'}
    actor(im,x,floor,t,gender,act,scene['emotion'],scale,progress=p,walk_speed=260/max(.01,duration)/scale,emotion_from=scene.get('emotion_from'),seated=seated)
    d=Draw(im)
    if loc=='desk':
        d.box((342,381,804,400),'#a38b6d',EDGE,3,r=5)
        for xx in (362,774):d.box((xx,400,xx+12,506),'#574e44',EDGE,2)
        d.path([('M',451,374),('L',569,374),('L',584,382),('L',444,382),('L',451,374)],'#ede1c7',EDGE,1)
    if loc in {'bedroom','desk'} and day=='night':
        for k in range(10):
            xx=130+(k*31)%145;yy=120+(k*47+t*32)%178;d.line([(xx,yy),(xx-2,yy+10)],'#718899',.8)
    # Framing is a screenplay choice, never an automatic halfway cut.
    if shot in {'close','reaction'}:
        z=1.85;cw,ch=W/z,H/z;cx=x*S;cy=229*S
        left=max(0,min(W-cw,cx-cw/2));top=max(0,min(H-ch,cy-ch/2))
        im=im.crop((round(left),round(top),round(left+cw),round(top+ch))).resize((W,H),Image.Resampling.LANCZOS)
    if shot=='insert':
        from .art import insert_shot
        detail=dict(scene,action=act if act in {'phone','send','receive'} else 'write')
        # Receive is already readable; send reveals typed words, then SENT.
        ip=1 if act=='receive' else p
        im=insert_shot(im,detail,gender,t,ip)
    caption=scene.get('caption',subtitle)
    if .08<=p<=.91:label(im,caption,80,size=38)
    text=scene.get('dialogue','')
    if .25<=p<=.88:label(im,text,810,size=36,bubble=True)
    if .18<=p<=.88:label(im,scene.get('shadow_text',''),714,color='#ed8279',size=36)
    hud=scene.get('hud','')
    if hud:ImageDraw.Draw(im).text((76,40),hud,font=font(28),fill='#dcd6c7')
    if index==total-1 and p>.75:
        im=Image.blend(im,Image.new('RGBA',im.size,'#111720'),envelope(p,.75,1))
    return im.convert('RGB')
