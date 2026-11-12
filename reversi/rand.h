/* SCC$rand.h#mwc0.01/26Apr1991 */
/* include file for rand.c by Joel Matthew Rees -- Jan 1990
*  Modified for MS-DOS/TURBO-C March 1991
*  new OS-9/CoCo version Apr 1991
*/

#ifndef TRUE
#include <common.h>
#endif

#ifdef RAND
#define EXTERN
#else
#define EXTERN extern
#endif


EXTERN trandize();
EXTERN uint trand( /* uint limit */ );

#undef EXTERN
