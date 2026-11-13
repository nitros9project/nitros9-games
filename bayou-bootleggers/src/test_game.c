#include <assert.h>
#include <stdio.h>
#include "game.h"
static void empty(Game *g) { int i; for(i=0;i<MAX_FOES;i++) g->foe[i].hp=0; }
int main(void) {
    Game g; int i,hp;
    game_init(&g);
    assert(g.lives==3 && game_remaining(&g)==3);
    empty(&g);
    for(i=0;i<200;i++) game_step(&g,LEFT|UP);
    assert(g.p.x==34 && g.p.y==124);
    game_init(&g); empty(&g);
    g.foe[0].hp=3; g.foe[0].x=g.p.x+20; g.foe[0].y=g.p.y;
    game_step(&g,ATTACK); assert(g.foe[0].hp==2);
    for(i=0;i<8;i++) game_step(&g,ATTACK);
    assert(g.foe[0].hp==2); /* Cooldown prevents an immediate repeat. */
    game_step(&g,ATTACK); assert(g.foe[0].hp==1);
    game_init(&g); empty(&g); g.p.attack=4;
    game_step(&g,RIGHT|DOWN); assert(g.p.x==46 && g.p.y==154);
    game_init(&g); empty(&g);
    g.foe[0].hp=3; g.foe[0].x=64; g.foe[0].y=152; g.foe[0].attack=7;
    game_step(&g,ATTACK); assert(g.foe[0].attack==0 && g.foe[0].stun>0);
    game_init(&g); empty(&g);
    for(i=0;i<2;i++) { g.foe[i].hp=3; g.foe[i].x=180; g.foe[i].y=152; }
    for(i=0;i<12;i++) game_step(&g,0);
    assert(g.foe[1].y-g.foe[0].y>=12);
    game_init(&g); empty(&g);
    g.foe[0].hp=3; g.foe[0].x=g.p.x-20; g.foe[0].y=g.p.y;
    game_step(&g,ATTACK); assert(g.foe[0].hp==3); /* must face target */
    game_init(&g); empty(&g);
    g.foe[0].hp=3; g.foe[0].x=g.p.x+20; g.foe[0].y=g.p.y+25;
    game_step(&g,ATTACK); assert(g.foe[0].hp==3); /* must share lane */
    game_init(&g); empty(&g);
    g.foe[0].hp=2; g.foe[0].x=g.p.x+20; g.foe[0].y=g.p.y;
    game_step(&g,JUMP|ATTACK);
    assert(g.foe[0].hp==0 && g.score==100);
    game_init(&g); empty(&g);
    g.foe[0].hp=3; g.foe[0].x=g.p.x+20; g.foe[0].y=g.p.y;
    g.foe[0].attack=2; g.invuln=0; g.jump=8; hp=g.p.hp;
    game_step(&g,0); assert(g.p.hp==hp); /* airborne dodge */
    g.jump=0; g.foe[0].attack=2;
    game_step(&g,0); assert(g.p.hp==hp-1);
    g.foe[0].attack=2;
    game_step(&g,0); assert(g.p.hp==hp-1); /* grace period */
    game_init(&g); empty(&g); g.p.hp=0;
    game_step(&g,0); assert(g.lives==2 && g.p.hp==8);
    empty(&g); g.p.x=284; game_step(&g,0); assert(g.room==1);
    empty(&g); g.p.x=284; game_step(&g,0);
    assert(g.room==2 && g.foe[0].hp==12 && g.foe[GATOR_SLOT].hp==5 && game_remaining(&g)==2);
    empty(&g); g.p.x=284; game_step(&g,0); assert(g.won);
    game_init(&g); g.lives=1; g.p.hp=0; game_step(&g,0); assert(g.over);
    /* Wildlife warns, locks its direction, lunges, and respects dodges. */
    game_init(&g); empty(&g);
    g.foe[GATOR_SLOT].hp=3; g.foe[GATOR_SLOT].cool=0;
    g.p.x=190; g.p.y=168; g.invuln=0;
    game_step(&g,0); assert(g.foe[GATOR_SLOT].attack==18);
    hp=g.p.hp;
    for(i=0;i<9;i++) game_step(&g,0);
    assert(g.foe[GATOR_SLOT].x==224 && g.p.hp==hp);
    game_step(&g,0); assert(g.foe[GATOR_SLOT].x==220);
    for(i=0;i<7;i++) game_step(&g,0);
    assert(g.p.hp==hp-1 && g.foe[GATOR_SLOT].cool==45);
    game_step(&g,0); assert(g.foe[GATOR_SLOT].y==163);
    game_init(&g); empty(&g);
    g.foe[GATOR_SLOT].hp=1; g.foe[GATOR_SLOT].x=64;
    g.foe[GATOR_SLOT].y=g.p.y; g.foe[GATOR_SLOT].attack=12;
    game_step(&g,ATTACK);
    assert(g.foe[GATOR_SLOT].hp==0 && g.foe[GATOR_SLOT].attack==0 && g.score==150);
    game_init(&g); empty(&g);
    g.foe[GATOR_SLOT].hp=3; g.foe[GATOR_SLOT].x=74;
    g.foe[GATOR_SLOT].y=170; g.foe[GATOR_SLOT].face=-1;
    g.foe[GATOR_SLOT].attack=8; g.p.y=168; g.jump=8; g.invuln=0;
    hp=g.p.hp; game_step(&g,0); assert(g.p.hp==hp);
    puts("PASS: alligator warning, lunge, retreat, paddle interruption, score and airborne dodge");
    puts("PASS: movement, facing, lanes, repeat attack, swing footwork, interrupted wind-up, crew spacing, jump strike, dodge, damage grace, lives, rooms, boss, win/loss");
    return 0;
}
