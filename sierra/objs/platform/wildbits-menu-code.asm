* Process-private modal menu. Existing labels/controllers retain their ABI.
* Display a paged list of titled items; disabled entries cannot be selected.
GameMenuInput       equ       *
                    ifne      GAME_TRACE
                    ldu       <resourcebase
                    inc       gametracemenuhit,u
                    endc
                    tst       <menuready
                    lbeq      MenuInvalid
                    tst       <menuitems
                    lbeq      GameCycleSuccess
                    lbsr      AssetUnmap
                    lbcs      GameCycleReturn
                    lbsr      PictureUnmap
                    lbcs      GameCycleReturn
                    ldu       <resourcebase
                    leax      textcharacters,u
                    leay      resourcecommands,u
                    ldd       #1000
                    pshs      d
GameMenuSave        ldd       ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       GameMenuSave
                    leas      2,s
                    clr       inventoryselected,u
                    clr       inventoryselected+1,u
GameMenuDraw        ldu       <resourcebase
                    leax      textcharacters,u
                    ldy       #1000
GameMenuWhite       lda       #32
                    sta       ,x
                    lda       #$0F
                    sta       1000,x
                    leax      1,x
                    leay      -1,y
                    bne       GameMenuWhite
                    leax      GameMenuTitle,pcr
                    leay      textcharacters+42,u
                    lbsr      InventoryString
                    leax      GameMenuHelp,pcr
                    leay      textcharacters+961,u
                    lbsr      InventoryString
                    clra
                    ldb       inventoryselected+1,u
                    cmpb      #21
                    blo       GameMenuPage
                    lda       #21
GameMenuPage        sta       inventorytop+1,u
                    clr       inventorytop,u
                    sta       inventoryprevious+1,u
                    clr       inventoryprevious,u
                    lda       #3
                    sta       inventoryrow,u
GameMenuItem        ldb       inventoryprevious+1,u
                    cmpb      <menuitems
                    lbhs      GameMenuPresent
                    lda       #6
                    mul
                    leax      menuentries,u
                    leax      d,x
                    pshs      x
                    lda       inventoryrow,u
                    ldb       #40
                    mul
                    leay      textcharacters,u
                    leay      d,y
                    pshs      y
                    ldb       #40
                    lda       inventoryprevious+1,u
                    cmpa      inventoryselected+1,u
                    bne       GameMenuNormal
                    lda       #$F0
                    bra       GameMenuRowColor
GameMenuNormal      lda       #$0F
                    tst       4,x
                    bne       GameMenuRowColor
                    lda       #$7F
GameMenuRowColor    sta       1000,y
                    leay      1,y
                    decb
                    bne       GameMenuRowColor
                    puls      y
                    leay      2,y
                    ldb       3,x
                    lda       #4
                    mul
                    leax      menutitles,u
                    ldd       d,x
                    leax      menutext,u
                    leax      d,x
                    ldb       #38
                    lbsr      GameMenuLabel
                    leax      GameMenuColon,pcr
                    lbsr      GameMenuLabel
                    puls      x
                    pshs      x
                    lda       inventoryrow,u
                    ldb       #40
                    mul
                    addd      #40
                    leax      textcharacters,u
                    leax      d,x
                    pshs      y
                    tfr       x,d
                    subd      ,s++
                    stb       inventorykey,u
                    puls      x
                    ldd       ,x
                    leax      menutext,u
                    leax      d,x
                    ldb       inventorykey,u
                    lbsr      GameMenuLabel
                    inc       inventoryprevious+1,u
                    inc       inventoryrow,u
                    lda       inventoryrow,u
                    cmpa      #24
                    lblo      GameMenuItem
GameMenuPresent     lbsr      GameDrawText
                    lbcs      GameMenuRestore
GameMenuWait        lbsr      foreground
                    lbcs      GameMenuRestore
                    clra
                    ldb       #SS.Ready
                    os9       I$GetStt
                    bcc       GameMenuReadKey
                    cmpb      #E$NotRdy
                    lbne      GameMenuRestore
                    ldx       #2
                    os9       F$Sleep
                    bra       GameMenuWait
GameMenuReadKey     ldu       <resourcebase
                    leax      parsercharacter,u
                    ldy       #1
                    clra
                    os9       I$Read
                    lbcs      GameMenuRestore
                    ldu       <resourcebase
                    lda       parsercharacter,u
                    cmpa      #5
                    beq       GameMenuCancel
                    cmpa      #27
                    beq       GameMenuCancel
                    cmpa      #13
                    beq       GameMenuSelect
                    cmpa      #12
                    beq       GameMenuUp
                    cmpa      #8
                    beq       GameMenuUp
                    cmpa      #10
                    beq       GameMenuDown
                    cmpa      #9
                    bne       GameMenuWait
GameMenuDown        inc       inventoryselected+1,u
                    lda       inventoryselected+1,u
                    cmpa      <menuitems
                    blo       GameMenuChanged
                    clr       inventoryselected+1,u
                    bra       GameMenuChanged
GameMenuUp          tst       inventoryselected+1,u
                    bne       GameMenuDecrement
                    lda       <menuitems
                    sta       inventoryselected+1,u
GameMenuDecrement   dec       inventoryselected+1,u
GameMenuChanged     lbra      GameMenuDraw
GameMenuSelect      ldb       inventoryselected+1,u
                    lda       #6
                    mul
                    leax      menuentries,u
                    leax      d,x
                    tst       4,x
                    lbeq      GameMenuWait
                    ldb       2,x
                    lbsr      InputControllerAddress
                    ora       ,x
                    sta       ,x
GameMenuCancel      clrb
GameMenuRestore     pshs      cc,b
                    ldu       <resourcebase
                    leax      resourcecommands,u
                    leay      textcharacters,u
                    ldd       #1000
                    pshs      d
GameMenuCopyBack    ldd       ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       GameMenuCopyBack
                    leas      2,s
                    puls      cc,b
                    lbcs      GameCycleReturn
                    lbsr      GameComposeScene
                    lbcs      GameCycleReturn
                    lbra      RefreshPicture
GameMenuLabel       tstb
                    beq       GameMenuLabelDone
                    lda       ,x+
                    beq       GameMenuLabelDone
                    sta       ,y+
                    decb
                    bra       GameMenuLabel
GameMenuLabelDone   rts
GameMenuTitle       fcc       /Game menu/
                    fcb       0
GameMenuColon       fcc       /: /
                    fcb       0
GameMenuHelp        fcc       /Arrows select; ENTER opens; ESC cancels/
                    fcb       0
