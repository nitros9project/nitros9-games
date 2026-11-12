/*

    solitaire.c

    Pyramid Solitaire for the CoCo 3
    Version 1.4

    Copyright (c) 1989
    Zack C. Sessions
    ColorSystems

*/

#define MAIN 1
#include <stdio.h>
#include <wind.h>
#include <mouse.h>
#include <buffs.h>
#include <time.h>
#include <errno.h>
#include <os9.h>
#define TRUE 1
#define FALSE 0
#define OFF 0
int path;
#define UPDATE 3
#define TIMEOUT 10
#define FOLLOW 1
#define MOUSSIG 10
#define WHITE 0
#define BLUE  1
#define BLACK 2
#define RED   3

#define ONCE FALSE

 MSRET msinfo;
 int sigcode;
 int x, y;
 int grpnum;
 char msg[40];
 struct deckcard {
    int     card;
    int     suit;
 } ;
 struct deckcard deck[52];
 int dptr;

 struct deckcard pile[24];
 int pptr;

 struct deckcard pyr[7][7];
 int xpos[7][7], ypos[7][7];

 int endit;
 int pisel, pysel;
 int col, row;
 int sx, sy;
 int selcnt;
 int won_game;
 int some_used;

#include "solitaire.h"

cwait(x,y)
 int *x, *y;
{
    int xit = FALSE;
    while(!xit) {
        tsleep(0);
        if (sigcode==MOUSSIG) {
            _gs_mouse(path,&msinfo);
            if ((msinfo.pt_valid) && (msinfo.pt_stat!=WR_OFWIN)) {
                xit = TRUE;
                *x = msinfo.pt_acx;
                *y = msinfo.pt_acy;
            }
        }
    }
}
de_sel()
{
    FColor(path,BLACK);
    if(pisel) {
        pisel = FALSE;
        SetDPtr(path,8,94);
        Box(path,68,138);
    }
    if(pysel) {
        pysel = FALSE;
        SetDPtr(path,xpos[sx][sy],ypos[sx][sy]);
        Box(path,xpos[sx][sy]+60,ypos[sx][sy]+44);
    }
    selcnt = 0;
}
s_pile()
{
    if (pptr == 0) {
        FColor(path,RED);
        BColor(path,BLUE);
        CurXY(path,19,23);
        write(path,"Pile is empty!",14);
        Bell(path);
        tsleep(90);
        CurXY(path,19,23);
        ErEOLine(path);
        return;
    }
    d_card(8,94,-3,0);
    ++selcnt;
    if ((pile[pptr-1].card == 12)&&(selcnt == 1)) {
        --pptr;
        some_used = TRUE;
        pisel = FALSE;
        selcnt = 0;
        if(pptr==0)
            d_card(8,94,-1,0);
        else
            d_card(8,94,pile[pptr-1].card,pile[pptr-1].suit);
        return;
    }
    if (selcnt == 2) {
    selcnt = 0;
    if (pysel) {
        pysel = FALSE;
        pisel = FALSE;
        if (pyr[sx][sy].card + pile[pptr-1].card == 11) {
            some_used = TRUE;
            pyr[sx][sy].card = -1;
            --pptr;
            FColor(path,BLUE);
            SetDPtr(path,xpos[sx][sy],ypos[sx][sy]);
            Bar(path,xpos[sx][sy]+60,ypos[sx][sy]+44);
            if ((sx==0)&&(sy==0))
                won_game = 1;
            else {
                refresh(sx,sy);
                d_card(8,94,-3,0);
                if (pptr==0)
                    d_card(8,94,-1,0);
                else
                    d_card(8,94,pile[pptr-1].card,pile[pptr-1].suit);
            }
        }
        else {
            FColor(path,RED);
            BColor(path,BLUE);
            CurXY(path,19,23);
            write(path,"Invalid move!",13);
            Bell(path);
            tsleep(90);
            CurXY(path,19,23);
            ErEOLine(path);
            FColor(path,BLACK);
            SetDPtr(path,xpos[sx][sy],ypos[sx][sy]);
            Box(path,xpos[sx][sy]+60,ypos[sx][sy]+44);
            SetDPtr(path,8,94);
            Box(path,68,138);
        }
    }
    else {
        FColor(path,RED);
        BColor(path,BLUE);
        CurXY(path,19,23);
        write(path,"Invalid move!",13);
        Bell(path);
        tsleep(90);
        CurXY(path,19,23);
        ErEOLine(path);
        FColor(path,BLACK);
        SetDPtr(path,8,94);
        Box(path,68,138);
    }
        return;
    }
    pisel = TRUE;
}
refresh(i,j)
 int i, j;
{
    int x, y, z;
    z = 1;
    for (x=i-1; x<7; ++x) {
        for (y=j-1; y<j+z; ++y)
            if (((x==i)&&(y==j))||((x<0)||(x>6)||(y<0)||(y>x)))
                ;
            else
                if (pyr[x][y].card>=0)
                   d_card(xpos[x][y],ypos[x][y],pyr[x][y].card,pyr[x][y].suit);
        ++z;
    }
}
s_pyr()
{
    if(row<6) {
        if ((pyr[row+1][col].card >= 0)||(pyr[row+1][col+1].card >= 0)) {
            FColor(path,RED);
            BColor(path,BLUE);
            CurXY(path,19,23);
            write(path,"Card is not free!",17);
            Bell(path);
            tsleep(90);
            CurXY(path,19,23);
            ErEOLine(path);
            return;
        }
    }
    if (pyr[row][col].card<0)
        return;
    d_card(xpos[row][col],ypos[row][col],-3,0);
    ++selcnt;
    if ((pyr[row][col].card == 12)&&(selcnt == 1)) {
        FColor(path,BLUE);
        SetDPtr(path,xpos[row][col],ypos[row][col]);
        Bar(path,xpos[row][col]+60,ypos[row][col]+44);
        if ((row==0)&&(col==0))
            won_game = 1;
        else {
            refresh(row,col);
            pyr[row][col].card = -1;
            selcnt = 0;
            pysel = FALSE;
            some_used = TRUE;
            return;
        }
    }
    if (selcnt == 2) {
        selcnt = 0;
        if (pysel) {
            pysel = FALSE;
            pisel = FALSE;
            if (pyr[sx][sy].card + pyr[row][col].card == 11) {
                some_used = TRUE;
                pyr[sx][sy].card = -1;
                pyr[row][col].card = -1;
                FColor(path,BLUE);
                SetDPtr(path,xpos[sx][sy],ypos[sx][sy]);
                Bar(path,xpos[sx][sy]+60,ypos[sx][sy]+44);
                refresh(sx,sy);
                FColor(path,BLUE);
                SetDPtr(path,xpos[row][col],ypos[row][col]);
                Bar(path,xpos[row][col]+60,ypos[row][col]+44);
                refresh(row,col);
            }
            else {
                FColor(path,RED);
                BColor(path,BLUE);
                CurXY(path,19,23);
                write(path,"Invalid move!",13);
                Bell(path);
                tsleep(90);
                CurXY(path,19,23);
                ErEOLine(path);
                FColor(path,BLACK);
                SetDPtr(path,xpos[sx][sy],ypos[sx][sy]);
                Box(path,xpos[sx][sy]+60,ypos[sx][sy]+44);
                SetDPtr(path,xpos[row][col],ypos[row][col]);
                Box(path,xpos[row][col]+60,ypos[row][col]+44);
            }
        }
        else {
            if (pile[pptr-1].card + pyr[row][col].card == 11) {
                some_used = TRUE;
                --pptr;
                pyr[row][col].card = -1;
                FColor(path,BLUE);
                SetDPtr(path,xpos[row][col],ypos[row][col]);
                Bar(path,xpos[row][col]+60,ypos[row][col]+44);
                if ((row==0)&&(col==0))
                    won_game = 1;
                else {
                    refresh(row,col);
                    if(pptr==0)
                        d_card(8,94,-1,0);
                    else
                        d_card(8,94,pile[pptr-1].card,pile[pptr-1].suit);
                }
            }
            else {
                FColor(path,RED);
                BColor(path,BLUE);
                CurXY(path,19,23);
                write(path,"Invalid move!",13);
                Bell(path);
                tsleep(90);
                CurXY(path,19,23);
                ErEOLine(path);
                FColor(path,BLACK);
                SetDPtr(path,xpos[row][col],ypos[row][col]);
                Box(path,xpos[row][col]+60,ypos[row][col]+44);
                SetDPtr(path,8,94);
                Box(path,68,138);
            }
        }
        return;
    }
    if (selcnt < 3) {
        sx = row;
        sy = col;
    }
    pysel = TRUE;
}
end_game(name)
 char *name;
{
    SetGC(path,0,0);
    FColor(path,RED);
    BColor(path,BLUE);
    Clear(path);
    Font(path,GRP_FONT,FNT_S8X8);
    CurXY(path,11,7);
    puts("I hope you enjoyed");
    CurXY(path,16,9);
    puts("playing");
    CurXY(path,(40-strlen(name))/2,11);
    puts(name);
    CurXY(path,17,13);
    puts("from");
    CurXY(path,13,15);
    puts("ColorSystems");
    tsleep(200);
    exit(0);
}
main()
{
    int i, j, k, l, m;
    int code;

    grpnum = getpid();
    path = 1;
    DWEnd(path);
    DWSet(path,6,0,0,40,24,0,1,2);
    Select(path);
    Palette(path,WHITE,63);
    Palette(path,BLUE,9);
    Palette(path,BLACK,0);
    Palette(path,RED,36);
    CurOff(path);
    if (_ss_wset(path,WT_PBOX,NULL)<0) {
        CurOn(path);
        exit(errno);
    }

    intercept(sighandler);
    SetGC(path,GRP_PTR,PTR_ARR);
    _ss_mous(path,UPDATE,TIMEOUT,FOLLOW);
    sigcode=0;
    _ss_msig(path,MOUSSIG);

    Border(path,BLACK);
    BColor(path,BLUE);
    FColor(path,RED);
    Clear(path);
    CurXY(path,2,7);
    puts("What kind of monitor are you using?");
    CurXY(path,12,10);
    puts("RGB       CMP");
    endit = FALSE;
    while(!endit) {
        cwait(&x,&y);
        if((y>78)&&(y<89)) {
            if((x>190)&&(x<241)) {
                endit = TRUE;
                BColor(path,WHITE);
                CurXY(path,11,10);
                puts(" RGB ");
            }
            else
                if((x>352)&&(x<405)) {
                    endit = TRUE;
                    Palette(path,BLUE,11);
                    Palette(path,RED,7);
                    BColor(path,WHITE);
                    CurXY(path,21,10);
                    puts(" CMP ");
                }
        }
    }
    SetGC(path,0,0);
    _ss_mous(path,UPDATE,TIMEOUT,0);
    tsleep(60);
/*
    Introduction Routine
*/
    Font(path,GRP_FONT,FNT_S8X8);
    BColor(path,BLUE);
    FColor(path,RED);
    Clear(path);
    CurXY(path,8,2);
    puts("Pyramid Solitaire V1.4");
    CurXY(path,17,4);
    puts("for");
    CurXY(path,11,6);
    puts("OS9 & MultiVue!!");
    CurXY(path,10,11);
    puts("Copyright  c  1989");
    SetDPtr(path,342,92);
    Circle(path,9);
    CurXY(path,18,13);
    puts("by");
    CurXY(path,11,15);
    puts("Zack C. Sessions");
    CurXY(path,18,17);
    puts("of");
    CurXY(path,13,19);
    puts("ColorSystems");
    CurXY(path,7,22);
    puts("Click to Start the Game!");
    Bell(path);

    _ss_mous(path,UPDATE,TIMEOUT,FOLLOW);
    sigcode=0;
    _ss_msig(path,MOUSSIG);
    cwait(&x,&y);
    _ss_mous(path,UPDATE,TIMEOUT,0);

    BColor(path,BLUE);
    FColor(path,RED);
    Clear(path);
    CurXY(path,11,11);
    puts("Please wait  . . .");
    dfn_stuff();
    CurXY(path,11,11);
    BColor(path,BLUE);
    ErLine(path);

/*
    game initialization code
*/

    new_display();
    SetGC(path,GRP_PTR,PTR_ARR);
    _ss_mous(path,UPDATE,TIMEOUT,FOLLOW);
    sigcode=0;
    _ss_msig(path,MOUSSIG);

    for(;;) {
        cwait(&x,&y);
        SetGC(path,0,0);
        _ss_mous(path,UPDATE,TIMEOUT,0);
        check_loc(x, y, &code, &i, &j);
        row = i;
        col = j;
        switch (code) {
            case 1: s_pile();
                    break;
            case 2: deal_deck();
                    break;
            case 3: s_pyr();
                    break;
            case 4: CurXY(path,42,7);
                    BColor(path,WHITE);
                    FColor(path,RED);
                    puts(" QUIT ");
                    tsleep(30);
                    KilBuf(path,grpnum,OFF);
                    end_game("Pyramid Solitaire");
            case 5: CurXY(path,42,9);
                    BColor(path,WHITE);
                    FColor(path,RED);
                    puts(" RE-DEAL ");
                    tsleep(30);
                    new_display();
                    break;
            case 6: CurXY(path,42,11);
                    BColor(path,WHITE);
                    FColor(path,RED);
                    puts(" CANCEL ");
                    tsleep(30);
                    de_sel();
                    CurXY(path,42,11);
                    BColor(path,BLUE);
                    FColor(path,RED);
                    puts(" CANCEL ");
                    break;
        }
        if (won_game==1) {
            Font(path,GRP_FONT,FNT_S8X8);
            BColor(path,WHITE);
            FColor(path,RED);
            Clear(path);
            CurXY(path,14,10);
            puts("You've won !!!");
            CurXY(path,9,14);
            puts("Click for another game!");
            sigcode=0;
            _ss_msig(path,MOUSSIG);
            tsleep(0);
            new_display();
        }

        SetGC(path,GRP_PTR,PTR_ARR);
        _ss_mous(path,UPDATE,TIMEOUT,FOLLOW);
        sigcode=0;
        _ss_msig(path,MOUSSIG);
    }
}
