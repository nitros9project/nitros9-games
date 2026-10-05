* Unsigned decimal conversion; input D in the owner's supported domain.
* DECIMAL_OUTPUT_END supplies X=last buffer byte; caller owns enough space
* for the number plus NUL. DECIMAL_OUTPUT_DIVIDE takes D/U and returns
* quotient U and remainder D, preserving X/Y. Return X=first digit, D/U=0.
UIntToDecStr        DECIMAL_OUTPUT_END
                    clr       ,x
UIntToDecLoop       ldu       #$000A
                    DECIMAL_OUTPUT_DIVIDE
                    addb      #$30
                    stb       ,-x
                    tfr       u,d
                    cmpd      #$0000
                    bhi       UIntToDecLoop
                    rts
