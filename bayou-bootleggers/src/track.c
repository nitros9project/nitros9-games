/* Original CoCo 3 / NitrOS-9 graphics-window implementation. */
#include <cgfx.h>
#include <os.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#ifdef BAYOU_PROFILE
#include <time.h>
#endif
#include "race.h"
#include "render.h"
static path_id w;
static Game game;
static Race race;
static unsigned char gallop;
#ifdef BAYOU_PROFILE
static int drawn;
#endif
/* Each screen owns its clean patches from two flips ago. Keeping both
   sets below 16K of process data leaves three slots for mapped video. */
static unsigned char saved[2][4][512];
static unsigned char hud_backdrop[1920],patch[PATCH_BYTES];
static unsigned char screen_block,screen_blocks,*video;
static int screen_offset,video_first=-1,video_count;
int unmap_video(unsigned char *address,int count);
static View views[4];
static struct { path_id path; unsigned char block; int offset;
    View old[4]; int hp,lives,score,message,cheer;
} screens[2];
static View *previous;
static int page, double_buffer;
static void use_page(int n) {
    if(video) { unmap_video(video,video_count); video=0; }
    page=n; w=screens[n].path; screen_block=screens[n].block;
    screen_offset=screens[n].offset; previous=screens[n].old;
}
static int hud_hp=-1,hud_lives=-1,hud_score=-1;
static const unsigned char pal[16]={0,1,3,2,19,4,36,34,38,54,55,5,9,18,27,63};
/* CoCo 3 NitrOS-9 Level 2 keeps D.Sec/D.Tick at $2D/$2E in physical
   block zero. F$CpyMem reads them through a temporary DAT image, without
   touching the interrupt source or occupying a permanent video mapping. */
asm int tick_clock(void) {
    asm {
        pshs u,y
        leas -2,s
        leau ,s
        leax tick_dat,pcr
        tfr x,d
        ldx #$002d
        ldy #2
        os9 $1b           ; F$CpyMem copies two clock bytes into this stack
        bcs tick_error
        lda ,s
        ldb #60
        mul
        addd #60
        subb 1,s
        sbca #0
        bra tick_return
tick_error
        ldd #-1
tick_return
        leas 2,s
        puls u,y,pc
tick_dat
        fdb 0,0,0,0,0,0,0,0
    }
}
asm int screen_info(path_id path,unsigned char *block,unsigned char *blocks,int *offset) {
    asm {
_os9err EXTERNAL
        pshs u,y
        lda 7,s
        ldb #SS_ScInf
        os9 I$GetStt
        bcs screen_info_error
        stb [8,s]
        sta [10,s]
        stx [12,s]
        puls u,y
        clra
        clrb
        rts
screen_info_error
        puls u,y
        lbra _os9err
    }
}
asm int map_video(int block,int count,unsigned char **address) {
    asm {
_os9err EXTERNAL
        pshs u,y
        ldx 6,s
        ldb 9,s
        os9 $4f           ; F$MapBlk maps only the screen physical RAM
        bcs map_video_error
        stu [10,s]
        puls u,y
        clra
        clrb
        rts
map_video_error
        puls u,y
        lbra _os9err
    }
}
asm int unmap_video(unsigned char *address,int count) {
    asm {
_os9err EXTERNAL
        pshs u,y
        ldu 6,s
        ldb 9,s
        os9 $50           ; F$ClrBlk removes the temporary user mapping
        puls u,y
        lbcs _os9err
        clra
        clrb
        rts
    }
}
/* The race fits in two code banks and two data banks. Keep all four
   framebuffer banks mapped, so HUD work never remaps the playfield. */
static int video_range(void) {
    if(video) return 0;
    if(map_video(screen_block,4,&video)) return 1;
    video_first=0; video_count=4;
    return 0;
}
static void rect(int x,int y,int x2,int y2,int c) {
    _cgfx_fcolor(w,c); _cgfx_bcolor(w,c);
    _cgfx_setdptr(w,x,y); _cgfx_bar(w,x2,y2);
}
static void text(int x,int y,const char *s,int c) {
    _cgfx_fcolor(w,c); _cgfx_bcolor(w,0);
    _cgfx_curxy(w,x,y); cwrite(w,s,strlen(s));
}
static int upload(const unsigned char *data,int x,int y,int width,int height) {
    int row,stride=width>>1;
    unsigned char *h;
    if(video_range()) return 1;
    h=video+screen_offset+y*160+(x>>1);
    for(row=0;row<height;row++) memcpy(h+row*160,data+row*stride,stride);
    return 0;
}
static int scene(const char *name) {
    path_id file;
    int count,y,h,i,row;
    char path[64];
    sprintf(path,"/dd/BAYOU/%s.bin",name);
    if(_os_open(path,FAM_READ,&file)) {
        sprintf(path,"assets/%s.bin",name);
        if(_os_open(path,FAM_READ,&file)) return 1;
    }
    for(y=0;y<200;y+=16) {
        h=200-y; if(h>16) h=16;
        count=h*160;
        i=_os_read(file,patch,&count);
        if(i || count!=h*160) { _os_close(file); return 1; }
        for(row=0;row<h;row++) {
            if(y+row<12) memcpy(hud_backdrop+(y+row)*160,patch+row*160,160);
        }
        if(upload(patch,0,y,320,h)) { _os_close(file); return 1; }
    }
    _os_close(file);
    for(i=0;i<4;i++) { previous[i].visible=0; previous[i].hp=0; }
    hud_hp=hud_lives=hud_score=-1;
    screens[page].hp=-1; screens[page].message=-99; screens[page].cheer=-1;
    return 0;

}
static int background(void) {
    const char *name="track";
    if(scene(name)) return 1;
    if(double_buffer) {
        unsigned char *src,*dst;
        int i,other=page^1;
        if(screens[page].offset!=screens[other].offset) {
            use_page(other);
            return scene(name);
        }
        /* Two single-bank mappings fit beside the program and stack.
           Copy all four physical banks, including harmless screen padding. */
        if(video) { unmap_video(video,video_count); video=0; }
        for(i=0;i<4;i++) {
            if(map_video(screens[page].block+i,1,&src)) return 1;
            if(map_video(screens[other].block+i,1,&dst)) {
                unmap_video(src,1); return 1;
            }
            memcpy(dst,src,8192);
            unmap_video(dst,1); unmap_video(src,1);
        }
        for(i=0;i<4;i++) screens[other].old[i].visible=0;
        screens[other].hp=-1; screens[other].message=-99; screens[other].cheer=-1;
    }
    return 0;
}
#ifdef RACE_PHASES
static int phases[4];
static void phase(int index,int *start) {
    int now=tick_clock(),delta=now-*start;
    if(delta<0) delta+=3600;
    phases[index]+=delta; *start=now;
}
#endif
static void frame(void) {
    int i,message;
    unsigned char *at;
    char label[24];
#ifdef RACE_PHASES
    int mark=tick_clock();
#endif
    use_page(page^1);
    gallop++;
    for(i=0;i<4;i++) {
        views[i].x=34+race.pos[i]/5;
        views[i].y=views[i].depth=124+i*20;
        views[i].face=1; views[i].kind=i;
        views[i].hp=1; views[i].visible=1;
        views[i].pose=race.over || race.countdown || race.finish[i]?0:(gallop+i)&3;
    }
    if(video_range()) return;
    for(i=0;i<4;i++) if(previous[i].visible) {
        at=video+screen_offset+(previous[i].y-31)*160+((previous[i].x&~1)-16)/2;
        copy32(at,saved[page][i],144,0);
    }
    for(i=0;i<4;i++) if(!previous[i].visible || views[i].x!=previous[i].x) {
        at=video+screen_offset+(views[i].y-31)*160+((views[i].x&~1)-16)/2;
        copy32(saved[page][i],at,0,144);
    }
#ifdef RACE_PHASES
    phase(0,&mark);
#endif
    render_actors(video+screen_offset+53*160,160,0,53,320,135,views);
#ifdef RACE_PHASES
    phase(1,&mark);
#endif
    memcpy(previous,views,sizeof(views));
    game.lives=race.place; game.p.hp=(race.stamina+11)/12;
    /* The HUD updates in five-metre increments, avoiding expensive
       digit drawing on every gallop frame. Internal race distance is exact. */
    game.score=((RACE_LENGTH-race.pos[0]+49)/50)*5;
    if(game.lives!=screens[page].lives || game.p.hp!=screens[page].hp || game.score!=screens[page].score) {
        render_hud(hud_backdrop,video+screen_offset,&game);
        screens[page].lives=game.lives; screens[page].hp=game.p.hp; screens[page].score=game.score;
    }
    /* Update each hidden page only when a new cheer arrives. The banner
       stays above all horse patches, so restoring sprites cannot erase it. */
    if(screens[page].cheer!=race.crowd.version) {
        rect(8,28,311,48,0);
        text(2,4,crowd_names[race.crowd.speaker],9);
        text(2,5,crowd_lines[race.crowd.line],10); Flush();
        screens[page].cheer=race.crowd.version;
    }
    message=race.countdown?(race.countdown-1)/15+1:(race.over?-1:0);
    if(message!=screens[page].message) {
        screens[page].message=message;
        rect(208,12,319,22,0);
        if(race.countdown) sprintf(label,"READY %d",message);
        else if(race.over) sprintf(label,"FINISHED");
        else sprintf(label,"GO TEE-BOY!");
        text(26,2,label,9); Flush();
        if(race.over) {
            rect(34,48,285,76,0);
            text(7,6,race.place==1?"TEE-BOY WINS! ALLEZ!":"GOOD RUN, TEE-BOY!",9);
            text(7,8,"R: RACE AGAIN   Q: QUIT",10); Flush();
        }
    }
#ifdef RACE_PHASES
    phase(2,&mark);
#endif
    _cgfx_select(w); Flush();
#ifdef RACE_PHASES
    phase(3,&mark);
#endif
}
static int init_buffers(void) {
    int i;
    struct sgbuf opts;
    if(screen_blocks==4) {
        if(_os_open("/w",FAM_READ|FAM_WRITE,&screens[1].path)) return 1;
        w=screens[1].path;
        if(_cgfx_dwset(w,8,0,0,40,25,15,0,0) || Flush()) {
            _os_close(w); w=screens[0].path; return 1;
        }
        _cgfx_ss_mtyp(w,1); _cgfx_curoff(w); _cgfx_scalesw(w,0);
        for(i=0;i<16;i++) _cgfx_palette(w,i,pal[i]);
        Flush();
        if(!_os_gs_popt(w,&opts)) {
            opts.sg_echo=opts.sg_pause=opts.sg_kbich=opts.sg_kbach=0;
            _os_ss_popt(w,&opts);
        }
        _os_ss_keysense(w,1);
        if(screen_info(w,&screens[1].block,&screen_blocks,&screens[1].offset) || screen_blocks!=4) {
            _os_close(w); w=screens[0].path; return 1;
        }
        double_buffer=1; use_page(0);
    }
    return 0;
}
int main(void) {
    struct sgbuf opts;
    int i,keys,ready,count,ticks,last,now,elapsed,steps;
    char c;
    previous=screens[0].old;
    render_race_init();
    if(_os_open("/w",FAM_READ|FAM_WRITE,&w)) return 1;
    if(_cgfx_dwset(w,8,0,0,40,25,15,0,0) || Flush()) goto done;
    _cgfx_ss_mtyp(w,1); _cgfx_curoff(w); _cgfx_scalesw(w,0); _cgfx_select(w); Flush();
    ticks=2; _os9_sleep(&ticks);
    if(!_os_gs_popt(w,&opts)) {
        opts.sg_echo=opts.sg_pause=opts.sg_kbich=opts.sg_kbach=0;
        _os_ss_popt(w,&opts);
    }
    _os_ss_keysense(w,1);
    if(screen_info(w,&screen_block,&screen_blocks,&screen_offset) || screen_blocks!=4) goto done;
    screens[0].path=w; screens[0].block=screen_block; screens[0].offset=screen_offset;
#ifdef RACE_BENCH
    {
        path_id report;
        int start,elapsed,n;
        char result[80];
        race_init(&race); race.countdown=0;
        if(init_buffers() || background()) goto done;
        start=tick_clock();
        for(i=0;i<120;i++) { race_step(&race,RIGHT); frame(); }
        elapsed=tick_clock()-start; if(elapsed<0) elapsed+=3600;
        sprintf(result,"120 race frames: %d ticks, final distance %d\r",elapsed,race.pos[0]);
        _os_delete("/dd/BAYOU/racebench.txt",0);
        if(!_os_create("/dd/BAYOU/racebench.txt",FAM_WRITE,&report,FAP_READ|FAP_WRITE)) {
            n=strlen(result); _os_write(report,result,&n);
#ifdef RACE_PHASES
            sprintf(result,"copy %d sprite %d hud %d flip %d ticks\r",phases[0],phases[1],phases[2],phases[3]);
            n=strlen(result); _os_write(report,result,&n);
#endif
            _os_close(report);
        }
        goto done;
    }
#else
    if(scene("rtitle")) goto done;
    _cgfx_ss_mtyp(w,1); ticks=2; _os9_sleep(&ticks);
    for(i=0;i<16;i++) _cgfx_palette(w,i,pal[i]); Flush();
    do {
        keys=0; _os_gs_keysense(w,&keys); ticks=3; _os9_sleep(&ticks);
        if(!_os_gs_ready(w,&ready) && ready) {
            count=1; _os_read(w,&c,&count); if(c=='q'||c=='Q') goto done;
        }
    } while(!(keys & JUMP));
    race_init(&race);
    crowd_init(&race.crowd,(unsigned int)tick_clock());
    if(init_buffers() || background()) goto done;
    last=tick_clock();
    for(;;) {
        keys=0; _os_gs_keysense(w,&keys);
        while(!_os_gs_ready(w,&ready) && ready) {
            count=1; if(_os_read(w,&c,&count)) break;
            if(c=='q'||c=='Q') goto done;
            if((c=='r'||c=='R') && race.over) {
                race_init(&race); crowd_init(&race.crowd,(unsigned int)tick_clock()); if(background()) goto done; last=tick_clock();
            }
        }
        now=tick_clock(); elapsed=now-last; if(elapsed<0) elapsed+=3600;
        while(now>=0 && elapsed<4) {
            ticks=5-elapsed; _os9_sleep(&ticks);
            now=tick_clock(); elapsed=now-last; if(elapsed<0) elapsed+=3600;
        }
        steps=elapsed>>2; if(steps<1) steps=1; if(steps>12) steps=12;
        last=now-(elapsed&3); if(last<0) last+=3600;
        for(i=0;i<steps;i++) race_step(&race,keys);
        frame();
    }
#endif
done:
    _os_ss_keysense(w,0);
    if(video) unmap_video(video,video_count);
    Flush(); _os_close(w);
    if(double_buffer) _os_close(screens[page^1].path);
    return 0;
}
