/* Draw a complete pre-mirrored sprite into a 160-byte-stride framebuffer.
   The stream omits every fully transparent pixel pair. */
#ifdef _CMOC_VERSION_
asm void draw_sprite(unsigned char *dst,const unsigned char *src,const unsigned char *map) {
    asm {
        pshs u,y
        ldu 6,s           ; row origin in the mapped video window
        ldx 8,s           ; run stream
        ldy 10,s          ; palette table for packed pixel pairs
        leas -4,s
        lda #44
        sta ,s            ; remaining rows
sprite_row
        lda ,x+
        sta 1,s           ; remaining runs on this row
        beq sprite_next_row
sprite_run
        ldb ,x+           ; run offset in bytes
        pshs u            ; preserve row origin
        leau b,u
        lda ,x+           ; high bits identify the entire run's mask
        tfr a,b
        andb #63
        stb 5,s           ; remaining bytes in run
        bita #128
        bne sprite_low
        bita #64
        bne sprite_high
sprite_opaque
        clra
        ldb ,x+
        lda d,y           ; translate both packed pixels at once
        sta ,u+
        dec 5,s
        bne sprite_opaque
        bra sprite_run_done
sprite_low
        clra
        ldb ,x+
        lda d,y
        ldb ,u
        andb #$f0         ; retain transparent high pixel
        pshs b
        ora ,s+
        sta ,u+
        dec 5,s
        bne sprite_low
        bra sprite_run_done
sprite_high
        clra
        ldb ,x+
        lda d,y
        ldb ,u
        andb #$0f         ; retain transparent low pixel
        pshs b
        ora ,s+
        sta ,u+
        dec 5,s
        bne sprite_high
sprite_run_done
        puls u            ; restore row origin for the next run
        dec 1,s
        bne sprite_run
sprite_next_row
        leau 160,u
        dec ,s
        bne sprite_row
        leas 4,s
        puls u,y,pc
    }
}
#endif
