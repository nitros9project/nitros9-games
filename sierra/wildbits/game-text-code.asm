GameTextInitialize  ldu       <resourcebase
                    leax      textcharacters,u
                    ldy       #1000
GameTextClear       clr       ,x+
                    leay      -1,y
                    bne       GameTextClear
                    rts

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
* Formatting directives require a bounded formatter, not literal rendering.
GameTextValidate    lda       ,x+
                    beq       GameTextStore
                    cmpa      #'%
                    lbeq      GameTextNeedsFormatter
                    bra       GameTextValidate
GameTextStore       ldx       textpointer,u
                    lda       ,x+
                    stx       textpointer,u
                    tsta
                    beq       GameTextPresent
                    cmpa      #10
                    beq       GameTextNewline
                    cmpa      #13
                    beq       GameTextNewline
                    pshs      a
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
                    blo       GameTextStore
GameTextNewline     clr       textcolumn,u
                    inc       textrow,u
                    lda       textrow,u
                    cmpa      #25
                    blo       GameTextStore
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

GameDrawText        ldx       <resourcebase
                    clr       textindex,x
                    clr       textindex+1,x
                    clr       textrow,x
                    clr       textcolumn,x
                    ldd       #1000
                    std       textend,x
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
