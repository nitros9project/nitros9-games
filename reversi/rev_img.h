/* include file for the reversi image file
* May 1991 -- Joel Matthew Rees
*
* The y dimension is the same as the x dimension for all images in this file.
*/


/* the font, with x dimension, screen type, and buffer length
*/
extern char gcfont[];
extern int gcfontx, gcfontty, gcfontln;


/* the playing pieces, with x dimension, screen type, and buffer length
*/
extern int piecex, piecety;
extern char black[], white[];
extern int blackln, whiteln;


/* the cursors, with x dimension, screen type, and buffer length
*/
extern int cursx, cursty;
extern char illegal[], arcxhair[];
extern int illln, arcxhaln;
