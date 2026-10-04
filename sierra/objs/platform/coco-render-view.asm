* CoCo packed-pixel renderer: render-view.
* Keep optimized loops intact. See ../../PORTABILITY.md.

DrawView            lda       >PicVisible pic_visible
                    lbeq      DrawViewDone skip draw if picture not visible
                    ldu       $02,s     load view structure pointer
                    ldd       $08,u     load block number from view struct
                    lbsr      SetMapBlock map the block for source data
                    ldx       <$10,u    load pointer from view struct offset $10
                    ldd       ,x        load word at that pointer (view width)
                    std       <RowStride save as row stride
                    ldd       <$14,u    load block number from view+$14
                    lbsr      SetMapBlock map the second block
                    ldx       <$12,u    load pointer from view struct offset $12
                    ldd       ,x        load word at that pointer (view height)
                    std       <RowCount save as row count
                    ldd       <$10,u    reload view+$10
                    std       <$12,u    update view+$12 with it
                    ldd       $08,u     reload view block number
                    std       <$14,u    update view+$14 with it
                    lda       $04,u     load view X position
                    ldb       <ViewRightX load right-edge clip X
                    cmpa      <$1B,u    compare X with view's prev X
                    bcs       ClipXSmall branch if cur X < prev X
                    sta       <ClipLeft save X as left clip boundary
                    stb       <ClipRight save right-edge as clip right
                    lda       <$1B,u    load previous X
                    ldb       <StripWidth load strip pixel width
                    bra       ComputeClipWidth
ClipXSmall          ldb       <$1B,u    load previous X as left clip
                    stb       <ClipLeft save as left boundary
                    ldb       <StripWidth load strip width
                    stb       <ClipRight save as right boundary
                    ldb       <ViewRightX load right-edge X
ComputeClipWidth    stb       <OverlapLeft save overlap left boundary
                    inca                A = cur X + 1
                    suba      <OverlapLeft A = overlap width candidate
                    ldb       <ClipLeft load clip left
                    incb                B = ClipLeft + 1
                    subb      <ClipRight B = clip width
                    stb       <ClipWidth save clip width
                    cmpa      <ClipWidth compare overlap vs clip width
                    bcs       AdjustClipWidth use clip width if overlap is smaller
                    lda       <ClipWidth use clip width as limit
AdjustClipWidth     nega                negate to invert
                    adda      <ClipLeft A = ClipLeft - overlap width
                    inca                adjust for final right clip
                    sta       <ClipRight save computed clip right
                    lda       $03,u     load view Y position
                    ldb       <RowStride load row stride
                    cmpa      <$1A,u    compare Y with view's prev Y
                    bhi       ClipYGreater branch if cur Y > prev Y
                    sta       <DrawY1   save Y as top of draw region
                    stb       <OverlapTop save row stride as overlap top
                    lda       <$1A,u    load previous Y
                    ldb       <RowCount load row count
                    bra       ComputeClipHeight
ClipYGreater        ldb       <$1A,u    load previous Y as draw start
                    stb       <DrawY1   save as top of draw region
                    ldb       <RowCount load row count
                    stb       <OverlapTop save as overlap top
                    ldb       <RowStride load row stride
ComputeClipHeight   stb       <OverlapSize save overlap size
                    adda      <OverlapSize A = Y + overlap = bottom extent
                    sta       <ClipBottom save as clip bottom
                    lda       <DrawY1   load draw start Y
                    adda      <OverlapTop add overlap top to get draw bottom
                    cmpa      <ClipBottom compare against clip bottom
                    bhi       SetupDrawCall use draw bottom if it exceeds clip
                    lda       <ClipBottom use clip bottom as limit
SetupDrawCall       suba      <DrawY1   height = bottom - top
                    sta       <ClipHeight save computed clip height
                    ldd       <ClipRight load clip right/left pair
                    pshs      b,a       push column args for DrawStrip
                    ldd       <DrawY1   load draw Y start / clip height
                    pshs      b,a       push row args for DrawStrip
                    lbsr      DrawStrip render clipped view to screen
                    leas      $04,s     pop 4 bytes of args
DrawViewDone        rts

* This jumbled mass of bytes disassembles
* but looks like a data block
* or probably a bit map ???
* BitmapFont - DrawSprites is 1024 bytes of data
