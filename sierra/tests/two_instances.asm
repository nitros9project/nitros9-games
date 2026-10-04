* Boot-test AutoEx: launch the same interpreter on two distinct VDG devices.
                    use       defsfile
                    mod       eom,name,Prgrm+Objct,ReEnt,start,$100
                    org       0
Child1              rmb       1
Child2              rmb       1
name                fcs       /AutoEx/
                    fcb       1
start               leax      V1Name,pcr
                    bsr       Terminal
                    bcs       Fail
                    bsr       ForkGame
                    bcs       Fail
                    sta       <Child1
                    leax      V2Name,pcr
                    bsr       Terminal
                    bcs       Fail
                    bsr       ForkGame
                    bcs       Fail
                    sta       <Child2
Waiting             os9       F$Wait
                    bcs       Fail
                    tstb
                    bne       Fail
                    os9       F$Wait
Fail                os9       F$Exit
Terminal            pshs      x
                    clra
                    os9       I$Close
                    lda       #1
                    os9       I$Close
                    lda       #2
                    os9       I$Close
                    puls      x
                    lda       #READ.+WRITE.
                    os9       I$Open
                    bcs       TerminalRet
                    clra
                    os9       I$Dup
                    bcs       TerminalRet
                    clra
                    os9       I$Dup
TerminalRet         rts
ForkGame            leax      GameName,pcr
                    leau      Params,pcr
                    ldy       #3
                    ldd       #$1100
                    os9       F$Fork
                    rts
V1Name              fcc       '/v1'
                    fcb       C$CR
V2Name              fcc       '/v2'
                    fcb       C$CR
GameName            fcc       'sierra'
                    fcb       C$CR
Params              fcc       '-m'
                    fcb       C$CR
                    emod
eom                 equ       *
                    end
