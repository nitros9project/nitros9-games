* One 8K service window; retain the OS-returned address for unmapping.
mapblock            clra
                    ldb       <blockindex
                    addd      <firstblock
                    tfr       d,x
                    ldb       #1
                    os9       F$MapBlk
                    bcs       mapret
                    stu       <mapbase
                    inc       <mapped
                    andcc     #$FE
mapret              rts
unmap               ldu       <mapbase
                    ldb       #1
                    os9       F$ClrBlk
                    bcs       unmapret
                    clr       <mapped
                    andcc     #$FE
unmapret            rts

* Pure conversion boundary: X=160 combined pixels,Y=320 output pixels.
* Low nibble color -> palette indices 1..16; duplicate horizontally.
ConvertRow          ldb       #PictureWidth
convertpixel        lda       ,x+
                    anda      #$0F
                    inca
                    sta       ,y+
                    sta       ,y+
                    decb
                    bne       convertpixel
                    rts
* Visibility handling uses intercepted U, never the interrupted DP.
intercept           cmpb      #SignalBg
                    bne       signalforeground
                    stb       paused,u
                    rti
signalforeground    cmpb      #SignalFg
                    bne       signalabort
                    clr       paused,u
                    ifne      GAME_PRESENTATION
                    inc       gameclockreset,u
                    endc
                    rti
signalabort         cmpb      #S$Abort
                    blo       signalreturn
                    cmpb      #S$Intrpt
                    bhi       signalreturn
                    stb       aborted,u
                    ifne      PRESENT_PICTURE
                    ldb       #E$PrcAbt
                    stb       decodeerror,u
                    ifne      AGI_ASSET
                    stb       asseterror,u
                    endc
                    endc
signalreturn        rti

foreground          pshs      x
waitforeground      tst       <aborted
                    bne       foregroundabort
                    tst       <paused
                    beq       foregroundready
                    ldx       #2        one tick; bounded foreground race
                    os9       F$Sleep
                    bra       waitforeground
foregroundabort     ldb       #E$PrcAbt
                    orcc      #1
                    puls      x,pc
foregroundready     clrb
                    puls      x,pc

* Input and output must identify the same terminal before changing graphics.
CheckTerminal       ldu       <dbase
                    leax      inputname,u
                    clra
                    ldb       #SS.DevNm
                    os9       I$GetStt
                    bcs       terminalreturn
                    ldu       <dbase
                    leax      outputname,u
                    lda       #1
                    ldb       #SS.DevNm
                    os9       I$GetStt
                    bcs       terminalreturn
                    ldu       <dbase
                    leax      inputname,u
                    leay      outputname,u
                    ldb       #32
terminalcompare     lda       ,x+
                    cmpa      ,y+
                    bne       terminalbad
                    tsta
                    beq       terminalok
                    bmi       terminalok
                    decb
                    bne       terminalcompare
terminalbad         ldb       #E$IllArg
                    orcc      #1
terminalreturn      rts
terminalok          clrb
                    rts
