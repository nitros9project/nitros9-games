* Native argument/validation adapter; byte arithmetic belongs to the common engine.
GameMathCommand     ldu       <resourcebase
                    leay      vmarguments,u
                    ldb       <vmopcode
                    cmpb      #167
                    blo       GameMathReady
                    ldb       vmarguments+1,u
                    lda       <vmopcode
                    cmpa      #168
                    bne       GameMathDivisor
                    VARIABLE_TABLE
                    abx
                    ldb       ,x
GameMathDivisor     tstb
                    lbeq      ObjectBadIndex
GameMathReady       ldb       <vmopcode
                    subb      #165
                    lslb
                    leax      GameMathHandlers,pcr
                    ldd       b,x
                    leax      d,x
                    jsr       ,x
                    clrb
                    rts
GameMathHandlers    fdb       cmd_multn-GameMathHandlers
                    fdb       cmd_multv-GameMathHandlers
                    fdb       cmd_divn-GameMathHandlers
                    fdb       cmd_divv-GameMathHandlers
MATH_DIVIDE         macro
                    lbsr      Div8
                    endm
                    use       shared/math-commands.asm

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
