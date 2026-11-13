#ifndef BAYOU_GAME_H
#define BAYOU_GAME_H
#define UP 8
#define DOWN 16
#define LEFT 32
#define RIGHT 64
#define JUMP 128
#define ATTACK 2
#define MAX_FOES 3
#define GATOR_SLOT 2
typedef struct { int x,y,hp,face,attack,cool,stun; } Actor;
typedef struct {
    Actor p, foe[MAX_FOES];
    int room,lives,score,jump,invuln,previous,won,over,tick;
} Game;
void game_init(Game *g);
void game_step(Game *g,int keys);
int game_height(Game *g);
int game_remaining(Game *g);
#endif
