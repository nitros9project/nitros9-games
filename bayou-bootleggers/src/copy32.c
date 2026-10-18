/* Tight race-only 32x32 packed background patches; skip follows 16 bytes. */
#ifdef _CMOC_VERSION_
asm void copy32(unsigned char *dst,const unsigned char *src,int dstskip,int srcskip) {
    asm {
        pshs u,y
        ldu 6,s
        ldx 8,s
        ldy #32
copy32_row
        ldd 0,x
        std 0,u
        ldd 2,x
        std 2,u
        ldd 4,x
        std 4,u
        ldd 6,x
        std 6,u
        ldd 8,x
        std 8,u
        ldd 10,x
        std 10,u
        ldd 12,x
        std 12,u
        ldd 14,x
        std 14,u
        leax 16,x
        leau 16,u
        ldd 10,s
        leau d,u
        ldd 12,s
        leax d,x
        leay -1,y
        bne copy32_row
        puls u,y,pc
    }
}
#else
#include <string.h>
void copy32(unsigned char *dst,const unsigned char *src,int dstskip,int srcskip) {
    int row;
    for(row=0;row<32;row++) { memcpy(dst,src,16); dst+=16+dstskip; src+=16+srcskip; }
}
#endif
