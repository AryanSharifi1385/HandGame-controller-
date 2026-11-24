from PIL import Image, ImageDraw, ImageFilter
import random, math, os
W,H=1600,460
OUT='theme_art'
os.makedirs(OUT,exist_ok=True)

def lerp(a,b,t): return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))
def gradient(top,bottom):
    im=Image.new('RGB',(W,H)); p=im.load()
    for y in range(H):
        c=lerp(top,bottom,y/(H-1))
        for x in range(W): p[x,y]=c
    return im

def polygon(draw, pts, fill): draw.polygon(pts, fill=fill)
def save(name, im):
    # cinematic vignette and darken left-side copy zone for readability
    overlay=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(overlay)
    for x in range(W):
        alpha=int(168*max(0,1-x/(W*.64)))
        od.line((x,0,x,H), fill=(3,5,12,alpha))
    # vignette subtle bottom strip
    for y in range(H-100,H):
        alpha=int(75*(y-(H-100))/100)
        od.line((0,y,W,y), fill=(0,0,0,alpha))
    im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')
    im.save(os.path.join(OUT,name+'.jpg'),quality=91,optimize=True)

# Cyberpunk: megacity, neon towers, rain, magenta/cyan
random.seed(22)
im=gradient((13,13,35),(5,8,17)); d=ImageDraw.Draw(im,'RGBA')
# haze
haze=Image.new('RGBA',(W,H),(0,0,0,0)); hd=ImageDraw.Draw(haze)
for x,col,rad in [(1020,(255,28,160,80),220),(1350,(0,225,255,75),190),(750,(100,30,255,50),180)]:
    hd.ellipse((x-rad,100-rad,x+rad,100+rad),fill=col)
haze=haze.filter(ImageFilter.GaussianBlur(75)); im=Image.alpha_composite(im.convert('RGBA'),haze); d=ImageDraw.Draw(im,'RGBA')
for i in range(45):
    x=random.randint(650,W); bw=random.randint(20,75); bh=random.randint(70,300); y=H-bh
    col=random.choice([(8,14,31,255),(13,20,44,255),(18,15,43,255)])
    d.rectangle((x,y,x+bw,H),fill=col,outline=(70,80,120,110),width=1)
    for wx in range(x+5,x+bw-3,10):
        for wy in range(y+8,H-15,17):
            if random.random()<.45: d.rectangle((wx,wy,wx+3,wy+6),fill=random.choice([(0,245,255,190),(255,40,170,180),(255,200,80,150)]))
for i in range(140):
    x=random.randint(600,W); y=random.randint(0,H); d.line((x,y,x-12,y+random.randint(12,38)),fill=random.choice([(0,240,255,75),(255,35,150,75)]),width=1)
# skyline road glow
polygon(d,[(920,H),(1150,330),(1290,330),(1510,H)],(9,15,29,255)); d.line((1215,350,1390,H),fill=(0,230,255,130),width=4)
save('cyberpunk',im)

# Ghost of Tsushima: misty Japanese mountains, red sun, pagoda, falling leaves
random.seed(23); im=gradient((28,38,50),(188,112,78)); d=ImageDraw.Draw(im,'RGBA')
d.ellipse((1050,30,1330,310),fill=(224,82,62,210))
polygon(d,[(520,300),(760,120),(930,260),(1080,140),(1320,315),(1530,200),(W,300),(W,H),(500,H)],(38,52,48,220))
polygon(d,[(640,350),(880,215),(1080,350),(1240,240),(1460,365),(W,300),(W,H),(580,H)],(20,35,34,245))
# torii gate
red=(116,39,35,255); d.rectangle((1030,240,1050,440),fill=red); d.rectangle((1190,240,1210,440),fill=red); d.rectangle((1000,222,1240,242),fill=red); d.rectangle((1020,202,1220,219),fill=red)
# grass / leaves
for i in range(120):
 x=random.randint(650,W); y=random.randint(30,H); r=random.randint(2,7); d.ellipse((x-r,y-r,x+r,y+r),fill=random.choice([(213,92,55,180),(237,166,85,170),(166,47,43,170)]))
# distant temple
for lev in range(3):
 y=315+lev*28; x=1330-lev*20; wid=120-lev*12
 polygon(d,[(x-15,y),(x+wid//2,y-22),(x+wid+15,y),(x+wid,y+8),(x,y+8)],(30,31,29,255)); d.rectangle((x+12,y+8,x+wid-12,y+48),fill=(22,27,26,255))
save('ghost_of_tsushima',im)

# Last of Us: reclaimed city ruins, forest, overgrowth, overcast
random.seed(24); im=gradient((42,57,51),(119,126,96)); d=ImageDraw.Draw(im,'RGBA')
# cloud haze
cloud=Image.new('RGBA',(W,H),(0,0,0,0)); cd=ImageDraw.Draw(cloud)
for i in range(18):
 x=random.randint(500,W); y=random.randint(-40,210); rx=random.randint(80,200); ry=random.randint(20,65); cd.ellipse((x-rx,y-ry,x+rx,y+ry),fill=(188,190,157,25))
im=Image.alpha_composite(im.convert('RGBA'),cloud.filter(ImageFilter.GaussianBlur(30))); d=ImageDraw.Draw(im,'RGBA')
# ruined towers
for x,w,h in [(760,130,260),(900,160,330),(1100,100,210),(1250,180,290),(1450,120,245)]:
 y=H-h; d.rectangle((x,y,x+w,H),fill=(42,53,45,255),outline=(86,99,76,255),width=3)
 for yy in range(y+20,H-20,35):
  for xx in range(x+12,x+w-10,25):
   if random.random()<.65: d.rectangle((xx,yy,xx+9,yy+15),fill=(20,31,28,220))
# vegetation
for i in range(80):
 x=random.randint(630,W); y=random.randint(220,H); d.line((x,y,x+random.randint(-12,12),y-random.randint(20,80)),fill=(30,68,43,190),width=random.randint(2,5))
 for j in range(3):
  xx=x+random.randint(-15,15); yy=y-random.randint(15,70); d.ellipse((xx-10,yy-5,xx+10,yy+5),fill=random.choice([(54,91,50,190),(72,107,53,190),(113,128,68,170)]))
# birds
for x,y in [(1190,130),(1230,160),(1330,115),(1410,145)]: d.arc((x,y,x+18,y+12),200,340,fill=(28,37,31,200),width=2)
save('the_last_of_us',im)

# God of War: frozen mountains, aurora, rune-like light arcs
random.seed(25); im=gradient((6,23,42),(57,86,106)); d=ImageDraw.Draw(im,'RGBA')
for i in range(5):
 pts=[]; x0=500+i*170
 pts=[(x0,H),(x0+90,100+random.randint(-20,60)),(x0+180,H)]
 polygon(d,pts,random.choice([(35,61,78,230),(48,75,89,240),(72,101,113,230)]))
 polygon(d,[(x0+60,260),(x0+90,100),(x0+120,260)],(205,224,226,170))
# aurora curves
for j,col in enumerate([(85,235,199,80),(95,178,255,75),(174,123,255,65)]):
 pts=[]
 for x in range(600,W+1,20): pts.append((x,70+int(38*math.sin(x/115+j)+j*22)))
 d.line(pts,fill=col,width=12)
# runic circles/marks
for x,y in [(1220,300),(1390,270),(1510,350)]:
 d.ellipse((x-38,y-38,x+38,y+38),outline=(173,219,238,120),width=2); d.line((x,y-25,x,y+25),fill=(173,219,238,130),width=2); d.line((x-18,y,x+18,y),fill=(173,219,238,130),width=2)
save('god_of_war',im)

# GTA VI: tropical neon skyline, palm silhouettes, sunset, coastal boulevard
random.seed(26); im=gradient((42,20,73),(255,106,115)); d=ImageDraw.Draw(im,'RGBA')
d.ellipse((1030,65,1330,365),fill=(255,187,155,180))
# ocean bands
for y in range(285,390,14): d.line((620,y,W,y+random.randint(-5,5)),fill=(46,205,210,80),width=3)
# art deco skyline
for x in range(700,W,75):
 h=random.randint(90,250); w=random.randint(42,68); y=H-h
 d.rectangle((x,y,x+w,H),fill=random.choice([(26,29,63,245),(47,29,76,245),(32,49,83,245)]),outline=(255,110,172,150),width=2)
 for yy in range(y+15,H-10,20): d.line((x+6,yy,x+w-6,yy),fill=(47,221,229,100),width=2)
# palms
for x,y in [(850,290),(1480,280)]:
 d.line((x,y+160,x+15,y),fill=(22,28,48,255),width=8)
 for ang in range(0,360,45):
  ex=x+int(75*math.cos(math.radians(ang))); ey=y+int(35*math.sin(math.radians(ang)))
  d.line((x+15,y,ex,ey),fill=(20,35,55,255),width=6)
save('gta_vi',im)

# Matrix: digital green rain / abstract terminal city
random.seed(27); im=gradient((2,11,8),(4,26,15)); d=ImageDraw.Draw(im,'RGBA')
for x in range(580,W,22):
 y=random.randint(-300,100); length=random.randint(120,400)
 for i in range(length//16):
  yy=y+i*16
  if 0<=yy<H:
   col=(62,255,119,random.randint(45,170)); d.line((x,yy,x,yy+10),fill=col,width=random.choice([1,2]))
# abstract server racks
for x in range(720,W,145):
 d.rounded_rectangle((x,130,x+100,H-18),radius=7,fill=(3,18,12,180),outline=(28,117,57,150),width=2)
 for y in range(150,H-25,26): d.line((x+12,y,x+88,y),fill=(24,140,66,110),width=2)
save('matrix',im)

# Synthwave: retro sunset, purple mountains, neon grid
random.seed(28); im=gradient((18,8,53),(183,35,133)); d=ImageDraw.Draw(im,'RGBA')
d.ellipse((1000,55,1320,375),fill=(255,112,196,220))
for y in range(215,360,16): d.rectangle((1000,y,1320,y+5),fill=(43,14,74,240))
polygon(d,[(520,H),(800,190),(930,310),(1090,145),(1290,330),(1450,210),(W,H)],(32,18,83,255))
# grid perspective
for y in [330,350,375,405,440]: d.line((620,y,W,y),fill=(0,240,255,140),width=2)
for x in range(620,W+1,80): d.line((1120,305,x,H),fill=(0,240,255,100),width=2)
save('synthwave',im)

# Arctic: aurora over ice peaks, premium cold-blue atmosphere
random.seed(29); im=gradient((7,26,50),(49,93,125)); d=ImageDraw.Draw(im,'RGBA')
# aurora veils
veil=Image.new('RGBA',(W,H),(0,0,0,0)); vd=ImageDraw.Draw(veil)
for i,col in enumerate([(69,255,213,75),(75,182,255,65),(169,123,255,55)]):
 pts=[]
 for x in range(520,W+1,16): pts.append((x,50+i*20+int(50*math.sin(x/135+i))))
 vd.line(pts,fill=col,width=28)
im=Image.alpha_composite(im.convert('RGBA'),veil.filter(ImageFilter.GaussianBlur(22))); d=ImageDraw.Draw(im,'RGBA')
polygon(d,[(540,H),(750,230),(870,330),(1060,130),(1240,300),(1400,190),(W,310),(W,H)],(20,43,67,255))
polygon(d,[(990,220),(1060,130),(1120,230),(1080,210),(1050,228)],(226,243,255,220))
polygon(d,[(680,300),(750,230),(800,290),(760,275)],(222,240,252,180))
for i in range(180):
 x=random.randint(600,W); y=random.randint(0,H); r=random.choice([1,1,2]); d.ellipse((x-r,y-r,x+r,y+r),fill=(220,244,255,random.randint(70,180)))
save('arctic',im)
print('created', len(os.listdir(OUT)), 'theme backgrounds')
