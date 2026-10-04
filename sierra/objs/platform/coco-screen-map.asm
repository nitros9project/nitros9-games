* CoCo memory backend: screen-map.
* Included in place to preserve code addresses and instruction timing.
* See ../../PORTABILITY.md for dependencies and current contract.

SetMapBlock         cmpa      <MmuBlkNum check MMU block
                    beq       MapBlockOk if block 0  OK to leave
                    orcc      #IntMasks Turn off interrupts
                    sta       <MmuBlkNum store the value passed in by a
                    lda       <SierraPdBlk get sierra process descriptor map block
                    sta       >DatTask1Slot1 map it in to $2000-$3FFF
                    ldx       <Sierra2ndBlk 2nd 8K data block in Sierra
                    lda       <MmuBlkNum get mmu block num
                    sta       ,x        store block number at slot 0
                    stb       $02,x     store block number at slot 2
                    std       >DatTask1Slot1 Map it into task 1 block 2
                    andcc     #^IntMasks turn on interrupts $AF
MapBlockOk          rts
