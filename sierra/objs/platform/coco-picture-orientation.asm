* CoCo platform boundary: picture-orientation.
* Included in place; see ../../PORTABILITY.md.

gfx_picbuff_update_remap
PicBufUpdateRemap   ldx       #gfx_picbuff starting low address of srceen mem
NibbleSwapLoop      lda       ,x        get the first byte  bit order 0,1,2,3,4,5,6,7
                    clrb                empty b
                    lsra                shift one bit from a
                    rorb                into b
                    lsra                shift second bit from a
                    rorb                rotate into b
                    lsra                and again
                    rorb                rotate into b
                    lsra                and finally once more
                    rorb                nibble swap complete in b
                    stb       ,x        were changing x anyway so use it for temp storage
                    ora       ,x        or that with acca so now bit order from orig
*                        is 4,5,6,7,0,1,2,3
                    sta       ,x+       put it back at x and go for the next one
                    cmpx      #gbuffend ending high address of screen mem
                    bcs       NibbleSwapLoop loop until entire buffer remapped
                    rts                 buffer remap complete return
