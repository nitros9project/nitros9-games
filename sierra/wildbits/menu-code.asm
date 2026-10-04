* AGI menu construction. Owner buffers: eight 4-byte titles, thirty-two
* 6-byte items, and 768 bytes of NUL-terminated labels. Drawing/navigation
* remain a separate component; no resource pointer is stored in these records.
MenuInitialize      clr       <menucount
                    clr       <menuitems
                    clr       <menucurrent
                    clr       <menuready
                    clr       <menutextused
                    clr       <menutextused+1
                    rts
MenuCommand         ldb       <vmopcode
                    cmpb      #156
                    beq       MenuSetTitle
                    cmpb      #157
                    beq       MenuSetItem
                    cmpb      #158
                    lbeq      MenuSubmit
                    cmpb      #159
                    lbeq      MenuEnable
                    cmpb      #160
                    lbeq      MenuDisable
                    ldb       #E$UnkSvc
                    orcc      #1
                    rts
MenuCopyLabel       ldu       <resourcebase
                    ldb       vmarguments,u
                    lbsr      ReadLogicMessage
                    bcs       MenuReturn
                    tfr       y,d
                    addd      #1
                    addd      <menutextused
                    bcs       MenuFull
                    cmpd      #768
                    bhi       MenuFull
                    pshs      d
                    ldd       <menutextused
                    std       <menulabel
                    ldu       <resourcebase
                    leay      menutext,u
                    leay      d,y
MenuCopyByte        lda       ,x+
                    sta       ,y+
                    bne       MenuCopyByte
                    puls      d
                    std       <menutextused
                    clrb
MenuReturn          rts
MenuFull            ldb       #E$MemFul
                    orcc      #1
                    rts
MenuSetTitle        ldb       <menucount
                    cmpb      #8
                    bhs       MenuFull
                    lbsr      MenuCopyLabel
                    bcs       MenuReturn
                    ldu       <resourcebase
                    leax      menutitles,u
                    ldb       <menucount
                    stb       <menucurrent
                    lda       #4
                    mul
                    leax      d,x
                    ldd       <menulabel
                    std       ,x
                    ldb       <menuitems
                    stb       2,x
                    clr       3,x
                    inc       <menucount
                    clr       <menuready
                    clrb
                    rts
MenuSetItem         tst       <menucount
                    lbeq      MenuInvalid
                    ldb       <menuitems
                    cmpb      #32
                    bhs       MenuFull
                    lbsr      MenuCopyLabel
                    bcs       MenuReturn
                    ldu       <resourcebase
                    leax      menuentries,u
                    ldb       <menuitems
                    lda       #6
                    mul
                    leax      d,x
                    ldd       <menulabel
                    std       ,x
                    ldb       vmarguments+1,u
                    stb       2,x
                    ldb       <menucurrent
                    stb       3,x
                    lda       #1
                    sta       4,x
                    leax      menutitles,u
                    lda       #4
                    mul
                    leax      d,x
                    inc       3,x
                    inc       <menuitems
                    clr       <menuready
                    clrb
                    rts
MenuSubmit          tst       <menucount
                    beq       MenuInvalid
                    lda       #1
                    sta       <menuready
                    clrb
                    rts
MenuEnable          lda       #1
                    bra       MenuSetEnabled
MenuDisable         clra
MenuSetEnabled      sta       <menuoperation
                    ldu       <resourcebase
                    leax      menuentries,u
                    ldy       #0
                    ldb       vmarguments,u
MenuEnableNext      tfr       y,d
                    cmpb      <menuitems
                    bhs       MenuEnabledDone
                    ldb       vmarguments,u
                    cmpb      2,x
                    bne       MenuEnableAdvance
                    lda       <menuoperation
                    sta       4,x
MenuEnableAdvance   leax      6,x
                    leay      1,y
                    bra       MenuEnableNext
MenuEnabledDone     clrb
                    rts
MenuInvalid         ldb       #E$BMode
                    orcc      #1
                    rts
