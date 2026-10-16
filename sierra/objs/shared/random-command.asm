* Inclusive byte range selection for AGI random(min,max,destination).
* InitRandSeed returns B=random byte; Y points at the three operands.
* A=Div8 remainder. A wrapped range width of zero denotes all 256 bytes.
* Bounds wrap as bytes, including min>max; zero width stores the raw byte.
* Owners bind the variable table and random source.
CmdRandomImpl       lbsr      InitRandSeed get pseudo-random value into B
                    lda       $01,y     load range max (second arg)
                    suba      ,y++      subtract range min from max, advance Y by 2
                    inca                add 1 to get range size
                    bne       CmdRandomMod branch if range is non-zero
                    tfr       b,a       range was zero, use raw random value
                    bra       CmdRandomStore skip modulo
CmdRandomMod        lbsr      Div8      divide: A=divisor, B=dividend -> A=remainder
                    adda      -$02,y    add range min to get result in range
CmdRandomStore      RANDOM_VARIABLE_TABLE
                    ldb       ,y+       load destination variable number
                    abx                 index to destination variable
                    sta       ,x        store random result in variable
                    rts
