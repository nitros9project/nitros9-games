GameWanderCommand   lbsr      ObjectAddress
                    lbcs      ObjectReturn
                    lda       #1
                    sta       $22,x
                    clr       $27,x
                    lda       $26,x
                    ora       #$10
                    sta       $26,x
                    tst       2,x
                    lbne      ObjectDone
                    clr       <vmplayercontrol
                    lbra      ObjectDone
* Private 16-bit Galois LFSR; no mapped pointers or global random state.
GameRandomByte      ldx       <resourcebase
                    ldd       gamerandom,x
                    lsra
                    rorb
                    bcc       GameRandomStore
                    eora      #$B4
GameRandomStore     std       gamerandom,x
                    andcc     #$FE
                    rts
InitRandSeed        equ       GameRandomByte
DivideDivisor       equ       vmtemp
DivideBits          equ       vmleft
                    use       shared/divide-byte.asm
WANDER_PRIVATE_STATE equ      1
                    use       shared/object-wander.asm
