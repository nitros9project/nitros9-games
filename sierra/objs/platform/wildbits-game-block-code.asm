GameBlockCommand    ldx       <resourcebase
                    ldb       <vmopcode
                    cmpb      #91
                    beq       GameBlockClear
                    ldd       vmarguments,x
                    std       BlockLeft,x
                    ldd       vmarguments+2,x
                    std       BlockRight,x
                    lda       #1
                    sta       gameblockenabled,x
                    clrb
                    rts
GameBlockClear      clr       gameblockenabled,x
                    clrb
                    rts
BLOCK_PRIVATE_STATE equ       1
                    use       shared/object-block-test.asm
                    use shared/object-block-state.asm
GameCheckBlock      OBJECT_BLOCK_CLEAR u
                    bita      #2
                    bne       GameBlockAllowed
                    tst       gameblockenabled,x
                    beq       GameBlockAllowed
                    ldd       motionoldposition,x
                    lbsr      InBlockRect
                    sta       motioncollision,x
                    lda       motionx+1,x
                    ldb       motiony+1,x
                    lbsr      InBlockRect
                    cmpa      motioncollision,x
                    beq       GameBlockAllowed
GameBlockCrossing   OBJECT_BLOCK_STOP u,GameBlockStopped
GameBlockStopped    ldb       #1
                    rts
GameBlockAllowed    clrb
                    rts
