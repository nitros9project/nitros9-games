* wildbits-text-ui feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_DIALOG_CODE
* ===== wildbits-dialog-code =====
* print/print.v: modal text with private screen backup and no mapped wait.
* The picture/LZW command workspace is idle until the window is dismissed.
* Pause shares the modal restoration path. Rebaseline the game clock on
* resume so the time spent waiting does not advance AGI seconds/minutes.
GamePauseCommand    ldu       <resourcebase
                    clr       dialoginputmode,u
                    leax      GamePausePrompt,pcr
                    lbsr      GamePrintText
                    bcs       GamePauseReturn
                    ldu       <resourcebase
                    lda       #1
                    sta       gameclockreset,u
                    clrb
GamePauseReturn     rts
GamePausePrompt     fcc       /Game paused. Press a key to resume./
                    fcb       0

GamePrintCommand    ldu       <resourcebase
                    clr       dialoginputmode,u
                    ldb       vmarguments,u
                    lda       <vmopcode
                    cmpa      #102
                    bne       GamePrintMessage
                    leax      vmvariables,u
                    clra
                    ldb       d,x
GamePrintMessage    lbsr      ReadLogicMessage
                    lbcs      GameTextReturn
GamePrintText       ldu       <resourcebase
                    stx       textpointer,u
                    leax      textcharacters,u
                    leay      resourcecommands,u
                    ldd       #1000
                    pshs      d
GamePrintSave       ldd       ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       GamePrintSave
                    leas      2,s
                    lda       <vmtextforeground
                    ldb       <vmtextbackground
                    pshs      d
                    clr       <vmtextforeground
                    lda       #15
                    sta       <vmtextbackground
                    leax      textcharacters,u
                    ldy       #1000
GamePrintClear      lda       #32
                    sta       ,x
                    lda       #$0F
                    sta       1000,x
                    leax      1,x
                    leay      -1,y
                    bne       GamePrintClear
                    lda       #1
                    sta       dialogactive,u
                    sta       dialogwordstart,u
                    lda       #8
                    sta       textrow,u
                    lda       #2
                    sta       textcolumn,u
                    ldx       textpointer,u
                    lbsr      GameTextValidate
                    bcs       GamePrintRestore
GamePrintWait       lbsr      foreground
                    bcs       GamePrintRestore
                    lda       #0
                    ldb       #SS.Ready
                    os9       I$GetStt
                    bcc       GamePrintKey
                    cmpb      #E$NotRdy
                    bne       GamePrintRestore
                    ldx       #2
                    os9       F$Sleep
                    bra       GamePrintWait
GamePrintKey        lda       #0
                    ldu       <resourcebase
                    leax      parsercharacter,u
                    ldy       #1
                    os9       I$Read
                    lbcs      GamePrintRestore
                    ldu       <resourcebase
                    tst       dialoginputmode,u
                    beq       GamePrintRestore
                    lbsr      GameLineKey
                    lbcs      GamePrintRestore
                    tsta
                    lbeq      GamePrintWait
                    clrb
GamePrintRestore    pshs      cc,b
                    ldu       <resourcebase
                    clr       dialogactive,u
                    ldu       <resourcebase
                    leax      resourcecommands,u
                    leay      textcharacters,u
                    ldd       #1000
                    pshs      d
GamePrintCopyBack   ldd       ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       GamePrintCopyBack
                    leas      2,s
                    puls      cc,b
                    puls      a
                    sta       <vmtextforeground
                    puls      a
                    sta       <vmtextbackground
                    lbcs      GameTextReturn
                    lbsr      GameComposeScene
                    lbcs      GameTextReturn
                    lbra      RefreshPicture

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_DICTIONARY_CODE
* ===== wildbits-dictionary-code =====
* Random-access encoded byte provider over the existing 512-byte file buffer.
* X=file offset, U=input cursor; A=byte/C clear or B=OS error/C set.
* X/Y/U are preserved, B is scratch. No mapped slab crosses file I/O.
DictionaryReadAt    pshs      x,y,u
                    ldu       <resourcebase
                    tfr       x,d
                    subd      dictionarycachebase,u
                    cmpd      parserreadlength,u
                    blo       DictionaryReadCached
                    ldx       ,s
                    stx       dictionarycachebase,u
                    ldd       #0
                    std       parserreadindex,u
                    std       parserreadlength,u
                    tfr       x,u
                    ldx       #0
                    lda       <resourcepath
                    os9       I$Seek
                    bcs       DictionaryReadReturn
                    lbsr      ParserByte
                    bcs       DictionaryReadReturn
                    tfr       b,a
                    andcc     #$FE
DictionaryReadReturn puls    x,y,u,pc
DictionaryReadCached leay    assetinput,u
                    lda       d,y
                    andcc     #$FE
                    puls      x,y,u,pc
DictionaryPrefix    pshs      a
                    lbsr      DictionaryReadAt
                    bcs       DictionaryPrefixError
                    tfr       a,b
                    puls      a
                    leax      1,x
                    andcc     #$FE
                    rts
DictionaryPrefixError puls   a,pc
DictionaryReadID    pshs      x
                    leax      1,x
                    lbsr      DictionaryReadAt
                    bcs       DictionaryIDReturn
                    pshs      a
                    leax      1,x
                    lbsr      DictionaryReadAt
                    bcs       DictionaryIDError
                    tfr       a,b
                    puls      a
                    andcc     #$FE
DictionaryIDReturn  puls     x,pc
DictionaryIDError   leas     1,s
                    puls      x,pc
* Validation already established EOF only at an entry boundary or trailing zero.
* Restore the common frame before propagating a real seek/read error.
DictionaryReadFailure cmpb   #E$EOF
                    lbeq      LookupWordNotFound
                    leas      6,s
                    orcc      #1
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_TEXT_CODE
* ===== wildbits-game-text-code =====
GameTextInitialize  ldu       <resourcebase
                    leax      textcharacters,u
                    ldy       #1000
GameTextClear       clr       ,x+
                    leay      -1,y
                    bne       GameTextClear
                    rts

* draw.pic replaces all pixels within the configured 21-row picture area.
* Drop the corresponding saved text too, or the next frame resurrects old
* credits/messages over the new picture. Keep status/input rows outside it.
GameTextClearPicture ldu      <resourcebase
                    lda       <vmpicturetop
                    ldb       #40
                    mul
                    leax      textcharacters,u
                    leax      d,x
                    ldy       #840
                    bra       GameTextClear

* display/display.v. Messages are copied into private persistent cells;
* a framebuffer refresh can redraw them without reopening the logic slab.
GameDisplayCommand  ldu       <resourcebase
                    leax      vmarguments,u
                    lda       <vmopcode
                    cmpa      #104
                    bne       GameDisplayArguments
                    leay      vmvariables,u
                    ldb       ,x
                    clra
                    ldb       d,y
                    stb       ,x
                    ldb       1,x
                    ldb       d,y
                    stb       1,x
                    ldb       2,x
                    ldb       d,y
                    stb       2,x
GameDisplayArguments lda      ,x
                    cmpa      #25
                    lbhs      GameTextInvalid
                    sta       textrow,u
                    lda       1,x
                    cmpa      #40
                    lbhs      GameTextInvalid
                    sta       textcolumn,u
                    ldb       2,x
                    lbsr      ReadLogicMessage
                    lbcs      GameTextReturn
                    ldu       <resourcebase
                    stx       textpointer,u
* Expand copied messages without retaining resource-window pointers.
GameTextValidate    lbsr      GameFormatMessage
                    lbcs      GameTextReturn
                    stx       textpointer,u
GameTextStore       tst       dialogactive,u
                    beq       GameTextRead
                    tst       dialogwordstart,u
                    beq       GameTextRead
                    lda       textcolumn,u
                    cmpa      #2
                    bls       GameTextRead
                    ldx       textpointer,u
                    clrb
GameTextWordLength  lda       b,x
                    beq       GameTextWordEnd
                    cmpa      #32
                    beq       GameTextWordEnd
                    cmpa      #10
                    beq       GameTextWordEnd
                    cmpa      #13
                    beq       GameTextWordEnd
                    incb
                    cmpb      #38
                    blo       GameTextWordLength
GameTextWordEnd     addb      textcolumn,u
                    cmpb      #40
                    bls       GameTextRead
                    lda       #2
                    sta       textcolumn,u
                    inc       textrow,u
                    lda       textrow,u
                    cmpa      #25
                    lbhs      GameTextPresent
GameTextRead        ldx       textpointer,u
                    lda       ,x+
                    stx       textpointer,u
                    tsta
                    lbeq      GameTextPresent
                    cmpa      #10
                    beq       GameTextNewline
                    cmpa      #13
                    beq       GameTextNewline
                    tst       dialogactive,u
                    beq       GameTextCharacter
                    clr       dialogwordstart,u
                    cmpa      #32
                    bne       GameTextCharacter
                    inc       dialogwordstart,u
                    ldb       textcolumn,u
                    cmpb      #2
                    lbeq      GameTextStore
GameTextCharacter   pshs      a
                    lda       textrow,u
                    ldb       #40
                    mul
                    addb      textcolumn,u
                    adca      #0
                    leax      textcharacters,u
                    leax      d,x
                    puls      a
                    sta       ,x
                    lda       textrow,u
                    ldb       #40
                    mul
                    addb      textcolumn,u
                    adca      #0
                    leax      textcolors,u
                    leax      d,x
                    lda       <vmtextforeground
                    lsla
                    lsla
                    lsla
                    lsla
                    ora       <vmtextbackground
                    sta       ,x
                    inc       textcolumn,u
                    lda       textcolumn,u
                    cmpa      #40
                    lblo      GameTextStore
GameTextNewline     clr       textcolumn,u
                    tst       dialogactive,u
                    beq       GameTextAdvanceRow
                    lda       #2
                    sta       textcolumn,u
                    lda       #1
                    sta       dialogwordstart,u
GameTextAdvanceRow  inc       textrow,u
                    lda       textrow,u
                    cmpa      #25
                    lblo      GameTextStore
GameTextPresent     lbsr      AssetUnmap
                    bcs       GameTextReturn
                    tst       <bitmapowned
                    bne       GameDrawText
                    tst       <pictureowned
                    bne       GameTextShowPicture
                    lbsr      GameCreateScreen
                    bcs       GameTextReturn
GameTextShowPicture lbra      PresentPicture
GameTextNeedsFormatter ldb    #E$UnkSvc
                    orcc      #1
                    rts
GameTextInvalid     ldb       #E$IllArg
                    orcc      #1
GameTextReturn      rts

GameCreateScreen    lbsr      PictureAllocate
                    bcs       GameTextReturn
                    ldy       #0
GameBlankPage       tfr       y,d
                    lbsr      PicturePointer
                    tst       <decodeerror
                    bne       GameTextDecodeError
                    ldx       #8192
                    lda       #$40       opaque black with default priority
GameBlankByte       sta       ,u+
                    leax      -1,x
                    bne       GameBlankByte
                    leay      8192,y
                    cmpy      #32768
                    blo       GameBlankPage
                    lbsr      PictureUnmap
                    bcs       GameTextReturn
                    clrb
                    rts
GameTextDecodeError ldb       <decodeerror
                    orcc      #1
                    rts

                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_RENDER_TEXT
                    use platform/wildbits-text-ui.asm
* A bounded contiguous cell range; caller sets index/end/row/column.
GameDrawTextRange   lbsr      AssetUnmap
                    lbcs      GameTextReturn
                    lbsr      PictureUnmap
                    lbcs      GameTextReturn
                    lbsr      foreground
                    lbcs      GameTextReturn
                    ldx       <resourcebase
GameTextCell        ldd       textindex,x
                    leay      textcharacters,x
                    lda       d,y
                    lbeq      GameTextNextCell
                    anda      #$7F
                    ldb       #8
                    mul
                    leay      gamefont,x
                    leay      d,y
                    sty       textfontpointer,x
                    ldd       textindex,x
                    leay      textcolors,x
                    leay      d,y
                    lda       ,y
                    anda      #$0F
                    inca
                    sta       textbackground,x
                    lda       ,y
                    lsra
                    lsra
                    lsra
                    lsra
                    inca
                    sta       textforeground,x
                    clr       textglyphrow,x
GameTextGlyphRow    ldy       textfontpointer,x
                    lda       ,y+
                    sty       textfontpointer,x
                    sta       textbits,x
                    clr       textglyphpixel,x
GameTextGlyphPixel  lda       textbackground,x
                    lsl       textbits,x
                    bcc       GameTextPixelColor
                    lda       textforeground,x
GameTextPixelColor  sta       textcolor,x
                    lda       textrow,x
                    ldb       #8
                    mul
                    addb      textglyphrow,x
                    lda       #160
                    mul
                    lslb
                    rola
                    pshs      d
                    lda       textcolumn,x
                    ldb       #8
                    mul
                    addb      textglyphpixel,x
                    adca      #0
                    addd      ,s++
                    lbsr      GameFramePointer
                    lbcs      GameTextReturn
                    lda       textcolor,x
                    sta       ,u
                    inc       textglyphpixel,x
                    lda       textglyphpixel,x
                    cmpa      #8
                    blo       GameTextGlyphPixel
                    inc       textglyphrow,x
                    lda       textglyphrow,x
                    cmpa      #8
                    blo       GameTextGlyphRow
GameTextNextCell    ldd       textindex,x
                    addd      #1
                    std       textindex,x
                    cmpd      textend,x
                    bhs       GameTextDrawDone
                    inc       textcolumn,x
                    lda       textcolumn,x
                    cmpa      #40
                    lblo      GameTextCell
                    clr       textcolumn,x
                    inc       textrow,x
                    lbra      GameTextCell
GameTextDrawDone    tst       <mapped
                    lbeq      GameCycleSuccess
                    lbra      unmap

* D=framebuffer offset; return ephemeral U, preserve D/X/Y.
GameFramePointer    pshs      d,x,y
                    lsra
                    lsra
                    lsra
                    lsra
                    lsra
                    tst       <mapped
                    beq       GameFrameMap
                    cmpa      <blockindex
                    beq       GameFrameAddress
                    pshs      a
                    lbsr      unmap
                    puls      a
                    bcs       GameFrameReturn
GameFrameMap        sta       <blockindex
                    lbsr      mapblock
                    bcs       GameFrameReturn
GameFrameAddress    ldd       ,s
                    anda      #$1F
                    ldu       <mapbase
                    leau      d,u
                    andcc     #$FE
GameFrameReturn     puls      d,x,y,pc

* clear.lines(start,end,color): inclusive rows; persistent opaque blank cells.
GameClearLines      ldu       <resourcebase
                    lda       vmarguments,u
                    cmpa      #25
                    lbhs      GameTextInvalid
                    ldb       vmarguments+1,u
                    cmpb      #25
                    lbhs      GameTextInvalid
                    cmpb      vmarguments,u
                    lblo      GameTextInvalid
                    subb      vmarguments,u
                    incb
                    lda       #40
                    mul
                    tfr       d,y
                    lda       vmarguments,u
                    ldb       #40
                    mul
                    leax      textcharacters,u
                    leax      d,x
                    clra
                    tst       vmarguments+2,u
                    beq       GameClearCell
                    lda       #$FF
GameClearCell       ldb       #32
                    stb       ,x
                    sta       1000,x
                    leax      1,x
                    leay      -1,y
                    bne       GameClearCell
                    lbra      GameTextPresent

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_TEXT_DATA
* ===== wildbits-game-text-data =====
* Persistent text cells survive picture refreshes; zero means no overlay.
textcharacters      rmb      1000
* High nibble is logical foreground, low nibble logical background (0..15).
textcolors          rmb      1000
textpointer         rmb      2
textindex           rmb      2
textend             rmb      2
textfontpointer     rmb      2
textrow             rmb      1
textcolumn          rmb      1
textglyphrow        rmb      1
textglyphpixel      rmb      1
textbits            rmb      1
textcolor           rmb      1
textforeground      rmb      1
textbackground      rmb      1

* Inclusive occupied span for the scanline text renderer.
textfirstcolumn     rmb      1
textlastcolumn      rmb      1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_INVENTORY_CODE
* ===== wildbits-inventory-code =====
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
                    ifndef PLATFORM_WILDBITS_TEXT_UI_BINDINGS
                    use platform/wildbits-text-ui-bindings.asm
                    endc
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

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_INVENTORY_DATA
* ===== wildbits-inventory-data =====
* Process-private decrypted object file and mutable item rooms.
inventoryloaded     rmb       1
inventorylength     rmb       2
inventorycount      rmb       2
inventoryrooms      rmb       256
* Names exist only during loading/status; the decoder is idle then.
inventoryfile       equ       fillstack
inventorylist       equ       fillstack+3840
inventoryvisible    rmb       2
inventoryselected   rmb       2
inventorytop        rmb       2
inventoryrow        rmb       1
inventorykey        rmb       1
inventorynames      rmb       2
inventoryprevious   rmb       2
inventorypaint      rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_MENU_BUILD_CODE
* ===== wildbits-menu-build-code =====
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

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_MENU_CODE
* ===== wildbits-menu-code =====
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

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_MENU_DATA
* ===== wildbits-menu-data =====
* Private menu construction controls. Labels are copied out of logic slabs.
menucount           rmb       1
menuitems           rmb       1
menucurrent         rmb       1
menuready           rmb       1
menutextused        rmb       2
menulabel           rmb       2
menuoperation       rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_MESSAGE_CODE
* ===== wildbits-message-code =====
* ReadLogicMessage: B=1-based message number. X=private messagebuffer,
* Y=length excluding NUL on success; C/error B otherwise. U/DP retained.
* Message offsets are little endian relative to the length word following
* the count. Plain AGI logic strings use Avis Durgan; LZW strings are plain.
* Every table/string access is checked against the owned expanded slab.
ReadLogicMessage    stb       <messagenumber
                    ldd       <vmend
                    lbsr      AssetReadByte
                    lbcs      MessageReturn
                    stb       <messagecount
                    tst       <messagenumber
                    lbeq      MessageInvalid
                    ldb       <messagenumber
                    cmpb      <messagecount
                    lbhi      MessageInvalid
                    ldd       <vmend
                    addd      #1
                    std       <messagebase
                    lbsr      AssetReadWord
                    lbcs      MessageReturn
                    cmpd      #2
                    lblo      MessageInvalid
                    addd      <messagebase
                    lbcs      MessageInvalid
                    cmpd      <resourcelength
                    lbhi      MessageInvalid
                    std       <messageend
                    clra
                    ldb       <messagecount
                    lslb
                    rola
                    addd      #2
                    addd      <messagebase
                    lbcs      MessageInvalid
                    std       <messagestart
                    cmpd      <messageend
                    lbhi      MessageInvalid
                    clra
                    ldb       <messagenumber
                    lslb
                    rola
                    addd      <messagebase
                    lbsr      AssetReadWord
                    lbcs      MessageReturn
                    cmpd      #0
                    lbeq      MessageInvalid
                    addd      <messagebase
                    lbcs      MessageInvalid
                    cmpd      <messagestart
                    lblo      MessageInvalid
                    cmpd      <messageend
                    lbhs      MessageInvalid
                    std       <messageposition
                    subd      <messagestart
MessageKeyModulo    cmpd      #11
                    blo       MessageKeyReady
                    subd      #11
                    bra       MessageKeyModulo
MessageKeyReady     stb       <messagekey
                    clr       <messagelength
                    clr       <messagelength+1
MessageCopyNext     ldd       <messageposition
                    cmpd      <messageend
                    lbhs      MessageInvalid
                    lbsr      AssetReadByte
                    lbcs      MessageReturn
                    pshs      b
                    ldd       <messageposition
                    addd      #1
                    std       <messageposition
                    ldd       <resourcestored
                    cmpd      <resourcelength
                    puls      b
                    bne       MessagePlainByte
                    leax      MessageXorKey,pcr
                    lda       <messagekey
                    eorb      a,x
                    inc       <messagekey
                    lda       <messagekey
                    cmpa      #11
                    blo       MessagePlainByte
                    clr       <messagekey
MessagePlainByte    pshs      b
                    ldu       <resourcebase
                    leax      messagebuffer,u
                    ldd       <messagelength
                    leax      d,x
                    puls      b
                    stb       ,x
                    tstb
                    beq       MessageDone
                    ldd       <messagelength
                    addd      #1
                    std       <messagelength
                    cmpd      #512
                    blo       MessageCopyNext
                    ldb       #E$MemFul
                    orcc      #1
                    bra       MessageReturn
MessageDone         ldu       <resourcebase
                    leax      messagebuffer,u
                    ldy       <messagelength
                    clrb
MessageReturn       rts
MessageInvalid      ldb       #E$BMode
                    orcc      #1
                    rts

MessageXorKey       equ       XorKeyStr
                    use shared/agi-xor-key.asm

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_MESSAGE_DATA
* ===== wildbits-message-data =====
* Private mapped-logic message reader controls.
messagebase         rmb       2
messageend          rmb       2
messagestart        rmb       2
messageposition     rmb       2
messagelength       rmb       2
messagenumber       rmb       1
messagecount        rmb       1
messagekey          rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_PARSER_DATA
* ===== wildbits-parser-data =====
* Persistent submitted words must survive resource loads in the logic cycle.
parserline          rmb       40
parserword          rmb       40
parserids           rmb       40
parsercount         rmb       1
parserlength        rmb       1
parserposition      rmb       1
parserwordlength    rmb       1
parserbestlength    rmb       1
parserbestid        rmb       2
parserreadindex     rmb       2
parserreadlength    rmb       2
parserid            rmb       2
parsercharacter     rmb       1
parserseen          rmb       1
parserstart         rmb       2
parserlastline      rmb       40
parseroffsets       rmb       20
parserlengths       rmb       20
formatdepth         rmb       1
dialogactive        rmb       1
dialogwordstart     rmb       1
dialoginputmode     rmb       1
terminalchanged     rmb       1
terminalecho        rmb       1
terminaleof         rmb       1
terminalquit        rmb       1
* The old decoded-ID scratch is now the selected encoded entry offset.
dictionaryentry     equ       parserid
* Stream cache base adds two bytes, still within three private pages.
dictionarycachebase rmb       2
* Temporary offsets occupy idle formatter output only during ParserParse.
dictionarygroups    equ       fillstack+2048

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_RENDER_TEXT
* ===== wildbits-render-text =====
* Render occupied text rows horizontally, avoiding a MapBlk round trip for
* each character when its eight scanlines straddle a framebuffer page.
* rowoutput is private, and index zero means leave that framebuffer pixel.
GameDrawText        lbsr      AssetUnmap
                    lbcs      GameTextReturn
                    lbsr      PictureUnmap
                    lbcs      GameTextReturn
                    ldx       <resourcebase
                    clr       textrow,x
TextFastNextRow     lbsr      foreground
                    lbcs      GameTextReturn
                    ldx       <resourcebase
                    lda       textrow,x
                    ldb       #40
                    mul
                    leau      textcharacters,x
                    leau      d,u
                    ldb       #40
TextFastFind        lda       ,u+
                    bne       TextFastOccupied
                    decb
                    bne       TextFastFind
                    lbra      TextFastAdvanceRow
TextFastOccupied    negb
                    addb      #40
                    stb       textfirstcolumn,x
* Locate the final occupied cell. Render the bounded span, preserving holes.
                    lda       textrow,x
                    ldb       #40
                    mul
                    leau      textcharacters+40,x
                    leau      d,u
                    ldb       #39
TextFastFindLast    lda       ,-u
                    bne       TextFastLastFound
                    decb
                    bra       TextFastFindLast
TextFastLastFound   stb       textlastcolumn,x
                    clr       textglyphrow,x
TextFastGlyphRow    lda       textrow,x
                    ldb       #40
                    mul
                    addb      textfirstcolumn,x
                    adca      #0
                    std       textindex,x
                    lda       textfirstcolumn,x
                    sta       textcolumn,x
                    leay      rowoutput,x
TextFastCell        ldd       textindex,x
                    leau      textcharacters,x
                    lda       d,u
                    beq       TextFastEmpty
                    anda      #$7F
                    ldb       #8
                    mul
                    addb      textglyphrow,x
                    adca      #0
                    leau      gamefont,x
                    lda       d,u
                    sta       textbits,x
                    ldd       textindex,x
                    leau      textcolors,x
                    lda       d,u
                    tfr       a,b
                    anda      #$0F
                    inca
                    sta       textbackground,x
                    tfr       b,a
                    lsra
                    lsra
                    lsra
                    lsra
                    inca
                    sta       textforeground,x
                    ldb       #8
TextFastBits        lda       textbackground,x
                    lsl       textbits,x
                    bcc       TextFastPixel
                    lda       textforeground,x
TextFastPixel       sta       ,y+
                    decb
                    bne       TextFastBits
                    bra       TextFastNextCell
TextFastEmpty       clra
                    ldb       #8
TextFastBlank       sta       ,y+
                    decb
                    bne       TextFastBlank
TextFastNextCell    ldd       textindex,x
                    addd      #1
                    std       textindex,x
                    inc       textcolumn,x
                    lda       textcolumn,x
                    cmpa      textlastcolumn,x
                    lbls      TextFastCell
                    leay      rowoutput,x
                    sty       textfontpointer,x
                    lda       textrow,x
                    ldb       #8
                    mul
                    addb      textglyphrow,x
                    adca      #0
                    lda       #160
                    mul
                    lslb
                    rola
                    pshs      d
                    lda       textfirstcolumn,x
                    ldb       #8
                    mul
                    addd      ,s++
                    std       textindex,x
                    lda       textlastcolumn,x
                    suba      textfirstcolumn,x
                    inca
                    ldb       #8
                    mul
                    std       textend,x
TextFastWriteSpan   ldd       textindex,x
                    lbsr      GameFramePointer
                    lbcs      GameTextReturn
                    anda      #$1F
                    pshs      d
                    ldd       #8192
                    subd      ,s++
                    cmpd      textend,x
                    bls       TextFastSpanSize
                    ldd       textend,x
TextFastSpanSize    ldy       textfontpointer,x
                    pshs      d,x
                    tfr       d,x
TextFastCopy        lda       ,y+
                    beq       TextFastSkip
                    sta       ,u
TextFastSkip        leau      1,u
                    leax      -1,x
                    bne       TextFastCopy
                    puls      d,x
                    sty       textfontpointer,x
                    pshs      d
                    addd      textindex,x
                    std       textindex,x
                    ldd       textend,x
                    subd      ,s++
                    std       textend,x
                    bne       TextFastWriteSpan
                    inc       textglyphrow,x
                    lda       textglyphrow,x
                    cmpa      #8
                    lblo      TextFastGlyphRow
TextFastAdvanceRow  inc       textrow,x
                    lda       textrow,x
                    cmpa      #25
                    lblo      TextFastNextRow
                    tst       <mapped
                    lbeq      GameCycleSuccess
                    lbra      unmap

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_REPLAY_CODE
* ===== wildbits-replay-code =====
* Size/reset/checkpoint commands adapted from mnln's script-buffer routines.
* A record is D = operation/resource. C/error B on overflow; U retained.
ReplayInitialize    ldu       <resourcebase
                    ldb       vmarguments,u
                    stb       <replaylimit
                    clr       <replayused
                    clr       <replayused+1
                    clr       <replaycheckpoint
                    clr       <replaycheckpoint+1
                    clrb
                    rts
ReplayPush          pshs      d,x
                    tst       <replaylimit
                    beq       ReplayDisabled
                    clra
                    ldb       <replaylimit
                    lslb
                    rola
                    cmpd      <replayused
                    bls       ReplayOverflow
                    ldu       <resourcebase
                    leax      replaybuffer,u
                    ldd       <replayused
                    leax      d,x
                    ldd       ,s
                    std       ,x
                    ldd       <replayused
                    addd      #2
                    std       <replayused
                    puls      d,x
                    andcc     #$FE
                    rts
ReplayDisabled      puls      d,x
                    andcc     #$FE
                    rts
ReplayOverflow      puls      d,x
                    ldb       #E$MemFul
                    orcc      #1
                    rts
ReplaySaveCheckpoint    ldd       <replayused
                    std       <replaycheckpoint
                    clrb
                    rts
ReplayRestore       ldd       <replaycheckpoint
                    cmpd      <replayused
                    bhi       ReplayInvalid
                    std       <replayused
                    clrb
                    rts
ReplayInvalid       ldb       #E$BMode
                    orcc      #1
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_REPLAY_DATA
* ===== wildbits-replay-data =====
* Replay records store resource operations for eventual save/restore.
* Private control state; the owner supplies a 510-byte record buffer.
replaylimit         rmb       1
replayused          rmb       2
replaycheckpoint    rmb       2

                    else
                    error Unknown platform feature section
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
