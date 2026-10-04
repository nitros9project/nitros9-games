* Optional GAME_TRACE=1 build: report the exit byte and last instruction.
* Called after cleanup, with no mapping live; preserve the actual exit status.
GameTraceError      tstb
                    beq       GameTraceReturn
                    pshs      cc,d,x,y,u
                    pshs      b
                    leax      GameTracePrefix,pcr
                    ldu       <resourcebase
                    leay      picturestage,u
GameTraceCopy       lda       ,x+
                    sta       ,y+
                    bne       GameTraceCopy
                    leay      -1,y
                    puls      b
                    lbsr      GameTraceHex
                    lda       #C$SPAC
                    sta       ,y+
                    ldb       <vmopcode
                    lbsr      GameTraceHex
                    lda       #C$SPAC
                    sta       ,y+
                    ldu       <resourcebase
                    ldb       gametracestagebyte,u
                    lbsr      GameTraceHex
                    lda       #C$CR
                    sta       ,y+
                    ldu       <resourcebase
                    leax      picturestage,u
                    lda       #2
                    ldy       #80
                    os9       I$WritLn
                    puls      cc,d,x,y,u,pc
GameTraceReturn     rts
GameTraceHex        pshs      b
                    lsrb
                    lsrb
                    lsrb
                    lsrb
                    lbsr      GameTraceDigit
                    puls      b
                    andb      #15
GameTraceDigit      addb      #'0
                    cmpb      #'9
                    bls       GameTraceStore
                    addb      #7
GameTraceStore      stb       ,y+
                    rts
GameTracePrefix     fcc       /wbgame error, opcode: /
                    fcb       0

GameTraceStage      pshs      cc,u
                    bcc       GameTraceStageReturn
                    ldu       <resourcebase
                    tst       gametracestagebyte,u
                    bne       GameTraceStageReturn
                    sta       gametracestagebyte,u
GameTraceStageReturn puls     cc,u,pc
