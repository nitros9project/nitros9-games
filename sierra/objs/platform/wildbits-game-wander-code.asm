                    use       platform/wildbits-motion-setup.asm
                    use       shared/object-motion-setup.asm
GameWanderCommand   lbsr      ObjectAddress
                    lbcs      ObjectReturn
                    OBJECT_WANDER_SETUP x,GameWanderDone
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
