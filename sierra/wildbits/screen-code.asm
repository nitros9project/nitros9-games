ScreenInitialize    lda       #'_
                    sta       <vmcursor
                    lda       #15
                    sta       <vmtextforeground
                    clr       <vmtextbackground
                    clr       <vmstatusrow
                    clr       <vmstatusenabled
                    lda       #1
                    sta       <vmpicturetop
                    sta       <vminputenabled
                    sta       <vmgraphics
                    lda       #23
                    sta       <vminputrow
                    rts
ScreenCommand       ldu       <resourcebase
                    ldb       <vmopcode
                    cmpb      #108
                    beq       ScreenCursor
                    cmpb      #109
                    beq       ScreenColors
                    cmpb      #111
                    beq       ScreenConfigure
                    cmpb      #112
                    beq       ScreenStatusOn
                    cmpb      #113
                    beq       ScreenStatusOff
                    cmpb      #119
                    beq       ScreenInputOff
                    cmpb      #120
                    beq       ScreenInputOn
                    ldb       #E$UnkSvc
                    orcc      #1
                    rts
ScreenCursor        ldb       vmarguments,u
                    lbsr      ReadLogicMessage
                    bcs       ScreenReturn
                    lda       ,x
                    sta       <vmcursor
                    bra       ScreenDone
ScreenColors        ldd       vmarguments,u
                    cmpa      #15
                    bhi       ScreenInvalid
                    cmpb      #15
                    bhi       ScreenInvalid
                    sta       <vmtextforeground
                    stb       <vmtextbackground
                    bra       ScreenDone
ScreenConfigure     lda       vmarguments,u
                    cmpa      #4         21 picture rows within 25 text rows
                    bhi       ScreenInvalid
                    sta       <vmpicturetop
                    lda       vmarguments+1,u
                    cmpa      #24
                    bhi       ScreenInvalid
                    sta       <vminputrow
                    lda       vmarguments+2,u
                    cmpa      #24
                    bhi       ScreenInvalid
                    sta       <vmstatusrow
                    bra       ScreenDone
ScreenStatusOn      lda       #1
                    sta       <vmstatusenabled
                    bra       ScreenDone
ScreenStatusOff     clr       <vmstatusenabled
                    bra       ScreenDone
ScreenInputOff      clr       <vminputenabled
                    bra       ScreenDone
ScreenInputOn       lda       #1
                    sta       <vminputenabled
ScreenDone          clrb
ScreenReturn        rts
ScreenInvalid       ldb       #E$IllArg
                    orcc      #1
                    rts
