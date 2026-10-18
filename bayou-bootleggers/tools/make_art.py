#!/usr/bin/env python3
"""Author the game's indexed pixel art. Standard library only; no borrowed assets."""
from pathlib import Path
import math, random, struct, zlib

ROOT = Path(__file__).resolve().parents[1]
PALETTE = [0,1,3,2,19,4,36,34,38,54,55,5,9,18,27,63]
FONT = {
'A':['01110','10001','10001','11111','10001','10001','10001'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'F':['11111','10000','10000','11110','10000','10000','10000'],
'G':['01111','10000','10000','10111','10001','10001','01111'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['111','010','010','010','010','010','111'],
'J':['00111','00010','00010','00010','10010','10010','01100'],
'K':['10001','10010','10100','11000','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','11001','10101','10011','10011','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'Q':['01110','10001','10001','10001','10101','10010','01101'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
'W':['10001','10001','10001','10101','10101','11011','10001'],
'X':['10001','10001','01010','00100','01010','10001','10001'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'Z':['11111','00001','00010','00100','01000','10000','11111'],
'-':['000','000','000','111','000','000','000'],
'.':['0','0','0','0','0','1','1'],
':':['0','1','1','0','1','1','0'],
"'":['1','1','0','0','0','0','0'],
'!':['1','1','1','1','1','0','1'],
' ':['000']*7,
}

class Canvas:
    def __init__(self,w=320,h=200):
        self.w,self.h=w,h
        self.p=bytearray(w*h)
    def dot(self,x,y,c):
        if 0<=x<self.w and 0<=y<self.h: self.p[y*self.w+x]=c
    def rect(self,x,y,xx,yy,c):
        x,xx=max(0,x),min(self.w-1,xx)
        for row in range(max(0,y),min(self.h-1,yy)+1):
            if xx>=x: self.p[row*self.w+x:row*self.w+xx+1]=bytes([c])*(xx-x+1)
    def line(self,x,y,xx,yy,c):
        dx,dy=abs(xx-x),-abs(yy-y); sx=1 if x<xx else -1; sy=1 if y<yy else -1
        error=dx+dy
        while True:
            self.dot(x,y,c)
            if x==xx and y==yy: break
            e=2*error
            if e>=dy: error+=dy; x+=sx
            if e<=dx: error+=dx; y+=sy
    def poly(self,points,c):
        for y in range(min(p[1] for p in points),max(p[1] for p in points)+1):
            hits=[]
            for (x1,y1),(x2,y2) in zip(points,points[1:]+points[:1]):
                if (y1<=y<y2) or (y2<=y<y1):
                    hits.append(x1+(y-y1)*(x2-x1)/(y2-y1))
            hits.sort()
            for a,b in zip(hits[::2],hits[1::2]): self.rect(math.ceil(a),y,math.floor(b),y,c)
    def ellipse(self,x,y,rx,ry,c):
        for dy in range(-ry,ry+1):
            r=int(rx*math.sqrt(max(0,1-dy*dy/(ry*ry or 1))))
            self.rect(x-r,y+dy,x+r,y+dy,c)
    def text(self,s,x,y,c,scale=1,center=False):
        s=s.upper(); width=sum((len(FONT.get(ch,FONT[' '])[0])+1)*scale for ch in s)-scale
        if center: x-=width//2
        for ch in s:
            glyph=FONT.get(ch,FONT[' '])
            for yy,row in enumerate(glyph):
                for xx,bit in enumerate(row):
                    if bit=='1': self.rect(x+xx*scale,y+yy*scale,x+(xx+1)*scale-1,y+(yy+1)*scale-1,c)
            x+=(len(glyph[0])+1)*scale
    def packed(self):
        assert self.w%2==0
        return bytes((self.p[i]<<4)|self.p[i+1] for i in range(0,len(self.p),2))
    def png(self,path,scale=1):
        def rgb(v): return tuple((((v>>h)&1)*2+((v>>l)&1))*85 for h,l in [(5,2),(4,1),(3,0)])
        raw=bytearray()
        for y in range(self.h):
            row=bytearray([0])
            for x in range(self.w): row.extend(bytes(rgb(PALETTE[self.p[y*self.w+x]]))*scale)
            for _ in range(scale): raw.extend(row)
        def chunk(kind,data): return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
        data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',self.w*scale,self.h*scale,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')
        path.write_bytes(data)

def scene(room):
    r=random.Random(1042+room); a=Canvas()
    # Layered dusk, sparse stars, dithered low mist.
    a.rect(0,24,319,77,1); a.rect(0,78,319,103,11)
    for i in range(65): a.dot(r.randrange(320),r.randrange(26,73),2 if i%3 else 10)
    a.ellipse(266,43,13,13,9); a.ellipse(268,41,10,10,10)
    a.ellipse(270,38,3,2,9); a.ellipse(262,48,2,2,9)
    for i in range(24):
        x=i*15+r.randrange(8); y=90+r.randrange(7)
        a.poly([(x-12,103),(x-8,y-17),(x,y-24),(x+9,y-13),(x+13,103)],2)
    a.rect(0,102,319,123,2)
    for i in range(155):
        x=r.randrange(320); y=r.randrange(104,124)
        a.line(x,y,x+r.randrange(2,16),y,4 if i%4==0 else 1)
    # Moonlight catches broken ripples behind the wharf.
    for y in range(105,123,3):
        x=266+r.randrange(-14,10); a.line(x,y,x+r.randrange(8,27),y,9 if y%2 else 8)
    for x,top in [(9,33),(45,49),(292,45),(315,27)]:
        a.poly([(x-9,119),(x-3,top+18),(x,top),(x+4,top+19),(x+10,119)],3)
        a.line(x,top+6,x-16,top-3,3); a.line(x+2,top+19,x+19,top+3,3)
        for side in [-1,1]:
            for i in range(5):
                xx=x+side*(7+i*4); yy=top+8+i
                a.poly([(xx-12,yy+2),(xx-4,yy-6),(xx+5,yy-4),(xx+13,yy+5)],3)
                a.line(xx+4,yy+2,xx+3,yy+15+r.randrange(8),4)
                a.line(xx+7,yy+4,xx+6,yy+12,2)
        a.line(x-2,top+24,x-5,114,2)
    if room in (0,1):
        left,right=(74,174) if room==0 else (63,244)
        top=65 if room==0 else 49
        for x in range(left+8,right,29): a.rect(x,100,x+5,126,5); a.line(x+1,105,x+1,122,8)
        a.rect(left,top+13,right,109,5)
        for y in range(top+15,108,5): a.line(left+1,y,right-1,y,7)
        for i in range(65):
            x=r.randrange(left+2,right-4); y=r.randrange(top+15,107); a.line(x,y,x+3,y,8 if i%6==0 else 5)
        a.poly([(left-9,top+14),(left+14,top-1),(right-12,top-1),(right+10,top+14)],1)
        a.poly([(left-7,top+10),(left+14,top),(right-12,top),(right+8,top+10)],7)
        for x in range(left+15,right-12,8): a.line(x,top+1,x-13,top+9,8)
        a.line(left-8,top+12,right+9,top+12,5)
        for x in [left+12,right-29]:
            a.rect(x,top+22,x+17,top+39,1); a.rect(x+2,top+24,x+15,top+36,9)
            a.rect(x+3,top+25,x+14,top+35,8); a.line(x+8,top+24,x+8,top+37,5)
            a.line(x+1,top+30,x+16,top+30,5)
        a.rect((left+right)//2-9,top+24,(left+right)//2+11,109,1)
        a.rect((left+right)//2-7,top+26,(left+right)//2+9,108,5)
        a.dot((left+right)//2+6,95,9)
        a.rect(left-2,110,right+2,115,8); a.line(left-2,115,right+2,115,1)
        if room==1:
            a.rect(92,61,217,76,1); a.line(93,62,216,62,9)
            a.text('SHRIMP SHACK',154,65,9,center=True)
            for x in range(69,244,18):
                a.line(x,46,x+18,48,5); a.ellipse(x+9,49,1,2,9)
        else:
            a.rect(96,83,152,93,1); a.text('BAIT',124,85,10,center=True)
    else:
        # Shrimp trawler: wheelhouse, hull, rigging, nets, portholes.
        a.poly([(106,103),(289,103),(275,120),(132,120)],1)
        a.poly([(109,103),(286,103),(273,115),(135,115)],6)
        a.line(120,108,280,108,10); a.line(136,117,271,117,5)
        a.rect(178,73,244,102,5); a.rect(173,69,249,74,10)
        for x in [184,204,224]:
            a.rect(x,79,x+14,91,1); a.rect(x+2,81,x+11,88,4); a.line(x+3,87,x+8,82,14)
        a.text('NONC CLAUDE',210,95,9,center=True)
        a.rect(188,56,194,69,5); a.rect(188,54,195,57,1)
        a.line(148,39,148,103,8); a.line(261,49,261,103,8)
        a.line(148,41,260,64,10); a.line(148,43,112,101,5)
        a.line(261,51,284,103,5)
        a.poly([(150,50),(171,91),(152,91)],3)
        for y in range(58,92,5): a.line(152,y,151+(y-49)//2,y,4)
        a.ellipse(257,108,4,5,1); a.ellipse(257,108,2,3,8)
    # Perspective dock. Lines break at staggered joints; restrained grain.
    a.rect(0,124,319,183,5)
    for y in range(125,184,8):
        a.line(0,y,319,y,1); a.line(0,y+1,319,y+1,7)
        for x in range((y%3)*19,320,56):
            a.line(x,y+2,x+3,y+7,1); a.dot(x+5,y+3,8); a.dot(x+7,y+6,1)
    for i in range(370):
        x=r.randrange(320); y=r.randrange(126,183)
        if y%8>2: a.line(x,y,x+r.randrange(2,10),y,7 if i%7 else 8)
    a.rect(0,184,319,187,1); a.line(0,184,319,184,8)
    a.rect(0,188,319,199,0); a.text('ARROWS MOVE  SPACE JUMP  CTRL PADDLE  Q QUIT',160,191,10,center=True)
    # Dock posts, ropes, crates and a crawfish trap stay behind actors.
    for x in [17,302]:
        a.rect(x-4,104,x+4,125,1); a.rect(x-3,105,x+2,124,7)
        a.ellipse(x,104,4,2,8); a.line(x-2,109,x+3,109,10)
        a.line(x-2,112,x+3,112,8)
    a.line(22,110,48,113,8); a.line(48,113,70,110,8)
    for x,y in [(224,105),(245,109)]:
        a.rect(x,y,x+19,y+14,1); a.rect(x+1,y+1,x+18,y+12,7)
        a.line(x+2,y+2,x+16,y+11,8); a.line(x+17,y+2,x+3,y+11,8)
        a.line(x+1,y+5,x+18,y+5,5)
    a.rect(44,111,63,121,1)
    for x in range(46,63,3): a.line(x,112,x,120,8)
    a.line(45,115,62,115,7); a.line(45,119,62,119,7)
    # Integrated HUD frame.
    a.rect(0,0,319,23,0); a.line(0,23,319,23,8)
    a.text('BOOTS',8,3,9); a.text('HEALTH',72,3,9); a.text('SCORE',210,3,9)
    a.text(['CYPRESS LANDING','THE SHRIMP SHACK',"CAPTAIN'S WHARF"][room],8,14,10)
    return a

def sprite(pose):
    a=Canvas(48,44); bob=1 if pose==2 else 0
    lean=2 if pose==3 else -2 if pose==4 else 0
    # Rear arm, neck, trouser silhouette and individually shaded shrimp boots.
    a.poly([(15+lean,17+bob),(11+lean,23+bob),(12+lean,29+bob),(16+lean,28+bob),(18+lean,20+bob)],1)
    a.line(14+lean,22+bob,13+lean,26+bob,4)
    a.rect(18+lean,13+bob,25+lean,19+bob,1); a.rect(20+lean,14+bob,24+lean,18+bob,8)
    foot1,foot2=(15,27) if pose==1 else (19,23) if pose==2 else (17,25)
    if pose==5: foot1,foot2=14,28
    a.poly([(16+lean,27+bob),(28+lean,27+bob),(foot2+3,37),(foot2-2,39),(23,32),(foot1+3,39),(foot1-3,37)],1)
    a.poly([(17+lean,29+bob),(22+lean,29+bob),(foot1+2,37),(foot1-2,37)],12)
    a.poly([(23+lean,29+bob),(27+lean,29+bob),(foot2+2,37),(foot2-2,37)],4)
    a.line(19+lean,30+bob,foot1,36,14)
    for foot,yy in [(foot1,38),(foot2,39)]:
        if pose==5: yy-=3
        a.poly([(foot-3,yy-3),(foot+2,yy-3),(foot+3,yy),(foot+6,yy+1),(foot+6,yy+3),(foot-4,yy+3)],1)
        a.rect(foot-2,yy-2,foot+1,yy+1,5); a.line(foot-2,yy-2,foot+1,yy-2,8)
        a.line(foot-3,yy+2,foot+5,yy+2,7)
    # Shirt outline, rolled sleeves, vest seam, folds, belt buckle.
    a.poly([(16+lean,17+bob),(20+lean,16+bob),(26+lean,17+bob),(30+lean,22+bob),(27+lean,29+bob),(16+lean,29+bob),(14+lean,22+bob)],1)
    a.poly([(17+lean,18+bob),(21+lean,19+bob),(25+lean,18+bob),(28+lean,22+bob),(26+lean,27+bob),(17+lean,27+bob),(16+lean,22+bob)],14)
    a.poly([(17+lean,20+bob),(19+lean,22+bob),(19+lean,26+bob),(16+lean,26+bob)],4)
    a.line(23+lean,20+bob,23+lean,27+bob,4); a.dot(24+lean,22+bob,15)
    a.line(17+lean,26+bob,21+lean,25+bob,4); a.rect(16+lean,28+bob,27+lean,29+bob,5)
    a.rect(22+lean,28+bob,24+lean,29+bob,9)
    # Three-quarter face: ear, cheek highlight, sideburn, moustache, eye.
    a.poly([(17+lean,7+bob),(26+lean,7+bob),(28+lean,10+bob),(28+lean,12+bob),(30+lean,13+bob),(27+lean,14+bob),(26+lean,17+bob),(20+lean,17+bob),(17+lean,13+bob)],1)
    a.poly([(19+lean,8+bob),(26+lean,8+bob),(27+lean,12+bob),(29+lean,13+bob),(26+lean,14+bob),(25+lean,16+bob),(21+lean,16+bob),(19+lean,13+bob)],10)
    a.rect(18+lean,10+bob,20+lean,13+bob,8); a.dot(19+lean,11+bob,10)
    a.line(21+lean,15+bob,25+lean,15+bob,8)
    a.rect(26+lean,10+bob,27+lean,11+bob,1); a.dot(26+lean,10+bob,15)
    a.line(24+lean,13+bob,27+lean,13+bob,5)
    # Straw hat with crown, band, curved brim, and lit rim.
    a.poly([(13+lean,7+bob),(17+lean,5+bob),(18+lean,1+bob),(25+lean,0+bob),(28+lean,5+bob),(32+lean,7+bob),(31+lean,9+bob),(15+lean,9+bob)],1)
    a.poly([(17+lean,6+bob),(19+lean,2+bob),(24+lean,1+bob),(27+lean,6+bob)],9)
    a.line(19+lean,3+bob,24+lean,2+bob,10); a.line(18+lean,6+bob,27+lean,6+bob,8)
    a.line(14+lean,7+bob,31+lean,7+bob,9); a.line(17+lean,8+bob,29+lean,8+bob,8)
    # Forearm / paddle pose; attack silhouette extends well beyond the body.
    if pose==3:
        a.poly([(27,19+bob),(31,19+bob),(36,22+bob),(35,25+bob),(30,23+bob),(27,23+bob)],1)
        a.line(29,20+bob,34,23+bob,10); a.line(29,21+bob,33,23+bob,8)
        a.line(33,22,46,15,1); a.line(33,23,47,16,1); a.line(33,22,46,16,9)
        a.poly([(40,17),(44,12),(47,12),(48,15),(44,19)],1)
        a.poly([(41,17),(45,13),(47,13),(46,16),(44,18)],8)
        a.line(42,17,46,14,9)
        a.line(35,11,40,8,10); a.line(39,22,43,21,15)
    elif pose==4:
        a.poly([(27+lean,20),(32+lean,16),(34+lean,17),(31+lean,23),(28+lean,24)],1)
        a.line(29+lean,20,32+lean,17,10)
        a.line(30,14,39,4,1); a.line(31,14,40,4,9); a.ellipse(40,3,3,3,8)
    else:
        a.poly([(28+lean,20+bob),(31+lean,22+bob),(29+lean,28+bob),(25+lean,28+bob),(26+lean,25+bob)],1)
        a.line(29+lean,22+bob,28+lean,26+bob,10); a.dot(27+lean,27+bob,8)
        a.line(28+lean,28+bob,38+lean,34+bob,1); a.line(28+lean,27+bob,38+lean,33+bob,9)
        a.poly([(35+lean,30+bob),(41+lean,33+bob),(41+lean,37+bob),(38+lean,38+bob),(33+lean,33+bob)],1)
        a.poly([(35+lean,31+bob),(40+lean,34+bob),(40+lean,36+bob),(38+lean,36+bob),(34+lean,33+bob)],8)
        a.line(36+lean,32+bob,39+lean,35+bob,9)
    return a

def alligator(snap=False):
    a=Canvas(48,44)
    # Low, broad silhouette, ridged back, tapering tail and squat legs.
    a.poly([(1,40),(9,34),(17,30),(29,30),(35,33),(46,34),(47,40),
            (33,42),(14,41)],1)
    a.poly([(4,39),(15,33),(29,32),(35,35),(45,36),(45,39),(30,40),(14,39)],2)
    a.ellipse(23,35,11,4,3)
    for x in range(15,31,4):
        a.poly([(x,32),(x+1,28),(x+3,32)],1)
        a.dot(x+1,31,14)
    for x in (16,29):
        a.poly([(x,37),(x+5,37),(x+7,43),(x+1,43)],1)
        a.line(x+2,39,x+5,41,2)
        a.line(x+2,42,x+5,42,10)
    a.ellipse(34,33,4,4,1); a.dot(35,31,9); a.dot(36,31,1)
    if snap:
        a.poly([(34,34),(38,26),(46,24),(47,27),(40,33),(46,37),(46,40),(34,39)],1)
        a.line(37,32,45,26,2); a.line(36,38,45,38,3)
        a.line(38,34,44,36,8)
        for x,y in [(39,30),(42,28),(40,37),(44,38)]:
            a.line(x,y,x,y+2 if y<32 else y-2,15)
        # Warning splash above the snout stays within the cached patch.
        a.line(33,21,33,25,9); a.dot(33,27,9)
    else:
        a.line(36,35,45,35,3); a.line(35,38,45,38,1)
        for x in (39,43): a.dot(x,39,15)
    return a

def title():
    a=scene(2)
    a.rect(0,0,319,23,0)
    a.rect(30,29,289,157,1); a.rect(32,31,287,155,0)
    a.line(34,33,285,33,8); a.line(34,153,285,153,8)
    a.text('BAYOU',161,41,5,4,True); a.text('BAYOU',159,39,9,4,True)
    a.text('BOOTLEGGERS',161,74,5,3,True); a.text('BOOTLEGGERS',159,72,10,3,True)
    a.line(60,100,259,100,8)
    a.text('NONC CLAUDE STOLE YOUR SHRIMP BOAT.',160,109,10,center=True)
    a.text('TAKE IT BACK. ONE DOCK AT A TIME.',160,121,14,center=True)
    a.text('PRESS SPACE TO START',160,140,9,center=True)
    a.text('A LOUISIANA DOCKSIDE BRAWLER',160,174,10,center=True)
    return a

def pack_background(a):
    """Per-row PackBits, with 165 big-endian offsets for clipped decoding."""
    raw=a.packed(); offsets=[]; out=bytearray()
    for y in range(24,188):
        offsets.append(len(out)); data=raw[y*160:(y+1)*160]; i=0
        while i<160:
            run=1
            while i+run<160 and data[i+run]==data[i] and run<128: run+=1
            if run>=3:
                out.extend((128+run-1,data[i])); i+=run
            else:
                start=i; i+=run
                while i<160 and i-start<128:
                    r=1
                    while i+r<160 and data[i+r]==data[i] and r<128: r+=1
                    if r>=3: break
                    i+=min(r,128-(i-start))
                out.append(i-start-1); out.extend(data[start:i])
    offsets.append(len(out))
    result=struct.pack('>165H',*offsets)+out
    assert len(result)<=9216
    return result

def main():
    out=ROOT/'assets'; out.mkdir(exist_ok=True)
    for i in range(3):
        a=scene(i); (out/f'dock{i}.bin').write_bytes(a.packed()); a.png(out/f'dock{i}.png',2)
        (out/f'dock{i}.rle').write_bytes(pack_background(a))
    a=title(); (out/'title.bin').write_bytes(a.packed()); a.png(out/'title.png',2)
    poses=[sprite(i) for i in range(6)]+[alligator(),alligator(True)]
    data=bytearray(); offsets=[]
    for a in poses:
        for flip in [False,True]:
            offsets.append(len(data))
            for y in range(44):
                pixels=list(a.p[y*48:(y+1)*48])
                if flip: pixels.reverse()
                row=bytes((pixels[x]<<4)|pixels[x+1] for x in range(0,48,2))
                runs=[]; x=0
                while x<24:
                    if row[x]==0: x+=1; continue
                    start=x
                    # Runs share a transparency mode so native code can
                    # choose its opaque/masked loop once for the whole run.
                    mode = 128 if row[x]<16 else (64 if row[x]&15==0 else 0)
                    while x<24 and row[x]!=0:
                        next_mode = 128 if row[x]<16 else (64 if row[x]&15==0 else 0)
                        if next_mode!=mode: break
                        x+=1
                    runs.append((start,row[start:x],mode))
                data.append(len(runs))
                for start,run,mode in runs: data.extend((start,len(run)|mode)); data.extend(run)
    lines=['/* Generated by tools/make_art.py; transparent runs omitted. */',
           '#define SPRITE_W 48','#define SPRITE_H 44','#define SPRITE_VARIANTS 16',
           'static const unsigned int sprite_offsets[16] = {'+','.join(str(v) for v in offsets)+'};',
           'static const unsigned char sprite_stream['+str(len(data))+'] = {']
    lines += [','.join(str(v) for v in data[i:i+24])+',' for i in range(0,len(data),24)]
    lines.append('};')
    maps=[list(range(16)),[0,1,2,3,7,5,6,7,8,8,10,11,3,13,6,15],
          [0,1,2,3,11,5,6,7,8,10,10,11,12,13,11,15]]
    pairs=bytes((m[i>>4]<<4)|m[i&15] for m in maps for i in range(256))
    lines.append('static const unsigned char pair_colors[768] = {')
    lines += [','.join(str(v) for v in pairs[i:i+24])+',' for i in range(0,len(pairs),24)]
    lines.append('};')
    (ROOT/'src/sprites.h').write_text('\n'.join(lines)+'\n')
    sheet=Canvas(48*len(poses),44)
    for i,a in enumerate(poses):
        for y in range(44): sheet.p[y*sheet.w+i*48:y*sheet.w+(i+1)*48]=a.p[y*48:(y+1)*48]
    sheet.png(out/'sprites.png',3)
    # Representative artwork preview; native screenshots are kept separately.
    preview=scene(0)
    for x,y,pose,foe in [(75,164,3,False),(178,143,1,True),(235,168,2,True)]:
        p=poses[pose]
        remap={14:6,4:7,9:8,12:3} if foe else {}
        for yy in range(44):
            for xx in range(48):
                v=p.p[yy*48+xx]
                if v: preview.dot(x-24+xx,y-43+yy,remap.get(v,v))
    preview.png(out/'art-preview.png',2)
    print('Generated four 320x200 scenes and eight 48x44 transparent sprite poses.')

if __name__=='__main__': main()
