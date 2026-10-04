* CoCo loader/memory backend: map-restore.
* Included in place; see ../../PORTABILITY.md for ownership and constraints.

RestoreMmu          tst       >ProcMapReady
                    beq       RestoreMmuRet
                    clr       >ProcMapReady
                    orcc      #IntMasks Shut off interrupts
                    lda       <SierraPdBlk get MMU Block #
                    sta       >$FFA9    Restore original block 0 onto MMU
                    ldx       <Sierra2ndBlk reload Sierra DAT image pointer
                    ldd       >SierraMmuBlk3 Origanl 3rd block of MMU
                    std       1,x       restore 3rd block in Sierra's DAT map
                    stb       >$FFAA    Restore original block 1 onto MMU
                    ldd       >SierraMmuBlk2 Original 2nd block of MMU
                    std       -1,x      restore 2nd block in Sierra's DAT map
                    stb       >$FFA9    Restore block 0 again
                    andcc     #^IntMasks Turn interrupts back on

RestoreMmuRet       rts                 return from RestoreMmu
