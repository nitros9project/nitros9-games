/*
                       Hordes & Holes
Program by Bruce Terry
Written 02/07/1988
See Hordes.doc
*/
#include <stdio.h>
#include <sgstat.h>
#include <os9.h>
#include <time.h>
/* Key bits */
#define UP    0X08
#define DOWN  0X10
#define LEFT  0X20
#define RIGHT 0X40
/* Flags */
#define RPORT 0
#define LPORT 1
#define TRUE  1
#define FALSE 0
#define GO   1
#define STOP 0
/* Game characters */
#define MONSTER 0X58            /* "X" */
#define HOLE    0X2A            /* "*" */
#define PERSON  0X4F            /* "O" */
#define SPACE   0X20            /* " " */
/* Game constants */
#define STARTLIVES  4
#define HORDES     15
#define HOLES      15
#define VERTSIZE   23
#define BEGINLEVEL 10
/* Joystick sensitivity */
#define LOWSENSE  15
#define HIGHSENSE 48
typedef struct coord {
  int x,y;
};
struct coord person,monster[HORDES];
struct sgtbuf systime;
struct registers reg;
int old_x,old_y;
char field[VERTSIZE] [80];
char r;
int lives = STARTLIVES;
int monsters = HORDES;
int keyboard = TRUE;
int joy_port = RPORT;
int status = GO;
int level = BEGINLEVEL;
int score = 0;
int deadmonsters = 0;
int alive = TRUE;
int delay,sound_flg,cont;
unsigned getseed();
main() {
  struct sgbuf saved[2], raw;
  int tty;
  for (tty=0; tty<2; tty++) {
    getstat(0,tty,&saved[tty]);
    getstat(0,tty,&raw);
    raw.sg_echo = 0; raw.sg_pause = 0;
    setstat(0,tty,&raw);
  }
  setbuf(stdout,NULL);
  clrscr();
  curoff();
  curxy(33,5);
  printf("Hordes & Holes\n");
  curxy(33,10);
  printf("by Bruce Terry\n");
  curxy(30,20);
  printf("press a key to begin\n");
  while ((r = inkey()) == NULL);
  curon();
  clrscr();
  printf("Sound(y/n)?:\n");
  while ((r = inkey()) == NULL);
  sound_flg = 63;
  if ((r == 'N') || (r == 'n'))
    sound_flg = 0;
  clrscr();
  printf("Joystick(y/n)?:\n");
  while ((r = inkey()) == NULL);
  if ((r == 'y') || (r == 'Y')) {
    keyboard = FALSE;
    printf("\n(R)ight, (L)eft?:\n");
    while((r = inkey()) == NULL);
    if ((r == 'L') || (r == 'l'))
      joy_port = LPORT;
  }
  cont = TRUE;
  do {
    score = 0;
    lives = STARTLIVES;
    level = BEGINLEVEL;
    while (lives--) {
      clrscr();
      curoff();
      makefield();
      printfield();
      alive = TRUE;
      status = GO;
      deadmonsters = 0;
      for (delay = 4095;delay > 3000;delay -= 10)
        sound(1,sound_flg,delay);
      while (status) {
        if (keyboard)
          keyin();
        else
          joyin();
        attack();
        if ((!alive) || (deadmonsters == HORDES))
          status = STOP;
      }
      if (alive) {
        fflush(stdout);
        for (delay = 3000;delay < 4096;delay += 10)
          sound(1,sound_flg,delay);
        lives++;
        level++;
        if (level > HORDES)
          level = HORDES;
      }
      else
        deadsound();
    }
    clrscr();
    while((r = inkey()) != NULL);
    clrscr();
    curon();
    printf("Game over\n");
    printf("\nYour score was %d\n\n\n",score);
    printf("Another game(y/n)?:\n");
    while((r = inkey()) == NULL);
    if ((r == 'n') || (r == 'N'))
      cont = FALSE;
  }while(cont);
  clrscr();
  printf("Program terminated.\n");
  for (tty=0; tty<2; tty++) setstat(0,tty,&saved[tty]);
}
inkey() {
  char r;
  reg.rg_a = 1;
  reg.rg_b = SS_READY;
  _os9(I_GETSTT,&reg);
  if (reg.rg_b == 0XF6)
    return(NULL);
  read(1,&r,1);
  return(r);
}
bell() {
  putchar(0X07);
  fflush(stdout);
}
clrscr() {
  putchar(0X0C);
  fflush(stdout);
}
curoff() {
  printf("%c%c",0X05,0X20);
}
curon() {
  printf("%c%c",0X05,0X21);
}
curxy(x,y)
  char x,y;
{
  x += 0X20;
  y += 0X20;
  printf("%c%c%c",0X02,x,y);
}
revon() {
  printf("%c%c",0X1F,0X20);
}
revoff() {
  printf("%c%c",0X1F,0X21);
}
/* Integer form of the original base-10000 generator. */
unsigned getseed() {
  static unsigned seed;
  struct sgtbuf now;
  if (seed < 1 || seed > 9999) {
    getime(&now);
    seed = (now.t_minute & 255) * 100 + 1234 + (now.t_second & 255);
  }
  seed = ((long)seed * 221 + 2113) % 10000;
  return seed;
}
random(num)
int num;
{
  return ((long)getseed() * num) / 10000;
}
sound(dur,amp,frq)
  int dur,amp,frq;
{
  reg.rg_a = 1;
  reg.rg_b = 0X98;         /* SS.Tone */
  reg.rg_x = amp * 256 + dur;
  reg.rg_y = frq;
  _os9(I_SETSTT,&reg);
}
printfield() {
  int count1,count2;
  clrscr();
  revon();
  curxy(0,23);
  for (count1 = 0;count1 < 80;count1++)
    putchar(0X20);
  printf("%c%c%c",0X01,0X1F,0X30); /* insert line */
  curxy(0,23);
  for (count1 = 0;count1 < lives;count1++)
    putchar(PERSON);
  curxy(40,23);
  printf("Score:  %d",score);
  revoff();
  curxy(0,0);
  for (count1 = 0;count1 < VERTSIZE;count1++)
    for (count2 = 0;count2 < 80;count2++)
      putchar(field[count1] [count2]);
  fflush(stdout);
}
makefield() {
  int count1,count2,cell1,cell2,check;

  /* Clear field */

  clrscr();
  for (count1 = 0;count1 < VERTSIZE;count1++)
    for (count2 = 0;count2 < 80;count2++)
      field[count1] [count2] = SPACE;
  for (count1 = 0;count1 < HORDES;count1++) {
    /* Set monsters */
    check = 0;
    do {
      cell1 = random(VERTSIZE);
      cell2 = random(80);
      if (cell1 > (VERTSIZE - 1))
        cell1 = VERTSIZE - 1;
      if (cell2 > 79)
        cell2 = 79;
      check++;
      if (check > 5000) {
        fprintf(stderr,"Error - Too many monsters in field\n");
        exit(1);
      }
    }while(field[cell1] [cell2] != SPACE);
    field[cell1] [cell2] = MONSTER;
    monster[count1].x = cell2;
    monster[count1].y = cell1;
  }
    /* Set holes */
  for (count1 = 0;count1 < HOLES;count1++) {
    check = 0;
    do {
      cell1 = random(VERTSIZE);
      cell2 = random(80);
      if (cell1 > (VERTSIZE - 1))
        cell1 = VERTSIZE - 1;
      if (cell2 > 79)
        cell2 = 79;
      check++;
      if (check > 5000) {
        fprintf(stderr,"Error - Too many monsters in field\n");
        exit(1);
      }
    }while(field[cell1] [cell2] != SPACE);
    field[cell1] [cell2] = HOLE;
  }
  /* Set person */
  check = 0;
  do {
    cell1 = random(VERTSIZE);
    cell2 = random(80);
    check++;
    if (check > 5000) {
      fprintf(stderr,"Error - Too many monsters in field\n");
      exit(1);
    }
  }while(field[cell1] [cell2] != SPACE);
  field[cell1] [cell2] = PERSON;
  person.x = cell2;
  person.y = cell1;
}
joyin() {
  reg.rg_a = 1;
  reg.rg_b = SS_JOY;
  reg.rg_x = joy_port;
  _os9(I_GETSTT,&reg);
  old_x = person.x;
  old_y = person.y;
  if (reg.rg_x < LOWSENSE)
    person.x--;
  if (reg.rg_x > HIGHSENSE)
    person.x++;
  if (reg.rg_y < LOWSENSE)
    person.y++;
  if (reg.rg_y > HIGHSENSE)
    person.y--;
  if ((person.x != old_x) || (person.y != old_y))
    checkin();
}
keyin() {
  reg.rg_a = 1;
  reg.rg_b = 0X27;
  _os9(I_GETSTT,&reg);
  old_x = person.x;
  old_y = person.y;
  if ((reg.rg_a & UP) == UP)
    person.y--;
  if ((reg.rg_a & DOWN) == DOWN)
    person.y++;
  if ((reg.rg_a & LEFT) == LEFT)
    person.x--;
  if ((reg.rg_a & RIGHT) == RIGHT)
    person.x++;
  if ((person.x != old_x) || (person.y != old_y))
    checkin();
}
checkin() {
  char object;
  if ((person.x > 79) || (person.x < 0))
    person.x = old_x;
  if ((person.y > (VERTSIZE - 1)) || (person.y  < 0))
    person.y = old_y;
  object = field[person.y] [person.x];
  if ((object == HOLE) || (object == MONSTER))
    alive = FALSE;
  field[person.y] [person.x] = PERSON;
  curxy(person.x,person.y);
  putchar(PERSON);
  if ((old_x != person.x) || (old_y != person.y)) {
    field[old_y] [old_x] = SPACE;
    curxy(old_x,old_y);
    putchar(SPACE);
  }
}
deadsound() {
  int freq,count;
  fflush(stdout);
  for (count = 0;count < 10;count++)
    for (freq = 4095;freq > 3800;freq -= 10)
      sound(0,sound_flg,freq);
}

attack() {
  int count,x,y,difx,dify;
  static int block = 0;
  char check;
  for (count = 0;count < level;count++) {
    x = monster[block].x;
    y = monster[block].y;
    if (x != -1) {
      difx = person.x - x;
      dify = person.y - y;
      difx = abs(difx);
      dify = abs(dify);
      if (dify > difx)
        if (y > person.y)
          monster[block].y--;
        else
          monster[block].y++;
      else
        if (x > person.x)
          monster[block].x--;
        else
          monster[block].x++;
      if (monster[block].y > (VERTSIZE - 1))
        monster[block].y = (VERTSIZE - 1);
      if (monster[block].y < 0)
        monster[block].y = 0;
      if (monster[block].x > 79)
        monster[block].x = 79;
      if (monster[block].x < 0)
        monster[block].x = 0;
      check = field[monster[block].y] [monster[block].x];
      if (check != MONSTER) {
        field[y] [x] = SPACE;
        curxy(x,y);
        putchar(SPACE);
        if (field[monster[block].y] [monster[block].x] == PERSON)
          alive = FALSE;
        if (field[monster[block].y] [monster[block].x] == HOLE) {
          bell();
          curxy(monster[block].x,monster[block].y);
          putchar(HOLE);
          score += 10;
          curxy(48,23);
          revon();
          printf("%d",score);
          revoff();
          monster[block].x = -1;
          deadmonsters++;
        }
        else {
          field[monster[block].y] [monster[block].x] = MONSTER;
          curxy(monster[block].x,monster[block].y);
          putchar(MONSTER);
        }
      }
      else {
        monster[block].x = x;
        monster[block].y = y;
      }
    }
    block++;
    if (block == HORDES)
      block = 0;
  }
}
