#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "render.h"
#include "horses.h"
static unsigned char scene[32000],screen[2][32000],reference[32000],saved[2][4][512];
static View v[4],old[2][4];
int main(void) {
    Game hud;
    FILE *f; int pose,row,runs,x,b,n,mode,i,step,page;
    const unsigned char *p,*end;
    render_race_init();
    for(pose=0;pose<4;pose++) {
        p=sprite_stream+sprite_offsets[pose*2];
        end=pose<3?sprite_stream+sprite_offsets[(pose+1)*2]:sprite_stream+sizeof(sprite_stream);
        for(row=0;row<44;row++) {
            assert(p<end); runs=*p++; if(row<14) assert(runs==0);
            while(runs--) {
                assert(p+2<=end); x=*p++; b=*p++; n=b&63; mode=b&192;
                assert(n>0 && x+n<=24 && mode!=192 && p+n<=end);
                while(n--) { b=*p++; assert(b && mode==(b<16?128:((b&15)==0?64:0))); }
            }
        }
        assert(p==end);
    }
    v[0].x=80; v[0].y=v[0].depth=124; v[0].face=1; v[0].hp=v[0].visible=1;
    memset(reference,0,32000); render_actors(reference+53*160,160,0,53,320,135,v);
    n=0; for(i=0;i<32000;i++) if(reference[i]) n++;
    assert(n>60);
    for(b=1;b<4;b++) {
        v[0].kind=b; memset(screen[0],0,32000);
        render_actors(screen[0]+53*160,160,0,53,320,135,v);
        for(i=0;i<32000;i++) assert(screen[0][i]==pair_colors[b*256+reference[i]]);
    }
    memset(v,0,sizeof(v));
    memset(&hud,0,sizeof(hud)); hud.lives=4; hud.p.hp=8; hud.score=120;
    memset(scene,0,32000); render_hud(scene,reference,&hud);
    assert(reference[480+24]==0x0a); /* The top row of the place digit 4. */
    assert(reference[480+58]==0xee && reference[480+88]==0xee);
    hud.p.hp=0; hud.lives=1; render_hud(scene,reference,&hud);
    assert(reference[480+58]==0x55); /* Empty stamina overwrites filled cells. */
    f=fopen("assets/track.bin","rb"); assert(f);
    assert(fread(scene,1,32000,f)==32000); fclose(f);
    memcpy(screen[0],scene,32000); memcpy(screen[1],scene,32000);
    for(i=0;i<4;i++) {
        v[i].y=v[i].depth=124+i*20; v[i].face=1; v[i].kind=i; v[i].hp=v[i].visible=1;
    }
    for(step=0;step<120;step++) {
        page=step&1;
        for(i=0;i<4;i++) if(old[page][i].visible)
            copy32(screen[page]+(old[page][i].y-31)*160+((old[page][i].x&~1)-16)/2,saved[page][i],144,0);
        for(i=0;i<4;i++) {
            v[i].x=34+step*2-i; if(v[i].x<34) v[i].x=34;
            v[i].pose=(step+i)&3;
            if(!old[page][i].visible || v[i].x!=old[page][i].x)
                copy32(saved[page][i],screen[page]+(v[i].y-31)*160+((v[i].x&~1)-16)/2,0,144);
        }
        render_actors(screen[page]+53*160,160,0,53,320,135,v);
        memcpy(reference,scene,32000); render_actors(reference+53*160,160,0,53,320,135,v);
        assert(memcmp(screen[page],reference,32000)==0);
        memcpy(old[page],v,sizeof(v));
    }
    puts("PASS: horse run masks, four palettes and alternating race frames match clean redraws");
    return 0;
}
