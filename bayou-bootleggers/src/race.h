#ifndef BUSH_RACE_H
#define BUSH_RACE_H
#include "game.h"
#include "crowd.h"
#define RACE_LENGTH 1200
#define RACE_HORSES 4
typedef struct { Crowd crowd; int pos[4],finish[4],tick,countdown,stamina,place,over; } Race;
void race_init(Race *r);
void race_step(Race *r,int keys);
#endif
