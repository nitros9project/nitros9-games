/* Race streams are palette-translated once at startup. Keep the run
   length in B and combine masked bytes directly with framebuffer pixels. */
#ifdef _CMOC_VERSION_
asm void draw_sprite(unsigned char *dst,const unsigned char *src,const unsigned char *map) {
    asm {
        pshs u,y
        ldu 6,s
        ldx 8,s
        leas -2,s
        ; Compact art has fourteen empty rows before its 30-line image.
        leau 2240,u
        leax 14,x
        lda #30
        sta ,s
horse_row
        lda ,x+
        sta 1,s
        beq horse_next_row
horse_run
        ldb ,x+
        pshs u
        leau b,u
        lda ,x+
        tfr a,b
        andb #63
        bita #128
        bne horse_low
        bita #64
        bne horse_high
horse_opaque
        lda ,x+
        sta ,u+
        decb
        bne horse_opaque
        bra horse_run_done
horse_low
        lda ,u
        anda #$f0
        ora ,x+
        sta ,u+
        decb
        bne horse_low
        bra horse_run_done
horse_high
        lda ,u
        anda #$0f
        ora ,x+
        sta ,u+
        decb
        bne horse_high
horse_run_done
        puls u
        dec 1,s
        bne horse_run
horse_next_row
        leau 160,u
        dec ,s
        bne horse_row
        leas 2,s
        puls u,y,pc
    }
}
#endif
