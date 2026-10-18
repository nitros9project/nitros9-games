#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "render.h"
#include "sprites.h"
static unsigned char bg[986],hud_bg[1920],out[PATCH_BYTES+16],mirror[PATCH_BYTES];
static unsigned char asset[10000],raw[32000];
static unsigned char screen[2][32000],reference[32000],saved[2][4][1152];
static View v[4];
static View old[2][4];
static int get(const unsigned char *p,int stride,int x,int y) {
    int b=p[y*stride+x/2]; return x&1?b&15:b>>4;
}
/* The native blitter trusts the mode bits instead of checking pixels.
   Validate every generated run, including both mirrored directions. */
static void check_stream(void) {
    int pose,row,runs,n,mode,x,i,b;
    const unsigned char *p,*end;
    for(pose=0;pose<SPRITE_VARIANTS;pose++) {
        p=sprite_stream+sprite_offsets[pose];
        end=pose<SPRITE_VARIANTS-1?sprite_stream+sprite_offsets[pose+1]:sprite_stream+sizeof(sprite_stream);
        for(row=0;row<44;row++) {
            assert(p<end); runs=*p++;
            while(runs--) {
                assert(p+2<=end); x=*p++; b=*p++;
                n=b&63; mode=b&192;
                assert(n>0 && x+n<=24 && mode!=192 && p+n<=end);
                for(i=0;i<n;i++) {
                    b=*p++;
                    assert(b!=0);
                    assert(mode==(b<16?128:((b&15)==0?64:0)));
                }
            }
        }
        assert(p==end);
    }
}
int main(void) {
    int i,x,y,row,room,height,step,page,visible=0;
    Game g;
    FILE *file;
    char path[32];
    check_stream();
    /* 164 encoded rows, each containing 128 + 32 repetitions of 0x77. */
    for(i=0;i<=164;i++) { bg[i*2]=(i*4)>>8; bg[i*2+1]=i*4; }
    for(i=0;i<164;i++) { bg[330+i*4]=255; bg[331+i*4]=0x77; bg[332+i*4]=159; bg[333+i*4]=0x77; }
    memset(hud_bg,0x77,sizeof(hud_bg)); memset(out,0xcd,sizeof(out));
    render_patch(bg,out,0,30,64,50,v);
    for(i=0;i<1600;i++) assert(out[i]==0x77);
    assert(out[1600]==0xcd); /* No writes past the patch. */
    v[0].x=32; v[0].y=v[0].depth=74; v[0].hp=8;
    v[0].pose=0; v[0].face=1; v[0].visible=1;
    render_patch(bg,out,0,30,64,50,v);
    for(i=0;i<1600;i++) if(out[i]!=0x77) visible++;
    assert(visible>100 && visible<650);
    assert(get(out,32,0,0)==7); /* Transparent border keeps scene pixels. */
    v[0].face=-1;
    render_patch(bg,mirror,0,30,64,50,v);
    for(y=0;y<44;y++) for(x=0;x<48;x++)
        assert(get(out,32,8+x,1+y)==get(mirror,32,8+47-x,1+y));
    /* A clipped slice matches the same pixels in a full sprite patch. */
    v[0].face=1;
    render_patch(bg,mirror,16,42,32,24,v);
    for(y=0;y<24;y++) for(x=0;x<32;x++)
        assert(get(mirror,16,x,y)==get(out,32,16+x,12+y));
    /* A second opaque actor at the same location changes the cloth,
       while hiding it restores the first actor exactly. */
    v[1]=v[0]; v[1].kind=1;
    render_patch(bg,mirror,0,30,64,50,v);
    assert(memcmp(out,mirror,1600)!=0);
    v[1].visible=0; render_patch(bg,mirror,0,30,64,50,v);
    assert(memcmp(out,mirror,1600)==0);
    v[0].visible=0; v[1].visible=1; v[1].x=32;
    v[1].y=v[1].depth=84; v[1].pose=4; v[1].hp=3;
    render_patch(bg,out,0,30,64,50,v);
    assert(get(out,32,20,7)==9); /* Warning/hit-reaction bar is yellow. */
    v[1].kind=3; v[1].pose=7; v[1].y=74;
    render_patch(bg,out,0,30,64,50,v);
    assert(get(out,32,20,20)==9); /* Gator bar follows its low silhouette. */
    memset(&g,0,sizeof(g)); g.lives=3; g.p.hp=8; g.score=1200;
    render_hud(hud_bg,out,&g);
    assert(get(out,160,116,3)==14);
    g.p.hp=0; render_hud(hud_bg,out,&g);
    assert(get(out,160,116,3)==5);
    memset(v,0,sizeof(v));
    for(room=0;room<3;room++) {
        sprintf(path,"assets/dock%d.rle",room); file=fopen(path,"rb"); assert(file);
        assert(fread(asset,1,sizeof(asset),file)>330); fclose(file);
        sprintf(path,"assets/dock%d.bin",room); file=fopen(path,"rb"); assert(file);
        assert(fread(raw,1,sizeof(raw),file)==32000); fclose(file);
        for(y=24;y<188;y+=32) for(x=0;x<320;x+=64) {
            height=188-y; if(height>32) height=32;
            render_patch(asset,out,x,y,64,height,v);
            for(row=0;row<height;row++)
                assert(memcmp(out+row*32,raw+(y+row)*160+x/2,32)==0);
        }
    }
    memcpy(screen[0],raw,32000); memcpy(screen[1],raw,32000); memset(old,0,sizeof(old));
    for(i=0;i<4;i++) {
        v[i].x=80+i*24; v[i].y=v[i].depth=132+i*8;
        v[i].face=i&1?-1:1; v[i].kind=i?1:0;
        v[i].hp=i?3:8; v[i].visible=1;
    }
    for(step=0;step<40;step++) {
        page=step&1;
        for(i=0;i<4;i++) if(old[page][i].visible)
            copy48(screen[page]+(old[page][i].y-47)*160+((old[page][i].x&~1)-24)/2,saved[page][i],136,0);
        for(i=0;i<4;i++) {
            if(step<20) v[i].x+=2; v[i].pose=i==3?6+(step&1):(step+i)%6;
            if(i==3) v[i].kind=3; v[i].face=step&1?-1:1;
            if(i==0) { v[i].y=(step>=6 && step<=9)?108:132; v[i].visible=step%4!=3; }
            if(i==2) v[i].visible=step<12;
        }
        for(i=0;i<4;i++) if(v[i].visible &&
            (!old[page][i].visible || (v[i].x&~1)!=(old[page][i].x&~1) || v[i].y!=old[page][i].y))
            copy48(saved[page][i],screen[page]+(v[i].y-47)*160+((v[i].x&~1)-24)/2,0,136);
        render_actors(screen[page]+53*160,160,0,53,320,135,v);
        memcpy(reference,raw,sizeof(reference));
        render_actors(reference+53*160,160,0,53,320,135,v);
        assert(memcmp(screen[page],reference,32000)==0);
        memcpy(old[page],v,sizeof(v));
    }
    puts("PASS: native opaque and masked run metadata for all poses and facings");
    puts("PASS: packed transparency, mirroring, clipping, patch bounds, layering, palette variants, HUD health");
    puts("PASS: compressed background patches reproduce every byte of all three original scenes");
    puts("PASS: alternating saved-background screens match clean redraws through movement, overlaps, mirroring, jumping, blinking and removal");
    return 0;
}
