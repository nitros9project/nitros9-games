* Lazy bounded object-file load. No resource slab remains mapped across I/O.
* Names stay immutable after validation; only inventoryrooms changes.
InventoryLoad       ldu       <resourcebase
                    tst       inventoryloaded,u
                    lbne      InventorySuccess
InventoryLoadNames  lbsr      AssetUnmap
                    lbcs      InventoryReturn
                    lbsr      PictureUnmap
                    lbcs      InventoryReturn
                    ldy       <resourcenameend
                    leax      InventoryFilename,pcr
                    lbsr      ResourceSuffix
                    lbsr      OpenPicturePath
                    lbcs      ResourceFailed
                    ldu       <resourcebase
                    clr       inventorylength,u
                    clr       inventorylength+1,u
InventoryRead       ldd       inventorylength,u
                    leax      inventoryfile,u
                    leax      d,x
                    pshs      d
                    ldd       #2048
                    subd      ,s++
                    tfr       d,y
                    beq       InventoryProbe
                    lda       <resourcepath
                    os9       I$Read
                    bcs       InventoryReadEnd
                    cmpy      #0
                    lbeq      ResourceInvalid
                    tfr       y,d
                    ldu       <resourcebase
                    addd      inventorylength,u
                    cmpd      #2048
                    lbhi      ResourceInvalid
                    std       inventorylength,u
                    bra       InventoryRead
InventoryProbe      leax      picturestage,u
                    ldy       #1
                    lda       <resourcepath
                    os9       I$Read
                    lbcc      ResourceInvalid
InventoryReadEnd    cmpb      #E$EOF
                    lbne      ResourceFailed
                    lbsr      ResourceClose
                    lbcs      ResourceFailed
                    ldu       <resourcebase
                    ldd       inventorylength,u
                    cmpd      #3
                    lblo      InventoryInvalid
                    leax      inventoryfile,u
                    leau      d,x
                    lbsr      XorDecrypt
                    ldy       #0        ; retain the old countdown-loop result
                    ldu       <resourcebase
                    leax      inventoryfile,u
                    ldb       ,x
                    lda       1,x
                    cmpd      #768
                    lbhi      InventoryInvalid
                    pshs      d
                    addd      #3
                    std       inventorynames,u
                    cmpd      inventorylength,u
                    puls      d
                    lbhs      InventoryInvalid
                    tfr       d,y
                    clr       inventorycount,u
                    clr       inventorycount+1,u
InventoryCountLoop  cmpy      #0
                    beq       InventoryValidate
                    cmpy      #3
                    blo       InventoryInvalid
                    leay      -3,y
                    ldd       inventorycount,u
                    addd      #1
                    std       inventorycount,u
                    bra       InventoryCountLoop
InventoryValidate   leax      3,x
                    leay      inventoryrooms,u
                    ldd       inventorycount,u
                    pshs      d
InventoryEntry      ldd       ,s
                    beq       InventoryValidated
                    ldb       ,x
                    lda       1,x
                    addd      #3
                    cmpd      inventorynames,u
                    blo       InventoryEntryInvalid
                    cmpd      inventorylength,u
                    bhs       InventoryEntryInvalid
                    pshs      x,y
                    leay      inventoryfile,u
                    leay      d,y
InventoryName       cmpd      inventorylength,u
                    bhs       InventoryNameInvalid
                    tst       ,y+
                    beq       InventoryNameDone
                    addd      #1
                    bra       InventoryName
InventoryNameInvalid puls     x,y
InventoryEntryInvalid leas    2,s
                    bra       InventoryInvalid
InventoryNameDone   puls      x,y
                    tst       inventoryloaded,u
                    bne       InventoryKeepRoom
                    lda       2,x
                    sta       ,y
InventoryKeepRoom   leay      1,y
                    leax      3,x
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bra       InventoryEntry
InventoryValidated  leas      2,s
                    lda       #1
                    sta       inventoryloaded,u
InventorySuccess    clrb
InventoryReturn     rts
InventoryInvalid    ldb       #E$BMode
                    orcc      #1
                    rts
InventoryFilename   fcc       /object/
                    fcb       C$CR
                    use shared/xor-decrypt.asm

* Command rules shared with CoCo; item/name loading and storage stay native.
                    use       platform/wildbits-inventory-operands.asm
                    use       shared/inventory-commands.asm
InventoryCommand    lbsr      InventoryLoad
                    lbcs      InventoryReturn
                    ldu       <resourcebase
                    leay      vmarguments,u
                    ldb       <vmopcode
                    subb      #92
                    cmpb      #5
                    lbhi      InventoryInvalid
                    lslb
                    leax      InventoryCommands,pcr
                    ldd       b,x
                    leax      d,x
                    jmp       ,x
InventoryCommands   fdb       InventoryGet-InventoryCommands
                    fdb       InventoryGetVariable-InventoryCommands
                    fdb       InventoryDrop-InventoryCommands
                    fdb       InventoryPut-InventoryCommands
                    fdb       InventoryPutVariable-InventoryCommands
                    fdb       InventoryGetRoom-InventoryCommands
InventoryGet        INVENTORY_SET_LOCATION 0,$FF
                    clrb
                    rts
InventoryGetVariable INVENTORY_SET_LOCATION 1,$FF
                    clrb
                    rts
InventoryDrop       INVENTORY_SET_LOCATION 0,$00
                    clrb
                    rts
InventoryPut        INVENTORY_PUT_LOCATION 0
                    clrb
                    rts
InventoryPutVariable INVENTORY_PUT_LOCATION 1
                    clrb
                    rts
InventoryGetRoom    INVENTORY_GET_LOCATION
                    clrb
                    rts
InventoryVariableItemAddress ldb ,y+
                    leax      vmvariables,u
                    clra
                    ldb       d,x
                    bra       InventoryResolveItem
InventoryItemAddress ldb      ,y+
InventoryResolveItem clra
                    cmpd      inventorycount,u
                    lbhs      InventoryInvalid
                    leax      inventoryrooms,u
                    leax      d,x
                    andcc     #$FE
                    rts

* Modal status screen. Picture-command staging is dead after decoding and
* supplies the 2000-byte text backup; no resource loads occur while modal.
InventoryStatus     lbsr      InventoryLoadNames
                    lbcs      InventoryReturn
                    ldu       <resourcebase
                    leax      textcharacters,u
                    leay      resourcecommands,u
                    ldd       #1000
                    pshs      d
InventorySaveText   ldd       ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       InventorySaveText
                    leas      2,s
                    clr       inventoryvisible,u
                    clr       inventoryvisible+1,u
                    clr       inventoryselected,u
                    clr       inventoryselected+1,u
                    clr       inventorytop,u
                    clr       inventorytop+1,u
                    leax      inventoryrooms,u
                    leay      inventorylist,u
                    ldd       #0
InventoryBuildList  cmpd      inventorycount,u
                    bhs       InventoryRedraw
                    pshs      d
                    lda       ,x+
                    cmpa      #255
                    bne       InventoryListNext
                    ldb       1,s
                    stb       ,y+
                    ldd       inventoryvisible,u
                    addd      #1
                    std       inventoryvisible,u
InventoryListNext   puls      d
                    addd      #1
                    bra       InventoryBuildList
InventoryRedraw     leax      textcharacters,u
                    ldy       #1000
InventoryWhite      lda       #32
                    sta       ,x
                    lda       #$0F
                    sta       1000,x
                    leax      1,x
                    leay      -1,y
                    bne       InventoryWhite
                    leax      InventoryTitle,pcr
                    leay      textcharacters+42,u
                    lbsr      InventoryString
                    leax      InventoryReturnText,pcr
                    tst       vmflags+13,u
                    beq       InventoryFooter
                    leax      InventorySelectText,pcr
InventoryFooter     leay      textcharacters+961,u
                    lbsr      InventoryString
                    ldd       inventoryvisible,u
                    bne       InventoryItems
                    leax      InventoryNothing,pcr
                    leay      textcharacters+122,u
                    lbsr      InventoryString
                    lbra      InventoryPresent
InventoryItems      lda       #3
                    sta       inventoryrow,u
                    ldd       inventorytop,u
                    pshs      d
InventoryDrawItem   ldd       ,s
                    cmpd      inventoryvisible,u
                    bhs       InventoryItemsDone
                    leax      inventorylist,u
                    ldb       d,x
                    lda       #3
                    mul
                    leax      inventoryfile+3,u
                    leax      d,x
                    ldb       ,x
                    lda       1,x
                    leax      inventoryfile+3,u
                    leax      d,x
                    lda       inventoryrow,u
                    ldb       #40
                    mul
                    addd      #2
                    leay      textcharacters,u
                    leay      d,y
                    lbsr      InventoryString
                    tst       vmflags+13,u
                    beq       InventoryNextRow
                    ldd       ,s
                    cmpd      inventoryselected,u
                    bne       InventoryNextRow
                    lda       inventoryrow,u
                    ldb       #40
                    mul
                    leay      textcolors,u
                    leay      d,y
                    ldb       #40
InventoryHighlight  lda       #$F0
                    sta       ,y
                    leay      1,y
                    decb
                    bne       InventoryHighlight
InventoryNextRow    ldd       ,s
                    addd      #1
                    std       ,s
                    inc       inventoryrow,u
                    lda       inventoryrow,u
                    cmpa      #24
                    blo       InventoryDrawItem
InventoryItemsDone  leas      2,s
InventoryPresent    lbsr      GameTextPresent
                    lbcs      InventoryRestoreError
InventoryWait       lbsr      foreground
                    lbcs      InventoryRestoreError
                    ldu       <resourcebase
                    clra
                    ldb       #SS.Ready
                    os9       I$GetStt
                    bcc       InventoryReadKey
                    cmpb      #E$NotRdy
                    lbne      InventoryRestoreError
                    ldx       #2
                    os9       F$Sleep
                    lbra      InventoryWait
InventoryReadKey    ldu       <resourcebase
                    leax      inventorykey,u
                    ldy       #1
                    clra
                    os9       I$Read
                    lbcs      InventoryRestoreError
                    ldu       <resourcebase
                    cmpy      #1
                    lbne      InventoryWait
                    tst       vmflags+13,u
                    lbeq      InventoryDismiss
                    ldd       inventoryselected,u
                    std       inventoryprevious,u
                    lda       inventorykey,u
                    cmpa      #5
                    lbeq      InventoryCancel
                    cmpa      #27
                    lbeq      InventoryCancel
                    cmpa      #3
                    lbeq      InventoryCancel
                    cmpa      #13
                    lbeq      InventoryChoose
                    ldd       inventoryvisible,u
                    lbeq      InventoryWait
                    lda       inventorykey,u
                    cmpa      #12
                    beq       InventoryUp
                    cmpa      #10
                    lbne      InventoryWait
                    ldd       inventoryselected,u
                    addd      #1
                    cmpd      inventoryvisible,u
                    lbhs      InventoryWait
                    std       inventoryselected,u
                    subd      inventorytop,u
                    cmpd      #21
                    blo       InventoryDrawAgain
                    ldd       inventorytop,u
                    addd      #1
                    std       inventorytop,u
                    bra       InventoryPageChange
InventoryUp         ldd       inventoryselected,u
                    lbeq      InventoryWait
                    subd      #1
                    std       inventoryselected,u
                    cmpd      inventorytop,u
                    bhs       InventoryDrawAgain
                    std       inventorytop,u
InventoryPageChange lbra      InventoryRedraw
InventoryDrawAgain  lda       #$0F
                    sta       inventorypaint,u
                    ldd       inventoryprevious,u
                    lbsr      InventoryPaintRow
                    lbcs      InventoryRestoreError
                    ldu       <resourcebase
                    lda       #$F0
                    sta       inventorypaint,u
                    ldd       inventoryselected,u
                    lbsr      InventoryPaintRow
                    lbcs      InventoryRestoreError
                    lbra      InventoryWait
InventoryChoose     ldd       inventoryvisible,u
                    lbeq      InventoryCancel
                    ldd       inventoryselected,u
                    leax      inventorylist,u
                    lda       d,x
                    bra       InventorySelection
InventoryCancel     lda       #255
InventorySelection  sta       vmvariables+25,u
InventoryDismiss    clrb
InventoryRestoreError pshs    cc,b
                    ldu       <resourcebase
                    leax      resourcecommands,u
                    leay      textcharacters,u
                    ldd       #1000
                    pshs      d
InventoryRestoreText ldd      ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       InventoryRestoreText
                    leas      2,s
                    puls      cc,b
                    lbcs      InventoryReturn
                    lbsr      GameComposeScene
                    lbcs      InventoryReturn
                    lbra      RefreshPicture

* Change and draw only one highlight row when the visible page is unchanged.
InventoryPaintRow   ldx       <resourcebase
                    subd      inventorytop,x
                    addd      #3
                    stb       textrow,x
                    clr       textcolumn,x
                    lda       #40
                    mul
                    std       textindex,x
                    leay      textcolors,x
                    leay      d,y
                    addd      #40
                    std       textend,x
                    ldb       #40
InventoryPaintCell  lda       inventorypaint,x
                    sta       ,y
                    leay      1,y
                    decb
                    bne       InventoryPaintCell
                    lbra      GameDrawTextRange

* Render at most 38 columns. File names were bounded and NUL-validated.
InventoryString     ldb       #38
InventoryStringByte lda      ,x+
                    beq       InventoryStringDone
                    sta       ,y+
                    decb
                    bne       InventoryStringByte
InventoryStringDone rts
InventoryTitle      fcc       /You are carrying:/
                    fcb       0
InventoryNothing    fcc       /nothing/
                    fcb       0
InventoryReturnText fcc       /Press a key to return to the game/
                    fcb       0
InventorySelectText fcc       /ENTER selects; ESC cancels/
                    fcb       0

* has(item) and obj.in.room(item, room-variable) share the mutable room table.
InventoryTest       lbsr      InventoryLoad
                    lbcs      InventoryReturn
                    ldu       <resourcebase
                    leay      vmarguments,u
                    ldb       <vmopcode
                    cmpb      #9
                    beq       InventoryHas
                    cmpb      #10
                    lbne      InventoryInvalid
                    INVENTORY_ROOM_TEST
InventoryHas        INVENTORY_HAS_TEST
InventoryFalse      clrb
                    rts
