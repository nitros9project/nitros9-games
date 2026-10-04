* CoCo packed-pixel renderer: render-spans.
* Keep optimized loops intact. See ../../PORTABILITY.md.

CocoViewPal         fcb       $00
                    fcb       $11
                    fcb       $22
                    fcb       $33
                    fcb       $44
                    fcb       $55
                    fcb       $66
                    fcb       $77
                    fcb       $88
                    fcb       $99
                    fcb       $AA
                    fcb       $BB
                    fcb       $CC
                    fcb       $DD
                    fcb       $EE
                    fcb       $FF


* Clears the area allocated to the screen in sierra
* entry:
*      d -> value to be written to screen
*      x -> may contain a value so we save it
* exit:
*      d -> preserved
*      x -> restored to initial value
*      u -> contains starting address of the screen

ClearScreen         pshs      x         save the x values as this routine uses it
ClearScreenInit     ldu       #CocoFrameEnd    end address of high res screen
                    ldx       #CocoFrameBytes    Scrn is from $6000 to $D800
ClearWordLoop       std       ,--u      set it to value passed us in d & dec d
                    leax      -$02,x    decrement x
                    bne       ClearWordLoop keep going till all of screen is cleared
                    puls      x         restore x`
                    rts                 move on

* Loads D to clear screen
ZeroClearScreen     ldd       #$0000    zeros screen bytes
                    bsr       ClearScreen go clear it
                    rts

ClearScreenBlack    bsr       ZeroClearScreen clear screen to black
                    ldd       #$A8A0    Y2=$A8, Y1=$A0 (screen rows)
                    pshs      d         push row args onto stack
                    ldd       #$00A7    X2=$00, X1=$A7 (screen columns)
                    pshs      d         push column args onto stack
                    lbsr      DrawStrip
                    leas      $04,s     pop 4 bytes of args
                    rts

ClearWithPalette    lda       >SierraPalette load palette color byte
                    tfr       a,b       duplicate into both bytes of D
                    bsr       ClearScreen fill screen with that color word
                    ldd       #$0000    clears value at SprCurRow
                    std       <SprCurRow reset sprite row/col position
                    rts

DrawBorder          ldd       $06,s     load top-left row arg
                    pshs      d         push row start
                    ldd       $06,s     reload arg (stack shifted)
                    pshs      d         push row end
                    ldd       $06,s     reload arg (stack shifted)
                    pshs      d         push color arg
                    lbsr      FillSolidRect draw top edge
                    leas      $06,s     pop 6 bytes of args
                    clra                A=0 for column start
                    ldb       $06,s     load height arg
                    pshs      d         push row params
                    lda       #$01      col start = 1
                    ldb       $07,s     load height (stack adjusted)
                    subb      #$02      subtract 2 to skip top/bottom
                    pshs      d         push height-2
                    ldd       $06,s     load position arg
                    inca                advance row by 1
                    decb                reduce column by 1
                    pshs      d         push adjusted position
                    lbsr      FillSolidRect draw left edge
                    leas      $06,s     pop 6 bytes of args
                    clra                A=0 for column start
                    ldb       $06,s     load next arg
                    pshs      d         push row
                    lda       $06,s     load X position
                    suba      #$04      subtract 4 for right edge position
                    ldb       #$01      column width = 1
                    pshs      d         push right edge position
                    ldd       $06,s     load base position
                    adda      $09,s     add height to get bottom
                    suba      #$02      adjust for edges
                    subb      #$02      adjust column
                    pshs      d         push bottom position
                    lbsr      FillSolidRect draw right edge
                    leas      $06,s     pop 6 bytes of args
                    clra                A=0
                    ldb       $06,s     load arg
                    pshs      d
                    lda       #$01      col start = 1
                    ldb       $07,s
                    subb      #$02      height - 2
                    pshs      d
                    ldd       $06,s
                    inca                advance row
                    subb      $08,s     subtract width
                    addb      #$02      adjust for border
                    pshs      d
                    lbsr      FillSolidRect draw bottom-left corner edge
                    leas      $06,s     pop 6 bytes of args
                    clra
                    ldb       $06,s
                    pshs      d
                    lda       $06,s
                    suba      #$04
                    ldb       #$01
                    pshs      d
                    ldd       $06,s
                    inca
                    subb      #$02
                    pshs      d
                    lbsr      FillSolidRect draw bottom edge
                    leas      $06,s     pop 6 bytes of args
                    rts

SetupDrawStrip      ldd       $04,s     load row args from caller's frame
                    pshs      d         push first arg
                    ldd       $04,s     reload same arg (stack shifted)
                    pshs      d         push second arg
                    lbsr      DrawStrip
                    leas      $04,s     pop 4 bytes of args
                    rts

* first call in module is here
* who put what on the stack for us ?
DrawStrip           pshs      y         save Y (module entry absolute address)

                    ldd       $04,s     load row/column args
                    sta       <ScrAddrLo save row as screen address low byte
                    incb                B = bottom row + 1
                    subb      $06,s     B = height of strip in rows
                    lda       #CocoFrameStride A = 160 (bytes per screen row)
                    mul                 D = height × 160
                    addd      <ScrAddrHi add hi-res screen high byte
                    tfr       d,x       X = source pixel address
                    addd      <HiResBase add screen base offset
                    tfr       d,y       Y = destination screen address
                    leax      <$40,x    advance X by $40 (source offset)
                    ldd       $06,s     load strip dimension
                    std       <RowCount save row count and strip width

                    ldb       #CocoFrameStride B = 160 (full row width)
                    subb      <StripWidth B = stride = 160 - strip pixel width
                    clra                clear A for full D
                    std       <RowStride save row stride
                    sta       <MmuBlkNum clear MMU block tracking variable

                    orcc      #IntMasks disable interrupts
                    lda       <SierraPdBlk load Sierra process descriptor block#
                    sta       >DatTask1Slot1 second block in task 1
                    cmpx      #$A000    check if X is in high 8K window
                    bcs       MapBlockLow branch if X < $A000 (low window)

                    ldd       <BlkMapHigh load high-address block map entry
                    leax      >-$8000,x adjust X for high window (-$8000)
                    bra       MapBlockAndRender
MapBlockLow         ldd       <BlkMapLow load low-address block map entry
                    leax      >-$4000,x adjust X for low window (-$4000)
MapBlockAndRender   ldu       <Sierra2ndBlk load Sierra 2nd 8K data block ptr
                    sta       ,u        store block A at slot 0
                    stb       $02,u     store block B at slot 2
                    std       >DatTask1Slot1 map block into task 1
                    andcc     #^IntMasks re-enable interrupts

                    leau      >CocoViewPal,pcr point U to CoCo view palette table
DrawRowOuter        ldb       <StripWidth load pixel count for this row
DrawPixelInner      lda       ,x+       fetch source pixel byte, advance X
                    anda      #$0F      mask to 4-bit palette index
                    lda       a,u       translate through CoCo palette
                    sta       ,y+       write translated pixel, advance Y
                    decb                one fewer pixel this row
                    bne       DrawPixelInner loop until row complete
                    dec       <RowCount one fewer row remaining
                    beq       DrawStripDone pull our y and exit routine
                    ldd       <RowStride load row stride
                    leay      d,y       advance Y to next screen row
                    abx                 advance X by B (stride)
                    cmpx      #CocoFrameBase    check if X wrapped below screen base
                    bcs       DrawRowOuter branch if still in range

                    orcc      #IntMasks disable interrupts for block remap
                    lda       <SierraPdBlk reload Sierra PD block#
                    sta       >DatTask1Slot1 second block in task 1
                    ldd       <BlkMapHigh load high block map for remap
                    leax      >-$4000,x adjust X by -$4000 for new window
                    bra       MapBlockAndRender remap and continue rendering
DrawStripDone       puls      y         restore Y
                    rts


FillSolidRect       ldd       $02,s     load row/column args from stack
                    sta       <ScrAddrLo save row as screen address low
                    incb                B = bottom row + 1
                    subb      $04,s     B = strip height
                    lda       #CocoFrameStride A = 160
                    mul                 D = height × 160
                    addd      <ScrAddrHi Hi res screen mem address ($6000)
                    addd      <HiResBase add base screen offset
                    tfr       d,x       X = starting screen address
                    ldd       $04,s     load dimension arg
                    std       <RowCount save row count / strip width
                    ldb       #CocoFrameStride B = 160
                    subb      <StripWidth B = stride = 160 - strip width
                    stb       <RowStride save row stride
                    leau      >CocoViewPal,pcr point U to CoCo palette table
                    lda       $07,s     load fill color index
                    anda      #$0F      mask to 4-bit palette index
                    lda       a,u       look up translated fill color

FillRowOuter        ldb       <StripWidth pixels to fill in this row
FillPixelInner      sta       ,x+       write fill color, advance X
                    decb                one fewer pixel this row
                    bne       FillPixelInner loop until row filled

                    dec       <RowCount one fewer row remaining
                    beq       FillRectDone done when all rows filled
                    ldb       <RowStride load row stride
                    abx                 advance X to next row
                    bra       FillRowOuter fill next row
FillRectDone        rts


CopyStrip           leas      -$04,s    allocate 4 scratch bytes on stack
                    ldd       $0A,s     load destination arg (shifted by alloc)
                    std       $02,s     stash destination in scratch[2]
                    ldd       $08,s     load source arg
                    std       ,s        stash source in scratch[0]
                    lda       $07,s     load destination row
                    lsla                row × 2
                    lsla                row × 4
                    lsla                row × 8
                    ldb       #CocoFrameStride B = 160
                    mul                 D = row × 8 × 160 = row × 1280
                    std       <DrawY1   save Y pixel offset for destination
                    clra                clear A
                    ldb       $01,s     load scratch[1]
                    lslb                × 2
                    lslb                × 4 (column × 4 bytes per glyph col)
                    addd      <DrawY1   add Y offset to screen address
                    tfr       d,u       transfer result to U (source pointer)
                    leau      >CocoFrameBase,u  add screen base $6000
                    ldb       $02,s     load scratch[2]
                    lslb                × 2
                    lslb                × 4
                    lslb                × 8 (source col × 8)
                    lda       #CocoFrameStride A = 160
                    mul                 D = source col × 8 × 160
                    leax      d,u       X = source screen address
                    lda       $03,s     load source row
                    lsla
                    lsla
                    lsla                source row × 8
                    ldb       ,s        load scratch[0] (src col)
                    subb      $01,s     subtract scratch[1] (dest col)
                    incb                +1 for pixel width
                    lslb                × 2
                    lslb                × 4
                    abx                 advance X by col delta
                    exg       u,x       swap src/dst pointers
                    abx                 advance X (was U) by col delta
                    exg       u,x       swap back
CopyRowOuter        pshs      u,x,b,a   save pointers, col count, row count
CopyPixelInner      lda       ,-x       read source pixel (reverse scan)
                    sta       ,-u       write to destination (reverse scan)
                    decb                step back one pixel
                    bne       CopyPixelInner loop until col count zero
                    puls      u,x,b,a   restore pointers and counts
                    leau      >$00A0,u  advance U to next source row
                    leax      >$00A0,x  advance X to next dest row
                    cmpx      #CocoFrameEnd    check if X reached screen end
                    bcc       CopyStripDone done if past end of screen
                    deca                one fewer row
                    bne       CopyRowOuter loop while rows remain
CopyStripDone       leas      $04,s     free scratch bytes
                    rts
