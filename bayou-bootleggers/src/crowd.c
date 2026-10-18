#include "crowd.h"
const char *crowd_names[CROWD_MEN]={
    "MAN AT THE RAIL","CECIL BROWN","MAN WITH A CANE","OLD MAN AT THE RAIL",
    "LEROY PITRE","MAN IN A STRAW HAT","MAN BY THE FINISH"
};
/* Original track-side dialogue: Cajun English and Louisiana French.
   Accents are omitted because the CoCo's standard font is ASCII. */
const char *crowd_lines[CROWD_LINES]={
    "ALLEZ, TEE-BOY!","LACHE PAS LA PATATE!","MAIS, LOOK AT HIM GO!",
    "THAT'S MY HORSE, ME!","COURS, TEE-BOY, COURS!","LET HIM RUN, CHER!",
    "IL EST APRES COURIR!","AU RAS AU RAS!","ASTEUR, TEE-BOY!",
    "MAIS OUI, THAT'S IT!","TIENS BON, MON CHER!","THAT'S A RUN, CHER!"
};
/* Sixteen-bit LFSR: cheap on a 6809, seeded from the clock at the gate. */
static unsigned int next(Crowd *c) {
    unsigned int low=c->seed&1;
    c->seed=(c->seed>>1) ^ (low?0xb400:0);
    return c->seed;
}
void crowd_init(Crowd *c,unsigned int seed) {
    c->seed=seed?seed:0xace1;
    c->speaker=1; c->line=next(c)%CROWD_LINES;
    c->timer=30+(next(c)&31); c->version=0;
}
void crowd_step(Crowd *c) {
    int old=c->line;
    if(--c->timer>0) return;
    /* Introduce Cecil and Leroy before picking from the whole rail. */
    c->speaker=c->version==0?4:next(c)%CROWD_MEN;
    c->line=next(c)%CROWD_LINES;
    if(c->line==old) c->line=(old+1)%CROWD_LINES;
    c->timer=30+(next(c)&31); c->version++;
}
