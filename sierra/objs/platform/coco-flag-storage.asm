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
