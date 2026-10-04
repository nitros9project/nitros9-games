* F8 scanline flood fill. Bounded 2048-seed private work stack, not the CPU S.
* Match color white when color is enabled; otherwise priority 4 when only
* priority is enabled. Both enabled still match color, as in CoCo SbuffPicFill.
PicFill             lbsr      ReadXyPos
                    bcs       FillCommandRet
                    std       <PosInitX
                    lbsr      SbuffPicFill
                    bra       PicFill
FillCommandRet      rts
SbuffPicFill        pshs      x
                    lda       <DrawMask
                    lbeq      FillDone
                    cmpa      #$F0
                    bne       FillColor
                    lda       <DrawColor
                    anda      #$F0
                    cmpa      #$40
                    lbeq      FillDone
                    lda       #$F0
                    ldb       #$40
                    bra       FillBegin
FillColor           lda       <DrawColor
                    anda      #$0F
                    cmpa      #$0F
                    lbeq      FillDone
                    lda       #$0F
                    ldb       #$0F
FillBegin           sta       <fillmask
                    stb       <filltarget
                    clr       <filltop
                    clr       <filltop+1
                    ldd       <PosInitX
                    lbsr      FillPush
FillPop             tst       <decodeerror
                    lbne      FillDone
                    ldd       <filltop
                    lbeq      FillDone
                    subd      #2
                    std       <filltop
                    ldu       <resourcebase
                    leau      fillstack,u
                    leau      d,u
                    ldd       ,u
                    std       <fillx
                    lbsr      FillMatch
                    bne       FillPop
                    lda       <fillx
                    sta       <fillleft
FillSeekLeft        tst       <fillx
                    beq       FillLeftFound
                    dec       <fillx
                    lbsr      FillMatch
                    bne       FillLeftFound
                    lda       <fillx
                    sta       <fillleft
                    bra       FillSeekLeft
FillLeftFound       lda       <fillleft
                    sta       <fillx
FillPaintSpan       ldd       <fillx
                    std       <PosInitX
                    lbsr      SbuffPlot
                    lda       <fillx
                    sta       <fillright
                    cmpa      #159
                    beq       FillSpanDone
                    inc       <fillx
                    lbsr      FillMatch
                    beq       FillPaintSpan
FillSpanDone        clr       <filldirection
FillNeighborRow     lda       <filly
                    tst       <filldirection
                    bne       FillBelow
                    tsta
                    beq       FillNextDirection
                    deca
                    bra       FillScanBegin
FillBelow           cmpa      #167
                    beq       FillNextDirection
                    inca
FillScanBegin       sta       <fillneighbor
                    clr       <fillrun
                    lda       <fillleft
                    sta       <fillx
FillScanRun         pshs      b
                    ldb       <filly
                    pshs      b
                    ldb       <fillneighbor
                    stb       <filly
                    lbsr      FillMatch
                    pshs      cc
                    ldb       1,s
                    stb       <filly
                    puls      cc
                    leas      1,s
                    puls      b
                    bne       FillRunEnd
                    tst       <fillrun
                    bne       FillScanNext
                    inc       <fillrun
                    lda       <fillx
                    ldb       <fillneighbor
                    lbsr      FillPush
                    bra       FillScanNext
FillRunEnd          clr       <fillrun
FillScanNext        lda       <fillx
                    cmpa      <fillright
                    beq       FillNextDirection
                    inc       <fillx
                    bra       FillScanRun
FillNextDirection   inc       <filldirection
                    lda       <filldirection
                    cmpa      #2
                    blo       FillNeighborRow
                    lbra      FillPop
FillDone            puls      x,pc
FillPush            pshs      d
                    ldd       <filltop
                    cmpd      #4096
                    bhs       FillOverflow
                    ldu       <resourcebase
                    leau      fillstack,u
                    leau      d,u
                    addd      #2
                    std       <filltop
                    puls      d
                    std       ,u
                    rts
FillOverflow        ldb       #E$MemFul
                    stb       <decodeerror
                    puls      d,pc
FillMatch           pshs      d,x,y,u
                    ldb       <filly
                    lda       #160
                    mul
                    addb      <fillx
                    adca      #0
                    lbsr      PicturePointer
                    tst       <decodeerror
                    bne       FillNotMatch
                    lda       ,u
                    anda      <fillmask
                    cmpa      <filltarget
                    puls      d,x,y,u,pc
FillNotMatch        andcc     #$FB
                    puls      d,x,y,u,pc
