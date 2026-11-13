/* SCC$board.c#mwc0.01/26Apr1991 */
/* game board for reversi.c
*  by Joel Matthew Rees, Dec '89
*  Modified for MS-DOS/TURBO-C March 1991
*  eliminated BORDER, pWIDTH for speed -- JMR 13Apr1991
*  new OS-9/CoCo version Apr/May 1991
*  This program is assigned by the author to the public domain.
*/


#include <string.h>
#include <stdio.h>
#include <sgstat.h>
#include <common.h>


#include "rev_img.h"
#define BOARD
#include "board.h"


#define MAXUSER 16 /* assume no more than this */


#define CELL 22 /* even for border and center */
#define bdHOME 0
#define bdHOMEpx 2
#define bdFAR 23 /* ((CELL + 1) * WIDTH) / 8 */

/* p * 22 */
static uint off(p)
uint p;
{
  return p * 22 + 2;
}


#define PIECEoff 2 /* (CELL - piecex + 1) / 2 */
#define CURSORoff 7 /* (CELL - cursx + 1) / 2 */


/* buffer numbers: */
/* BLACK is 1, WHITE is -1 (= 255) */
/* ILLEGAL is 2, XHAIR is 3 */
#define FONT 4


/* window types */
#define WT40X24 1
#define WT80X24 2
#define WGHI2CO 5
#define WGMD4CO 6
#define WGHI4CO 7
#define WGMD16CO 8
/* colors (depend on put logic, also on palette settings) */
#define cWHITE 0
#define cBLUE 1
#define cBLACK 2
#define cGREEN 3
/* image put logic */
#define lNONE 0
#define lAND 1
#define lOR 2
#define lXOR 3
/* overlay window save select */
#define oSAVE 1
#define oNOSAVE 0


int path;

static struct sgbuf wstat;
int group;

/* set up a window as a graphics window to run the game in
*  return -1 if unable to set window up properly
*/
int gograph()
{
  if ((path = open("/w", _READ | _WRITE))  < 0) {
    fprintf(stderr, "error opening graphics window\n");
    exit (-1);
  }
  if (getstat(0, path, &wstat) < 0) {
    fprintf(stderr, "error accessing window modes\n");
    exit (-1);
  }
  wstat.sg_case = wstat.sg_echo = wstat.sg_alf = wstat.sg_pause = 0;
  if (setstat(0, path, &wstat) < 0) {
    fprintf(stderr, "error changing window modes\n");
    exit (-1);
  }
  DWSet(path, WGMD4CO, 0, 0, 40, 24, cBLUE, cGREEN, cBLUE);
  ScaleSw(path, FALSE);
  Select(path);
  group = getpid();
  CurOff(path);
  if (group == 0)
    group = MAXUSER; /* group 0 reserved */
  GPLoad(path, group, FONT, gcfontty, gcfontx, gcfontx, gcfontln, gcfont);
/*  write(path, gcfont, gcfontln); GPLoad actually takes care of this,
*   contrary to the what the MultiVue docs */
  Font(path, group, FONT);
  GPLoad(path, group, BLACK, piecety, piecex, piecex, blackln, black);
  GPLoad(path, group, WHITE, piecety, piecex, piecex, whiteln, white);
  GPLoad(path, group, ILLEGAL, cursty, cursx, cursx, illln, illegal);
  GPLoad(path, group, XHAIR, cursty, cursx, cursx, arcxhaln, arcxhair);
  LSet(path, lNONE);
  return (path);
}


endgraph()
{
  KilBuf(path, group, FONT);
  KilBuf(path, group, BLACK);
  KilBuf(path, group, WHITE);
  KilBuf(path, group, ILLEGAL);
  KilBuf(path, group, XHAIR);
  DWEnd(path);
  close(path);
  putchar(0x1b); putchar(0x21); /* reselect start window */
}


/* draw a line from (x0, y0) to (x, y)
*  leaves draw pointer at (x0, y0)
*/
static line(x0, y0, x, y)
int x0, y0, x, y;
{
  SetDPtr(path, x0, y0);
  Line(path, x, y);
}


/* set up the playing board on the screen, without pieces
*/
static grid(home, sq_sz, sq_ct)
uint home; uint sq_sz; uint sq_ct;
{
  uint i;
  uint term = sq_ct * sq_sz + home;

  for (i=home; i<=term; i+=sq_sz)
  {
    line(home, i, term, i);
    line(i, home, i, term);
  }
}


/* put board on screen
*/
putboard()
{
  OWSet(path, oNOSAVE, bdHOME, bdHOME, bdFAR, bdFAR, cBLUE, cGREEN);
  Clear(path);
  grid(bdHOMEpx, CELL, WIDTH); /* skip edge */
  OWEnd(path);
  OWSet(path, oNOSAVE, bdFAR, bdHOME, 40 - bdFAR, 24, cBLUE, cBLUE);
  Clear(path);
  OWEnd(path);
  OWSet(path, oNOSAVE, bdHOME, bdFAR, 40, 24 - bdFAR, cBLUE, cBLUE);
  Clear(path);
  OWEnd(path);
}


/* put a player's piece on the board at position (x, y)
*/
putpiece(player, x, y)
SQUARE player; uint x; uint y;
{
  PutBlk(path, group, player, off(x) + PIECEoff, off(y) + PIECEoff);
}


/* convert up to two digits of count into a decimal string in buffer
*  (buffer should be at least 3 bytes)
*  return address of buffer passed in
*/
static char *convert(buffer, count)
char *buffer; int count;
{
  register char *at = buffer;
  int dig1 = count / 10;

  if (dig1 != 0)
    *at++ = dig1 + '0';
  *at++ = (count % 10) + '0';
  *at = NUL;
  return (buffer);
}


#define gxHOME bdFAR
#define gxGL 24
#define gWID 32
#define gxGR 80
#define gxFAR 17
#define gyHOME 0
#define gyTURN 12
#define gySCORE 9
#define gyGAUGE 68 /* 9 * 8 - 4 */
#define gyFAR 15


static char buffer[4];

/* put a bar on the screen, with variable fill
*   puts bars upside up
*   alters the draw pointer
*/
static gauge(xhome, height, player)
uint xhome; uint height; int player;
{
  FColor(path, (player == WHITE) ? cWHITE : cBLACK);
  CurXY(path, (xhome >> 3) + 1, gySCORE);
  write(path, convert(buffer, height), 2);
  SetDPtr(path, xhome, gyGAUGE);
  Bar(path, xhome + gWID, gyGAUGE - height);
}


/* show count graphically and numerically,
*   using turn to determine gauge to put on left
*/
static gauges(bpts, wpts, turn)
uint bpts; uint wpts; SQUARE turn;
{
  int left = turn;

  OWSet(path, oNOSAVE, gxHOME, gyHOME, gxFAR, gyFAR, cGREEN, cBLUE);
  Clear(path);
  CurXY(path, 0, gyTURN);
  if (turn == NONE) {
    left = (wpts > bpts) ? WHITE : BLACK;
    if (bpts == wpts)
      write(path, "TIE!", 4);
    else {
      FColor(path, (left == WHITE) ? cWHITE : cBLACK);
      write(path, "WINNER:", 7);
      putpiece(left, 3, 4);
    }
  }
  else {
    FColor(path, (turn == WHITE) ? cWHITE : cBLACK);
    write(path, "TURN:", 5);
    putpiece(turn, 3, 4);
  }
  gauge(gxGL, (left == WHITE) ? wpts : bpts, left);
  gauge(gxGR, (left == WHITE) ? bpts : wpts, -left);
  OWEnd(path);
}


#define PROMPTLN bdFAR
#define vWIDE 40


/* clear a prompt line window and write in it
*  x and y are start, in absolute characters
*  if length is zero, uses length of string
*  clips if x + length > vWIDE - 1
   right justifies on bottom line
*/
static writelw(x, y, turn, s, len)
uint x; uint y; int turn; char *s; uint len;
{
  int color = (turn == WHITE) ? cWHITE : cBLACK;
  uint slen = strlen(s);

  if (x > vWIDE - 2)
    return;
  if (len == 0)
    len = slen;
  if (x + len > vWIDE - 1) /* avoid wrap */
    len = vWIDE - 1 - x;
  if (slen > len)
    slen = len;
  OWSet(path, oNOSAVE, x, y, len + 1, 1, color, cBLUE);
  Clear(path);
  if ((y == PROMPTLN) && (slen < len))
    CurXY(path, len - slen, 0);
  write(path, s, slen);
  OWEnd(path);
}


#define L1 16 /* gyFAR + 1 */
#define L2 17 /* gyFAR + 2 */
#define L3 18 /* gyFAR + 3 */

/* clear a prompt
*/
unprompt(words)
int words;
{
  switch(words) {
  case USER :
    writelw(25, L1, NONE, "", 12);
    writelw(25, L2, NONE, "", 10);
    writelw(25, L3, NONE, "", 6);
    break;
  case COMPUTER :
    writelw(25, L1, NONE, "", 6);
    break;
  }
  writelw(0, PROMPTLN, NONE, "", 40);
}


/* prompt player(s)
*/
prompt(words, turn)
int words; SQUARE turn;
{
  switch(words) {
  case USER :
    writelw(25, L1, turn, "move: <\xd2\xd4\xd1\xd3>", 12);
    writelw(25, L2, turn, "<C>omputer", 10);
    writelw(25, L3, turn, "<Q>uit", 6);
  case WILLPLAY :
    writelw(0, PROMPTLN, turn, "<ENTER> to play", 40);
    break;
  case COMPUTER :
    writelw(25, L1, turn, "<Q>uit", 6);
    writelw(0, PROMPTLN, turn, "... thinking ...", 40);
    break;
  case QUIT :
    writelw(0, PROMPTLN, turn, "> Press any key to end", 40);
    break;
  case REALLY :
    writelw(0, PROMPTLN, turn, "> Confirm quit? <Y/N>", 40);
    break;
  case NOGOOD :
    writelw(0, PROMPTLN, turn, "** Can't play here!", 40);
    break;
  case CONTINUE :
    writelw(0, PROMPTLN, turn, ">> Press any key to continue", 40);
    break;
  case NOPLAY :
    writelw(0, PROMPTLN, turn, "** No square playable! **", 40);
    break;
  }
}


/* put the pieces out, show counts and turn
*  if turn is 0, show winner
*/
display(tbd, turn)
LN *tbd; SQUARE turn;
{
  register SQUARE *bd = (SQUARE *) tbd;
/* MWC apparently sees tbd as char **! */
  uint i, j;
  SQUARE pc;
  int bct = 0;
  int wct = 0;

  OWSet(path, oNOSAVE, bdHOME, bdHOME, bdFAR, bdFAR, cBLUE, cGREEN);
  for (i = 0; i < WIDTH; i++)
    for (j = 0; j < WIDTH; j++) {
      pc = *bd++;
      if ((pc == BLACK) || (pc == WHITE)) {
        putpiece(pc, j, i);
        if (pc == BLACK)
          bct++;
        else
          wct++;
      }
    }
  gauges(bct, wct, turn);
  OWEnd(path);
}


/* OS-9 does this for us:
static uint px = bdHOMEpx;
static uint py = bdHOMEpx;
*/

/* put a cursor on the screen, remembering position
* The OS-9 cursor is independent of the active window.
* Translation of window to board is handled in off()
*/
showcursor(x, y, valid)
uint x; uint y; int valid;
{
  PutGC(path, off(x) + CURSORoff, off(y) + CURSORoff);
  SetGC(path, group, valid ? XHAIR : ILLEGAL);
}


/* remove cursor from remembered position
*/
clrcursor()
{
  SetGC(path, 0, ILLEGAL);
}
