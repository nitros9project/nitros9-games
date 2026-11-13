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
#include "game.h"
#include "render.h"
static path_id w;
static Game game;
#ifdef BAYOU_PROFILE
static int drawn;
#endif
/* Each screen owns its clean patches from two flips ago. Keeping both
   sets below 16K of process data leaves three slots for mapped video. */
static unsigned char saved[2][4][1152];
static unsigned char hud_backdrop[1920],patch[PATCH_BYTES];
static unsigned char screen_block,screen_blocks,*video;
static int screen_offset,video_first=-1,video_count;
int unmap_video(unsigned char *address,int count);
static View views[4];
static struct { path_id path; unsigned char block; int offset;
    View old[4]; int hp,lives,score;
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
static int video_range(int first,int count) {
    if(video && first>=video_first && first+count<=video_first+video_count) return 0;
    if(video) {
        if(unmap_video(video,video_count)) return 1;
        video=0;
    }
    if(map_video(screen_block+first,count,&video)) return 1;
    video_first=first; video_count=count;
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
    int offset,first,last,row,stride=width>>1;
    unsigned char *h;
    if(screen_blocks==4) {
        offset=screen_offset+y*160+(x>>1); first=offset>>13;
        last=(offset+(height-1)*160+stride-1)>>13;
        if(first>=1) { first=1; last=3; }
        if(video_range(first,last-first+1)) return 1;
        h=video+offset-(video_first<<13);
        for(row=0;row<height;row++) memcpy(h+row*160,data+row*stride,stride);
        return 0;
    }
    return 1;
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
    screens[page].hp=-1;
    return 0;

}
static int background(void) {
    char name[6];
    sprintf(name,"dock%d",game.room);
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
        screens[other].hp=-1;
    }
    return 0;
}
/* CoWin text rows are eight pixels tall. Shift the completed hint up
   three scanlines so it fits between the score and the HUD divider. */
static void exit_hint(void) {
    unsigned char *at;
    int row;
    text(26,2,"GO RIGHT >>>",9); Flush();
    if(video_range(0,1)) return;
    at=video+screen_offset+13*160+104;
    for(row=0;row<8;row++) { memcpy(at,at+480,48); at+=160; }
    memset(at,0,48); memset(at+160,0,48); memset(at+320,0x88,48);
}
static void frame(void) {
    int i,changed=0;
    Actor *a;
    if(double_buffer) {
        use_page(page^1);
        hud_hp=screens[page].hp; hud_lives=screens[page].lives; hud_score=screens[page].score;
    }
    for(i=0;i<4;i++) {
        a=i?&game.foe[i-1]:&game.p;
        views[i].x=a->x; views[i].y=a->y-(i?0:game_height(&game));
        views[i].depth=a->y; views[i].face=a->face;
        views[i].kind=i?(game.room==2?2:1):0;
        views[i].hp=a->hp;
        views[i].visible=a->hp>0 && (i || !game.invuln || !(game.tick&2));
        views[i].pose=0;
        if(a->x!=previous[i].x || views[i].y!=previous[i].y)
            views[i].pose=(game.tick&4)?1:2;
        if(!i && game.jump) views[i].pose=5;
        if(a->attack) views[i].pose=a->attack>3?4:3;
        if(a->stun) views[i].pose=4;
        if(i==GATOR_SLOT+1) {
            views[i].kind=3;
            views[i].pose=a->attack && !a->stun?7:6;
        }
        if(memcmp((const char *)&views[i],(const char *)&previous[i],sizeof(View))) changed=1;
    }
    /* An identical hidden page is already a complete frame. Keep the
       current front selected and preserve the input path associated with it. */
    if(!changed && hud_hp==game.p.hp && hud_lives==game.lives && hud_score==game.score) {
        if(double_buffer) use_page(page^1);
        return;
    }
#ifdef BAYOU_PROFILE
    drawn++;
#endif
    if(screen_blocks==4) {
        unsigned char *at;
        if(video_range(1,3)) return;
        for(i=0;i<4;i++) if(previous[i].visible) {
            at=video+screen_offset+(previous[i].y-47)*160+((previous[i].x&~1)-24)/2-8192;
            copy48(at,saved[page][i],136,0);
        }
        /* Capture every actor's CLEAN background before drawing any
           sprites. Overlapping cached patches therefore restore safely. */
        for(i=0;i<4;i++) if(views[i].visible &&
            (!previous[i].visible || (views[i].x&~1)!=(previous[i].x&~1) || views[i].y!=previous[i].y)) {
            /* A stationary actor already owns the correct clean patch,
               even when its pose, palette or health changes. */
            at=video+screen_offset+(views[i].y-47)*160+((views[i].x&~1)-24)/2-8192;
            copy48(saved[page][i],at,0,136);
        }
        render_actors(video+screen_offset+53*160-8192,160,0,53,320,135,views);
        memcpy(previous,views,sizeof(views));

    }
    if(hud_hp!=game.p.hp || hud_lives!=game.lives || hud_score!=game.score) {
        render_hud(hud_backdrop,patch,&game); upload(patch,0,0,320,12);
        hud_hp=game.p.hp; hud_lives=game.lives; hud_score=game.score;
        screens[page].hp=hud_hp; screens[page].lives=hud_lives; screens[page].score=hud_score;
    }
    if(!game_remaining(&game)) exit_hint();
    if(game.over||game.won) {
        rect(24,56,295,100,0);
        text(5,8,game.won?"YOUR BOAT. YOUR BAYOU. AGAIN.":"THE BAYOU GOT THE BEST OF YOU.",9);
        text(7,11,"R: PLAY AGAIN    Q: QUIT",15); Flush();
    }
    if(double_buffer) { _cgfx_select(w); Flush(); }
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
#ifdef BAYOU_PROFILE
static int profile_seconds(void) {
    _os_time t;
    _os_getime(&t);
    return t.minutes*60+t.seconds;
}
static void profile_report(path_id p,const char *label,int start,int repetitions) {
    char s[96];
    int n,elapsed=profile_seconds()-start;
    if(elapsed<0) elapsed+=3600;
    sprintf(s,"%s: %d operations, %d seconds\r",label,repetitions,elapsed);
    n=strlen(s); _os_write(p,s,&n);
}
static void profile_run(void) {
    path_id report;
    int i,start,n;
    char s[80];
    _os_delete("/dd/BAYOU/profile.txt",0);
    if(_os_create("/dd/BAYOU/profile.txt",FAM_WRITE,&report,FAP_READ|FAP_WRITE)) return;
    sprintf(s,"screen blocks=%d double buffered=%d\r",screen_blocks,double_buffer);
    n=strlen(s); _os_write(report,s,&n);
    start=profile_seconds();
    i=background();
    profile_report(report,"arena load and screen copy",start,1);
    n=video_range(1,3);
    if(i || n) { _os_close(report); return; }
    frame();
    drawn=0; start=profile_seconds();
    for(i=0;i<120;i++) { game_step(&game,RIGHT); frame(); }
    profile_report(report,"full frame",start,120);
    sprintf(s,"actual redraws=%d reused=%d\r",drawn,120-drawn);
    n=strlen(s); _os_write(report,s,&n);
    _os_close(report);
}
#endif
int main(void) {
    struct sgbuf opts;
    int i,keys,ready,count,oldroom,ticks,error,last,now,elapsed,steps;
    char c;
    previous=screens[0].old;
    if(_os_open("/w",FAM_READ|FAM_WRITE,&w)) {
        puts("Bayou needs NitrOS-9 Level 2 with CoWin and /w."); return 1;
    }
    error=_cgfx_dwset(w,8,0,0,40,25,15,0,0);
    if(Flush() || error) { _os_close(w); puts("Cannot allocate graphics window."); return 1; }
    _cgfx_ss_mtyp(w,1);
    _cgfx_curoff(w); _cgfx_scalesw(w,0); _cgfx_select(w); Flush();
    ticks=2; _os9_sleep(&ticks);
    for(i=0;i<16;i++) _cgfx_palette(w,i,pal[i]);
    Flush();
    if(!_os_gs_popt(w,&opts)) {
        opts.sg_echo=opts.sg_pause=opts.sg_kbich=opts.sg_kbach=0;
        _os_ss_popt(w,&opts);
    }
    _os_ss_keysense(w,1);
    if(screen_info(w,&screen_block,&screen_blocks,&screen_offset) || screen_blocks!=4) {
        goto asset_error;
    }
    screens[0].path=w; screens[0].block=screen_block; screens[0].offset=screen_offset;
    game_init(&game);
#ifdef BAYOU_PROFILE
    if(init_buffers()) goto asset_error;
    profile_run();
    goto done;
#else
    if(scene("title")) goto asset_error;
    /* The first artwork write can initialize CoWin's screen state. Apply
       the RGB palette after that initialization has completed. */
    _cgfx_ss_mtyp(w,1); ticks=2; _os9_sleep(&ticks);
    for(i=0;i<16;i++) _cgfx_palette(w,i,pal[i]);
    Flush();
    /* Title lettering and scenery are indexed pixel art, loaded in bands. */
    do { keys=0; _os_gs_keysense(w,&keys); ticks=3; _os9_sleep(&ticks);
        if(!_os_gs_ready(w,&ready) && ready) { count=1; _os_read(w,&c,&count); if(c=='q'||c=='Q') goto done; }
    } while(!(keys & JUMP));
    if(init_buffers()) goto asset_error;
    if(background()) goto asset_error;
    last=tick_clock();
    for(;;) {
        keys=0; _os_gs_keysense(w,&keys);
        /* Drain SCF's queued characters so modifier-key play cannot fill
           the input buffer. Letter X is an optional paddle input. */
        while(!_os_gs_ready(w,&ready) && ready) {
            count=1; if(_os_read(w,&c,&count)) break;
            if(c=='q'||c=='Q') goto done;
            if(c=='x'||c=='X') keys|=ATTACK;
            if((c=='r'||c=='R') && (game.over||game.won)) {
                game_init(&game); if(background()) goto asset_error; last=tick_clock();
            }
        }
        now=tick_clock(); steps=1;
        if(now>=0 && last>=0) {
            elapsed=now-last; if(elapsed<0) elapsed+=3600;
            while(elapsed<4) {
                ticks=5-elapsed; _os9_sleep(&ticks);
                now=tick_clock(); if(now<0) break;
                elapsed=now-last; if(elapsed<0) elapsed+=3600;
            }
            if(now>=0) {
                steps=elapsed>>2; if(steps<1) steps=1; if(steps>3) steps=3;
                last=now-(elapsed&3);
                if(last<0) last+=3600;
            }
        }
        oldroom=game.room;
        for(i=0;i<steps;i++) { game_step(&game,keys); if(oldroom!=game.room) break; }
        if(oldroom!=game.room) {
            if(background()) goto asset_error;
            last=tick_clock();
        }
        frame();
        if(now<0) { ticks=1; _os9_sleep(&ticks); }
    }
#endif
done:
    _os_ss_keysense(w,0);
    if(video) unmap_video(video,video_count);
    Flush(); _os_close(w);
    if(double_buffer) _os_close(screens[page^1].path);
    return 0;
asset_error:
    _os_ss_keysense(w,0);
    if(video) unmap_video(video,video_count);
    Flush(); _os_close(w);
    if(double_buffer) _os_close(screens[page^1].path);
    puts("Cannot load artwork. Install the BAYOU folder in /dd/BAYOU.");
    return 1;
}
