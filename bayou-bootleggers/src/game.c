#include "game.h"
static int distance(int a,int b) { return a>b?a-b:b-a; }
static void room_init(Game *g) {
    int i;
    g->p.x=44; g->p.y=152; g->p.face=1;
    g->p.attack=g->p.cool=g->p.stun=0;
    g->jump=0; g->invuln=18;
    for(i=0;i<MAX_FOES;i++) {
        Actor *e=&g->foe[i];
        e->x=194+i*32; e->y=132+i*18; e->face=-1;
        e->hp=g->room==2?(i==0?12:0):3+g->room;
        e->attack=e->cool=e->stun=0;
    }
    /* The third enemy slot is wildlife, so the renderer still draws at
       most four actors and needs no additional screen-cache RAM. */
    g->foe[GATOR_SLOT].x=224;
    g->foe[GATOR_SLOT].y=178;
    g->foe[GATOR_SLOT].hp=3+g->room;
    g->foe[GATOR_SLOT].cool=24;
}
void game_init(Game *g) {
    g->room=g->score=g->tick=g->previous=g->won=g->over=0;
    g->lives=3; g->p.hp=8;
    room_init(g);
}
int game_height(Game *g) {
    int t=g->jump;
    return t>8?(16-t)*3:t*3;
}
int game_remaining(Game *g) {
    int i,n=0;
    for(i=0;i<MAX_FOES;i++) if(g->foe[i].hp>0) n++;
    return n;
}
void game_step(Game *g,int keys) {
    int i,dx,dy,edge;
    Actor *p=&g->p;
    if(g->over || g->won) return;
    g->tick=(g->tick+1)&255;
    edge=keys & ~g->previous; g->previous=keys;
    if(g->invuln) g->invuln--;
    if(p->cool) p->cool--;
    if(p->attack) p->attack--;
    if(g->jump) g->jump--;
    if((edge & JUMP) && !g->jump) g->jump=16;
    /* Footwork remains available during a swing, at a reduced speed. */
    dx=p->attack?2:3;
    if(keys & LEFT) { p->x-=dx; p->face=-1; }
    if(keys & RIGHT) { p->x+=dx; p->face=1; }
    if(keys & UP) p->y-=2;
    if(keys & DOWN) p->y+=2;
    if(p->x<34) p->x=34;
    if(p->x>284) p->x=284;
    if(p->y<124) p->y=124;
    if(p->y>178) p->y=178;
    if((keys & ATTACK) && !p->cool) {
        p->attack=5; p->cool=9;
        for(i=0;i<MAX_FOES;i++) {
            Actor *e=&g->foe[i];
            dx=e->x-p->x; dy=distance(e->y,p->y);
            if(e->hp>0 && dy<14 && distance(e->x,p->x)<38 && dx*p->face>=0) {
                e->hp-=g->jump?2:1; e->stun=10; e->attack=0;
                if(i==GATOR_SLOT) { e->cool=40; }
                e->x+=p->face*12;
                if(e->x<34) e->x=34;
                if(e->x>284) e->x=284;
                if(e->hp<=0) g->score+=i==GATOR_SLOT?150:(g->room==2?1000:100);
            }
        }
    }
    for(i=0;i<MAX_FOES;i++) {
        Actor *e=&g->foe[i];
        if(e->hp<=0) continue;
        if(e->attack) e->attack--;
        if(e->cool) e->cool--;
        if(e->stun) { e->stun--; continue; }
        if(i==GATOR_SLOT) {
            /* Open jaws warn for ten ticks, then the locked direction
               carries an eight-tick lunge up onto the boards. */
            if(e->attack) {
                if(e->attack<=8) {
                    e->x+=e->face*4;
                    e->y-=2;
                    if(e->x<34) e->x=34;
                    if(e->x>284) e->x=284;
                    if(distance(p->x,e->x)<29 && distance(p->y,e->y)<14
                        && game_height(g)<12 && !g->invuln) {
                        p->hp--; g->invuln=16;
                    }
                }
                if(e->attack==1) e->cool=45;
            } else {
                if(e->y<178) e->y++;
                e->face=p->x<e->x?-1:1;
                if(!e->cool && distance(p->x,e->x)<70 && distance(p->y,e->y)<36)
                    e->attack=18;
            }
            continue;
        }
        dx=p->x-e->x; dy=p->y-e->y; e->face=dx<0?-1:1;
        /* A visible wind-up gives the player time to step aside or jump. */
        if(e->attack) {
            if(e->attack==1 && distance(p->x,e->x)<29 && distance(p->y,e->y)<12
                && game_height(g)<12 && !g->invuln) {
                p->hp--; g->invuln=16;
            }
        } else if(distance(p->x,e->x)<26 && distance(p->y,e->y)<10) {
            if(!e->cool) { e->attack=7; e->cool=g->room==2?12:22; }
        } else {
            if(dx>22) e->x++;
            if(dx< -22) e->x--;
            /* Approach on opposite sides of the player's lane. Both
               offsets remain within paddle and enemy-strike reach. */
            dy+=i?8:-8;
            if(dy>0) e->y++;
            if(dy<0) e->y--;
            if(e->y<124) e->y=124;
            if(e->y>178) e->y=178;
        }
    }
    if(p->hp<=0) {
        if(--g->lives<=0) { g->over=1; return; }
        p->hp=8; p->x=44; g->invuln=36; g->jump=0;
    }
    if(!game_remaining(g) && p->x>=280) {
        if(g->room==2) g->won=1;
        else { g->room++; if(p->hp<6) p->hp=6; room_init(g); }
    }
}
