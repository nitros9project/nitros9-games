* CoCo memory backend: logic-map.
* Included in place to preserve code addresses and instruction timing.
* See ../../PORTABILITY.md for dependencies and current contract.

SetLogicPage        cmpa      <$000A    check if page already set
                    beq       SetLogicPageRet skip if no change needed
                    orcc      #$50      disable interrupts during switch
                    std       <$000A    save new page number
                    lda       <$0042    load current MMU shadow byte
                    sta       >$FFA9    write to MMU slot 9
                    ldx       <$0043    load MMU control register ptr
                    lda       <$000A    load new page high byte
                    sta       ,x        set MMU slot high
                    stb       $02,x     set MMU slot low
                    std       >$FFA9    commit page change to MMU
                    andcc     #$AF      re-enable interrupts
SetLogicPageRet     rts
