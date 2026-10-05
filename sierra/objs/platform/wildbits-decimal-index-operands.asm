* Keep the complete product until overflow is checked; record accepted digits.
DECIMAL_INDEX_ADJUST macro
                    subd      #$30
                    endm
DECIMAL_INDEX_VALIDATE macro
                    adca      #0
                    tsta
                    bne       DecimalIndexOverflow
                    stb       parserwordlength,u
                    inc       parserbestlength,u
                    endm
DECIMAL_INDEX_RETURN macro
                    andcc     #$FE
                    rts
                    endm
