#!/usr/bin/env python3
"""Original 16-color Louisiana bush-track scenery and galloping horses."""
from make_art import Canvas, ROOT
import random

def track():
    a=Canvas(); r=random.Random(1938)
    a.rect(0,24,319,79,1)
    a.ellipse(282,44,12,10,9)
    for x in range(-8,340,22):
        a.poly([(x-15,89),(x-9,56),(x,40+r.randrange(18)),(x+10,57),(x+17,89)],2)
        a.line(x,58,x,89,5)
        for y in range(62,86,6): a.line(x-5,y,x-3,y+8,3)
    a.rect(0,83,319,115,3)
    a.rect(0,116,319,187,5)
    for i in range(850):
        x=r.randrange(320); y=r.randrange(118,187)
        a.line(x,y,x+r.randrange(1,4),y,8 if i%3 else 7)
    for y in (130,148,166,184):
        for x in range(0,320,16): a.line(x,y,x+6,y,8)
    # Hand-painted starting post and checkered finishing upright.
    a.line(33,116,33,186,10)
    for y in range(116,188,4):
        a.rect(279,y,282,y+3,15 if (y//4)&1 else 1)
        a.rect(283,y,286,y+3,1 if (y//4)&1 else 15)
    a.rect(270,83,273,116,8); a.rect(300,83,303,116,8)
    a.rect(267,78,306,88,1); a.text('FINISH',287,79,10,center=True)
    # Old men along the rough timber rail: hats, moustaches, suspenders,
    # rolled sleeves, walking sticks and expressive raised arms.
    for i,x in enumerate((15,57,104,151,198,242,314)):
        y=70+(i%2)*4
        a.line(x-3,y+16,x-5,y+28,1); a.line(x+3,y+16,x+4,y+28,1)
        a.rect(x-6,y+27,x-2,y+29,5); a.rect(x+2,y+27,x+7,y+29,5)
        a.rect(x-5,y+6,x+5,y+18,1); a.rect(x-4,y+7,x+4,y+16,10 if i%2 else 14)
        a.line(x-2,y+8,x-2,y+17,5); a.line(x+2,y+8,x+2,y+17,5)
        a.rect(x-3,y-1,x+3,y+6,8); a.line(x-2,y+2,x+2,y+2,15)
        a.dot(x+2,y,1); a.line(x-4,y+6,x+3,y+6,10)
        a.rect(x-5,y-5,x+4,y-2,9); a.line(x-7,y-1,x+7,y-1,9)
        if i%2:
            a.line(x+5,y+8,x+10,y,8); a.line(x+10,y,x+9,y-7,10)
        else:
            a.line(x-5,y+9,x-10,y+12,8); a.line(x-10,y+12,x-10,y+29,9)
    for x in range(5,320,32): a.rect(x,94,x+2,118,8)
    for y in (98,109): a.rect(0,y,319,y+2,7); a.line(0,y,319,y,9)
    # Named spectators have small plaques on the rail below their hands.
    for name,x in [('CECIL BROWN',57),('LEROY PITRE',198)]:
        a.rect(x-31,88,x+31,97,0); a.text(name,x,89,10,center=True)
    # This clear sky strip holds the changing two-line speech banner.
    a.rect(8,28,311,48,0)
    a.rect(0,0,319,23,0); a.line(0,23,319,23,8)
    a.text('PLACE',8,3,9); a.text('STAMINA',72,3,9); a.text('TO GO',210,3,9); a.text('M',287,3,9)
    a.text('LINZAY DOWNS - EUNICE, LA',8,14,10)
    a.rect(0,188,319,199,0)
    a.text('HOLD RIGHT: GALLOP   SPACE: SPRINT   Q: QUIT',160,191,10,center=True)
    return a

def horse(pose):
    a=Canvas(48,44)
    bob=pose&1
    # Four readable gallop silhouettes, with individual dark hooves.
    legs=[[(12,29),(6,40),(11,42)],[(17,29),(22,38),(18,42)],
          [(29,28),(32,37),(38,42)],[(34,28),(42,36),(43,41)]]
    shifts=((0,0,0,0),(6,-5,-6,-4),(3,-2,-3,-1),(-3,4,2,0))[pose]
    for points,shift in zip(legs,shifts):
        p=[(x+shift*(j>0),y-bob) for j,(x,y) in enumerate(points)]
        a.line(*p[0],*p[1],1); a.line(*p[1],*p[2],1)
        a.line(p[0][0]+1,p[0][1],p[1][0]+1,p[1][1],8)
        a.line(p[1][0]+1,p[1][1],p[2][0]+1,p[2][1],8)
        a.rect(p[2][0]-1,p[2][1]-1,p[2][0]+2,p[2][1],5)
    a.poly([(11,21-bob),(5,20-bob),(1,31-bob),(4,33-bob),(9,25-bob)],1)
    a.ellipse(23,25-bob,15,7,1); a.ellipse(23,24-bob,13,5,8)
    a.line(12,22-bob,29,21-bob,9)
    a.poly([(29,24-bob),(32,15-bob),(38,9-bob),(43,13-bob),(47,17-bob),
            (46,21-bob),(39,20-bob),(36,29-bob)],1)
    a.poly([(31,25-bob),(34,17-bob),(39,12-bob),(41,15-bob),(46,18-bob),
            (45,20-bob),(38,18-bob),(34,28-bob)],8)
    a.line(33,17-bob,38,11-bob,5)
    a.poly([(38,12-bob),(37,6-bob),(40,10-bob),(42,7-bob),(42,14-bob)],8)
    a.dot(41,15-bob,15); a.dot(42,15-bob,1); a.dot(46,19-bob,1)
    a.line(39,18-bob,44,18-bob,9)
    a.rect(19,20-bob,29,27-bob,14); a.line(23,21-bob,26,21-bob,15)
    a.line(25,21-bob,25,25-bob,15)
    # Small jockey crouched forward over Tee-Boy's shoulders.
    a.poly([(20,17-bob),(25,11-bob),(31,13-bob),(33,18-bob),(27,18-bob),(24,23-bob)],1)
    a.line(23,16-bob,27,13-bob,14); a.line(26,14-bob,30,16-bob,14)
    a.line(29,17-bob,37,19-bob,10); a.line(22,19-bob,19,26-bob,1)
    a.rect(28,7-bob,32,11-bob,10); a.rect(27,5-bob,32,7-bob,9)
    a.line(27,7-bob,34,7-bob,9)
    return a

def main():
    assets=ROOT/'assets'; a=track()
    (assets/'track.bin').write_bytes(a.packed()); a.png(assets/'track.png',2)
    title=track(); title.rect(23,40,297,170,1); title.rect(25,42,295,168,0)
    title.text('LINZAY DOWNS',160,51,9,3,True)
    title.text('TEE-BOY RACES',160,79,10,2,True)
    for text,y in [('EUNICE, LOUISIANA',103),
                   ('HOLD RIGHT TO GALLOP',119),('SPACE FOR A BURST - SAVE YOUR STAMINA',131),
                   ('PRESS SPACE TO RACE',151)]: title.text(text,160,y,10,center=True)
    (assets/'rtitle.bin').write_bytes(title.packed()); title.png(assets/'rtitle.png',2)
    data=bytearray(); offsets=[]; poses=[]
    for i in range(4):
        full=horse(i); compact=Canvas(48,44)
        for y in range(30):
            for x in range(32): compact.dot(8+x,14+y,full.p[(y*44//30)*48+x*48//32])
        poses.append(compact)
    for a in poses:
        offsets.extend((len(data),len(data)))
        for y in range(44):
            row=bytes((a.p[y*48+x]<<4)|a.p[y*48+x+1] for x in range(0,48,2))
            runs=[]; x=0
            while x<24:
                if row[x]==0: x+=1; continue
                start=x; mode=128 if row[x]<16 else (64 if row[x]&15==0 else 0)
                while x<24 and row[x] and (128 if row[x]<16 else (64 if row[x]&15==0 else 0))==mode: x+=1
                runs.append((start,row[start:x],mode))
            data.append(len(runs))
            for start,run,mode in runs: data.extend((start,len(run)|mode)); data.extend(run)
    maps=[list(range(16)),[0,1,2,3,4,1,6,7,10,15,10,11,12,13,8,15],
          [0,1,2,3,4,1,6,7,5,8,10,11,12,13,9,15],
          [0,1,2,3,4,1,6,7,7,10,10,11,12,13,6,15]]
    pairs=bytes((m[i>>4]<<4)|m[i&15] for m in maps for i in range(256))
    lines=['/* Generated original galloping horse sprites. */','#define SPRITE_H 44','#define SPRITE_W 48',
           'static const unsigned int sprite_offsets[8]={'+','.join(map(str,offsets))+'};']
    for name,values in [('sprite_stream',data),('pair_colors',pairs)]:
        lines.append('static const unsigned char '+name+'['+str(len(values))+']={')
        lines.extend(','.join(map(str,values[i:i+24]))+',' for i in range(0,len(values),24)); lines.append('};')
    (ROOT/'src/horses.h').write_text('\n'.join(lines)+'\n')
    sheet=Canvas(192,44)
    for i,a in enumerate(poses):
        for y in range(44): sheet.p[y*192+i*48:y*192+(i+1)*48]=a.p[y*48:(y+1)*48]
    sheet.png(assets/'horses.png',3)
    print('Generated bush track, race title and four galloping horse poses.')
if __name__=='__main__': main()
