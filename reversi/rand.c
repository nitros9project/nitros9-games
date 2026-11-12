/* Portable form of Joel Rees's time-seeded rotate generator. */
#include <time.h>
#include "common.h"
#define RAND
#include "rand.h"
static uint state;
trandize()
{
    struct sgtbuf t;
    uint seconds, days;
    getime(&t);
    seconds=((t.t_hour & 255)*60 + (t.t_minute & 255))*60 + (t.t_second & 255);
    days=(t.t_year & 255)*372 + (t.t_month & 255)*31 + (t.t_day & 255);
    state ^= seconds ^ days ^ ((t.t_second & 255)<<5);
}
uint trand(limit)
uint limit;
{
    uint val,bit;
    if (limit==0) return 0;
    val=state % limit;
    bit=(limit | state) & 15;
    state += (limit>>8) | (limit<<8);
    if (bit) state=(state<<bit) | (state>>(16-bit));
    return val;
}
