* CoCo loader/memory backend: address-blocks.
* Included in place; see ../../PORTABILITY.md for ownership and constraints.

TwiddleAddr         tfr       x,d       Move address to D
*         exg   a,b          Swap MSB/LSB
*         lsrb               Divide MSB by 32 (calculate 8k block # in proc map)
*         lsrb
*         lsrb
*         lsrb
*         lsrb
*         pshs  b            Save block # in process map
*         ldu   #$FFA8       Point to start of user DAT image
*         lda   b,u
                    ldb       #8        hi_byte × 8 / 256 = 8K block index in A
                    mul                 compute block index from address high byte
                    pshs      a         save block index (0-7)
                    ldu       #mmubuf+8 point to task-1 physical MMU block table
                    lda       a,u       get MMU value
                    ldb       ,s        reload block index from stack
                    incb                index of next adjacent block
                    andb      #$07      wrap within 8 task-1 slots
                    ldb       b,u       read physical block # of adjacent slot
                    tfr       d,u       U = both physical block numbers
                    puls      a         restore block index
                    rts                 return: A=block index, U=physical block pair
