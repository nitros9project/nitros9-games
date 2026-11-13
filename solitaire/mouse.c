/* Current c3 ABI wrappers for the CoCo Level 2 mouse/window services. */
#include <os9.h>
_ss_mous(path,update,timeout,follow)
int path,update,timeout,follow;
{
    struct registers r;
    r.rg_a=path; r.rg_b=0x89;
    r.rg_x=(update<<8)|timeout; r.rg_y=follow;
    return _os9(I_SETSTT,&r);
}
_ss_msig(path,sig)
int path,sig;
{
    struct registers r;
    r.rg_a=path; r.rg_b=0x8a; r.rg_x=sig;
    return _os9(I_SETSTT,&r);
}
_gs_mouse(path,packet)
int path; char *packet;
{
    struct registers r;
    r.rg_a=path; r.rg_b=0x89; r.rg_x=packet; r.rg_y=0;
    return _os9(I_GETSTT,&r);
}
_ss_wset(path,type,desc)
int path,type; char *desc;
{
    struct registers r;
    r.rg_a=path; r.rg_b=0x86; r.rg_x=desc; r.rg_y=type;
    return _os9(I_SETSTT,&r);
}
