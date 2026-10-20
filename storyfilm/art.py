"""Original procedural artwork. Coordinates use a 960x540 design canvas."""
import math
import random
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 960, 540
INK = '#11141c'
SKIN = '#dedbd0'

@lru_cache(maxsize=32)
def font(size):
    for path in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'C:/Windows/Fonts/arial.ttf']:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def wrapped(text, width, size):
    d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    lines, line = [], ''
    for word in text.split():
        test = (line + ' ' + word).strip()
        if d.textlength(test, font=font(size)) > width and line:
            lines.append(line)
            line = word
        else:
            line = test
    return lines + ([line] if line else [])


def text_center(im, text, y, size=24, fill='#ede8da', width=820):
    d = ImageDraw.Draw(im)
    for line in wrapped(text, width, size):
        box = d.textbbox((0, 0), line, font=font(size))
        d.text(((W-(box[2]-box[0]))/2, y), line, font=font(size), fill=fill,
               stroke_width=2, stroke_fill='#080b11')
        y += int(size*1.35)


def glow(im, xy, color, radius=70, strength=65):
    layer = Image.new('RGBA', im.size)
    d = ImageDraw.Draw(layer)
    x, y = xy
    d.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(*color, strength))
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius/2)))


@lru_cache(maxsize=12)
def background(location):
    im = Image.new('RGBA', (W, H), '#0d121d')
    d = ImageDraw.Draw(im)
    for y in range(H):
        f = y/H
        d.line((0, y, W, y), fill=(int(13+8*f), int(18+8*f), int(29+9*f)))
    if location in {'bedroom', 'desk', 'gym'}:
        d.rectangle((50, 55, 910, 427), fill='#171d29', outline='#303647', width=2)
        for x in range(60, 920, 100):
            d.line((x, 58, x, 426), fill='#1c2330')
        d.rounded_rectangle((90, 85, 255, 270), radius=9, fill='#0b1425', outline='#4a5265', width=3)
        d.line((172, 86, 172, 268), fill='#4a5265', width=2)
        d.line((91, 177, 253, 177), fill='#4a5265', width=2)
        d.ellipse((205, 107, 228, 130), fill='#dae2e6')
        d.rectangle((0, 428, W, H), fill='#10151e')
        d.line((0, 428, W, 428), fill='#4a4550', width=2)
        if location == 'bedroom':
            d.rounded_rectangle((400, 340, 840, 401), radius=20, fill='#343b51', outline='#666b7d', width=3)
            d.rounded_rectangle((405, 328, 518, 361), radius=14, fill='#a3a2aa')
            d.rectangle((401, 394, 839, 412), fill='#2b2e3e')
            for x in (414, 819):
                d.rectangle((x, 409, x+10, 438), fill='#646173')
            d.rounded_rectangle((290, 353, 366, 429), radius=6, fill='#252b36', outline='#545461')
            d.rounded_rectangle((302, 327, 355, 351), radius=4, fill='#15151b')
            d.text((308, 330), '05:30', font=font(13), fill='#e46b72')
        elif location == 'desk':
            d.rectangle((350, 327, 845, 346), fill='#6c5749')
            for x in (370, 815):
                d.rectangle((x, 345, x+12, 432), fill='#443d3d')
            d.polygon([(707, 327), (741, 249), (783, 230)], fill='#4f535c')
            d.polygon([(749, 232), (795, 254), (817, 222), (774, 205)], fill='#bfa37b')
            d.rectangle((627, 309, 688, 326), fill='#b5ab94')
            glow(im, (735, 300), (255, 179, 82), 135, 65)
        else:
            d.rectangle((665, 115, 865, 390), fill='#212c3c', outline='#657086', width=3)
            d.line((763, 115, 763, 389), fill='#455066', width=2)
            for x in (95, 275):
                d.line((x, 261, x, 429), fill='#555e6b', width=8)
            d.line((75, 285, 300, 285), fill='#92969b', width=7)
            for x in (92, 270):
                d.rounded_rectangle((x, 257, x+20, 314), radius=5, fill='#252c38', outline='#70798b', width=2)
    else:
        rng = random.Random(45)
        for x in range(-20, 980, 75):
            top = rng.randint(170, 290)
            d.rectangle((x, top, x+65, 432), fill='#141c2a', outline='#222c3c')
            for xx in range(x+12, x+55, 23):
                for yy in range(top+18, 401, 38):
                    if rng.random() > .4:
                        d.rectangle((xx, yy, xx+8, yy+15), fill='#6c6251')
        d.ellipse((750, 66, 793, 109), fill='#d5dce2')
        glow(im, (773, 87), (154, 181, 226), 90, 42)
        d.rectangle((0, 431, W, H), fill='#10151d')
        d.line((0, 432, W, 432), fill='#515969', width=2)
        if location in {'street', 'park'}:
            for x in (135, 820):
                d.line((x, 150, x, 432), fill='#4a5362', width=5)
                d.rounded_rectangle((x-22, 146, x+22, 161), radius=5, fill='#e4d8b1')
                glow(im, (x, 170), (255, 200, 110), 105, 70)
        if location == 'park':
            for x in (45, 875):
                d.line((x, 216, x, 430), fill='#3e3b40', width=15)
                for dx, dy, r in [(-30, 0, 62), (30, -30, 73), (0, -70, 63)]:
                    d.ellipse((x+dx-r, 210+dy-r, x+dx+r, 210+dy+r), fill='#203331')
            for yy in (324, 343, 362):
                d.rounded_rectangle((340, yy, 650, yy+13), radius=3, fill='#6a5747')
            for xx in (360, 620):
                d.line((xx, 365, xx, 428), fill='#5c6069', width=7)
        if location == 'rooftop':
            d.rectangle((0, 421, W, 540), fill='#232b39')
            d.rectangle((0, 405, W, 423), fill='#566075')
            d.rectangle((74, 248, 219, 407), fill='#343c4a', outline='#687183', width=3)
    return im


def character(im, x, floor, t, gender='male', action='idle', emotion='neutral', scale=1., shadow=False):
    # All artwork is authored here, with no tracing or extracted assets.
    layer = Image.new('RGBA', (300, 360))
    d = ImageDraw.Draw(layer)
    bob = math.sin(t*2)*2
    cx, hy = 150, 83+bob
    outline = '#302f36'
    fill = '#dad6cb' if gender == 'male' else '#dfd8ce'
    if shadow:
        fill, outline = '#090b12', '#a4485b'
    sitting = action in {'sit', 'phone', 'write'}
    stride = math.sin(t*6)*23 if action == 'walk' else 0
    hip = 232 if not sitting else 218
    lw = 20 if gender == 'male' else 18
    def limb(points, width=lw):
        d.line(points, fill=outline, width=width+5, joint='curve')
        d.line(points, fill=fill, width=width, joint='curve')
        for px, py in (points[0], points[-1]):
            r=width/2
            d.ellipse((px-r, py-r, px+r, py+r), fill=fill)
    # Slightly varied torso contour; both adults remain bald and simply drawn.
    torso = [(126, 140), (115, 171), (120, 208), (111 if gender=='female' else 119, hip),
             (180 if gender=='female' else 174, hip), (178, 205), (183, 172), (174, 141)]
    if sitting:
        limb([(133, hip), (188, hip+14), (192, 289)])
        limb([(157, hip), (212, hip+17), (214, 289)])
    else:
        limb([(133, hip), (131-stride*.5, 267), (130-stride, 302)])
        limb([(163, hip), (165+stride*.5, 267), (168+stride, 302)])
    d.polygon(torso, fill=fill, outline=outline, width=3)
    if action == 'exercise':
        lift = (math.sin(t*2)+1)*28
        limb([(122, 157), (94, 170-lift), (78, 142-lift)])
        limb([(178, 157), (204, 170-lift), (222, 142-lift)])
        y=133-lift
        d.line((49, y, 251, y), fill='#a6adb5', width=7)
        for xx in (54, 225):
            d.rounded_rectangle((xx, y-23, xx+21, y+23), radius=4, fill='#333b4a', outline='#7c8696', width=2)
    elif action in {'phone', 'write'}:
        limb([(122, 158), (110, 197), (166, 182)])
        limb([(178, 157), (195, 194), (179, 174)])
        d.rounded_rectangle((163, 147, 191, 187), radius=5, fill='#192131', outline='#8991a2', width=2)
        d.rectangle((168, 154, 186, 178), fill='#6788a4')
        if action == 'write':
            d.rounded_rectangle((143,183,211,202),radius=2,fill='#d9d0b6',outline='#807c73',width=1)
            d.line((178, 167, 200+math.sin(t*5)*4, 195), fill='#e7bd77', width=3)
    elif action == 'reach':
        limb([(122, 158), (94, 126), (77, 101+math.sin(t)*5)])
        limb([(178, 158), (201, 128), (222, 105)])
    elif sitting:
        limb([(121, 160), (103, 195), (147, 224)])
        limb([(179, 160), (191, 194), (171, 225)])
    else:
        swing = stride*.6
        limb([(122, 157), (111+swing, 199), (110+swing, 232)])
        limb([(179, 157), (192-swing, 199), (190-swing, 232)])
    rx, ry = (55, 62) if gender == 'male' else (52, 61)
    d.ellipse((cx-rx, hy-ry, cx+rx, hy+ry), fill=fill, outline=outline, width=3)
    # Soft jaw line and fine outer lashes are the only facial gender cues.
    ey = hy+4
    blink = (t % 4.7) < .13
    for ex in (cx-22, cx+22):
        if blink:
            d.line((ex-10, ey, ex+10, ey), fill=outline, width=3)
        else:
            if emotion in {'sad', 'tired', 'worried'}:
                d.arc((ex-15, ey-6, ex+15, ey+22), 0, 180, fill='#8c8085', width=3)
            d.ellipse((ex-11, ey-12, ex+11, ey+13), fill='#efebe3', outline=outline, width=2)
            d.ellipse((ex-3, ey-3, ex+3, ey+5), fill='#24232b')
            if gender == 'female' and not shadow:
                side=-1 if ex<cx else 1
                d.line((ex+side*10, ey-7, ex+side*15, ey-11), fill=outline, width=2)
    if shadow:
        d.line((cx-33, ey, cx-12, ey+4), fill='#e68b96', width=4)
        d.line((cx+12, ey+4, cx+33, ey), fill='#e68b96', width=4)
    brow_y=ey-23
    if emotion in {'sad', 'worried'}:
        d.line((cx-35, brow_y+5, cx-12, brow_y-3), fill=outline, width=3)
        d.line((cx+12, brow_y-3, cx+35, brow_y+5), fill=outline, width=3)
    elif emotion == 'determined':
        d.line((cx-35, brow_y-2, cx-12, brow_y+5), fill=outline, width=4)
        d.line((cx+12, brow_y+5, cx+35, brow_y-2), fill=outline, width=4)
    else:
        d.line((cx-33, brow_y, cx-13, brow_y), fill=outline, width=3)
        d.line((cx+13, brow_y, cx+33, brow_y), fill=outline, width=3)
    if emotion == 'happy':
        d.arc((cx-15, hy+24, cx+15, hy+42), 0, 180, fill=outline, width=3)
    elif emotion in {'sad', 'worried'}:
        d.arc((cx-12, hy+29, cx+12, hy+45), 180, 360, fill=outline, width=3)
    else:
        d.line((cx-10, hy+33, cx+10, hy+33), fill=outline, width=3)
    if action == 'sleep':
        # Closed eyelids follow the head when the rig is rotated.
        d.ellipse((cx-rx+3,hy-ry+3,cx+rx-3,hy+ry-3), fill=fill)
        d.arc((cx-34,ey-8,cx-10,ey+8),0,180,fill=outline,width=3)
        d.arc((cx+10,ey-8,cx+34,ey+8),0,180,fill=outline,width=3)
        d.line((cx-8,hy+33,cx+8,hy+33),fill=outline,width=2)
        layer = layer.rotate(85, resample=Image.Resampling.BICUBIC, expand=True)
    if scale != 1:
        layer = layer.resize((int(layer.width*scale), int(layer.height*scale)), Image.Resampling.LANCZOS)
    dest = (int(x-layer.width/2), int(floor-layer.height+45*scale))
    if shadow:
        aura = Image.new('RGBA', im.size)
        aura.alpha_composite(layer, dest)
        alpha=aura.getchannel('A').filter(ImageFilter.GaussianBlur(14))
        tint=Image.new('RGBA', im.size, '#b74f66'); tint.putalpha(alpha.point(lambda a:int(a*.5)))
        im.alpha_composite(tint)
    im.alpha_composite(layer, dest)


def frame(scene, gender, title, t, duration, index, total, subtitle=''):
    im = background(scene['location']).copy()
    progress = t/max(duration, .01)
    act = scene['action']
    x = 480
    if scene['location']=='bedroom' and act=='sleep':
        x=625
    elif act=='walk':
        x=290+progress*350
    elif scene['location']=='desk':
        x=490
    floor = 437 if act not in {'sit','phone','write'} else 416
    if scene['shadow']:
        character(im, x-110, 435, t+.5, gender, 'idle', 'sad', 1.06, True)
    character(im, x, floor, t, gender, act, scene['emotion'], .91)
    # Sparse atmospheric drift, deterministic across runs.
    d=ImageDraw.Draw(im)
    for i in range(23):
        px=(i*149+t*(3+i%4))%W; py=(i*67+t*4)%420
        d.ellipse((px,py,px+1,py+1),fill=(170,184,207,65))
    # Slow camera push, then letterbox and text stay fixed.
    z=1.015+.035*progress
    cw,ch=int(W/z),int(H/z)
    left=int((W-cw)/2+math.sin(t*.14)*3)
    im=im.crop((left,(H-ch)//2,left+cw,(H-ch)//2+ch)).resize((W,H),Image.Resampling.BICUBIC)
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,37),fill='#080b11');d.rectangle((0,487,W,H),fill='#080b11')
    d.text((30,15),title[:65].upper(),font=font(11),fill='#aab3c3')
    d.text((865,15),f'{index+1:02d} / {total:02d}',font=font(11),fill='#aab3c3')
    if subtitle:
        text_center(im,subtitle,448,size=19,width=830)
    fade=min(1,t/.5,(duration-t)/.5)
    if fade<1:
        im=Image.blend(Image.new('RGBA',im.size,'#080b11'),im,max(0,fade))
    return im.convert('RGB')
