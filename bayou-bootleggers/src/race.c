#include "race.h"
void race_init(Race *r) {
    int i;
    crowd_init(&r->crowd,1);
    for(i=0;i<4;i++) r->pos[i]=r->finish[i]=0;
    r->tick=r->over=0; r->countdown=45; r->stamina=96; r->place=1;
}
void race_step(Race *r,int keys) {
    int i,speed;
    if(r->over) return;
    crowd_step(&r->crowd);
    if(r->countdown) { r->countdown--; return; }
    r->tick++;
    speed=3;
    if(keys & RIGHT) {
        speed=6;
        if((keys & JUMP) && r->stamina>=2) { speed=9; r->stamina-=2; }
        else if(!(keys & JUMP) && r->stamina<96) r->stamina++;
    } else { r->stamina+=3; if(r->stamina>96) r->stamina=96; }
    r->pos[0]+=speed;
    for(i=1;i<4;i++) r->pos[i]+=5+(i==1)+(((r->tick+i*9)&15)<5);
    for(i=0;i<4;i++) if(r->pos[i]>=RACE_LENGTH) {
        r->pos[i]=RACE_LENGTH;
        if(!r->finish[i]) r->finish[i]=r->tick;
    }
    r->place=1;
    for(i=1;i<4;i++) if(r->pos[i]>r->pos[0] ||
        (r->finish[0] && r->finish[i] && r->finish[i]<=r->finish[0])) r->place++;
    if(r->finish[0]) r->over=1;
}
