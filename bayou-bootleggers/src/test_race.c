#include <assert.h>
#include <stdio.h>
#include "race.h"
int main(void) {
    Race r; Crowd a,b; int i,before,old,last,version,saw_change=0;
    crowd_init(&a,1234); crowd_init(&b,1234);
    assert(a.speaker==1);
    old=a.line;
    for(i=0;i<65;i++) crowd_step(&a);
    assert(a.speaker==4 && a.line!=old);
    crowd_init(&a,1234);
    for(i=0;i<1000;i++) {
        last=a.line; version=a.version;
        crowd_step(&a); crowd_step(&b);
        if(a.version!=version) assert(a.line!=last);
        assert(a.speaker==b.speaker && a.line==b.line);
        assert(a.speaker>=0 && a.speaker<CROWD_MEN);
        assert(a.line>=0 && a.line<CROWD_LINES);
        assert(a.timer>0 && a.timer<=61);
        if(a.line!=old) saw_change=1;
    }
    assert(saw_change);
    race_init(&r);
    for(i=0;i<45;i++) race_step(&r,RIGHT|JUMP);
    assert(r.pos[0]==0 && r.countdown==0 && r.stamina==96);
    race_step(&r,RIGHT|JUMP); assert(r.pos[0]==9 && r.stamina==94);
    for(i=0;i<60;i++) race_step(&r,RIGHT|JUMP);
    assert(r.stamina>=0 && r.stamina<=96);
    before=r.stamina; race_step(&r,0); assert(r.stamina>before);
    race_init(&r);
    for(i=0;i<1000 && !r.over;i++) race_step(&r,RIGHT | (r.stamina>2?JUMP:0));
    assert(r.over && r.place==1 && r.pos[0]==RACE_LENGTH);
    before=r.tick; race_step(&r,RIGHT); assert(r.tick==before);
    race_init(&r);
    for(i=0;i<1000 && !r.over;i++) race_step(&r,0);
    assert(r.over && r.place==4);
    puts("PASS: seeded crowd cheers, named introductions, timing and valid selections");
    puts("PASS: race countdown, sprint drain, recovery, stamina bounds, victory, defeat and finish lock");
    return 0;
}
