* CoCo memory backend: engine-switch.
* Included in place to preserve code addresses and instruction timing.
* See ../../PORTABILITY.md for dependencies and current contract.

MmuSwitch           ldd       ,s++      load d with current stack pointer and bump it
*                         from mnln we come in with $4040
                    std       <CallerSp save the calling stack pointer in CallerSp
                    orcc      #IntMasks mask the interrupts
                    lda       <SierraPdBlk load Sierra's process descriptor block #
                    sta       ,x        x is loaded with value from ShdwRemap in mnln
                    sta       >$FFA9    task 1 block 2 x2000 - x3FFF
                    ldu       <Sierra2ndBlk point to Sierra's DAT image in process descriptor
                    lda       $06,x     get calling module's MMU block 6 entry
                    sta       MmuTask1Blk2,u save in Sierra's task-1 map slot 2
                    sta       >$FFAF    task 1 block 8 xE000 - xFFFF
                    lda       $05,x     get calling module's MMU block 5 entry
                    sta       MmuTask1Blk0,u save in Sierra's task-1 map slot 0
                    sta       >$FFAE    task 1 block 7 xC000 - xDFFF
                    lda       $04,x     get calling module's MMU block 4 entry
                    sta       MmuSaveTmp,u save to MMU scratch slot
                    sta       >$FFAD    task 1 block 6 xA000 - xBFFF
                    lda       $03,x     get calling module's MMU block 3 entry
                    sta       ScrEndAddr,u save to ScrEndAddr slot
                    sta       >$FFAC    task 1 block 5 x8000 - x9FFF
                    lda       $02,x     get calling module's MMU block 2 entry
                    sta       ScrStartAddr,u save to ScrStartAddr slot
                    sta       >$FFAB    task 1 block 4 x6000 - x7FFF
                    andcc     #^IntMasks unmask interrupts

                    lda       $07,x     get dispatch index from remap table
                    ldu       <EntryTable point to module entry vector table
                    adda      MmuTask1Blk0,u compute entry vector offset
                    jsr       a,u       dispatch to target module entry point

                    orcc      #IntMasks disable interrupts for MMU restore
                    lda       <SierraPdBlk Sierra's process descriptor block #
                    sta       >$FFA9    map Sierra's PD block into $2000
                    ldu       <Sierra2ndBlk point to Sierra's DAT image
                    lda       <MmuTask1Blk6 saved task-1 block 6 value
                    sta       MmuTask1Blk2,u restore DAT image entry for block 2
                    sta       >$FFAF    restore GIME MMU slot 7 (xE000)
                    lda       <MmuTask1Blk5 saved task-1 block 5 value
                    sta       MmuTask1Blk0,u restore DAT image entry for block 0
                    sta       >$FFAE    restore GIME MMU slot 6 (xC000)
                    lda       <MmuTask1Blk4 saved task-1 block 4 value
                    sta       MmuSaveTmp,u restore scratch slot
                    sta       >$FFAD    restore GIME MMU slot 5 (xA000)
                    lda       <MmuTask1Blk3 saved task-1 block 3 value
                    sta       ScrEndAddr,u restore ScrEndAddr slot
                    sta       >$FFAC    restore GIME MMU slot 4 (x8000)
                    lda       <MmuTask1Blk1 saved task-1 block 1 value
                    sta       MmuBlk2Orig,u restore MmuBlk2Orig slot
                    sta       >$FFAA    restore GIME MMU slot 2 (x4000)
                    lda       <MmuTask1Blk0 saved task-1 block 0 value
                    sta       ,u        restore DAT image task-1 slot 0
                    sta       >$FFA9    restore GIME MMU slot 1 (x2000)
                    andcc     #^IntMasks re-enable interrupts

                    jmp       [>$002A]  jump through CallerSp to restore caller
