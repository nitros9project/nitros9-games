/* SCC$board.h#mwc0.01/26Apr1991 */
/* include file for board.c
*  by Joel Matthew Rees, Dec '89,
*  Modified for MS-DOS/TURBO-C March 1991
*  eliminated BORDER, pWIDTH for speed -- JMR 13Apr1991
*  new OS-9/CoCo version Apr 1991
*  This program is assigned by the author to the public domain.
*/


#define BLACK 1
#define NONE 0
#define WHITE -BLACK

#define WIDTH 8
#define WM 7


typedef char SQUARE;
typedef SQUARE BD[WIDTH][WIDTH];
typedef SQUARE LN[WIDTH];


extern int path;
extern int group;


/* set up a hardware graphics window to run the game in
*  load the font and image buffers
*  return the path to the window, EOF on error
*/
extern int gograph();


/* close and deallocate the window, font and image buffers
*/
extern endgraph();


/* put board on screen
*/
extern putboard();

/* put a player's piece on the board at position (x, y)
*  home square is (0,0)
*/
extern putpiece( /* SQUARE player, uint x, uint y */ );

#define USER 1
#define COMPUTER 0
#define QUIT -1
#define REALLY -2
#define NOPLAY -3
#define CONTINUE -4
#define NOGOOD -5
#define WILLPLAY -6
/* prompt the player
*/
extern unprompt( /* message */ );
extern prompt( /* int message, SQUARE turn */ );

/* put the pieces out, show counts and turn
*  if turn is 0, show winner
*/
extern display( /* LN *bd, SQUARE turn */ );

#define ILLEGAL 2
#define XHAIR 3
/* put a cursor on the screen, remembering position
*  home square is (0,0)
*/
extern showcursor( /* uint x, uint y, int valid */ );

/* remove cursor from remembered position
*/
extern clrcursor();
