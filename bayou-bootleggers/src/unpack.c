/* Decode only the requested byte interval of one PackBits background row. */
#ifdef _CMOC_VERSION_
asm void unpack_row(const unsigned char *src,unsigned char *dst,int skip,int count) {
    asm {
        pshs u,y
        ldx 6,s           ; compressed source
        ldu 8,s           ; destination
        ldy 10,s          ; bytes to skip before copying
        ldd 12,s          ; bytes to output
        pshs d            ; remaining output count
        leas -3,s         ; packet type, length and consumed prefix
unpack_packet
        lda ,x+
        sta ,s            ; high bit distinguishes repeat packets
        anda #$7f
        inca
        sta 1,s           ; original packet length (1..128)
        clr 2,s
        cmpy #0
        beq unpack_copy
        clra
        ldb 1,s
        pshs d
        cmpy ,s           ; does skip consume this whole packet?
        blo unpack_prefix
        tfr y,d
        subd ,s++
        tfr d,y
        tst ,s
        bmi unpack_skip_repeat
        ldb 1,s
        abx               ; skip all literal bytes
        bra unpack_packet
unpack_skip_repeat
        leax 1,x          ; a repeat packet has only one data byte
        bra unpack_packet
unpack_prefix
        leas 2,s
        tfr y,d
        stb 2,s           ; prefix of this packet is discarded
        ldy #0
unpack_copy
        lda 1,s
        suba 2,s          ; remaining bytes in this packet
        ldb 4,s           ; low byte of output count (at most 160)
        cmpa 4,s
        bls unpack_take
        tfr b,a           ; clip this packet to the output interval
unpack_take
        sta 1,s           ; amount to emit
        tst ,s
        bmi unpack_repeat
        ldb 2,s
        abx               ; advance past a discarded literal prefix
        ldb 1,s
unpack_literal_loop
        lda ,x+
        sta ,u+
        decb
        bne unpack_literal_loop
        bra unpack_done_packet
unpack_repeat
        lda ,x+
        ldb 1,s
unpack_repeat_loop
        sta ,u+
        decb
        bne unpack_repeat_loop
unpack_done_packet
        ldb 4,s
        subb 1,s
        stb 4,s
        bne unpack_packet
        leas 5,s
        puls u,y,pc
    }
}
#else
#include <string.h>
void unpack_row(const unsigned char *s,unsigned char *out,int skip,int count) {
    int at=0,n,start,take; unsigned char code;
    while(count>0) {
        code=*s++; n=(code&127)+1;
        if(at+n>skip) {
            start=skip>at?skip-at:0; take=n-start;
            if(take>count) take=count;
            if(code&128) memset(out,*s,take); else memcpy(out,s+start,take);
            out+=take; count-=take; skip+=take;
        }
        at+=n; s+=(code&128)?1:n;
    }
}
#endif
