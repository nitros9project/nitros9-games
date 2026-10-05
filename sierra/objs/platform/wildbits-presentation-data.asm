* Private presentation controls; include in the private direct page.
dbase               rmb       2
filepath            rmb       1
fileopen            rmb       1
bitmapowned         rmb       1
firstblock          rmb       2
mapbase             rmb       2
mapped              rmb       1
blockindex          rmb       1
frameoffset         rmb       2
sourceptr           rmb       2
remaining           rmb       2
chunk               rmb       2
rows                rmb       1
                    ifne      GAME_PRESENTATION
presentbatchrows    rmb       1
gamepresentdirty    rmb       3
presentband         rmb       1
presentationconfigured rmb   1
                    endc
aborted             rmb       1
errorcode           rmb       1
paused              rmb       1
registered          rmb       1
nearend             equ       .
