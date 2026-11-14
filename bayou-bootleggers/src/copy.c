/* Copy a 48-pixel by 48-line packed patch between RAM and the framebuffer.
   Stride arguments are the bytes to skip AFTER each 24-byte scan line. */
#ifdef _CMOC_VERSION_
asm void copy48(unsigned char *dst,const unsigned char *src,int dstskip,int srcskip) {
    asm {
        pshs u,y
        ldu 6,s
        ldx 8,s
        ldy #48
copy48_row
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
        ldd 16,x
        std 16,u
        ldd 18,x
        std 18,u
        ldd 20,x
        std 20,u
        ldd 22,x
        std 22,u
        leax 24,x
        leau 24,u
        ldd 10,s
        leau d,u
        ldd 12,s
        leax d,x
        leay -1,y
        bne copy48_row
        puls u,y,pc
    }
}
#else
#include <string.h>
void copy48(unsigned char *dst,const unsigned char *src,int dstskip,int srcskip) {
    int row;
    for(row=0;row<48;row++) { memcpy(dst,src,24); dst+=24+dstskip; src+=24+srcskip; }
}
#endif
