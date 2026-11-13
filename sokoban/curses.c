/* curses.c */
/* Replaces unix curses, for coco only */

#include <stdio.h>
/* This file implements the small curses subset used by the game. */
#include <os9.h>
#include <sgstat.h>

/* Global Strings */
char stout[] = {0x1f, 0x20, 0},
     stend[] = {0x1f, 0x21, 0},
     mv[]    = {2, 0, 0, 0},
     deline[] = {0x1f, 0x31, 0},
     stout1[] = {0x1b, 0x53, 0x21, 0},
     stend1[] = {0x1b, 0x53, 0x20, 0},
     cleol1[] = {0x1b, 0x41, 0},
     clbot1[] = {0x1b, 0x42, 0};

int level1;

refresh()
{
    /* do nothing */
}

move(y, x)
int y, x;
{
    mv[1] = x +32;
    mv[2] = y + 32;
    fputs(mv, stdout);
}

clear()
{
    putchar(12);
}

clrtoeol()
{
    if(level1)
        fputs(cleol1, stdout);
    else
        putchar(4);
}

mvclr(y, x)
int y, x;
{
   move(y, x);
   clrtoeol();
}

deleteln()
{
    fputs(deline, stdout);
}

standout()
{
    if(level1)
        fputs(stout1, stdout);
    else
        fputs(stout, stdout);
}

standend()
{
    if(level1)
        fputs(stend1, stdout);
    else
        fputs(stend, stdout);
}

clrtobot()
{
    if(level1)
        fputs(clbot1, stdout);
    else
        putchar(11);
}

int getch()
{
    return getchar();
}

mvaddstr(y, x, str)
int y, x; char *str;
{
    mv[1] = x +32;
    mv[2] = y + 32;
    fputs(mv, stdout);
    fputs(str, stdout);
}

mvaddch(y, x, ch)
int y, x; char ch;
{
    mv[1] = x +32;
    mv[2] = y + 32;
    fputs(mv, stdout);
    putchar(ch);
}

addch(ch)
char ch;
{
    putchar(ch);
    return ch;
}

addstr(str)
char *str;
{
    return(fputs(str, stdout));
}

sound_bell()
{
    putchar(7);
}

static struct sgbuf saved[2];

noecho()
{
    struct sgbuf block;
    int path;
    for (path=0; path<2; path++) {
        getstat(0,path,&saved[path]);
        getstat(0,path,&block);
        block.sg_echo = 0;
        block.sg_pause = 0;
        setstat(0,path,&block);
    }
}

echo()
{
    int path;
    for (path=0; path<2; path++) setstat(0,path,&saved[path]);
}

testlevel()
{
struct registers reg;

    _os9(F_ID, &reg);
    _os9(F_SUSER, &reg);

    if(reg.rg_b)
        level1 = 1;
    else
        level1 = 0;
}
