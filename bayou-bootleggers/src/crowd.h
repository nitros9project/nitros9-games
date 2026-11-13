#ifndef LINZAY_CROWD_H
#define LINZAY_CROWD_H
#define CROWD_MEN 7
#define CROWD_LINES 12
typedef struct { unsigned int seed; int speaker,line,timer,version; } Crowd;
extern const char *crowd_names[CROWD_MEN];
extern const char *crowd_lines[CROWD_LINES];
void crowd_init(Crowd *c,unsigned int seed);
void crowd_step(Crowd *c);
#endif
