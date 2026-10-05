* Restore only the options this process changes. Keep CTRL-C as an interrupt.
GameTerminalEnter   leas      -32,s
                    leax      ,s
                    clra
                    ldb       #SS.Opt
                    os9       I$GetStt
                    bcs       GameTerminalReturn
                    tst       ,x
                    bne       GameTerminalInvalid
                    ldu       <resourcebase
                    lda       PD.EKO-PD.OPT,x
                    sta       terminalecho,u
                    lda       PD.EOF-PD.OPT,x
                    sta       terminaleof,u
                    lda       PD.QUT-PD.OPT,x
                    sta       terminalquit,u
                    clr       PD.EKO-PD.OPT,x
                    clr       PD.EOF-PD.OPT,x
                    clr       PD.QUT-PD.OPT,x
                    lda       #1
                    sta       terminalchanged,u
                    clra
                    ldb       #SS.Opt
                    os9       I$SetStt
GameTerminalReturn  leas      32,s
                    rts
GameTerminalInvalid ldb       #E$BMode
                    orcc      #1
                    bra       GameTerminalReturn
GameTerminalRestore ldu       <resourcebase
                    tst       terminalchanged,u
                    beq       GameTerminalSuccess
                    leas      -32,s
                    leax      ,s
                    clra
                    ldb       #SS.Opt
                    os9       I$GetStt
                    bcs       GameTerminalReturn
                    ldu       <resourcebase
                    lda       terminalecho,u
                    sta       PD.EKO-PD.OPT,x
                    lda       terminaleof,u
                    sta       PD.EOF-PD.OPT,x
                    lda       terminalquit,u
                    sta       PD.QUT-PD.OPT,x
                    clra
                    ldb       #SS.Opt
                    os9       I$SetStt
                    bcs       GameTerminalReturn
                    ldu       <resourcebase
                    clr       terminalchanged,u
                    bra       GameTerminalReturn
GameTerminalSuccess clrb
                    rts
