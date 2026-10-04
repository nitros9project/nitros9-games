* CoCo memory backend: map-snapshot.
* Included in place to preserve code addresses and instruction timing.
* See ../../PORTABILITY.md for dependencies and current contract.

mmuini1             lbsr      mmuini2
                    pshs      cc,d,x,y
                    orcc      #IntMasks
                    lda       >mmubuf+9
                    pshs      a
                    clr       >$FFA9
                    ldx       >D.SysDAT+$2000
                    leax      $2000,x    the system descriptor is in system block 0
                    ldy       #mmubuf
                    ldb       #8
m2lup               lda       1,x       low byte of the physical block number
                    sta       ,y+
                    leax      2,x
                    decb
                    bne       m2lup
                    puls      a
                    sta       >$FFA9
                    puls      cc,d,x,y,pc
* Get $FFA8-$FFAF
mmuini2             pshs      cc,x,y    save registers across system calls
                    orcc      #$50      disable interrupts
                    os9       F$ID      get our ID#
                    ldx       #gprbuf point to process descriptor buffer
                    os9       F$GPrDsc  get our process descriptor
                    leay      $41,x     point to our mmu block values
                    ldx       #mmubuf+8 destination: task-1 MMU snapshot buffer
                    ldb       #8        copy 8 MMU block entries
mloop               lda       ,y++      read MMU value from process descriptor
                    sta       ,x+       store block number and advance
                    decb                decrement copy count
                    bne       mloop     loop until all 8 copied
                    puls      cc,x,y,pc restore registers and return
