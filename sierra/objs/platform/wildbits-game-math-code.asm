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
                    leay      vmarguments,u
                    lbsr      CmdRandomImpl
                    clrb
                    rts
                    use       platform/wildbits-random-operands.asm
                    use       shared/random-command.asm
