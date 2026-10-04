* CoCo memory backend: priority-map.
* Included in place to preserve code addresses and instruction timing.
* See ../../PORTABILITY.md for dependencies and current contract.

MapShdwPage         orcc      #$50      disable interrupts for MMU access
                    lda       >$FFA9    read current MMU slot 9
                    ldb       <$0042    load shadow page number
                    stb       >$FFA9    map shadow page to slot 9
                    ldx       <$0043    load MMU control ptr
                    ldb       <$005F    load base priority page
                    addb      #$08      advance 8 pages into shadow
                    stb       $04,x     update MMU slot 4
                    stb       >$FFAB    write to MMU hardware
                    sta       >$FFA9    restore original slot 9
                    andcc     #$AF      re-enable interrupts
                    rts
