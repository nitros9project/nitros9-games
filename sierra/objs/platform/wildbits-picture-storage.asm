* Native mapped line/plot primitives. No direct mapped-pointer increments
* survive an 8K crossing; PicturePointer caches the current physical page.
SbuffXLine          sta       <ScratchAC
                    cmpa      <PosInitX
                    bhs       XLineStart
                    ldb       <PosInitX
                    stb       <PosFinalX
                    sta       <PosInitX
XLineStart          lbsr      SbuffPlot
                    lda       <PosInitX
                    cmpa      <PosFinalX
                    beq       XLineDone
                    inc       <PosInitX
                    bra       XLineStart
XLineDone           lda       <ScratchAC
                    sta       <PosInitX
                    rts
SbuffYLine          stb       <ScratchAC
                    cmpb      <PosInitY
                    bhs       YLineStart
                    lda       <PosInitY
                    sta       <PosFinalY
                    stb       <PosInitY
YLineStart          lbsr      SbuffPlot
                    ldb       <PosInitY
                    cmpb      <PosFinalY
                    beq       YLineDone
                    inc       <PosInitY
                    bra       YLineStart
YLineDone           ldb       <ScratchAC
                    stb       <PosInitY
                    rts
SbuffPlot           pshs      d,x,y,u
                    ldb       <PosInitY
                    lda       #160
                    mul
                    addb      <PosInitX
                    adca      #0
                    lbsr      PicturePointer
                    tst       <decodeerror
                    bne       PlotDone
                    lda       ,u
                    ora       <DrawMask
                    anda      <DrawColor
                    sta       ,u
PlotDone            puls      d,x,y,u,pc
