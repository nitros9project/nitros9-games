#include "damage.h"
static int smaller(int a,int b) { return a<b?a:b; }
static int larger(int a,int b) { return a>b?a:b; }
void damage_add(DamageList *list,int x,int y,int right,int bottom) {
    Damage *d;
    x=larger(0,x)&~1; right=(smaller(320,right)+1)&~1;
    y=larger(24,y); bottom=smaller(188,bottom);
    if(x>=right || y>=bottom) return;
    if(list->count>=8) {
        d=&list->rect[7];
        d->x=smaller(d->x,x); d->right=larger(d->right,right);
        d->y=smaller(d->y,y); d->bottom=larger(d->bottom,bottom);
        return;
    }
    d=&list->rect[list->count++];
    d->x=x; d->y=y; d->right=right; d->bottom=bottom;
}
void damage_merge(DamageList *list) {
    int i,j,again=1;
    unsigned int sum,area;
    Damage *a,*b,u;
    while(again) {
        again=0;
        for(i=0;i<list->count && !again;i++) for(j=i+1;j<list->count;j++) {
            a=&list->rect[i]; b=&list->rect[j];
            if(a->x>b->right || b->x>a->right || a->y>b->bottom || b->y>a->bottom) continue;
            u.x=smaller(a->x,b->x); u.y=smaller(a->y,b->y);
            u.right=larger(a->right,b->right); u.bottom=larger(a->bottom,b->bottom);
            sum=((a->right-a->x)>>1)*(a->bottom-a->y)+((b->right-b->x)>>1)*(b->bottom-b->y);
            area=((u.right-u.x)>>1)*(u.bottom-u.y);
            /* Avoid rebuilding the same overlapping actors repeatedly,
               but do not turn sparse damage into a full-screen repaint. */
            if(sum>=17494 || area<=sum+(sum>>1)) {
                *a=u; list->rect[j]=list->rect[--list->count]; again=1; break;
            }
        }
    }
}
