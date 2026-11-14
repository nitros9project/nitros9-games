#include <string.h>
#include "render.h"
#ifdef BUSH_TRACK
#include "horses.h"
#else
#include "sprites.h"
#endif
#ifdef BUSH_TRACK
static unsigned char rival_stream[3][sizeof(sprite_stream)];
void render_race_init(void) {
    int kind,pose,row,runs,n;
    unsigned char *p;
    const unsigned char *map;
    for(kind=0;kind<3;kind++) {
        memcpy(rival_stream[kind],sprite_stream,sizeof(sprite_stream));
        map=pair_colors+(kind+1)*256;
        for(pose=0;pose<4;pose++) {
            p=rival_stream[kind]+sprite_offsets[pose*2];
            for(row=0;row<44;row++) {
                runs=*p++;
                while(runs--) {
                    p++; n=(*p++)&63;
                    while(n--) { *p=map[*p]; p++; }
                }
            }
        }
    }
}
#endif
void blit_row(unsigned char *dst,const unsigned char *src,const unsigned char *map,int count,int flip);
void draw_sprite(unsigned char *dst,const unsigned char *src,const unsigned char *map);
void unpack_row(const unsigned char *src,unsigned char *dst,int skip,int count);
/* Palette index 0 is transparent in sprite data, so dark outlines use 1.
   Player, deckhand and captain share poses with distinct cloth/hat colors. */
#ifdef BUSH_TRACK
static const unsigned char packed_digits[10][21]={
{10,170,0,160,0,160,160,10,160,160,160,160,170,0,160,160,0,160,10,170,0},
{0,160,0,10,160,0,0,160,0,0,160,0,0,160,0,0,160,0,10,170,0},
{10,170,0,160,0,160,0,0,160,0,10,0,0,160,0,10,0,0,170,170,160},
{170,170,0,0,0,160,0,0,160,10,170,0,0,0,160,0,0,160,170,170,0},
{0,10,0,0,170,0,10,10,0,160,10,0,170,170,160,0,10,0,0,10,0},
{170,170,160,160,0,0,160,0,0,170,170,0,0,0,160,0,0,160,170,170,0},
{10,170,0,160,0,0,160,0,0,170,170,0,160,0,160,160,0,160,10,170,0},
{170,170,160,0,0,160,0,10,0,0,160,0,10,0,0,10,0,0,10,0,0},
{10,170,0,160,0,160,160,0,160,10,170,0,160,0,160,160,0,160,10,170,0},
{10,170,0,160,0,160,160,0,160,10,170,160,0,0,160,0,0,160,10,170,0},
};
#else
static const unsigned char digits[10][7]={
    {14,17,19,21,25,17,14},{4,12,4,4,4,4,14},
    {14,17,1,2,4,8,31},{30,1,1,14,1,1,30},
    {2,6,10,18,31,2,2},{31,16,16,30,1,1,30},
    {14,16,16,30,17,17,14},{31,1,2,4,8,8,8},
    {14,17,17,14,17,17,14},{14,17,17,15,1,1,14}
};
static void pixel(unsigned char *p,int stride,int x,int y,unsigned char c) {
    unsigned char *d=p+y*stride+(x>>1);
    if(x&1) *d=(*d&240)|c;
    else *d=(*d&15)|(c<<4);
}

#endif

#ifndef _CMOC_VERSION_
void render_patch(const unsigned char *bg,unsigned char *out,int x,int y,int width,int height,const View *v) {
    render_to(bg,out,width>>1,x,y,width,height,v);
}
void render_to(const unsigned char *bg,unsigned char *out,int stride,int x,int y,int width,int height,const View *v) {
    int row;
    const unsigned char *offsets;
    unsigned char *scan;
    offsets=bg+(y-24)*2; scan=out;
    for(row=0;row<height;row++) {
        unpack_row(bg+330+((unsigned int)offsets[0]<<8)+offsets[1],scan,x>>1,width>>1);
        offsets+=2; scan+=stride;
    }
    render_actors(out,stride,x,y,width,height,v);
}

#endif
void render_actors(unsigned char *out,int stride,int x,int y,int width,int height,const View *v) {
    int row,i,j,k,order[4],tmp,px,py,start,end,sx,first,last,flip,kind,runs,length,offset;
    const unsigned char *map,*sprite,*source;
    const View *actor;
    unsigned char *dest;
#ifndef BUSH_TRACK
    int hp;
    unsigned char c;
#endif
    for(i=0;i<4;i++) order[i]=i;
    for(i=0;i<3;i++) for(j=i+1;j<4;j++) if(v[order[i]].depth>v[order[j]].depth) {
        tmp=order[i]; order[i]=order[j]; order[j]=tmp;
    }
    for(k=0;k<4;k++) {
        i=order[k]; actor=v+i;
        if(!actor->visible) continue;
        px=(actor->x&~1)-24-x; py=actor->y-43-y;
#ifndef _CMOC_VERSION_
        start=py<0?-py:0; end=height-py;
        if(end>SPRITE_H) end=SPRITE_H;
        if(start>=end || px>=width || px+SPRITE_W<=0) continue;
#endif
        kind=actor->kind; flip=actor->face<0;
#ifndef BUSH_TRACK
        hp=actor->hp;
#endif
#ifdef BUSH_TRACK
        map=pair_colors;
#else
        map=pair_colors+(kind==3?0:kind*256);
#endif
#ifdef BUSH_TRACK
        sprite=(kind?rival_stream[kind-1]:sprite_stream)+sprite_offsets[actor->pose*2+flip];
#else
        sprite=sprite_stream+sprite_offsets[actor->pose*2+flip];
#endif
#ifdef _CMOC_VERSION_
        draw_sprite(out+py*stride+(px>>1),sprite,map);
#else
        {
            source=sprite;
            for(row=0;row<SPRITE_H;row++) {
                runs=*source++;
                for(j=0;j<runs;j++) {
                    offset=*source++; length=(*source++)&63;
                    sprite=source; source+=length;
                    if(row<start || row>=end) continue;
                    sx=(px>>1)+offset;
                    first=sx<0?-sx:0;
                    last=(width>>1)-sx; if(last>length) last=length;
                    if(first>=last) continue;
                    dest=out+(py+row)*stride+sx+first;
                    blit_row(dest,sprite+first,map,last-first,0);
                }
            }
        }
#endif
#ifndef BUSH_TRACK
        if(i>0) {
            py=actor->y-(kind==3?24:47)-y; px=(actor->x&~1)-12-x;
            if(py>=0 && py+1<height) {
                dest=out+py*stride;
                for(j=0;j<12;j++) {
                    sx=(px>>1)+j;
                    if(sx>=0 && sx<(width>>1)) {
                        c=j<hp?(actor->pose==4 || actor->pose==7?0x99:0x66):0x11;
                        dest[sx]=c; dest[sx+stride]=c;
                    }
                }
            }
        }
#endif
    }
}
#ifdef BUSH_TRACK
static void number(unsigned char *out,int x,int value,int count) {
    int i,row,n;
    unsigned char *at;
    const unsigned char *glyph;
    for(i=count-1;i>=0;i--) {
        n=value%10; value/=10;
        at=out+480+(x>>1)+i*3; glyph=packed_digits[n];
        for(row=0;row<7;row++) { memcpy(at,glyph,3); at+=160; glyph+=3; }
    }
}
void render_hud(const unsigned char *bg,unsigned char *out,const Game *g) {
    int i,row;
    unsigned char *at,c;
#ifndef _CMOC_VERSION_
    memcpy(out,bg,1920);
#endif
    number(out,46,g->lives,1); number(out,250,g->score,5);
    for(i=0;i<8;i++) {
        at=out+480+58+i*4; c=i<g->p.hp?0xee:0x55;
        for(row=0;row<7;row++) { memset(at,c,3); at+=160; }
    }
}
#else
static void number(unsigned char *out,int x,int value,int count) {
    int i,row,col,n;
    for(i=count-1;i>=0;i--) {
        n=value%10; value/=10;
        for(row=0;row<7;row++) for(col=0;col<5;col++)
            if(digits[n][row] & (16>>col)) pixel(out,160,x+i*6+col,row+3,10);
    }
}
void render_hud(const unsigned char *bg,unsigned char *out,const Game *g) {
    int i,x,y;
    memcpy(out,bg,1920);
    number(out,46,g->lives,1); number(out,250,g->score,5);
    for(i=0;i<8;i++) for(y=3;y<10;y++) for(x=0;x<5;x++)
        pixel(out,160,116+i*7+x,y,i<g->p.hp?14:5);
}

#endif
