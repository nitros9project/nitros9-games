#ifndef BAYOU_DAMAGE_H
#define BAYOU_DAMAGE_H
typedef struct { int x,y,right,bottom; } Damage;
typedef struct { int count; Damage rect[8]; } DamageList;
void damage_add(DamageList *list,int x,int y,int right,int bottom);
void damage_merge(DamageList *list);
#endif
