* Private interpreter controls; variables/flags/argument staging are separate
* from this direct-page area. Script positions are offsets, never mapped pointers.
vmip                rmb       2
vmend               rmb       2
vmsteps             rmb       2
vmopcode            rmb       1
vmargcount          rmb       1
vmargindex          rmb       1
vmtemp              rmb       1
vmleft              rmb       1
vmright             rmb       1
vmcondition         rmb       1
vmoractive          rmb       1
vmorvalue           rmb       1
vmnegate            rmb       1
vmerror             rmb       1
vmcurrent           rmb       1
vmdepth             rmb       1
vmrequested         rmb       1
vmcacheindex        rmb       1
vmslot              rmb       2
vmcleanup           rmb       1
