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
TextFastOccupied    clr       textglyphrow,x
TextFastGlyphRow    lda       textrow,x
                    ldb       #40
                    mul
                    std       textindex,x
                    clr       textcolumn,x
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
                    cmpa      #40
                    blo       TextFastCell
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
                    std       textindex,x
                    ldd       #320
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
