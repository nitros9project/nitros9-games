* CoCo platform boundary: presentation.
* Included in place; see ../../PORTABILITY.md.

gfx_picbuff_update  tst       >GfxPicBufRotate test UI nibble-swap mode
                    beq       GfxUpdateBlit skip swap in normal picture mode
                    lda       #$00      shdw dispatch 0: swap combined-byte nibbles in place
                    sta       <$0021    store twiddle opcode
                    ldx       <$0028    load shadow copy context ptr
                    jsr       >$0701    execute in-place nibble swap; not a buffer copy
*
*======================================================================
* SCREEN BLIT
*   Triggers a full-screen blit from the shadow buffer to the display by
*   calling the scrn module's update routine.
*======================================================================
*
GfxUpdateBlit       ldd       #$A8A0    blit destination row/col
                    pshs      b,a       push destination argument
                    ldd       #$00A7    blit source descriptor
                    pshs      b,a       push source argument
                    lda       #$00      MMU twiddle opcode $00 = blit
                    sta       <$0019    store twiddle opcode
                    ldx       <$0026    load blit context pointer
                    jsr       >$0701    execute screen blit
                    leas      $04,s     discard two arguments
                    rts
