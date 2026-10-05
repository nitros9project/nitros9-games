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
GameCheckBlock      lda       $26,u
                    anda      #$7F
                    sta       $26,u
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
                    lda       $26,u
                    ora       #$80
                    sta       $26,u
                    clr       $21,u
                    tst       motionid,x
                    bne       GameBlockStopped
                    clr       vmvariables+6,x
GameBlockStopped    ldb       #1
                    rts
GameBlockAllowed    clrb
                    rts
