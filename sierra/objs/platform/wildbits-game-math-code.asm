* Byte arithmetic keeps AGI modulo-256 results and bounded divisors.
GameMathCommand     ldu       <resourcebase
                    leax      vmvariables,u
                    clra
                    ldb       vmarguments,u
                    leax      d,x
                    ldb       vmarguments+1,u
                    lda       <vmopcode
                    bita      #1
                    bne       GameMathOperand
                    leay      vmvariables,u
                    clra
                    ldb       d,y
GameMathOperand     lda       <vmopcode
                    cmpa      #167
                    bhs       GameMathDivide
                    lda       ,x
                    mul
                    stb       ,x
                    clrb
                    rts
GameMathDivide      tstb
                    lbeq      ObjectBadIndex
                    tfr       b,a
                    ldb       ,x
                    lbsr      Div8
                    stb       ,x
                    clrb
                    rts
GameRandomCommand   ldu       <resourcebase
                    lda       vmarguments,u
                    cmpa      vmarguments+1,u
                    lbhi      ObjectBadIndex
                    ldb       vmarguments+2,u
                    pshs      d
                    ldb       vmarguments+1,u
                    subb      vmarguments,u
                    incb
                    pshs      b
                    lbsr      GameRandomByte
                    lda       ,s+
                    tsta
                    beq       GameRandomWholeByte
                    lbsr      Div8
                    tfr       a,b
GameRandomWholeByte addb     ,s
                    lda       1,s
                    leax      vmvariables,u
                    pshs      b
                    tfr       a,b
                    clra
                    leax      d,x
                    puls      b
                    stb       ,x
                    leas      2,s
                    clrb
                    rts
