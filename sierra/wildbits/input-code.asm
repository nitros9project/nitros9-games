InputInitialize     clr       <vmkeycount
                    clr       <vmhavekey
                    ldu       <resourcebase
                    leax      vmcontrollers,u
                    ldy       #32
                    clra
InputClearController sta      ,x+
                    leay      -1,y
                    bne       InputClearController
                    rts
SetKeyCommand       ldu       <resourcebase
                    leax      vmkeys,u
                    ldy       #0
InputFindKey        tfr       y,d
                    cmpb      <vmkeycount
                    bhs       InputAddKey
                    ldd       vmarguments,u
                    cmpd      ,x
                    beq       InputStoreKey
                    leax      3,x
                    leay      1,y
                    bra       InputFindKey
InputAddKey         ldb       <vmkeycount
                    cmpb      #50
                    bhs       InputKeyFull
                    inc       <vmkeycount
InputStoreKey       ldd       vmarguments,u
                    std       ,x
                    ldb       vmarguments+2,u
                    stb       2,x
                    clrb
                    rts
InputKeyFull        ldb       #E$MemFul
                    orcc      #1
                    rts
InputTest           ldb       <vmopcode
                    cmpb      #12
                    beq       InputControllerTest
                    cmpb      #13
                    beq       InputHaveKeyTest
                    cmpb      #14
                    beq       InputSaidTest
                    ldb       #E$UnkSvc
                    orcc      #1
                    rts
InputControllerTest ldu       <resourcebase
                    ldb       vmarguments,u
                    lbsr      InputControllerAddress
                    bita      ,x
                    beq       InputTestFalse
                    ldb       #1
                    andcc     #$FE
                    rts
* B=controller (all 256 supported); X=private byte, A=one-bit mask.
InputControllerAddress pshs   b
                    andb      #7
                    leax      InputControllerMasks,pcr
                    lda       b,x
                    puls      b
                    lsrb
                    lsrb
                    lsrb
                    pshs      a
                    clra
                    leax      vmcontrollers,u
                    leax      d,x
                    puls      a,pc
InputControllerMasks fcb      1,2,4,8,16,32,64,128
InputHaveKeyTest    ldb       <vmhavekey
                    andcc     #$FE
                    rts
InputSaidTest       ldu       <resourcebase
                    tst       vmflags+2,u
                    beq       InputTestFalse
* A submitted sentence requires the native word matcher; it cannot be skipped.
                    ldb       #E$UnkSvc
                    orcc      #1
                    rts
InputTestFalse      clrb
                    rts
