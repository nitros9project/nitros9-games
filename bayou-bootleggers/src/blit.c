/* Transparent packed-pixel row compositor. The native hot loop uses only
   6809 instructions; the portable version is exercised by host tests. */
#ifdef _CMOC_VERSION_
asm void blit_row(unsigned char *dst,const unsigned char *src,const unsigned char *map,int count,int flip) {
    asm {
        pshs u,y          ; preserve frame and static-data registers
        ldy 6,s           ; destination byte pointer
        ldx 8,s           ; source pointer (end of range when mirrored)
        ldu 10,s          ; translation table for 256 packed pixel pairs
        ldb 13,s          ; clipped byte count, at most twenty-four
        pshs b            ; remaining count is one local stack byte
blit_next
        tst 16,s          ; test the mirror flag
        beq blit_forward
        ldb ,-x           ; mirrored rows traverse source backwards
        tfr b,a           ; retain source while swapping its nibbles
        lsrb
        lsrb
        lsrb
        lsrb
        lsla
        lsla
        lsla
        lsla
        pshs b
        ora ,s+
        tfr a,b
        bra blit_pixels
blit_forward
        ldb ,x+           ; read the next packed source pixel pair
blit_pixels
        beq blit_advance  ; a transparent pair leaves the backdrop intact
        clra
        lda d,u           ; translate both pixels with one lookup
        pshs a
        bitb #$f0
        beq blit_merge_low
        bitb #$0f
        beq blit_merge_high
        puls a            ; two opaque pixels need no background read
        sta ,y
        bra blit_advance
blit_merge_low
        ldb ,y
        andb #$f0         ; preserve the high background pixel
        orb ,s+
        stb ,y
        bra blit_advance
blit_merge_high
        ldb ,y
        andb #$0f         ; preserve the low background pixel
        orb ,s+
        stb ,y
blit_advance
        leay 1,y          ; advance one output byte
        dec ,s
        bne blit_next
        leas 1,s          ; discard the remaining-count byte
        puls u,y,pc       ; restore preserved registers and return
    }
}
#else
void blit_row(unsigned char *dst,const unsigned char *src,const unsigned char *map,int count,int flip) {
    unsigned char c;
    while(count--) {
        c=flip?*--src:*src++;
        if(flip) c=(c<<4)|(c>>4);
        if(c>>4) *dst=(*dst&15)|(map[c]&240);
        if(c&15) *dst=(*dst&240)|(map[c]&15);
        dst++;
    }
}
#endif
