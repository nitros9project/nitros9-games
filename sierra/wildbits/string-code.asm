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
StringCopy          lda       ,x+
                    sta       ,y+
                    beq       StringDone
                    decb
                    bne       StringCopy
                    clr       ,y
StringDone          clrb
StringReturn        rts
StringInvalid       ldb       #E$IllArg
                    orcc      #1
                    rts
