#ifndef BAYOU_RENDER_H
#define BAYOU_RENDER_H
#include "game.h"
#define PATCH_BYTES 2560
typedef struct { int x,y,depth,pose,face,kind,hp,visible; } View;
void render_patch(const unsigned char *bg,unsigned char *out,int x,int y,int width,int height,const View *views);
void render_to(const unsigned char *bg,unsigned char *out,int stride,int x,int y,int width,int height,const View *views);
void render_actors(unsigned char *out,int stride,int x,int y,int width,int height,const View *views);
void copy48(unsigned char *dst,const unsigned char *src,int dstskip,int srcskip);
void render_race_init(void);
void copy32(unsigned char *dst,const unsigned char *src,int dstskip,int srcskip);
void render_hud(const unsigned char *bg,unsigned char *out,const Game *game);
#endif
