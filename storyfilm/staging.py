"""Reusable, text-led acting and staging. Coordinates are authored at 1080p."""
import math
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter
from .motion import action_progress, walk_position, text_count, send_time, text_finished, WALK_SPEED, WALK_PHASE, WALK_SECONDS, walk_weight
from .art import Draw, capsule, jointed, smooth, glow, gradient, wrapped, font, W, H, S

SKIN='#e9dfcb'; SHADE='#b8aa96'; EDGE='#171c24'

def envelope(p,a,b):return smooth(0,1,(p-a)/max(.001,b-a))


def actor(im,x,floor,t,gender='male',action='idle',emotion='neutral',scale=1.,shadow=False,progress=.5,walk_speed=24,emotion_from=None,seated=None,gaze_target=None,gesture='none',intensity=.7,send_at=1.2,write_until=3.,effort=1.):
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
        lift=envelope(p,.18,.46)*(1-envelope(p,.7,.94))*effort;crouch=12*(1-lift)
    walk=action=='walk';phase=t*WALK_PHASE;stride=walk_weight(t) if walk else 0
    bob=-abs(math.sin(phase))*3*stride if walk else 0
    # Emotional posture changes once per shot, with a restrained breath between actions.
    mood=envelope(t,.15,.8)
    start_low=emotion_from in {'sad','tired','worried','hurt','ashamed'} if emotion_from else emotion in {'sad','tired','worried','hurt','ashamed'}
    end_low=emotion in {'sad','tired','worried','hurt','ashamed'}
    hunch=(float(start_low)*(1-mood)+float(end_low)*mood)*(.6+.4*intensity)
    lean+=hunch*7
    bob+=math.sin(t*1.7)*.65
    hip=(200+lean*.36,352+crouch+(20 if sitting else 0)+bob)
    shoulder=(200+lean,250+crouch+(20 if sitting else 0)+bob)
    head=(shoulder[0]+8*hunch,170+6*hunch+crouch+(20 if sitting else 0)+bob)
    if action in {'phone','write','send','receive'}:head=(head[0]+7,head[1]+1)
    cloth='#7f8d93' if gender=='male' else '#a18e98';pants='#44494f'
    # Shoes and curved substantial legs. Linear stance cancels world movement.
    for j in range(2):
        side=-1 if j==0 else 1;ax=200+side*25;fy=490
        if sitting:
            knee=(ax+34,423);foot=(ax+35,490)
        elif walk:
            ph=(phase+j*math.pi)%(2*math.pi);span=walk_speed*math.pi/(2*WALK_PHASE)*stride
            if ph<math.pi:dx=span*(1-2*ph/math.pi);dy=0
            else:
                z=(ph-math.pi)/math.pi;dx=smooth(-span,span,z);dy=math.sin(z*math.pi)*26*stride
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
    swing=math.sin(phase)*19*stride if walk else 0
    left=[(sx-45,sy+8),(sx-59,sy+65),(sx-55+swing,sy+113)]
    right=[(sx+45,sy+8),(sx+59,sy+65),(sx+55-swing,sy+113)]
    if sitting:
        left=[(sx-45,sy+8),(sx-65,sy+60),(sx-5,sy+79)]
        right=[(sx+45,sy+8),(sx+62,sy+61),(sx+31,sy+72)]
    if action in {'phone','send','receive','dismiss'}:
        raise_hand=envelope(p,.08,.30)
        left[-1]=(sx-5,sy+87-raise_hand*31);right[-1]=(sx+30,sy+79-raise_hand*29)
    if action=='write':
        stroke=math.sin(t*8)*4 if .25<t<write_until else 0
        left[-1]=(sx-8,sy+70);right[-1]=(sx+46+stroke,sy+62)
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
    g=action if action in {'wipe_tear','clench','lookaway'} else gesture
    touch=envelope(t,.12,.65)*(1-envelope(t,1.25,1.65))
    if g=='wipe_tear':right=[(sx+45,sy+8),(sx+80,sy-15),(sx+55*(1-touch)+(hx+29-sx)*touch,sy+100*(1-touch)+(hy+15-sy)*touch)]
    if g=='clench':
        right[-1]=(sx+48,sy+98-8*touch);left[-1]=(sx-48,sy+98-8*touch)
    if g=='fidget':right[-1]=(right[-1][0]+math.sin(t*15)*2.2,right[-1][1])
    for arm in (left,right):
        jointed(d,arm,29,cloth);ax,ay=arm[-1]
        d.ellipse((ax-16,ay-7,ax+16,ay+21),SKIN,EDGE,2)
    if action in {'phone','send','receive','dismiss'}:
        ax,ay=left[-1];d.box((ax+3,ay-36,ax+31,ay+24),'#202932','#87949c',2,r=6)
        d.box((ax+7,ay-29,ax+27,ay+15),'#82a9b4',r=3)
        if action=='send' and send_at-.18<t<send_at+.18:d.ellipse((ax+23,ay+4,ax+38,ay+18),SKIN,EDGE,1)
    if action=='write':
        ax,ay=right[-1];d.line([(ax+7,ay-21),(ax-9,ay+26)],'#bfa278',4)
    if action=='exercise':
        yy=left[-1][1]+8;d.line([(sx-119,yy),(sx+119,yy)],'#bac2c7',5)
        for xx in (sx-120,sx+102):d.box((xx,yy-27,xx+18,yy+27),'#222830','#737f88',2,r=5)
    d.ellipse((hx-65,hy-69,hx+66,hy+65),SHADE,EDGE,3)
    d.ellipse((hx-63,hy-68,hx+60,hy+59),SKIN)
    d.path([('M',hx-48,hy-41),('C',hx-35,hy-58,hx-8,hy-62,hx+12,hy-57)],None,'#f6eedc',4)
    current=emotion_from if emotion_from and t<.38 else emotion
    tired=current in {'sad','tired','hurt','ashamed'}; worried=current=='worried'
    eyes_y=hy+7+(4 if tired else 0)+(3 if action in {'phone','send','receive','write'} else 0)
    gaze=(2+4*envelope(p,.08,.3)) if action in {'phone','receive','send','dismiss','write','reach','knock'} else 2
    if gaze_target=='window':gaze=-6
    elif gaze_target=='ground':eyes_y+=4;gaze=-1
    elif gaze_target=='door':gaze=7
    elif gaze_target=='camera':gaze=0
    if action=='lookaway':gaze=-7*envelope(t,.12,.65)
    blink=(t%4.7)>.0 and (t%4.7)<.12
    if action=='sleep':blink=True
    for ex in (hx-25,hx+25):
        if blink:d.line([(ex-7,eyes_y+1),(ex+7,eyes_y+1)],EDGE,2)
        else:d.ellipse((ex-5+gaze,eyes_y-7,ex+5+gaze,eyes_y+(4 if tired else 7)),EDGE)
        if tired:d.path([('M',ex-11,eyes_y+11),('C',ex-4,eyes_y+16,ex+7,eyes_y+17,ex+12,eyes_y+10)],None,'#b4a395',1.5)
    if current in {'sad','worried','tired','hurt','ashamed'}:
        d.line([(hx-40,hy-9),(hx-12,hy-17)],EDGE,3);d.line([(hx+12,hy-17),(hx+40,hy-9)],EDGE,3)
    elif current in {'determined','angry'}:
        d.line([(hx-40,hy-18),(hx-12,hy-9)],EDGE,3);d.line([(hx+12,hy-9),(hx+40,hy-18)],EDGE,3)
    else:
        d.line([(hx-39,hy-15),(hx-13,hy-16)],EDGE,2);d.line([(hx+13,hy-16),(hx+39,hy-15)],EDGE,2)
    if current=='relieved':d.path([('M',hx-11,hy+37),('C',hx,hy+43,hx+9,hy+42,hx+15,hy+36)],None,EDGE,2)
    elif current=='happy':d.path([('M',hx-13,hy+35),('C',hx,hy+47,hx+10,hy+42,hx+19,hy+32)],None,EDGE,3)
    elif worried:d.ellipse((hx-5,hy+34,hx+9,hy+43),EDGE)
    elif tired:d.path([('M',hx-15,hy+40),('C',hx-3,hy+32,hx+10,hy+33,hx+18,hy+39)],None,EDGE,2.5)
    else:d.line([(hx-13,hy+37),(hx+16,hy+37)],EDGE,2.5)
    if current in {'hurt','ashamed'}:
        tear=envelope(t,.4,1.3)*14*intensity
        d.line([(hx+29,eyes_y+13),(hx+30,eyes_y+13+tear)],'#8bafb9',2)
    if current=='angry':d.line([(hx-13,hy+39),(hx+18,hy+39)],EDGE,4)
    if gender=='female':
        d.path([('M',hx-66,hy-7),('C',hx-74,hy-72,hx-17,hy-91,hx+29,hy-68),('C',hx+63,hy-55,hx+68,hy-24,hx+62,hy+3),('C',hx+37,hy-5,hx+23,hy-26,hx+20,hy-47),('C',hx-8,hy-26,hx-37,hy-39,hx-66,hy-7)],'#453d42',EDGE,2)
    if action=='sleep':
        layer=layer.rotate(83,resample=Image.Resampling.BICUBIC,expand=True)
    if scale!=1:layer=layer.resize((round(layer.width*scale),round(layer.height*scale)),Image.Resampling.LANCZOS)
    dest=(round(x*S-400*scale),round(floor*S-490*S*scale))
    if action=='sleep':dest=(round(x*S-layer.width*.5),round(floor*S-layer.height*.65))
    im.alpha_composite(layer,dest)
    if action=='write':
        ax,ay=right[-1]
        world=lambda xx,yy:(x+(xx-200)*scale,floor+(yy-490)*scale)
        return {'pen':[world(ax+7,ay-21),world(ax-9,ay+26)]}
    return None


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


def label(im,text,y=70,color='#f4f1e5',size=36,width=1540,bubble=False,cx=None):
    if not text:return
    cx=W/2 if cx is None else cx
    lines=wrapped(text,width,size);dd=ImageDraw.Draw(im)
    lineheight=round(size*1.4)
    if bubble:
        tw=max(dd.textlength(line,font=font(size)) for line in lines)
        dd.rounded_rectangle((cx-tw/2-25,y-16,cx+tw/2+25,y+len(lines)*lineheight+12),radius=20,fill=(15,20,28,240),outline=color,width=2)
    for j,line in enumerate(lines):
        tw=dd.textlength(line,font=font(size));dd.text((cx-tw/2,y+j*lineheight),line,font=font(size),fill=color,stroke_width=2,stroke_fill='#141a22')


def stage(scene,gender,title,t,duration,index,total,subtitle=''):
    p=t/max(.001,duration);ambient=scene.get('ambient_start',0)+t;loc=scene['location'];act=scene['action'];day=scene.get('time','night')
    im=set_design(loc,day,scene.get('state','normal')).copy()
    weather=scene.get('weather','rain' if loc in {'bedroom','desk'} and day=='night' else 'clear')
    outdoors=loc in {'street','park','rooftop'}
    if weather=='snow' and outdoors:
        sd=Draw(im)
        sd.path([('M',0,457),('C',220,447,320,470,480,456),('C',640,448,760,467,960,453),('L',960,464),('L',0,468),('L',0,457)],'#bcc8cf')
        for k in range(55):
            xx=(k*167+ambient*(16+k%4*7))%960;yy=(k*79+ambient*(21+k%5*4))%540
            r=1+k%3*.55;sd.ellipse((xx-r,yy-r,xx+r,yy+r),'#c8d4dd')
    elif weather=='rain' and outdoors:
        sd=Draw(im)
        for k in range(50):
            xx=(k*137-ambient*26)%960;yy=(k*83+ambient*170)%540
            sd.line([(xx,yy),(xx-4,yy+15)],'#8597a8',.8)
    shot=scene.get('shot','wide');scale=.83;x=490;floor=473
    if act=='walk':x=walk_position(t);scale=.8
    if act in {'knock','reach'}:x=252;scale=.83
    if loc=='desk':x=480;floor=487;scale=.82
    if loc=='park' and act in {'sit','phone','send','receive'}:floor=475;scale=.88
    if act=='sleep':x=576;floor=370;scale=.72
    sh=scene.get('shadow','none');sh='loom' if sh is True else 'none' if sh is False else sh
    shadow_actor(im,x+151,floor,t,p,sh,scene.get('shadow_size',1.))
    d=Draw(im);d.ellipse((x-67,floor-4,x+70,floor+12),'#19212a')
    seated=act in {'sit','phone','send','receive','write'} and loc in {'park','bedroom','desk'}
    pose=actor(im,x,floor,t,gender,act,scene['emotion'],scale,progress=action_progress(act,scene.get('hold_at',t) if scene.get('hold_at') is not None else t),walk_speed=WALK_SPEED/scale,emotion_from=scene.get('emotion_from'),seated=seated,gaze_target=scene.get('gaze'),gesture=scene.get('gesture','none'),intensity=scene.get('intensity',.7),send_at=send_time(scene.get('prop_text',''),scene.get('pretyped',False)),write_until=text_finished(scene.get('prop_text',''),'write'),effort=scene.get('effort',1.))
    d=Draw(im)
    if loc=='desk':
        d.box((342,381,804,400),'#a38b6d',EDGE,3,r=5)
        for xx in (362,774):d.box((xx,400,xx+12,506),'#574e44',EDGE,2)
        d.path([('M',451,374),('L',569,374),('L',584,382),('L',444,382),('L',451,374)],'#ede1c7',EDGE,1)
        if act=='write' and isinstance(pose,dict):
            amount=text_count(scene.get('prop_text',''),t,'write')/max(1,len(scene.get('prop_text','')))
            if amount:d.line([(461,377),(461+amount*72,377)],'#53575a',.6)
            # Paper is in front of the body; the pencil must be in front of paper.
            a,b=pose['pen'];d.line([a,b],'#bfa278',4*scale)
            d.line([b,(b[0]-scale,b[1]+2*scale)],EDGE,scale)
    if loc in {'bedroom','desk'} and weather=='rain':
        for k in range(10):
            xx=130+(k*31)%145;yy=120+(k*47+ambient*32)%178;d.line([(xx,yy),(xx-2,yy+10)],'#718899',.8)
    if loc=='bedroom':
        secs=int(scene.get('clock_minutes',22*60)*60+ambient);d.box((805,355,866,382),'#151a21','#656e77',2,r=5);d.text((810,361),f'{secs//3600%24:02d}:{secs//60%60:02d}',13,'#e1a092')
    if loc in {'bedroom','desk','gym'}:
        seconds=scene.get('clock_minutes',22*60)*60+ambient
        cx,cy=815,143;d.ellipse((cx-31,cy-31,cx+31,cy+31),'#d8d4c9',EDGE,2)
        for k in range(12):
            a=k*math.pi/6;d.line([(cx+26*math.sin(a),cy-26*math.cos(a)),(cx+29*math.sin(a),cy-29*math.cos(a))],EDGE,1)
        for angle,length,color,width in [(seconds/43200*2*math.pi,15,EDGE,2.5),(seconds/3600*2*math.pi,23,EDGE,1.5),(int(seconds)/60*2*math.pi,25,'#a2534e',.8)]:
            d.line([(cx,cy),(cx+length*math.sin(angle),cy-length*math.cos(angle))],color,width)
    # Framing is a screenplay choice, never an automatic halfway cut.
    if shot in {'close','reaction'}:
        z=1.85;cw,ch=W/z,H/z;cx=x*S;cy=229*S
        left=max(0,min(W-cw,cx-cw/2));top=max(0,min(H-ch,cy-ch/2))
        im=im.crop((round(left),round(top),round(left+cw),round(top+ch))).resize((W,H),Image.Resampling.LANCZOS)
    if shot=='insert':
        from .art import insert_shot
        detail=dict(scene,action=act if act in {'phone','send','receive','dismiss'} else 'write')
        # Receive is already readable; send reveals typed words, then SENT.
        ip=1 if act=='receive' else p
        im=insert_shot(im,detail,gender,t,ip)
    caption=scene.get('caption',subtitle)
    if .08<=p<=.91:label(im,caption,930 if shot=='insert' else 60,size=36)
    text=scene.get('dialogue','')
    if .25<=p<=.88:label(im,text,810,size=36,bubble=True)
    if .18<=p<=.88:label(im,scene.get('shadow_text',''),230,color='#ed8279',size=32,width=560,cx=1580)
    hud=scene.get('hud','')
    if hud:ImageDraw.Draw(im).text((76,40),hud,font=font(28),fill='#dcd6c7')
    if index==total-1 and t>duration-.65:
        im=Image.blend(im,Image.new('RGBA',im.size,'#111720'),envelope(t,duration-.65,duration))
    return im.convert('RGB')
