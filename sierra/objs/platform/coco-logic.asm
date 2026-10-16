* coco-logic feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_COCO_FLAG_STORAGE
* ===== coco-flag-storage =====
* CoCo packed-bit flag storage; A=index, helpers preserve Y/U.
SetFlag             bsr       GetFlagBitAddr get bit mask (A) and byte address (X)
                    ora       ,x        OR bit mask into flag byte
                    sta       ,x        store updated flag byte
                    rts

ClearFlag           bsr       GetFlagBitAddr get bit mask (A) and byte address (X)
                    coma                invert bit mask to produce AND mask
                    anda      ,x        AND inverted mask to clear the bit
                    sta       ,x        store updated flag byte
                    rts

ToggleFlag          bsr       GetFlagBitAddr get bit mask (A) and byte address (X)
                    eora      ,x        XOR to toggle the flag bit
                    sta       ,x        store updated flag byte
                    rts
TestFlag            bsr       GetFlagBitAddr get bit mask (A) and byte address (X)
                    anda      ,x        AND mask with flag byte (result: 0=clear, nonzero=set)
                    rts
GetFlagBitAddr      tfr       a,b       copy flag number to B
                    leax      >FlagBitTable,pcr point X to bit-mask lookup table
                    anda      #$07      flag number mod 8 → bit index within byte
                    lda       a,x       load bit mask for this flag bit
                    lsrb                shift flag number right 3 (÷8)
                    lsrb                (second shift)
                    lsrb                → byte offset into flag table
                    ldx       #$01AE    base address of flag table
                    abx                 index to the correct flag byte
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_LOGIC_MAP
* ===== coco-logic-map =====
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

                    else
                    error Unknown platform feature section
                    endc
                    endc
