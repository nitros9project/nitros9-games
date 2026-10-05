                    use       shared/bounded-string-copy.asm
* Private 12-slot, 40-byte string table matching the existing CoCo layout.
StringsInitialize   ldu       <resourcebase
                    leax      vmstrings,u
                    ldy       #480
                    clra
StringsClear        sta       ,x+
                    leay      -1,y
                    bne       StringsClear
                    rts
SetStringCommand    ldu       <resourcebase
                    lda       vmarguments,u
                    cmpa      #12
                    bhs       StringInvalid
                    ldb       vmarguments+1,u
                    lbsr      ReadLogicMessage
                    bcs       StringReturn
                    ldu       <resourcebase
                    leay      vmstrings,u
                    lda       vmarguments,u
                    ldb       #40
                    mul
                    leay      d,y
                    ldb       #39
                    BOUNDED_STRING_COPY y,StringCopy,StringDone,BOUNDED_BYTE_COUNT
                    clrb
StringReturn        rts
StringInvalid       ldb       #E$IllArg
                    orcc      #1
                    rts

                    ifne      GAME_PRESENTATION
* Condition 15 uses the CoCo normalization/comparison body on private slots.
StringCompareTest   ldu       <resourcebase
                    ldd       vmarguments,u
                    cmpa      #12
                    lbhs      StringInvalid
                    cmpb      #12
                    lbhs      StringInvalid
                    lbsr      MatchWord
                    ldu       <resourcebase
                    tfr       a,b
                    andcc     #$FE
                    rts
NORMAL_STRING_TABLE macro
                    ldu       <resourcebase
                    leau      vmstrings,u
                    endm
NORMAL_STRING_FOLD  equ       ParserLower
                    use       shared/compare-strings.asm
                    use       shared/string-punctuation.asm
                    endc
