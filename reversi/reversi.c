/* SCC$reversi.c#mwc0.01/26Apr1991 */
/* reversi: a game like Othello
*  An OS-9 version in C, by Joel Matthew Rees, Dec '89
*  Drastically modified for MS-DOS/TURBO-C March 1991 -- jmr
*  new OS-9/CoCo version Apr/May 1991
*  Copyright 1991 Joel Matthew Rees
*  eliminated BORDER, pWIDTH for speed -- JMR 13Apr1991
*  This program and all object code generated from it and its excerpts
*  are assigned by the author to the public domain.
*/

/*
   problems with (LN *) casting!
*/


#include <stdio.h>
#include <process.h>
#include <ctype.h>
#include <common.h>
#include <keybd.h>
#include "rand.h"
#include "board.h"


static char gbuf[4];

/* this probably ought have been defined in board.c!
*  getc for a path rather than a file pointer
*/
int getch(path)
int path;
{
  read(path, gbuf, 1);
  return(gbuf[0]);
}


#define KBRDY 1

/* this might also ought have been defined in board.c!
*  check for input available
*/
int kbhit(p)
int p;
{
  return (getstat(KBRDY, p) != EOF);
}


/* eat NUL prebytes and force upper case
*  caveats: punctuation (0x20 -- 0x3f) gets forced to control characters
*/
int getarrow()
{ int temp;

  while ((temp = getch(path)) == NUL) ;
  return (temp & ~0x20);
}


/* strategic values of board positions */
BD vals =
{
  {   8,  -4,   4,   2,   2,   4,  -4,   8 },
  {  -4,  -7,  -2,  -1,  -1,  -2,  -7,  -4 },
  {   4,  -2,   1,   0,   0,   1,  -2,   4 },
  {   2,  -1,   0,   0,   0,   0,  -1,   2 },
  {   2,  -1,   0,   0,   0,   0,  -1,   2 },
  {   4,  -2,   1,   0,   0,   1,  -2,   4 },
  {  -4,  -7,  -2,  -1,  -1,  -2,  -7,  -4 },
  {   8,  -4,   4,   2,   2,   4,  -4,   8 }
};

SQUARE *valp = (SQUARE *) vals;


#define DEPTH 7 /* must be one less than a power of two */
BD board[DEPTH + 1];
static int top = 0; /* top of the various stacks */
static int level; /* level of look-ahead */


/* for a fast offset and a cast that doesn't work in MWC
 should be LN *boardof(x)
*/
SQUARE *boardof(x)
int x; /* LSByte only */
{
  return (SQUARE *)board + x * WIDTH * WIDTH;
}


/* translate an arrow key to cursor motion
*  Permute graphics mapping in this function
*  Perform bounding ELSEWHERE!!!
*/
SQUARE *cursmove(cursor, key)
SQUARE *cursor; uint key;
{ int k_d;

  switch (key) {
  case LEFT:
    k_d = -1; break;
  case RIGHT:
    k_d = 1; break;
  case DOWN:
    k_d = WIDTH; break;
  case UP:
    k_d = -WIDTH; break;
  case 'C':
    cursor = NULL; /* fall through */
  default:
    k_d = 0;
  }
  if (k_d != 0) {
    cursor += k_d;
  }
  return (cursor);
}


/* convert pointers to indices
*  8 byte wide board is faster than to / and %
* #asm code assumes sizeof(board) < 128
*/
xy(bd, pos, ax, ay)
LN *bd; SQUARE *pos; int *ax; int *ay;
{
  int dif = pos - (SQUARE *)bd;
  *ay = dif / WIDTH;
  *ax = dif % WIDTH;
}


/* erase board and fill in borders
*/
init(tboard)
LN *tboard;
{
  register SQUARE *bd = (SQUARE *) tboard;
  SQUARE *lim = ((SQUARE *) tboard) + WIDTH * WIDTH;

  while (bd < lim)
    *bd++ = NONE;
}


#define RANK7 (WIDTH * (WIDTH - 1))


/* check all directions for a scoring line
*  quits as soon as a scoring line is found
*  returns TRUE if scoring line found
*  This might be done in a loop, but it should be faster unrolled
*/
int radar(bd, player, pos)
LN *bd; SQUARE player; SQUARE *pos;
{
  register SQUARE *base = (SQUARE *) bd;
  int ipos = pos - base;
  int beam = ipos;
  SQUARE other = -player;

  if ((*pos == NONE) && (((unsigned) beam) < WIDTH * WIDTH)) {
    if (beam < WIDTH * (WIDTH - 2)) { /* up the array */
      if (base[beam += WIDTH] == other)
        while (beam < RANK7)
          if (base[beam += WIDTH] != other)
            if (base[beam] == player)
              goto ping;
            else
              break;
      beam = ipos;
      if ((beam & WM) < 6) /* up & right */
        if (base[beam += WIDTH + 1] == other)
          while (((beam & WM) < 7) && (beam < RANK7))
            if (base[beam += WIDTH + 1] != other)
              if (base[beam] == player)
                goto ping;
              else
                break;
      beam = ipos;
      if ((beam & WM) > 1) /* up & left */
        if (base[beam += WIDTH - 1] == other)
          while (((beam & WM) > 0) && (beam < RANK7))
            if (base[beam += WIDTH - 1] != other)
              if (base[beam] == player)
                goto ping;
              else
                break;
    }
    beam = ipos;
    if (beam >= WIDTH * 2) { /* down the array */
      if (base[beam -= WIDTH] == other)
        while (beam >= WIDTH)
          if (base[beam -= WIDTH] != other)
            if (base[beam] == player)
              goto ping;
            else
              break;
      beam = ipos;
      if ((beam & WM) < 6) /* down & right */
        if (base[beam -= WIDTH - 1] == other)
          while (((beam & WM) < 7) && (beam > WIDTH))
            if (base[beam -= WIDTH - 1] != other)
              if (base[beam] == player)
                goto ping;
              else
                break;
      beam = ipos;
      if ((beam & WM) > 1) /* down & left */
        if (base[beam -= WIDTH + 1] == other)
          while (((beam & WM) > 0) && (beam > WIDTH))
            if (base[beam -= WIDTH + 1] != other)
              if (base[beam] == player)
                goto ping;
              else
                break;
    }
    beam = ipos;
    if ((beam & WM) < 6) /* right */
      if (base[++beam] == other)
        while ((beam & WM) < 7)
          if (base[++beam] != other)
            if (base[beam] == player)
              goto ping;
            else
              break;
    beam = ipos;
    if ((beam & WM) > 1) /* left */
      if (base[--beam] == other)
        while ((beam & WM) > 0)
          if (base[--beam] != other)
            if (base[beam] == player)
              goto ping;
            else
              break;
  }
  return(FALSE);
ping:
  return(TRUE);
}


/* put a piece down and capture lines
*  returns count captured, does not count piece played
*/
int play(bd, pos, player)
LN *bd; SQUARE *pos; SQUARE player;
{
  register SQUARE *base = (SQUARE *) bd;
  int ipos = pos - base;
  int beam = ipos;
  int pcs = 0;
  SQUARE other = -player;

  if ((*pos == NONE) && (((unsigned) beam) < WIDTH * WIDTH)) {
    while (beam < RANK7) /* up the array */
      if (base[beam += WIDTH] != other)
        break;
    if (base[beam] == player)
      while (base[beam -= WIDTH] == other) {
        base[beam] = player;
        pcs++;
      }
    beam = ipos;
    while (beam >= WIDTH) /* down the array */
      if (base[beam -= WIDTH] != other)
        break;
    if (base[beam] == player)
      while (base[beam += WIDTH] == other) {
        base[beam] = player;
        pcs++;
      }
    beam = ipos;
    while ((beam & WM) < 7) /* right */
      if (base[++beam] != other)
        break;
    if (base[beam] == player)
      while (base[--beam] == other) {
        base[beam] = player;
        pcs++;
      }
    beam = ipos;
    while ((beam & WM) > 0) /* left */
      if (base[--beam] != other)
        break;
    if (base[beam] == player)
      while (base[++beam] == other) {
        base[beam] = player;
        pcs++;
      }
    beam = ipos; /* up & right */
    while (((beam & WM) < 7) && (beam < RANK7))
      if (base[beam += WIDTH + 1] != other)
        break;
    if (base[beam] == player)
      while (base[beam -= WIDTH + 1] == other) {
        base[beam] = player;
        pcs++;
      }
    beam = ipos; /* up & left */
    while (((beam & WM) > 0) && (beam < RANK7))
      if (base[beam += WIDTH - 1] != other)
        break;
    if (base[beam] == player)
      while (base[beam -= WIDTH - 1] == other) {
        base[beam] = player;
        pcs++;
      }
    beam = ipos; /* down & right */
    while (((beam & WM) < 7) && (beam >= WIDTH))
      if (base[beam -= WIDTH - 1] != other)
        break;
    if (base[beam] == player)
      while (base[beam += WIDTH - 1] == other) {
        base[beam] = player;
        pcs++;
      }
    beam = ipos; /* down & left */
    while (((beam & WM) > 0) && (beam >= WIDTH))
      if (base[beam -= WIDTH + 1] != other)
        break;
    if (base[beam] == player)
      while (base[beam += WIDTH + 1] == other) {
        base[beam] = player;
        pcs++;
      }
    if (pcs > 0) {
      *pos = player;
      if (top == level + 1)
        pcs += valp[pos - (SQUARE *) bd];
    }
  }
  return(pcs);
}


/* seek a playable position, from pos, in increasing order
*  restores pos to board boundaries before seeking
*  before or after board will start at bd[0][0]
*  tests (restored) pos first
*  return NULL if no position playable after returning to pos
*/
SQUARE *seek(bd, pos, turn)
LN *bd; SQUARE *pos; SQUARE turn;
{
  register SQUARE *hunt;
  SQUARE *bhome = (SQUARE *) bd;
  SQUARE *bend = (SQUARE *) bd + WIDTH * WIDTH - 1;

  if ((pos < bhome) || (pos > bend))
    pos = bhome;
  hunt = pos;
  do {
    if (*hunt == NONE)
      if (radar(bd, turn, hunt)) {
        pos = NULL; /* force hunt != pos */
        break;
      }
    if (++hunt > bend)
      hunt = bhome;
  } while (hunt != pos);
  return (hunt == pos ? NULL : hunt);
}


/* wrap pos around center
*/
SQUARE *wrapsq(bd, pos, lo, hi)
LN *bd; SQUARE *pos; int lo; int hi;
{ int i, j;

  xy(bd, pos, &j, &i);
  if (i < lo)
    i = hi;
  else if (i > hi)
    i = lo;
  if (j < lo)
    j = hi;
  else if (j > hi)
    j = lo;
  return ((SQUARE *) bd + (i << 3) + j);
}


/* drop out unceremoniously
*  (have to provide some orderly emergency exit!)
*/
quit(turn)
SQUARE turn;
{
  int resp;

  Bell(path);
  prompt(REALLY, turn);
  resp = tolower(getch(path));
  if ((resp == 'y') || (resp == 'q')) {
    endgraph();
    printf("So glad you could join us!\n");
    exit(0);
  }
  unprompt(REALLY);
}


/* copy top level to test level,
*  initializes and cancels operations on test level,
*/
revert()
{
  SQUARE *scan = (SQUARE *)board + top * WIDTH * WIDTH;
  int n;
  for (n=0; n<WIDTH*WIDTH; n++) scan[n] = scan[n-WIDTH*WIDTH];
}


/* find best play, recursive to level
*  return a value for the play
*  uses *pos to seed seek()
*  also uses *pos to flag noplay for next level of recursion
*  displays the cursor when evaluating level 0
*  also checks for keyboard quit when evaluating level 0
*/
int eval(turn, pos)
SQUARE turn; SQUARE **pos;
{
  SQUARE *test; /* should be (LN *) */
  register SQUARE *check = (*pos) + WIDTH * WIDTH;
  SQUARE *oldc = NULL;
  SQUARE *best = NULL;
  int val;
  int oldv = MININT;
  int x, y;
  SQUARE *other = NULL;

  test = boardof(++top);
  revert();
  check = seek(test, check - WIDTH - 1, turn); /* seek neighboring */
  oldc = check; /* flag end */
  other = check; /* flag noplay for deeper levels */
  do {
    if (check != NULL) {
      if (top == 1) {
        if (kbhit(path))
          if ((getch(path) | 0x20) == 'q')
            quit(turn);
        xy(test, check, &x, &y);
        showcursor(x, y, TRUE);
      }
      val = play(test, check, turn);
    }
    else {
      val = 0;
      if ((check == NULL) && (*pos == NULL))
        break; /* no play left */
    }
    if (top < level)
      val -= eval(-turn, &other);
    if (val > oldv) {
      oldv = val;
      best = check;
    }
    else if ((val == oldv) && (trand(1001 + top) & 32))
      best = check;
    revert();
    check++;
    if (top == 1) {
      if (kbhit(path))
        if ((getch(path) | 0x20) == 'q')
          quit(turn);
      clrcursor();
    }
  } while ((check = seek(test, check, turn)) != oldc);
  --top;
  *pos = (best == NULL) ? NULL : boardof(top) + (best - (SQUARE *) test);
  return(oldv);
}


/* get a play from a user
*  return NULL if computer selected or no play
*/
SQUARE *getuplay(turn, pos)
SQUARE turn; SQUARE *pos;
{
  SQUARE *cursor = seek(board, pos - WIDTH - 1, turn); /* neighbor */
  uint key;
  int x, y;

  if (cursor != NULL) {
    Bell(path);
    prompt(WILLPLAY, turn);
    key = 1; /* not NUL, no action */
    do {
      xy(board, cursor, &x, &y);
      showcursor(x, y, (key != NUL));
      cursor = cursmove(cursor, key = getarrow());
      if (key == 'Q')
        quit(turn);
      clrcursor();
      if (cursor != NULL)
        cursor = wrapsq(board, cursor, 0, 7);
      else
        break;
      if (radar(board, turn, cursor)) {
        Bell(path);
        prompt(WILLPLAY, turn);
      }
      else {
        key = NUL;
        prompt(NOGOOD, turn);
      }
    } while(key != '\r');
  }
  unprompt(WILLPLAY);
  return(cursor);
}


static int turnf[BLACK - WHITE + 1]; /* set by getprefs */
static int *uturn = turnf + 1; /* for accessing turn by player */

/* get a position to play a turn
*  returns the position to play
*/
SQUARE *getplay(turn)
SQUARE turn;
{
  static SQUARE *mem = (SQUARE *) board;
  SQUARE *mtemp;

  if (uturn[turn]) {
    prompt(USER, turn);
    mtemp = getuplay(turn, mem);
    unprompt(USER);
  }
  if (!uturn[turn] || (mtemp == NULL)) {
    prompt(COMPUTER, turn);
    eval(turn, &mem);
    unprompt(COMPUTER);
  }
  else
    mem = mtemp;
  return(mem);
}


/* find an empty position in the center four
*  forces pos to "nearest" center position if out of bounds
*  returns pos found or NULL
*/
SQUARE *seekctr(pos)
register SQUARE *pos;
{ SQUARE *pos33 = (SQUARE *) board + 3 * WIDTH + 3;
  SQUARE *pos43 = pos33 + WIDTH;
  SQUARE *old = NULL;

  if (pos < pos33)
    pos = pos33;
  while (TRUE) {
    if ((pos > pos33 + 1) && (pos < pos43))
      pos = pos43;
    else if (pos > pos43 + 1)
      pos = pos33;
    if ((*pos == NONE) || (pos == old))
      break;
    if (old == NULL)
      old = pos;
    pos++;
  }
  return (*pos == NONE ? pos : NULL);
}


/* let user select one of first four moves
*  returns position selected
*  if no position available, returns NULL
*/
SQUARE *getuctr(turn)
SQUARE turn;
{
  SQUARE *cursor = seekctr((SQUARE *) board);
  uint key;
  int x, y;

  if (cursor != NULL) {
    Bell(path);
    prompt(WILLPLAY, turn);
    key = 1; /* not NUL, no action */
    do {
      xy(board, cursor, &x, &y);
      showcursor(x, y, (key != NUL));
      cursor = cursmove(cursor, key = getarrow());
      if (key == 'Q')
        quit(turn);
      clrcursor();
      if (cursor != NULL)
        cursor = wrapsq(board, cursor, 3, 4);
      else
        break;
      if (*cursor != NONE) {
        prompt(NOGOOD, turn);
        key = NUL;
      }
      else
        prompt(WILLPLAY, turn);
    } while(key != '\r');
  }
  unprompt(WILLPLAY);
  return(cursor);
}


/* have computer find one of the first four moves
*  return position found or NULL
*/
SQUARE *getcctr()
{ SQUARE *pos = (SQUARE *) board + WIDTH * 3 + 3;

  if (trand(129) & 8)
    pos++;
  if (trand(511) & 4)
    pos += WIDTH;
  return (seekctr(pos));
}


/* set by getprefs
*  flag diagonal first four plays
*/
static int diag;


firstplay()
{ SQUARE turn = BLACK;
  SQUARE *pos = NULL;
  SQUARE *pos43 = (SQUARE *) board + 4 * WIDTH + 3;
  int off;

  while (TRUE) {
    display((SQUARE *) board, turn);
    prompt(uturn[turn], turn);
    if (uturn[turn])
      pos = getuctr(turn);
    if (!uturn[turn] || (pos == NULL))
      pos = getcctr();
    unprompt(uturn[turn]);
    if (pos == NULL)
      break;
    *pos = turn;
    if (diag) {
      off = pos43 - pos + 1;
      *((off & 1) ? pos + 1 : pos - 1) = -turn;
      pos += (pos >= pos43) ? -WIDTH : WIDTH;
      *pos = -turn;
      *((off & 1) ? pos + 1 : pos - 1) = turn;
      break;
    }
    turn = -turn;
  }
}


/* read a char and flush to EOL
*/
int getc2cr()
{ int ch = getchar();

  while (getchar() != '\n') ;
  return (ch);
}


getprefs()
{ trandize();
  printf("A game of Reversi\n\n");
  printf("Copyright 1991, Joel Matthew Rees\n");
  printf("   565 E. Mansfield Ave,\n   South Salt Lake City, Utah 84106\n\n");
  printf("Enter skill level <0 .. %d>\n", DEPTH);
  level = (DEPTH & getc2cr());
  printf("\nWill the computer play black? <y/n>\n");
  uturn[BLACK] = !(tolower(getc2cr()) == 'y');
  printf("\nWill the computer play white? <y/n>\n");
  uturn[WHITE] = !(tolower(getc2cr()) == 'y');
  printf("\nWill the first four plays be\n   diagonal <y/n>\n");
  diag = tolower(getc2cr()) == 'y';
  printf("\nInstructions:\n");
  printf("Use cursor keys\n   and press <ENTER> to select play.\n");
  printf("Press <C>\n   to have the computer play for you.\n");
  printf("Press any key to start the game.\n");
  getchar();
  trandize();
}


main()
{
  int noplay = FALSE;
  SQUARE turn = BLACK;
  SQUARE *pos;

  getprefs();
  gograph();
  init(board);
  putboard();
  firstplay();
  do {
    display(board, turn);
    prompt(CONTINUE, turn);
    getch(path);
    if ((pos = getplay(turn)) == NULL) {
      noplay++;
      prompt(NOPLAY, turn);
    }
    else {
      noplay = FALSE;
      play(board, pos, turn);
    }
    turn = -turn;
  } while (noplay < 2);
  display(board, 0);
  prompt(QUIT, turn);
  getch(path);
  endgraph();
  printf("Thank you.\n  Come again.\n");
  return(0);
}
