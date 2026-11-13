/*
    CoCothello.c

    Version 1.2

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
int path;
#define UPDATE 3
#define TIMEOUT 10
#define FOLLOW 1
#define MOUSSIG 10
#define YELLOW 0
#define BLUE 1
#define BLACK 2
#define RED 3
#define B -1
#define W 1

 char *copyright[] = {"CoCothello.c Copyright (c) 1989 ",
                      "ColorSystems, Zack C. Sessions"};

 int  def_play_mode = TRUE;

 int fast;
 MSRET msinfo;
 int sigcode;
 int cmp;
 int x, y;
 int sx, sy;
 int i, j;
 int h1;
 int c1;
 int s2;
 int c;
 int h;
 int f;
 char msg[40];
 int board[10][10];
 int x9;
 int y9;
 int i4[9] = {0,0,-1,-1,-1,0,1,1,1};
 int j4[9] = {0,1,1,0,-1,-1,-1,0,1};
 int n1;
 int z;
 int s3;
 int u;
 int t1;
 int t2;
 int f1;
 int s1;
 int i3, j3;
 int b1;
 int end_game;
 int c_forfeit;
 int h_forfeit;
 int funct;

sighandler(sig)
{
    sigcode = sig;
    _ss_msig(path,MOUSSIG);
}
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
new_game()
{
/*
    game initialization code
*/
    int     i, j, k, l;
    struct sgtbuf tim;
/*  ramdomize */
    getime(&tim);
    i = tim.t_hour;
    j = tim.t_minute;
    k = tim.t_second;
    l = 3600 * i + 60 * j + k;
    srand(l);
    for(i=0; i<10; ++i)
        for(j=0; j<10; ++j)
            board[i][j] = 0;
    board[4][4] = 1;
    board[5][5] = 1;
    board[4][5] = -1;
    board[5][4] = -1;
    end_game = FALSE;
    c_forfeit = FALSE;
    h_forfeit = FALSE;
    n1 = 4;
    z = 0;
    x9 = 1;
    y9 = 1;
    h1 = 2;
    c1 = 2;
    BColor(path,BLACK);
    FColor(path,YELLOW);
    Clear(path);
    for(i=0; i<8; ++i)
        for(j=0; j<8; ++j)
            if(rema(i)==rema(j)) {
                SetDPtr(path,j*47,i*24);
                Bar(path,j*47+45,i*24+23);
            }
    SetDPtr(path,0,0);
    Box(path,376,191);
    for(i=1; i<9; ++i)
        for(j=1; j<9; ++j)
            if(board[i][j]!=0)
                d_piece(i,j);
    FColor(path,YELLOW);
    Font(path,GRP_FONT,FNT_S6X8);
    CurXY(path,38,0);
    puts("CoCothello");

    SetGC(path,GRP_PTR,PTR_ARR);
    sigcode=0;
    _ss_mous(path,UPDATE,TIMEOUT,FOLLOW);

    if(sopt("Should I play my","best strategy?"," YES ","  NO  ")==0)
        s2 = 2;
    else
        s2 = 0;

    if(sopt("Which color do you","want?"," RED "," BLUE ")==0) {
        c = B;
        h = W;
    }
    else {
        c = W;
        h = B;
    }

    if(sopt("Do you want to go","first?"," YES ","  NO  ")==0)
        f = h;
    else
        f = c;

    SetGC(path,0,0);
    _ss_mous(path,UPDATE,TIMEOUT,0);
    CurXY(path,40,3);
    puts("Score");
    CurXY(path,36,5);
    puts("You       Me");
    CurXY(path,33,13);
    puts("QUIT");
    CurXY(path,33,15);
    puts("NEW GAME");
    CurXY(path,33,17);
    puts("FORFEIT");
    d_score();
    if(f==c)
        c_move();
}
int check1()
{
    int i1, j1;
    for(i1=-1; i1<2; ++i1)
        for(j1=-1; j1<2; ++j1)
            if(board[i+i1][j+j1]==t2)
                return(1);
    return(0);
}
check2(scoreit)
 int scoreit;
{
      int k, k1, i6, j6, s3;
      for(s1=0, k=1; k<9; ++k) {
          i6 = i + i4[k];
          j6 = j + j4[k];
          s3 = 0;
          while(board[i6][j6]==t2) {
              ++s3;
              i6+=i4[k];
              j6+=j4[k];
              if(board[i6][j6]==t1)
                  break;
              if(board[i6][j6]==0) {
                  s3 = 0;
                  break;
              }
          }
          s1+=s3;
          if((s3!=0)&&(scoreit)) {
              i6 = i;
              j6 = j;
              for(k1=0; k1<=s3; ++k1) {
                  board[i6][j6] = t1;
                  d_piece(i6,j6);
                  i6+=i4[k];
                  j6+=j4[k];
              }
          }
      }
}
rema(x)
 int x;
{
    return (x+1) & 1;
}
d_score()
{
    FColor(path,YELLOW);
    CurXY(path,37,7);
    ErEOLine(path);
    sprintf(msg,"%2d",h1);
    puts(msg);
    CurXY(path,46,7);
    sprintf(msg,"%2d",c1);
    puts(msg);
}
d_piece(i0,j0)
 int i0, j0;
{
    int     bg;
    if(rema(i0)==rema(j0))
        bg = BLACK;
    else
        bg = YELLOW;
    if(board[i0][j0]<0)
        FColor(path,BLUE);
    else
        if(board[i0][j0]>0)
            FColor(path,RED);
        else
            FColor(path,bg);
    SetDPtr(path,(i0-1)*47+23,(j0-1)*24+12);
    Circle(path,18);
    FFill(path);
}
b_piece(i0,j0)
 int i0, j0;
{
    int     bg;
    if(rema(i0)==rema(j0))
        FColor(path,YELLOW);
    else
        FColor(path,BLACK);
    SetDPtr(path,(i0-1)*47+23,(j0-1)*24+12);
    Circle(path,18);
    FFill(path);
}
get_loc(x,y)
 int x, y;
{
    if(x<377) {
        sx = x/47+1;
        sy = y/24+1;
        funct = 0;
    }
    else
        if((x>397)&&(x<446)&&(y>103)&&(y<112)) {
            sx = 0;
            sy = 0;
            funct = 1;
        }
        else
            if((x>397)&&(x<494)&&(y>119)&&(y<128)) {
                sx = 0;
                sy = 0;
                funct = 2;
            }
            else
                if((x>397)&&(x<482)&&(y>135)&&(y<144)) {
                    sx = 0;
                    sy = 0;
                    funct = 3;
                }
                else
                    funct = -1;
}
int sopt(s1,s2,s3,s4)
 char *s1, *s2, *s3, *s4;
{
    int i;
    int sel;
    BColor(path,BLACK);
    FColor(path,YELLOW);
    CurXY(path,32,10);
    puts(s1);
    CurXY(path,32,11);
    puts(s2);
    CurXY(path,35,14);
    puts(s3);
    CurXY(path,44,14);
    puts(s4);
    sigcode=0;

    i = 0;
    while(i==0) {
        tsleep(0);
        _gs_mouse(path,&msinfo);
        if((msinfo.pt_valid) && (msinfo.pt_stat!=WR_OFWIN)) {
            x = msinfo.pt_acx;
            y = msinfo.pt_acy;
            if((y>111)&&(y<120))
                if((x>433)&&(x<489)) {
                    CurXY(path,35,14);
                    BColor(path,RED);
                    puts(s3);
                    sel = 0;
                    i = 1;
                    tsleep(30);
                }
                else
                    if((x>541)&&(x<589)) {
                        CurXY(path,44,14);
                        BColor(path,RED);
                        puts(s4);
                        sel = 1;
                        i = 1;
                        tsleep(30);
                    }
        }
    }
    BColor(path,BLACK);
    CurXY(path,32,10);
    ErEOLine(path);
    CurXY(path,32,11);
    ErEOLine(path);
    CurXY(path,35,14);
    ErEOLine(path);
    return(sel);
}
do_move(f_flag)
 int f_flag;
{
      FColor(path,YELLOW);
      if(f_flag)
          if(c_forfeit)
              end_game = TRUE;
          else
              h_forfeit = TRUE;
      else {
          t1 = h;
          t2 = c;
          if(board[sx][sy]!=0) {
              CurXY(path,32,22);
              ErEOLine(path);
              CurXY(path,32,23);
              ErEOLine(path);
              CurXY(path,32,22);
              puts("That square is");
              CurXY(path,32,23);
              write(path,"already occupied!",17);
              Bell(path);
              tsleep(30);
              CurXY(path,32,22);
              ErEOLine(path);
              CurXY(path,32,23);
              ErEOLine(path);
              return;
          }
          i = sx;
          j = sy;
          if(check1()!=1) {
              CurXY(path,32,22);
              ErEOLine(path);
              CurXY(path,32,23);
              ErEOLine(path);
              CurXY(path,32,22);
              puts("That is an");
              CurXY(path,32,23);
              write(path,"invalid move!",13);
              Bell(path);
              tsleep(30);
              CurXY(path,32,22);
              ErEOLine(path);
              CurXY(path,32,23);
              ErEOLine(path);
              return;
          }
          check2(FALSE);
          if(s1<=0) {
              CurXY(path,32,22);
              ErEOLine(path);
              CurXY(path,32,23);
              ErEOLine(path);
              CurXY(path,32,22);
              puts("That is an");
              CurXY(path,32,23);
              write(path,"invalid move!",13);
              Bell(path);
              tsleep(30);
              CurXY(path,32,22);
              ErEOLine(path);
              CurXY(path,32,23);
              ErEOLine(path);
              return;
          }
          h_forfeit = FALSE;
          check2(TRUE);
          FColor(path,YELLOW);
          CurXY(path,32,22);
          ErEOLine(path);
          CurXY(path,32,23);
          ErEOLine(path);
          CurXY(path,32,22);
          sprintf(msg,"That gives you %2d",s1);
          puts(msg);
          CurXY(path,32,23);
          write(path,"of my pieces.",13);
          h1 = h1 + s1 + 1;
          c1-=s1;
          ++n1;
          d_score();
          if((c1==0)||(n1==64))
              end_game = TRUE;
          tsleep(120);
          CurXY(path,32,22);
          ErEOLine(path);
          CurXY(path,32,23);
          ErEOLine(path);
      }
      BColor(path,BLACK);
      FColor(path,YELLOW);
      if(h_forfeit) {
          tsleep(60);
          CurXY(path,32,17);
          puts(" FORFEIT ");
      }
      if(!end_game)
          c_move();
      if(end_game) {
          CurXY(path,33,13);
          ErEOLine(path);
          CurXY(path,33,15);
          ErEOLine(path);
          CurXY(path,33,17);
          ErEOLine(path);
          CurXY(path,32,20);
          if(h1==c1)
              puts("A tie!!!");
          else {
              if(h1>c1)
                  puts("You won!!!");
              else
                  puts("Sorry, I win.");
              CurXY(path,32,21);
              puts("That was a");
              CurXY(path,32,22);
              c1 = (64 * abs(c1-h1))/n1;
              if(c1<11)
                  puts("squeaker!!!");
              else
                  if(c1<25)
                      puts("hot game!!");
                  else
                      if(c1<39)
                          puts("fight.");
                      else
                          if(c1<53)
                              puts("walkaway.");
                          else
                              puts("perfect game!");
          }
          SetGC(path,GRP_PTR,PTR_ARR);
          sigcode=0;
          _ss_mous(path,UPDATE,TIMEOUT,FOLLOW);
          if(sopt("Do you want to","play again?"," YES "," NO ")==0) {
              SetGC(path,0,0);
              _ss_mous(path,UPDATE,TIMEOUT,0);
              new_game();
          }
          else
              endgame("CoCothello");
      }
}
c_move()
{
    int     k;
    FColor(path,YELLOW);
    BColor(path,BLACK);
    CurXY(path,32,23);
    write(path,"My move.",8);
    tsleep(60);
    b1 = -1;
    i3 = 0;
    j3 = 0;
    t1 = c;
    t2 = h;
    for(i=1; i<9; ++i)
        for(j=1; j<9; ++j) {
            if(board[i][j]==0) {
                if(check1()!=0) {
                    check2(FALSE);
                    if(s1!=0) {
                        if((i-1)*(i-8)==0)
                            s1+=s2;
                        if((j-1)*(j-8)==0)
                            s1+=s2;
                        if(s1>=b1) {
                            if(s1<=b1) {
                                if(rand()>(32767/2)) {
                                    b1 = s1;
                                    i3 = i;
                                    j3 = j;
                                }
                            }
                            else {
                                b1 = s1;
                                i3 = i;
                                j3 = j;
                            }
                        }
                    }
                }
            }
        }
    CurXY(path,32,23);
    ErEOLine(path);
    if(b1<=0) {
        CurXY(path,32,22);
        ErEOLine(path);
        CurXY(path,32,23);
        ErEOLine(path);
        CurXY(path,32,22);
        puts("I have to forfeit");
        CurXY(path,32,23);
        write(path,"my move!!",9);
        Bell(path);
        if(h_forfeit)
            end_game = TRUE;
        else
            c_forfeit = TRUE;
        tsleep(60);
        CurXY(path,32,22);
        ErEOLine(path);
        CurXY(path,32,23);
        ErEOLine(path);
        return;
    }
    c_forfeit = FALSE;
    i = i3;
    j = j3;
    board[i][j] = t1;
    BColor(path,BLACK);
    CurXY(path,32,22);
    ErEOLine(path);
    CurXY(path,32,23);
    ErEOLine(path);
    write(path,"I move to ...",13);
    d_piece(i,j);
    for(k=0; k<3; ++k) {
        b_piece(i,j);
        d_piece(i,j);
    }
    if(!fast) {
        BColor(path,BLACK);
        FColor(path,YELLOW);
        CurXY(path,32,22);
        ErEOLine(path);
        puts("Click to see");
        CurXY(path,32,23);
        ErEOLine(path);
        write(path,"the result.",11);
        cwait(&x,&y);
    }
    check2(TRUE);
    FColor(path,YELLOW);
    BColor(path,BLACK);
    CurXY(path,32,22);
    ErEOLine(path);
    CurXY(path,32,23);
    ErEOLine(path);
    sprintf(msg,"That gives me %2d",s1);
    CurXY(path,32,22);
    puts(msg);
    CurXY(path,32,23);
    write(path,"of your pieces.",15);
    c1 = c1 + s1 + 1;
    h1-=s1;
    ++n1;
    d_score();
    tsleep(90);
    if((h1==0)||(n1==64))
        end_game = TRUE;
    CurXY(path,32,22);
    ErEOLine(path);
    CurXY(path,32,23);
    ErEOLine(path);
}
endgame(name)
 char *name;
{
    SetGC(path,0,0);
    FColor(path,3);
    BColor(path,1);
    Clear(path);
    Font(path,200,1);
    CurXY(path,11,7);
    puts("I hope you enjoyed");
    CurXY(path,16,9);
    puts("playing");
    CurXY(path,(40-strlen(name))/2-1,11);
    puts(name);
    CurXY(path,17,13);
    puts("from");
    CurXY(path,13,15);
    puts("ColorSystems");
    tsleep(200);
    exit(0);
}
main(argc,argv)
 int argc;
 char *argv[];
{
    int i;
    int code;
    int endit;
    char *p;
    char cc;

    fast = def_play_mode;
    i = 0;
    if(argc > 1) {
        ++argv;
        for(p = *argv; cc = *p; ++p) {
            switch (cc) {
                case 'r' :   i = -1;
                             break;
                case 'R' :   i = -1;
                             break;
                case 'c' :   i = 1;
                             break;
                case 'C' :   i = 1;
                             break;
                case 'f' :   fast = TRUE;
                             break;
                case 'F' :   fast = TRUE;
                             break;
                case 's' :   fast = FALSE;
                             break;
                case 'S' :   fast = FALSE;
                             break;
            }
        }
    }

    path = 1;
    Palette(path,0,63);
    Palette(path,BLUE,9);
    Palette(path,BLACK,0);
    Palette(path,RED,36);
    path = 1;
    DWEnd(path);
    DWSet(path,6,0,0,40,24,0,1,2);
    Select(path);
    CurOff(path);
    if (_ss_wset(path,WT_PBOX,NULL)<0) {
        CurOn(path);
        exit(errno);
    }

    Border(path,BLACK);
    intercept(sighandler);
    _ss_msig(path,MOUSSIG);

    if(i == 0) {
        BColor(path,BLUE);
        FColor(path,RED);
        Clear(path);
        CurXY(path,2,7);
        puts("What kind of monitor are you using?");
        CurXY(path,12,10);
        puts("RGB       CMP");
        endit = FALSE;
        SetGC(path,GRP_PTR,PTR_ARR);
        _ss_mous(path,UPDATE,TIMEOUT,FOLLOW);
        sigcode=0;
        while(!endit) {
            cwait(&x,&y);
            if((y>78)&&(y<89)) {
                if((x>190)&&(x<241)) {
                    endit = TRUE;
                    cmp = FALSE;
                    BColor(path,0);
                    CurXY(path,11,10);
                    puts(" RGB ");
                }
                else
                    if((x>352)&&(x<405)) {
                        endit = TRUE;
                        cmp = TRUE;
                        Palette(path,BLUE,11);
                        Palette(path,RED,7);
                        BColor(path,0);
                        CurXY(path,21,10);
                        puts(" CMP ");
                    }
            }
        }
        SetGC(path,0,0);
        _ss_mous(path,UPDATE,TIMEOUT,0);
        tsleep(60);
    }
    else
        if(i == 1) {
            Palette(path,BLUE,11);
            Palette(path,RED,7);
        }
/*
    Introduction
*/
    BColor(path,BLUE);
    FColor(path,RED);
    Clear(path);
    Font(path,200,1);
    CurXY(path,12,2);
    puts("CoCothello V1.2");
    CurXY(path,15,4);
    puts("for the");
    CurXY(path,11,6);
    puts("Color Computer 3");
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

    cwait(&x,&y);

    if(cmp)
        Palette(path,YELLOW,36);
    else
        Palette(path,YELLOW,54);
    SetGC(path,0,0);
    _ss_mous(path,UPDATE,TIMEOUT,0);
    new_game();

    SetGC(path,GRP_PTR,PTR_ARR);
    sigcode=0;
    _ss_mous(path,UPDATE,TIMEOUT,FOLLOW);

    for(;;) {
        cwait(&x,&y);

        SetGC(path,0,0);
        _ss_mous(path,UPDATE,TIMEOUT,0);

        get_loc(x,y);

        switch (funct) {
            case 0 :    do_move(FALSE);
                        break;
            case 1 :    BColor(path,RED);
                        FColor(path,YELLOW);
                        CurXY(path,32,13);
                        puts(" QUIT ");
                        tsleep(60);
                        endgame("CoCothello");
                        break;
            case 2 :    BColor(path,RED);
                        FColor(path,YELLOW);
                        CurXY(path,32,15);
                        puts(" NEW GAME ");
                        tsleep(60);
                        new_game();
                        break;
            case 3 :    BColor(path,RED);
                        FColor(path,YELLOW);
                        CurXY(path,32,17);
                        puts(" FORFEIT ");
                        do_move(TRUE);
                        break;
        }

        SetGC(path,GRP_PTR,PTR_ARR);
        sigcode=0;
        _ss_mous(path,UPDATE,TIMEOUT,FOLLOW);
    }
}
