* CoCo platform boundary: service-check.
* Included in place; see ../../PORTABILITY.md.

CheckInstanceServices lda     #StdIn
                    ldb       #SS.DevNm
                    ldx       #gprbuf
                    os9       I$GetStt
                    bcs       InstanceServiceRet
                    lda       #StdOut
                    ldb       #SS.DevNm
                    ldx       #gprbuf+32
                    os9       I$GetStt
                    bcs       InstanceServiceRet
                    ldx       #gprbuf
                    ldy       #gprbuf+32
                    ldb       #32
InstanceNameLoop    lda       ,x+
                    cmpa      ,y+
                    bne       InstanceServiceBad
                    tsta
                    beq       InstanceNamesMatch
                    bmi       InstanceNamesMatch
                    decb
                    bne       InstanceNameLoop
InstanceServiceBad  comb
                    ldb       #E$IllArg
                    rts
InstanceNamesMatch  lda       #StdOut
                    ldb       #SS.AScrn
                    os9       I$GetStt  query the ownership-aware application-screen ABI
                    bcs       InstanceServiceRet
                    cmpx      #2
                    bcc       InstanceServiceOK
                    comb
                    ldb       #E$UnkSvc
InstanceServiceRet  rts
InstanceServiceOK   clrb
                    rts
