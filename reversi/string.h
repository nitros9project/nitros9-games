/* string.h -- function prototypes and stuff for string handling
*  Joel Rees, June 1990
*/

/* char *strcat(char *dst, char *src); */
char *strcat();

/* char *strncat(char *dst, char *src, int n); */
char *strncat();

/* int strcmp(char *dst, char *src); */
int strcmp();

/* int strncmp(char *dst, char *src, int n); */
int strncmp();

/* char *strcpy(char *dst, char *src); */
char *strcpy();

/* char *strncpy(char *dst, char *src, int n); */
char *strncpy();

/* char *strhcpy(char *dst, char *src); b7 set in terminator (OS-9) */
char *strhcpy();

/* char *strlen(char *str); */
int strlen();

/* char *index(char *str, int ch); */
char *index();
#define strchr index /* portability */

/* char *rindex(char *str, int ch); */
char *rindex();
#define strrchr rindex /* portability */
