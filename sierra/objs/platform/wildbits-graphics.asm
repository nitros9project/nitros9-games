* wildbits-graphics feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_DECODER_DATA
* ===== wildbits-decoder-data =====
* Private state for the mapped picture decoder; include before resource-data.
DrawColor           rmb       1
DrawMask            rmb       1
PosInitX            rmb       1
PosInitY            rmb       1
PosFinalX           rmb       1
PosFinalY           rmb       1
ScratchA2           rmb       1
ScratchA3           rmb       1
ScratchA4           rmb       1
ScratchA5           rmb       1
ScratchA6           rmb       1
ScratchA7           rmb       1
ScratchA8           rmb       1
ScratchA9           rmb       1
ScratchAA           rmb       1
ScratchAB           rmb       1
ScratchAC           rmb       1
ScratchAD           rmb       2
PenStatus           rmb       1
picturefirst        rmb       2
pictureowned        rmb       1
picturemapped       rmb       1
picturepage         rmb       1
picturemapbase      rmb       2
pictureoffset       rmb       2
pictureoutoffset    rmb       2
picturechunk        rmb       2
pictureexiterror    rmb       1
filltop             rmb       2
fillmask            rmb       1
filltarget          rmb       1
fillx               rmb       1
filly               rmb       1
fillleft            rmb       1
fillright           rmb       1
fillneighbor        rmb       1
fillrun             rmb       1
filldirection       rmb       1
decodeend           rmb       2
decodeerror         rmb       1
decodevalue         rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_DECODER_FILL
* ===== wildbits-decoder-fill =====
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

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_DECODER_LINES
* ===== wildbits-decoder-lines =====
* Picture command algorithms are assembled by both CoCo and Wild Bits.
                    use       shared/picture-colors.asm
                    use       shared/picture-commands.asm
                    use       shared/picture-coordinates.asm
                    use       shared/picture-line.asm
* Assembly-time platform selection.
* Shared line/pen entry: SbuffPlot uses PosInitX/Y and DrawColor/Mask in DP.
* Wild Bits preserves D,X,Y,U and reports mapped-access errors in decodeerror.
* CoCo retains its contiguous-buffer pointer result and optimized span loops.
                    ifne      WILDBITS
                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_PICTURE_STORAGE
                    use platform/wildbits-graphics.asm
                    else
PLATFORM_SECTION    set PLATFORM_COCO_PICTURE_STORAGE
                    use platform/coco-graphics.asm
                    endc

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_DECODER_PEN
* ===== wildbits-decoder-pen =====
* Native F9/FA handlers. CoCo pen geometry and texture sequence retained.
* Command X is private; tables are immutable PCR-relative data.
ReadPenStatus       lbsr      ReadNext
                    cmpa      #cmd_start
                    lbhs      DecodeInvalid
                    sta       <PenStatus
                    lbsr      ReadNext
                    rts
PlotWithPen         lda       <PenStatus
                    bita      #$20
                    beq       PenSolidPosition
                    lbsr      ReadNext
                    cmpa      #cmd_start
                    bhs       PenCommandRet
                    sta       <ScratchA6
                    lbsr      ReadInitialPos
                    bra       PenPositionReady
PenSolidPosition    lbsr      ReadXyPos
PenPositionReady    bcs       PenCommandRet
                    std       <ScratchA2
                    pshs      x
                    lbsr      PlotWithPen2
                    puls      x
                    bra       PlotWithPen
PenCommandRet       rts

                    use       shared/picture-pen.asm
                    use       shared/picture-pen-tables.asm

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_FONT_CODE
* ===== wildbits-font-code =====
* Load the canonical font from the execution directory once per process.
* Keeping immutable font bytes out of the program avoids an extra code block.
GameFontLoad        leax      GameFontName,pcr
                    lda       #READ.+EXEC.
                    os9       I$Open
                    lbcs      ResourceFailed
                    sta       <resourcepath
                    inc       <resourceopen
                    ldu       <resourcebase
                    leax      gamefont,u
                    ldy       #1024
                    lbsr      ResourceReadExact
                    lbcs      ResourceFailed
* Reject trailing bytes as well as short fonts.
                    ldu       <resourcebase
                    leax      picturestage,u
                    ldy       #1
                    lda       <resourcepath
                    os9       I$Read
                    lbcc      ResourceInvalid
                    cmpb      #E$EOF
                    lbne      ResourceFailed
                    lbsr      ResourceClose
                    lbcs      ResourceFailed
                    clrb
                    rts
GameFontName        fcc       /wbfont/
                    fcb       C$CR

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_BACKGROUND_CODE
* ===== wildbits-game-background-code =====
* Keep the decoded background separate from the sprite composition buffer.
* Copy through the idle private 8K command workspace; one foreign mapping.
* Decoder/asset loading and modal backup restoration finish before entry.
GameSaveBackground  lbsr      AssetUnmap
                    lbcs      GameBackgroundReturn
                    ldx       <resourcebase
                    tst       gamebackgroundowned,x
                    bne       GameBackgroundAllocated
                    lda       #0
                    ldb       #$D4
                    ldx       #4
                    os9       I$SetStt
                    lbcs      GameBackgroundReturn
                    tfr       x,d
                    ldx       <resourcebase
                    std       gamebackgroundfirst,x
                    inc       gamebackgroundowned,x
GameBackgroundAllocated clr  gamecopydirection,x
                    bra       GameCopyBackground
GameRestoreBackground lbsr   AssetUnmap
                    lbcs      GameBackgroundReturn
                    ldx       <resourcebase
                    tst       gamebackgroundowned,x
                    lbeq      GameBackgroundInvalid
                    tst       gamebackgroundclean,x
                    lbne      GameBackgroundDone
                    lbra      GameRestoreSprites
GameCopyBackground  lbsr      PictureUnmap
                    lbcs      GameBackgroundReturn
                    ldx       <resourcebase
                    ldd       gamebackgroundfirst,x
                    std       <assetfirst
                    lda       #4
                    sta       <assetblocks
                    clr       <assetowned
                    clr       <pictureoutoffset
                    clr       <pictureoutoffset+1
GameBackgroundChunk ldd       #26880
                    subd      <pictureoutoffset
                    lbeq      GameBackgroundDone
                    cmpd      #8192
                    bls       GameBackgroundSize
                    ldd       #8192
GameBackgroundSize  std       <picturechunk
                    tfr       d,y
                    ldd       <pictureoutoffset
                    tst       gamecopydirection,x
                    bne       GameReadBackground
                    lbsr      PicturePointer
                    tst       <decodeerror
                    lbne      GameBackgroundDecodeError
                    bra       GameStageBackground
GameReadBackground  lbsr      AssetPointer
                    tst       <asseterror
                    lbne      GameBackgroundAssetError
GameStageBackground leax      resourcecommands,x
GameBackgroundRead  ldd       ,u++
                    std       ,x++
                    leay      -2,y
                    bne       GameBackgroundRead
                    lbsr      PictureUnmap
                    lbcs      GameBackgroundReturn
                    lbsr      AssetUnmap
                    lbcs      GameBackgroundReturn
                    ldx       <resourcebase
                    ldd       <pictureoutoffset
                    tst       gamecopydirection,x
                    bne       GameWritePicture
                    lbsr      AssetPointer
                    tst       <asseterror
                    lbne      GameBackgroundAssetError
                    bra       GameWriteBackground
GameWritePicture    lbsr      PicturePointer
                    tst       <decodeerror
                    lbne      GameBackgroundDecodeError
GameWriteBackground leax      resourcecommands,x
                    ldy       <picturechunk
GameBackgroundWrite ldd       ,x++
                    std       ,u++
                    leay      -2,y
                    bne       GameBackgroundWrite
                    lbsr      PictureUnmap
                    bcs       GameBackgroundReturn
                    lbsr      AssetUnmap
                    bcs       GameBackgroundReturn
                    ldd       <pictureoutoffset
                    addd      <picturechunk
                    std       <pictureoutoffset
                    ldx       <resourcebase
                    lbra      GameBackgroundChunk
GameBackgroundDone  ldx       <resourcebase
                    lbsr      GameForgetSprites
                    lda       #1
                    sta       gamebackgroundclean,x
                    ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    clrb
GameBackgroundReturn rts
GameBackgroundInvalid ldb     #E$BMode
                    orcc      #1
                    rts
GameBackgroundDecodeError ldb <decodeerror
                    orcc      #1
                    rts
GameBackgroundAssetError ldb  <asseterror
                    orcc      #1
                    rts
GameReleaseBackground lbsr   PictureUnmap
                    bcs       GameBackgroundReturn
                    lbsr      AssetUnmap
                    bcs       GameBackgroundReturn
                    ldx       <resourcebase
                    tst       gamebackgroundowned,x
                    beq       GameBackgroundDone
                    ldx       gamebackgroundfirst,x
                    ldu       #4
                    lda       #0
                    ldb       #$D5
                    os9       I$SetStt
                    bcs       GameBackgroundReturn
                    ldx       <resourcebase
                    clr       gamebackgroundowned,x
                    clrb
                    rts

                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_SPRITE_BACKGROUND
                    use platform/wildbits-graphics.asm

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_PICTURE_CODE
* ===== wildbits-game-picture-code =====
* Native game picture commands. The instruction stream is restored after
* copying picture commands into private decoder workspace. Combined pixels,
* resource slabs and framebuffers never have simultaneous mappings.
GamePictureArgument ldu       <resourcebase
                    leax      vmvariables,u
                    ldb       vmarguments,u
                    clra
                    ldb       d,x
                    lda       #1
                    lbsr      VmLoadResource
                    rts
GameLoadPicture     lbsr      GamePictureArgument
                    bcs       GamePictureReturn
                    ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    clrb
GamePictureReturn   rts
GameDiscardPicture  ldu       <resourcebase
                    leax      vmvariables,u
                    ldb       vmarguments,u
                    clra
                    ldb       d,x
                    lda       #1
                    lbra      VmDiscardResource
GameDrawPicture     lbsr      GamePictureArgument
                    bcs       GamePictureReturn
                    lbsr      VmRestoreAsset
                    ldd       <resourcelength
                    std       <gamepicturelength
                    lbsr      AssetUnmap
                    bcs       GamePictureReturn
                    lbsr      PictureRelease
                    bcs       GamePictureReturn
                    ldu       <resourcebase
                    ldx       #0                logical input offset, not a mapped pointer
                    ldy       <gamepicturelength
                    lbsr      DecodeLines
                    bcs       GamePictureReturn
                    ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    lbsr      PictureUnmap
                    lbcs      GamePictureReturn
                    lbsr      GameTextClearPicture
                    lbsr      GameDamageAll
                    ldx       <resourcebase
                    tst       gamebackgroundowned,x
                    lbne      GameSaveBackground
                    clrb
                    rts
GamePictureAssetError ldb      <asseterror
                    orcc      #1
                    rts
GamePictureInvalid  ldb       #E$BMode
                    orcc      #1
                    rts
* Refill the private 8-KiB input chunk only at logical page boundaries.
* The picture mapping is released before mapping its source slab; plotting
* resumes with source unmapped. No command pointer survives an OS mapping.
GameReadPictureChunk pshs    d,x,y,u
                    tfr       x,d
                    std       <resourcepointer
                    ldd       <decodeend
                    subd      <resourcepointer
                    cmpd      #8192
                    bls       GamePictureChunkSize
                    ldd       #8192
GamePictureChunkSize std     <resourceremaining
                    lbsr      PictureUnmap
                    bcs       GamePictureChunkError
                    ldd       <resourcepointer
                    lbsr      AssetPointer
                    ldb       <asseterror
                    bne       GamePictureChunkError
                    ldx       <resourcebase
                    leax      resourcecommands,x
                    ldy       <resourceremaining
GamePictureChunkCopy lda     ,u+
                    sta       ,x+
                    leay      -1,y
                    bne       GamePictureChunkCopy
                    lbsr      AssetUnmap
                    bcs       GamePictureChunkError
                    puls      d,x,y,u,pc
GamePictureChunkError stb     <decodeerror
                    puls      d,x,y,u,pc

GameShowPicture     lbsr      GameCloseWindow
                    lbcs      GamePictureReturn
                    lbsr      AssetUnmap
                    lbcs      GamePictureReturn
                    tst       <pictureowned
                    beq       GamePictureInvalid
                    lbsr      PresentPicture
                    rts

* Static cels become part of the saved picture, rather than animated objects.
* The temporary 43-byte object record and resolved operands live on the stack.
GameAddToPicture    leas      -50,s
                    leax      ,s
                    ldu       <resourcebase
                    leay      vmarguments,u
                    ldb       #7
                    pshs      b
AddPicArguments     ldb       ,y+
                    lda       <vmopcode
                    cmpa      #123
                    bne       AddPicArgumentReady
                    clra
                    pshs      x
                    leax      vmvariables,u
                    ldb       d,x
                    puls      x
AddPicArgumentReady stb       ,x+
                    dec       ,s
                    bne       AddPicArguments
                    leas      1,s
                    lda       4,s
                    cmpa      #168
                    lbhs      AddPicInvalid
                    lda       6,s
                    cmpa      #15
                    lbhi      AddPicInvalid
                    ldd       #$0500
                    lbsr      ReplayPush
                    lbcs      AddPicReturn
                    ldd       ,s
                    lbsr      ReplayPush
                    lbcs      AddPicReturn
                    ldd       2,s
                    lbsr      ReplayPush
                    lbcs      AddPicReturn
                    lda       6,s
                    lsla
                    lsla
                    lsla
                    lsla
                    ora       5,s
                    tfr       a,b
                    lda       4,s
                    lbsr      ReplayPush
                    lbcs      AddPicReturn
                    leax      7,s
                    ldb       #43
AddPicClearRecord   clr       ,x+
                    decb
                    bne       AddPicClearRecord
                    leax      7,s
                    lda       #$FF
                    sta       2,x               decoration must not publish ego flags
                    stx       <viewobject
                    lda       ,s
                    sta       5,x
                    lda       1,s
                    sta       $0A,x
                    lda       2,s
                    sta       $0E,x
                    ldd       3,s
                    std       3,x
                    lda       #8                ignore horizon for static decoration
                    sta       $26,x
                    lbsr      ViewSelect
                    lbcs      AddPicReturn
                    leau      7,s
                    lda       5,s
                    cmpa      #15
                    lbhi      AddPicInvalid
                    sta       $24,u
                    bne       AddPicPriorityReady
                    lbsr      SpriteCalculatePriority
AddPicPriorityReady ldx      <resourcebase
                    tst       gamebackgroundowned,x
                    beq       AddPicRender
                    lbsr      GameRestoreBackground
                    lbcs      AddPicReturn
AddPicRender        leau      7,s
                    lbsr      SpriteRenderObject
                    lbcs      AddPicReturn
                    lda       6,s
                    cmpa      #3
                    bhi       AddPicSaveBackground
                    leau      7,s
                    lbsr      AddPicControlBox
                    lbcs      AddPicReturn
AddPicSaveBackground lbsr    GameSaveBackground
                    lbcs      AddPicReturn
                    lbsr      GameComposeScene
AddPicReturn        leas      50,s
                    rts
AddPicInvalid       ldb       #E$IllArg
                    orcc      #1
                    bra       AddPicReturn

* U=clipped cel record, A=control priority. Stamp only the box perimeter,
* up to the beginning of the baseline's default-priority band or cel top.
AddPicControlBox    lsla
                    lsla
                    lsla
                    lsla
                    ora       #$0F
                    ldb       <DrawColor
                    pshs      b
                    ldb       <DrawMask
                    pshs      b
                    sta       <DrawColor
                    lda       #$F0
                    sta       <DrawMask
                    ldb       4,u
                    cmpb      #48
                    blo       AddPicBoxHeight
                    subb      #48
AddPicBoxBand       cmpb      #12
                    blo       AddPicBoxHeight
                    subb      #12
                    bra       AddPicBoxBand
AddPicBoxHeight     incb
                    cmpb      $1D,u
                    bls       AddPicBoxHeightReady
                    ldb       $1D,u
AddPicBoxHeightReady decb
                    lda       4,u
                    sta       <PosInitY
                    pshs      b
                    suba      ,s+
                    sta       <PosFinalY
                    pshs      a                retain top across line endpoint updates
                    lda       3,u
                    sta       <PosInitX
                    adda      $1C,u
                    deca
                    sta       <PosFinalX
                    lbsr      SbuffXLine
                    lda       3,u
                    sta       <PosInitX
                    lda       ,s
                    sta       <PosInitY
                    lda       <PosFinalX
                    lbsr      SbuffXLine
                    lda       3,u
                    sta       <PosInitX
                    ldb       4,u
                    stb       <PosFinalY
                    lbsr      SbuffYLine
                    lda       <PosFinalX
                    sta       <PosInitX
                    puls      a
                    sta       <PosInitY
                    ldb       4,u
                    lbsr      SbuffYLine
                    puls      d
                    stb       <DrawColor
                    sta       <DrawMask
                    ldb       <decodeerror
                    beq       AddPicBoxReturn
                    orcc      #1
AddPicBoxReturn     rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_PICTURE_DATA
* ===== wildbits-game-picture-data =====
* Transient picture-command staging. Slab ownership remains in the cache.
gamepicturelength   rmb       2

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_RENDER_CODE
* ===== wildbits-game-render-code =====
* Compose views over an immutable background. Sort visible objects by
* priority and baseline Y; equal keys retain object-number order.
GameComposeScene    lbsr      AssetUnmap
                    lbcs      SpriteReturn
                    lbsr      PictureUnmap
                    lbcs      SpriteReturn
                    ldx       <resourcebase
                    clr       spritecount,x
                    clr       spriteid,x
SpriteCollect       ldb       spriteid,x
                    lda       #43
                    mul
                    leau      vmobjects,x
                    leau      d,u
                    lda       $26,u
                    anda      #$41
                    cmpa      #$41
                    bne       SpriteCollectNext
                    stu       spriteobject,x
                    lbsr      SpriteCalculatePriority
                    lda       $24,u
                    ldb       4,u
                    std       spritekey,x
                    ldb       spritecount,x
                    lda       #4
                    mul
                    leay      spritelist,x
                    leay      d,y
SpriteInsert        leau      spritelist,x
                    pshs      u
                    cmpy      ,s++
                    beq       SpriteInsertHere
                    ldd       spritekey,x
                    cmpd      -4,y
                    bhs       SpriteInsertHere
                    ldd       -4,y
                    std       ,y
                    ldd       -2,y
                    std       2,y
                    leay      -4,y
                    bra       SpriteInsert
SpriteInsertHere    ldd       spritekey,x
                    std       ,y
                    ldd       spriteobject,x
                    std       2,y
                    inc       spritecount,x
SpriteCollectNext   inc       spriteid,x
                    ldb       spriteid,x
                    cmpb      #64
                    blo       SpriteCollect
                    tst       gamebackgroundowned,x
                    bne       SpriteRestoreBackground
                    tst       spritecount,x
                    lbeq      SpriteSceneDone
                    lbsr      GameSaveBackground
                    lbcs      SpriteReturn
                    bra       SpriteBackgroundReady
SpriteRestoreBackground lbsr GameRestoreBackground
                    lbcs      SpriteReturn
SpriteBackgroundReady ldx    <resourcebase
                    clr       spriteorder,x
SpriteDrawNext      ldb       spriteorder,x
                    cmpb      spritecount,x
                    bhs       SpriteSceneDone
                    clr       gamebackgroundclean,x
                    lda       #4
                    mul
                    leay      spritelist,x
                    leay      d,y
                    ldu       2,y
                    lbsr      SpriteRenderObject
                    lbcs      SpriteReturn
                    ldx       <resourcebase
                    inc       spriteorder,x
                    bra       SpriteDrawNext
SpriteSceneDone     clrb
SpriteReturn        rts

* Default AGI priority: 4 above row 48; subsequent 12-row bands are 5..14.
SpriteCalculatePriority lda       $26,u
                    bita      #4
                    bne       SpritePriorityDone
                    lda       #4
                    ldb       4,u
                    cmpb      #48
                    blo       SpritePriorityStore
                    lda       #1
SpritePriorityBand  subb      #12
                    bcs       SpritePriorityStore
                    inca
                    bra       SpritePriorityBand
SpritePriorityStore sta       $24,u
SpritePriorityDone  rts

* U=private object record. Read one bounded RLE row into private staging,
* unmap the view, then plot it in the combined buffer. Never map both.
                    ifndef PLATFORM_WILDBITS_OBJECTS_BINDINGS
                    use platform/wildbits-objects-bindings.asm
                    endc
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
SpriteRenderObject  ldx       <resourcebase
                    stu       spriteobject,x
                    OBJECT_SPRITE_VISIBILITY_BEGIN
                    ldb       $1C,u
                    lbeq      SpriteInvalid
                    cmpb      #160
                    lbhi      SpriteInvalid
                    stb       spritewidth,x
                    ldb       $1D,u
                    lbeq      SpriteInvalid
                    cmpb      #168
                    lbhi      SpriteInvalid
                    stb       spriteheight,x
                    ldb       $24,u
                    cmpb      #15
                    lbhi      SpriteInvalid
                    stb       spritepriority,x
                    ldb       $12,u
                    tfr       b,a
                    andb      #$0F
                    stb       spritetransparent,x
                    clr       spritemirror,x
                    bita      #$80
                    beq       SpriteNotMirrored
                    lsra
                    lsra
                    lsra
                    lsra
                    anda      #7
                    cmpa      $0A,u
                    beq       SpriteNotMirrored
                    inc       spritemirror,x
SpriteNotMirrored   clra
                    ldb       4,u
                    subb      spriteheight,x
                    sbca      #0
                    addd      #1
                    std       spriterowy,x
                    ldd       $10,u
                    addd      #3
                    lbcs      SpriteInvalid
                    std       spriteoffset,x
                    ldb       5,u
                    lda       #2
                    lbsr      VmLoadResource
                    lbcs      SpriteReturn
                    lbsr      VmRestoreAsset
                    ldx       <resourcebase
                    clr       spritecachemode,x
                    lda       spritewidth,x
                    ldb       spriteheight,x
                    mul
                    cmpd      #8192
                    bhi       SpriteReadRow
                    inc       spritecachemode,x
                    lda       spriteheight,x
                    sta       spritecacherows,x
                    leay      resourcecommands,x
                    sty       spritecachepointer,x
SpriteReadRow       ldx       <resourcebase
                    leay      spriterow,x
* Plotting and mirroring read only the validated cel width.
                    ldb       spritewidth,x
                    lda       #$FF
SpriteClearRow      sta       ,y+
                    decb
                    bne       SpriteClearRow
                    clr       spritecolumn,x
SpriteReadRun       ldd       spriteoffset,x
                    lbsr      AssetReadByte
                    lbcs      SpriteRestoreLogic
                    pshs      b
                    ldd       spriteoffset,x
                    addd      #1
                    std       spriteoffset,x
                    puls      b
                    tstb
                    beq       SpriteRowReady
                    tfr       b,a
                    andb      #15
                    lbeq      SpriteInvalidRestore
                    stb       spriterun,x
                    addb      spritecolumn,x
                    cmpb      spritewidth,x
                    lbhi      SpriteInvalidRestore
                    lsra
                    lsra
                    lsra
                    lsra
                    sta       spritecolor,x
                    ldb       spritecolumn,x
                    leay      spriterow,x
                    clra
                    leay      d,y
                    lda       spritecolor,x
                    cmpa      spritetransparent,x
                    bne       SpriteOpaqueRun
                    lda       #$FF
SpriteOpaqueRun     sta       ,y+
                    inc       spritecolumn,x
                    dec       spriterun,x
                    bne       SpriteOpaqueRun
                    bra       SpriteReadRun
SpriteRowReady      lda       spritecachemode,x
                    cmpa      #1
                    bne       SpritePlotReady
                    leau      spriterow,x
                    ldy       spritecachepointer,x
                    ldb       spritewidth,x
SpriteCacheStore    lda       ,u+
                    sta       ,y+
                    decb
                    bne       SpriteCacheStore
                    sty       spritecachepointer,x
                    dec       spritecacherows,x
                    lbne      SpriteReadRow
                    inc       spritecachemode,x
                    leay      resourcecommands,x
                    sty       spritecachepointer,x
                    lbsr      AssetUnmap
                    lbcs      SpriteRestoreLogic
                    ldx       <resourcebase
SpriteReadCached    ldu       spritecachepointer,x
                    leay      spriterow,x
                    ldb       spritewidth,x
SpriteCacheRead     lda       ,u+
                    sta       ,y+
                    decb
                    bne       SpriteCacheRead
                    stu       spritecachepointer,x
SpritePlotReady     lbsr      AssetUnmap
                    lbcs      SpriteRestoreLogic
                    ldx       <resourcebase
                    ldd       spriterowy,x
                    cmpd      #168
                    lbhs      SpriteNextRow
                    ldu       spriteobject,x
                    lda       3,u
                    cmpa      #160
                    lbhs      SpriteNextRow
                    ldb       #160
                    subb      3,u
                    cmpb      spritewidth,x
                    bls       SpriteClipWidth
                    ldb       spritewidth,x
SpriteClipWidth     stb       dirtycolumns,x
                    ldb       spriterowy+1,x
                    lda       #160
                    mul
                    addb      3,u
                    adca      #0
                    std       spriterowoffset,x
                    clr       spritecolumn,x
SpritePlotNext      ldb       spritecolumn,x
                    tst       spritemirror,x
                    beq       SpriteSourceColumn
                    ldb       spritewidth,x
                    decb
                    subb      spritecolumn,x
SpriteSourceColumn  leay      spriterow,x
                    lda       b,y
                    cmpa      #$FF
                    lbeq      SpriteNextColumn
                    sta       spritecolor,x
                    ldd       spriterowoffset,x
                    addb      spritecolumn,x
                    adca      #0
                    lbsr      PicturePointer
                    tst       <decodeerror
                    lbne      SpriteDecodeError
                    lda       ,u
                    lsra
                    lsra
                    lsra
                    lsra
                    cmpa      #2
                    bls       SpriteControlPixel
                    cmpa      spritepriority,x
                    bhi       SpriteNextColumn
                    lda       spritepriority,x
                    lsla
                    lsla
                    lsla
                    lsla
                    ora       spritecolor,x
                    sta       ,u
                    OBJECT_SPRITE_VISIBLE_PIXEL
                    bra       SpriteNextColumn
* Priority 15 cannot be occluded by any four-bit picture priority. Avoid
* rescanning down to the bottom for every flag pixel and mapping all pages
* along the way. Keep the original control nibble in the composed buffer.
SpriteControlPixel  lda       spritepriority,x
                    cmpa      #15
                    bne       SpriteControlNeedsSearch
                    lda       ,u
                    anda      #$F0
                    ora       spritecolor,x
                    sta       ,u
                    OBJECT_SPRITE_VISIBLE_PIXEL
                    bra       SpriteNextColumn
SpriteControlNeedsSearch ldd  <pictureoffset
                    pshs      d
SpriteControlSearch addd      #160
                    cmpd      #26880
                    bhs       SpriteControlDraw
                    lbsr      PicturePointer
                    tst       <decodeerror
                    bne       SpriteControlError
                    lda       ,u
                    lsra
                    lsra
                    lsra
                    lsra
                    cmpa      #2
                    bhi       SpriteControlFound
                    ldd       <pictureoffset
                    bra       SpriteControlSearch
SpriteControlFound  cmpa      spritepriority,x
                    bhi       SpriteControlHidden
SpriteControlDraw   ldd       ,s
                    lbsr      PicturePointer
                    tst       <decodeerror
                    bne       SpriteControlRestoreError
                    lda       ,u
                    anda      #$F0
                    ora       spritecolor,x
                    sta       ,u
                    OBJECT_SPRITE_VISIBLE_PIXEL
SpriteControlHidden equ       *
* Search success still has the original-offset word on the stack.
                    leas      2,s
                    bra       SpriteNextColumn
SpriteControlError  equ       *
SpriteControlRestoreError leas 2,s
                    lbra      SpriteDecodeError
SpriteNextColumn    inc       spritecolumn,x
                    ldb       spritecolumn,x
                    cmpb      dirtycolumns,x
                    lblo      SpritePlotNext
SpriteNextRow       lda       spritecachemode,x
                    cmpa      #2
                    beq       SpriteKeepPicture
                    lbsr      PictureUnmap
                    bcs       SpriteRestoreLogic
SpriteKeepPicture   equ       *
                    ldx       <resourcebase
                    ldd       spriterowy,x
                    addd      #1
                    std       spriterowy,x
                    dec       spriteheight,x
                    beq       SpriteRememberDone
                    lda       spritecachemode,x
                    cmpa      #2
                    lbeq      SpriteReadCached
                    lbra      SpriteReadRow
SpriteRememberDone  equ       *
                    lbsr      GameRememberSprite
                    OBJECT_SPRITE_VISIBILITY_FINISH SpriteVisibilityDone,SpriteEgoVisible
SpriteRestoreLogic  pshs      cc,b
                    lbsr      PictureUnmap
                    bcs       SpriteRestoreError
                    lbsr      AssetUnmap
                    bcs       SpriteRestoreError
                    ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    puls      cc,b,pc
SpriteRestoreError  leas      2,s
                    rts
SpriteInvalidRestore ldb      #E$BMode
                    orcc      #1
                    bra       SpriteRestoreLogic
SpriteDecodeError   ldb       <decodeerror
                    orcc      #1
                    bra       SpriteRestoreLogic
SpriteInvalid       ldb       #E$BMode
                    orcc      #1
                    rts

* draw/erase only alter visibility, then recompose all visible objects.
GameObjectVisibility lbsr    ObjectAddress
                    lbcs      SpriteReturn
                    lda       $26,x
                    ldb       <vmopcode
                    cmpb      #36
                    beq       GameHideObject
                    ldd       $10,x
                    lbeq      SpriteInvalid
                    lda       $26,x
                    ora       #$11
                    bra       GameVisibilityStore
GameHideObject      anda      #$FE
GameVisibilityStore sta       $26,x
                    lbra      GameComposeScene

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_RENDER_DATA
* ===== wildbits-game-render-data =====
* Private renderer state outside the direct page. No mapped pointers persist.
gamebackgroundfirst rmb      2
gamebackgroundowned rmb      1
gamebackgroundclean rmb      1
gamecopydirection   rmb      1
dirtyobject         rmb      2
* Erasure finishes before rendering; keep the current row offset in its
* inactive cursor word, without retaining any mapped pointer.
spriterowoffset     equ      dirtyobject
dirtyrows           rmb      1
dirtycolumns        rmb      1
spriteobject        rmb      2
spriteoffset        rmb      2
spritecachepointer  rmb      2
spritecachemode     rmb      1
spritecacherows     rmb      1
spriterowy          rmb      2
spritewidth         rmb      1
spriteheight        rmb      1
spritecolumn        rmb      1
spriterun           rmb      1
spritecolor         rmb      1
spritetransparent   rmb      1
spritemirror        rmb      1
spritepriority      rmb      1
spriteid            rmb      1
spriteorder         rmb      1
spritecount         rmb      1
spritekey           rmb      2
* Collection finishes before any cel draw. The insertion key is dead while
* rendering, which reads only spritelist; reuse its first byte for visibility.
* This storage is private to the process and neither phase runs in an intercept.
spriteinvisible     equ      spritekey
spritelist          rmb      256
spriterow           rmb      160

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_PICTURE_MEMORY
* ===== wildbits-picture-memory =====
* Private combined-picture storage: four owned physical blocks, one mapping.
* SS.GfxAlloc/Free on stdin's terminal: no bitmap, layer or palette is changed.
* Validate stdin's device type before sending a graphics allocation code.
* A startup script may supply RBF stdin; its SetStt is not a graphics service.
PictureAllocate     ldu       <resourcebase
                    leax      picturestage,u
                    lda       #0
                    ldb       #SS.Opt
                    os9       I$GetStt
                    lbcs      PictureError
                    ldu       <resourcebase
                    tst       picturestage,u       SCF device type is zero
                    beq       PictureAllocateSCF
                    ldb       #E$BMode
                    lbra      PictureError
PictureAllocateSCF  lda       #0
                    ldb       #$D4
                    ldx       #4
                    os9       I$SetStt
                    lbcs      PictureError
                    stx       <picturefirst
                    inc       <pictureowned
                    clrb
                    rts
PictureError        stb       <decodeerror
                    orcc      #1
                    rts
PictureUnmap        tst       <picturemapped
                    beq       PictureUnmapped
                    ldu       <picturemapbase
                    ldb       #1
                    os9       F$ClrBlk
                    lbcs      PictureError
                    clr       <picturemapped
PictureUnmapped     clrb
                    rts
PictureRelease      lbsr      PictureUnmap
                    bcs       PictureReleaseRet
                    tst       <pictureowned
                    beq       PictureUnmapped
                    lda       #0
                    ldb       #$D5
                    ldx       <picturefirst
                    ldu       #4
                    os9       I$SetStt
                    lbcs      PictureError
                    clr       <pictureowned
                    clrb
PictureReleaseRet   rts

* D=logical offset. U=pointer for this access only. Preserves X,Y and D.
* No pointer may be retained across another PicturePointer call.
PicturePointer      pshs      d
                    std       <pictureoffset
                    tst       <decodeerror
                    bne       PicturePointerRet
* Cache the encoded 8K page; shift only when a mapping changes.
                    anda      #$E0
                    tst       <picturemapped
                    beq       PictureMap
                    cmpa      <picturepage
                    beq       PictureAddress
PictureMap          pshs      x,y
                    pshs      a
                    lbsr      PictureUnmap
                    puls      a
                    bcs       PictureMapDone
                    sta       <picturepage
                    lsra
                    lsra
                    lsra
                    lsra
                    lsra
                    tfr       a,b
                    clra
                    addd      <picturefirst
                    tfr       d,x
                    ldb       #1
                    os9       F$MapBlk
                    bcs       PictureMapError
                    stu       <picturemapbase
                    inc       <picturemapped
PictureMapDone      puls      x,y
                    bcs       PicturePointerRet
PictureAddress      ldd       <pictureoffset
                    anda      #$1F
                    ldu       <picturemapbase
                    leau      d,u
PicturePointerRet   puls      d,pc
PictureMapError     lbsr      PictureError
                    bra       PictureMapDone
PictureClear        pshs      x
                    ldy       #0
PictureClearPage    tfr       y,d
                    lbsr      PicturePointer
                    tst       <decodeerror
                    bne       PictureClearDone
                    ldx       #4096
                    ldd       #$4F4F
PictureClearWord    std       ,u++
                    leax      -1,x
                    bne       PictureClearWord
                    leay      $2000,y
                    cmpy      #$8000
                    blo       PictureClearPage
PictureClearDone    puls      x,pc

* Export via private staging, never I$Write with a foreign mapping live.
PictureWrite        clr       <pictureoutoffset
                    clr       <pictureoutoffset+1
PictureWriteChunk   ldd       #26880
                    subd      <pictureoutoffset
                    beq       PictureWriteDone
                    cmpd      #512
                    bls       PictureWriteSize
                    ldd       #512
PictureWriteSize    std       <picturechunk
                    tfr       d,y
                    ldd       <pictureoutoffset
                    lbsr      PicturePointer
                    tst       <decodeerror
                    bne       PictureWriteFail
                    ldx       <resourcebase
                    leax      picturestage,x
PictureStageCopy    lda       ,u+
                    sta       ,x+
                    leay      -1,y
                    bne       PictureStageCopy
                    lbsr      PictureUnmap
                    bcs       PictureWriteFail
                    ldx       <resourcebase
                    leax      picturestage,x
                    stx       <resourcepointer
                    ldy       <picturechunk
                    sty       <resourceremaining
PictureStageWrite   lda       #1
                    ldx       <resourcepointer
                    ldy       <resourceremaining
                    os9       I$Write
                    lbcs      PictureError
                    cmpy      #0
                    beq       PictureWriteInvalid
                    cmpy      <resourceremaining
                    bhi       PictureWriteInvalid
                    tfr       y,d
                    addd      <resourcepointer
                    std       <resourcepointer
                    ldd       <resourceremaining
                    pshs      y
                    subd      ,s++
                    std       <resourceremaining
                    bne       PictureStageWrite
                    ldd       <pictureoutoffset
                    addd      <picturechunk
                    std       <pictureoutoffset
                    bra       PictureWriteChunk
PictureWriteDone    clrb
                    rts
PictureWriteInvalid ldb       #E$BMode
                    lbra      PictureError
PictureWriteFail    ldb       <decodeerror
                    orcc      #1
                    rts
DecodeIntercept     cmpb      #S$Abort
                    blo       DecodeSignalRet
                    cmpb      #S$Intrpt
                    bhi       DecodeSignalRet
                    ldb       #E$PrcAbt
                    stb       decodeerror,u
DecodeSignalRet     rti

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_PICTURE_STORAGE
* ===== wildbits-picture-storage =====
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

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_PRESENT_DAMAGE
* ===== wildbits-present-damage =====
* Twenty-one bits track eight-pixel bands of the combined AGI picture.
* Mark both erased footprints and newly painted footprints. First pictures
* and modal restoration force all bands; failed presentations retain damage.
GameDamageAll       ldd       #$00A0
                    lbsr      GameDamageBounds
                    lda       #$FF
                    sta       <gamepresentdirty
                    sta       <gamepresentdirty+1
                    sta       <gamepresentdirty+2
                    rts

* U=clipped saved rectangle (record bytes 6..9). Preserve caller registers.
GameDamageSprite    pshs      d,x,y,u
                    ldb       9,u
                    beq       DamageReturn
                    addb      7,u
                    decb
                    lsrb
                    lsrb
                    lsrb
                    pshs      b
                    lda       7,u
                    lsra
                    lsra
                    lsra
DamageBand          pshs      a
                    tfr       a,b
                    lslb
                    ldy       <dbase
                    leay      gamepresentbounds,y
                    leay      b,y
                    lda       6,u
                    anda      #$FE
                    cmpa      ,y
                    bhs       DamageRight
                    sta       ,y
DamageRight         lda       6,u
                    adda      8,u
                    inca
                    anda      #$FE
                    cmpa      1,y
                    bls       DamageHeight
                    sta       1,y
DamageHeight        puls      a
                    tfr       a,b
                    andb      #7
                    leax      DamageMasks,pcr
                    ldb       b,x
                    pshs      b
                    tfr       a,b
                    lsrb
                    lsrb
                    lsrb
                    ldx       <dbase
                    leax      gamepresentdirty,x
                    leax      b,x
                    ldb       ,x
                    orb       ,s+
                    stb       ,x
                    cmpa      ,s
                    beq       DamageMarked
                    inca
                    bra       DamageBand
DamageMarked        leas      1,s
DamageReturn        puls      d,x,y,u,pc

* A=band index; return zero flag set if no repaint is needed.
GameDamageTest      tfr       a,b
                    andb      #7
                    leax      DamageMasks,pcr
                    ldb       b,x
                    pshs      b
                    lsra
                    lsra
                    lsra
                    ldx       <dbase
                    leax      gamepresentdirty,x
                    lda       a,x
                    anda      ,s+
                    rts
DamageMasks         fcb       1,2,4,8,16,32,64,128

* D=left/right pair for all 21 bands; preserve the caller's X/Y.
GameDamageBounds    pshs      x,y
                    ldx       <dbase
                    leax      gamepresentbounds,x
                    ldy       #21
DamageBoundsNext    std       ,x++
                    leay      -1,y
                    bne       DamageBoundsNext
                    puls      x,y,pc

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_PRESENTATION_BUFFERS
* ===== wildbits-presentation-buffers =====
* Private row staging and terminal names.
                    ifeq      GAME_PRESENTATION
rowinput            rmb       PictureWidth
                    else
* Native presentation uses the idle command staging buffer, not rowinput.
gamepresentbounds   rmb       42
                    endc
rowoutput           rmb       PictureWidth*2
inputname           rmb       32
outputname          rmb       32

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_PRESENTATION_DATA
* ===== wildbits-presentation-data =====
* Private presentation controls; include in the private direct page.
dbase               rmb       2
filepath            rmb       1
fileopen            rmb       1
bitmapowned         rmb       1
firstblock          rmb       2
mapbase             rmb       2
mapped              rmb       1
blockindex          rmb       1
frameoffset         rmb       2
sourceptr           rmb       2
remaining           rmb       2
chunk               rmb       2
rows                rmb       1
                    ifne      GAME_PRESENTATION
presentbatchrows    rmb       1
gamepresentdirty    rmb       3
gamepresentleft     rmb       1
gamepresentright    rmb       1
gamepresentwidth    rmb       1
presentband         rmb       1
presentationconfigured rmb   1
                    endc
aborted             rmb       1
errorcode           rmb       1
paused              rmb       1
registered          rmb       1
nearend             equ       .

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_PRESENTATION_HELPERS
* ===== wildbits-presentation-helpers =====
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
ConvertRow          equ       *
                    ifne      GAME_PRESENTATION
                    ldb       <gamepresentwidth
                    else
                    ldb       #PictureWidth
                    endc
convertpixel        lda       ,x+
                    anda      #$0F
                    inca
                    sta       ,y+
                    sta       ,y+
                    decb
                    bne       convertpixel
                    rts
* Visibility handling uses intercepted U, never the interrupted DP.
intercept           equ       *
                    cmpb      #SignalBg
                    bne       signalforeground
                    stb       paused,u
                    rti
signalforeground    cmpb      #SignalFg
                    bne       signalabort
                    clr       paused,u
                    ifne      GAME_PRESENTATION
                    clr       presentationconfigured,u
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

foreground          pshs      x,y,u
waitforeground      tst       <aborted
                    bne       foregroundabort
                    tst       <paused
                    beq       foregroundready
                    ifne      GAME_PRESENTATION
                    lbsr      GameClockMute
                    bcs       foregrounderror
                    endc
                    ldx       #2        one tick; bounded foreground race
                    os9       F$Sleep
                    bra       waitforeground
foregroundabort     ldb       #E$PrcAbt
                    orcc      #1
                    puls      x,y,u,pc
foregroundready     equ       *
                    ifne      GAME_PRESENTATION
                    lbsr      GameClockUnmute
                    bcs       foregrounderror
                    endc
                    clrb
foregrounderror     puls      x,y,u,pc

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

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_PRESENTATION_PALETTE
* ===== wildbits-presentation-palette =====
* BGRA: index 0 transparent; 1..16 are the sixteen logical AGI colors.
palette             fcb       0,0,0,0,0,0,0,255,170,0,0,255,0,170,0,255
                    fcb       170,170,0,255,0,0,170,255,170,0,170,255
                    fcb       0,85,170,255,170,170,170,255,85,85,85,255
                    fcb       255,85,85,255,85,255,85,255,255,255,85,255
                    fcb       85,85,255,255,255,85,255,255,85,255,255,255
                    fcb       255,255,255,255

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_PRESENTATION
* ===== wildbits-presentation =====
* Shared native presentation entry points. No module header or fixed buffers.
* The combined buffer stays owned by the decoder. Only one mapping is live:
* copy a source span to private row staging, unmap, then map the framebuffer.
PresentationInitialize stu    <dbase
                    leax      dbase,u
                    ldb       #nearend-dbase
PresentationInitLoop clr      ,x+
                    decb
                    bne       PresentationInitLoop
                    stu       <dbase
                    clr       <presentoffset
                    clr       <presentoffset+1
                    rts
PresentPicture      lbsr      PictureUnmap
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #1
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    lbcs      PresentFailure
                    lbsr      CheckTerminal
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #2
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    lbcs      PresentFailure
                    ifne      GAME_PRESENTATION
                    tst       <bitmapowned
                    lbne      PresentReuseBitmap
                    endc
* Refuse an existing bitmap: it is not ours to modify or free.
                    lda       #1
                    ldb       #SS.AScrn
                    ldx       #0
                    ldy       #0
                    os9       I$SetStt
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #3
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    lbcs      PresentFailure
                    inc       <bitmapowned
* Query the actual first block,rather than relying on an old allocation ABI.
                    lda       #1
                    ldb       #WBBmBlk
                    ldy       #0
                    os9       I$GetStt
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #4
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    lbcs      PresentFailure
                    stx       <firstblock
                    lda       #0
                    ldb       #WBWSig
                    ldx       #SignalBg*256+SignalFg
                    os9       I$SetStt
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #5
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    lbcs      PresentFailure
                    inc       <registered
PresentClearBitmap  equ       *
                    ifne      GAME_PRESENTATION
                    lbsr      GameDamageAll
                    endc
                    clr       <blockindex
clearblock          lbsr      foreground
                    lbcs      PresentFailure
                    lbsr      mapblock
                    lbcs      PresentFailure
                    ldx       #BlockBytes
                    ifne      GAME_PRESENTATION
                    lda       <blockindex
                    cmpa      #9
                    bne       ClearVisibleBlock
                    ldx       #3072             retain owned persistent-dialog backup
ClearVisibleBlock   equ       *
                    endc
                    lda       #1        opaque black,not transparent index zero
clearbyte           sta       ,u+
                    leax      -1,x
                    bne       clearbyte
                    lbsr      unmap
                    lbcs      PresentFailure
                    tst       <aborted
                    lbne      PresentAbort
                    inc       <blockindex
                    lda       <blockindex
                    cmpa      #10
                    blo       clearblock
                    ifne      GAME_PRESENTATION
PresentReuseBitmap  clr       <presentoffset
                    clr       <presentoffset+1
                    clr       <presentband
PresentBandNext     lda       <presentband
                    cmpa      #21
                    lbhs      PresentFinishBands
                    lbsr      GameDamageTest
                    bne       PresentBandReady
                    inc       <presentband
                    bra       PresentBandNext
PresentBandReady    ldb       <presentband
                    lslb
                    ldx       <dbase
                    leax      gamepresentbounds,x
                    ldd       b,x
                    std       <gamepresentleft
                    subb      <gamepresentleft
                    stb       <gamepresentwidth
                    lda       <presentband
                    ldb       #5
                    mul
                    tfr       b,a
                    clrb
                    addb      <gamepresentleft
                    adca      #0
                    std       <presentoffset
                    lda       <vmpicturetop
                    adda      <presentband
                    ldb       #10
                    mul
                    tfr       b,a
                    clrb
                    pshs      d
                    clra
                    ldb       <gamepresentleft
                    lslb
                    rola
                    addd      ,s++
                    std       <frameoffset   picture top row * 8 * 320
                    endc
                    ifne      GAME_PRESENTATION
                    lda       #8
                    else
                    lda       #PictureHeight
                    endc
                    sta       <rows
PresentReadRow      lbsr      foreground
                    lbcs      PresentFailure
                    ldu       <dbase
                    ifne      GAME_PRESENTATION
* The first 2048 command bytes may hold a modal/line-editor backup.
* The remaining idle workspace holds this eight-row band and its expansion.
                    lda       <rows
PresentBatchSize    sta       <presentbatchrows
                    clra
                    ldb       <gamepresentwidth
                    std       <remaining
                    leax      resourcecommands+2048,u
                    else
                    leax      rowinput,u
                    ldd       #PictureWidth
                    std       <remaining
                    endc
                    stx       <sourceptr
PresentReadSpan     ldd       <presentoffset
                    anda      #$1F
                    pshs      d
                    ldd       #BlockBytes
                    subd      ,s++
                    cmpd      <remaining
                    bls       PresentReadSize
                    ldd       <remaining
PresentReadSize     std       <chunk
                    ldd       <presentoffset
                    lbsr      PicturePointer
                    tst       <decodeerror
                    lbne      PresentDecodeFailure
                    ldx       <sourceptr
                    ldy       <chunk
PresentCopySource   equ       *
                    ifne      GAME_PRESENTATION
                    ldd       ,u++
                    std       ,x++
                    leay      -2,y
                    else
                    lda       ,u+
                    sta       ,x+
                    leay      -1,y
                    endc
                    bne       PresentCopySource
                    stx       <sourceptr
                    ifeq      GAME_PRESENTATION
                    lbsr      PictureUnmap
                    endc
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #6
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    lbcs      PresentFailure
                    ldd       <presentoffset
                    addd      <chunk
                    std       <presentoffset
                    ldd       <remaining
                    subd      <chunk
                    std       <remaining
                    bne       PresentReadSpan
                    ifne      GAME_PRESENTATION
                    clra
                    ldb       #160
                    subb      <gamepresentwidth
                    addd      <presentoffset
                    std       <presentoffset
                    dec       <presentbatchrows
                    beq       PresentSourceReady
                    clra
                    ldb       <gamepresentwidth
                    std       <remaining
                    bra       PresentReadSpan
PresentSourceReady  lbsr      PictureUnmap
                    lbcs      PresentFailure
                    endc
                    ldu       <dbase
                    ifne      GAME_PRESENTATION
                    leax      resourcecommands+2048,u
                    leay      resourcecommands+4096,u
                    ldb       <rows
                    pshs      b
PresentConvertBatch lbsr      ConvertRow
                    dec       ,s
                    bne       PresentConvertBatch
                    leas      1,s
                    ldu       <dbase
                    leax      resourcecommands+4096,u
                    stx       <sourceptr
                    clra
                    ldb       <gamepresentwidth
                    lslb
                    rola
                    else
                    leax      rowinput,u
                    leay      rowoutput,u
                    lbsr      ConvertRow
                    ldu       <dbase
                    leax      rowoutput,u
                    stx       <sourceptr
                    ldd       #320
                    endc
                    std       <remaining
writespan           ldd       <frameoffset
                    ifne      GAME_PRESENTATION
                    lbsr      GameFramePointer
                    lbcs      PresentFailure
                    anda      #$1F
                    else
                    ldd       <frameoffset
                    anda      #$1F
                    pshs      d         offset inside mapped block
                    ldd       <frameoffset
                    lsra
                    lsra
                    lsra
                    lsra
                    lsra
                    sta       <blockindex
                    lbsr      mapblock
                    lbcs      PresentFailure
                    puls      d
                    leau      d,u
                    endc
                    pshs      d
                    ldd       #BlockBytes
                    subd      ,s++
                    cmpd      <remaining
                    bls       sized
                    ldd       <remaining
sized               std       <chunk
                    tfr       d,y
                    ldx       <sourceptr
copyspan            equ       *
                    ifne      GAME_PRESENTATION
                    ldd       ,x++
                    std       ,u++
                    leay      -2,y
                    else
                    lda       ,x+
                    sta       ,u+
                    leay      -1,y
                    endc
                    bne       copyspan
                    stx       <sourceptr
                    ldd       <frameoffset
                    addd      <chunk
                    std       <frameoffset
                    ldd       <remaining
                    subd      <chunk
                    std       <remaining
                    ifeq      GAME_PRESENTATION
                    lbsr      unmap
                    lbcs      PresentFailure
                    endc
                    tst       <aborted
                    lbne      PresentAbort
                    ldd       <remaining
                    bne       writespan
                    ifne      GAME_PRESENTATION
                    clra
                    ldb       #160
                    subb      <gamepresentwidth
                    lslb
                    rola
                    addd      <frameoffset
                    std       <frameoffset
                    dec       <rows
                    beq       PresentBandWritten
                    clra
                    ldb       <gamepresentwidth
                    lslb
                    rola
                    std       <remaining
                    lbra      writespan
PresentBandWritten  lbsr      unmap
                    lbcs      PresentFailure
                    else
                    dec       <rows
                    endc
                    lbne      PresentReadRow
                    ifne      GAME_PRESENTATION
                    inc       <presentband
                    lbra      PresentBandNext
PresentFinishBands  equ       *
                    endc
                    lbsr      foreground
                    lbcs      PresentFailure
                    ifne      GAME_PRESENTATION
                    tst       <presentationconfigured
                    lbne      PresentDrawTextOnly
                    endc
                    leax      palette,pcr
                    ldy       #0
                    ldu       #17
                    lda       #1
                    ldb       #WBClutWrite
                    os9       I$SetStt
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #7
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    lbcs      PresentFailure
                    lda       #1
                    ldb       #SS.Palet
                    ldx       #0
                    ldy       #0
                    os9       I$SetStt
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #8
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    lbcs      PresentFailure
                    lda       #1
                    ldb       #SS.PScrn
                    ldx       #0
                    ldy       #0
                    os9       I$SetStt
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #9
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    lbcs      PresentFailure
                    lda       #1
                    ldb       #SS.DScrn
                    ldx       #FX_BM+FX_GRF
                    ldy       #FT_OMIT
                    os9       I$SetStt
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #10
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    lbcs      PresentFailure
                    ifne      GAME_PRESENTATION
                    lda       #1
                    sta       <presentationconfigured
PresentDrawTextOnly equ       *
                    lbsr      GameDrawText
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #11
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    lbcs      PresentFailure
                    clr       <gamepresentdirty
                    clr       <gamepresentdirty+1
                    clr       <gamepresentdirty+2
                    ldd       #$A000
                    lbsr      GameDamageBounds
                    endc
                    ifeq      GAME_PRESENTATION
                    lda       #0
                    ldu       <dbase
                    leax      rowinput,u
                    ldy       #1
                    os9       I$Read    any key returns to text
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #12
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    bcs       PresentFailure
                    endc
                    clrb
                    rts
PresentAbort        ldb       #E$PrcAbt
PresentFailure      orcc      #1
                    rts
PresentDecodeFailure ldb      <decodeerror
                    bra       PresentFailure

* Release only resources this process acquired. Preserve the first error.
PresentationRelease clr       <errorcode
                    tst       <mapped
                    beq       PresentReleaseSignal
                    lbsr      unmap
                    bcc       PresentReleaseSignal
                    stb       <errorcode
                    lbsr      unmap
PresentReleaseSignal tst      <registered
                    beq       PresentReleaseBitmap
                    lda       #0
                    ldb       #WBWSig
                    ldx       #0
                    os9       I$SetStt
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #13
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    bcs       PresentReleaseError
                    clr       <registered
PresentReleaseBitmap tst      <bitmapowned
                    beq       PresentReleaseResult
                    lda       #1
                    ldb       #SS.DScrn
                    ldx       #FX_TXT
                    ldy       #FT_OMIT
                    os9       I$SetStt
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #14
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    bcs       PresentReleaseError
                    lda       #1
                    ldb       #SS.FScrn
                    ldy       #0
                    os9       I$SetStt
                    ifne      GAME_TRACE
                    pshs      cc,a
                    lda       #15
                    lbsr      GameTraceStage
                    puls      cc,a
                    endc
                    bcs       PresentReleaseError
                    clr       <bitmapowned
PresentReleaseResult ldb      <errorcode
                    beq       PresentReleased
                    orcc      #1
                    rts
PresentReleased     clrb
                    rts
PresentReleaseError tst       <errorcode
                    bne       PresentReleaseResult
                    stb       <errorcode
                    bra       PresentReleaseResult

                    ifne      GAME_PRESENTATION
* Modal overlays can cover pixels outside the game picture. Clear the whole
* owned bitmap before restoring the picture and persistent text cells.
RefreshPicture      lbsr      AssetUnmap
                    lbcs      PresentFailure
                    lbsr      PictureUnmap
                    lbcs      PresentFailure
                    tst       <bitmapowned
                    lbeq      PresentPicture
                    lbra      PresentClearBitmap
                    endc

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_SCREEN_CODE
* ===== wildbits-screen-code =====
ScreenInitialize    lda       #'_
                    sta       <vmcursor
                    lda       #15
                    sta       <vmtextforeground
                    clr       <vmtextbackground
                    clr       <vmstatusrow
                    clr       <vmstatusenabled
                    lda       #1
                    sta       <vmpicturetop
                    sta       <vminputenabled
                    sta       <vmgraphics
                    lda       #23
                    sta       <vminputrow
                    rts
ScreenCommand       ldu       <resourcebase
                    ldb       <vmopcode
                    cmpb      #108
                    beq       ScreenCursor
                    cmpb      #109
                    beq       ScreenColors
                    cmpb      #111
                    beq       ScreenConfigure
                    cmpb      #112
                    beq       ScreenStatusOn
                    cmpb      #113
                    beq       ScreenStatusOff
                    cmpb      #119
                    beq       ScreenInputOff
                    cmpb      #120
                    beq       ScreenInputOn
                    ldb       #E$UnkSvc
                    orcc      #1
                    rts
ScreenCursor        ldb       vmarguments,u
                    lbsr      ReadLogicMessage
                    bcs       ScreenReturn
                    lda       ,x
                    sta       <vmcursor
                    bra       ScreenDone
ScreenColors        ldd       vmarguments,u
                    cmpa      #15
                    bhi       ScreenInvalid
                    cmpb      #15
                    bhi       ScreenInvalid
                    sta       <vmtextforeground
                    stb       <vmtextbackground
                    bra       ScreenDone
ScreenConfigure     lda       vmarguments,u
                    cmpa      #4         21 picture rows within 25 text rows
                    bhi       ScreenInvalid
                    sta       <vmpicturetop
                    lda       vmarguments+1,u
                    cmpa      #24
                    bhi       ScreenInvalid
                    sta       <vminputrow
                    lda       vmarguments+2,u
                    cmpa      #24
                    bhi       ScreenInvalid
                    sta       <vmstatusrow
                    bra       ScreenDone
ScreenStatusOn      lda       #1
                    sta       <vmstatusenabled
                    bra       ScreenDone
ScreenStatusOff     clr       <vmstatusenabled
                    bra       ScreenDone
ScreenInputOff      clr       <vminputenabled
                    bra       ScreenDone
ScreenInputOn       lda       #1
                    sta       <vminputenabled
ScreenDone          clrb
ScreenReturn        rts
ScreenInvalid       ldb       #E$IllArg
                    orcc      #1
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_SCREEN_DATA
* ===== wildbits-screen-data =====
* Private AGI text/picture configuration, consumed by game presentation.
vmcursor            rmb       1
vmtextforeground    rmb       1
vmtextbackground    rmb       1
vmpicturetop        rmb       1
vminputrow          rmb       1
vmstatusrow         rmb       1
vmstatusenabled     rmb       1
vminputenabled      rmb       1
vmgraphics          rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_SPRITE_BACKGROUND
* ===== wildbits-sprite-background =====
* Native records reserve bytes 6..9 for the last rendered clipped rectangle
* (x, top, width, height). Height zero means no footprint to erase.
GameRememberSprite  ldu       spriteobject,x
                    lda       3,u
                    cmpa      #160
                    bhs       SpriteRememberNone
                    sta       6,u
                    lda       #160
                    suba      3,u
                    cmpa      $1C,u
                    bls       SpriteRememberWidth
                    lda       $1C,u
SpriteRememberWidth sta       8,u
                    clra
                    ldb       4,u
                    addd      #1
                    pshs      d
                    clra
                    ldb       $1D,u
                    pshs      d
                    ldd       2,s
                    subd      ,s++
                    bpl       SpriteRememberTop
                    ldd       #0
SpriteRememberTop   cmpd      #168
                    bhs       SpriteRememberOutside
                    stb       7,u
                    puls      d
                    cmpd      #168
                    bls       SpriteRememberBottom
                    ldd       #168
SpriteRememberBottom subb    7,u
                    stb       9,u
                    lbsr      GameDamageSprite
                    clrb
                    rts
SpriteRememberOutside leas   2,s
SpriteRememberNone  clr       9,u
                    clrb
                    rts

GameForgetSprites   ldx       <resourcebase
                    leau      vmobjects,x
                    ldb       #64
SpriteForgetNext    clr       9,u
                    leau      43,u
                    decb
                    bne       SpriteForgetNext
                    rts

* Restore only pixels the previous composition actually touched. Stage a
* rectangle privately before changing mappings. Very large cels retain the
* bounded full-background fallback. Never map source and destination together.
GameRestoreSprites  lbsr      PictureUnmap
                    lbcs      GameBackgroundReturn
                    ldx       <resourcebase
                    ldd       gamebackgroundfirst,x
                    std       <assetfirst
                    lda       #4
                    sta       <assetblocks
                    clr       <assetowned
                    leau      vmobjects,x
                    stu       dirtyobject,x
SpriteEraseNext     ldu       dirtyobject,x
                    tst       9,u
                    beq       SpriteEraseAdvance
                    lbsr      GameDamageSprite
                    lda       8,u
                    ldb       9,u
                    mul
                    cmpd      #8192
                    bls       SpriteEraseSmall
                    lbsr      GameDamageAll
                    lda       #1
                    sta       gamecopydirection,x
                    lbra      GameCopyBackground
SpriteEraseSmall    clr       gamecopydirection,x
                    lbsr      SpriteEraseStage
                    lbcs      GameBackgroundReturn
                    lbsr      AssetUnmap
                    lbcs      GameBackgroundReturn
                    ldx       <resourcebase
                    inc       gamecopydirection,x
                    lbsr      SpriteEraseStage
                    lbcs      GameBackgroundReturn
                    lbsr      PictureUnmap
                    lbcs      GameBackgroundReturn
                    ldx       <resourcebase
                    ldu       dirtyobject,x
                    clr       9,u
SpriteEraseAdvance  leau      43,u
                    stu       dirtyobject,x
                    leay      vmobjects+2752,x
                    pshs      y
                    cmpu      ,s++
                    blo       SpriteEraseNext
                    lbra      GameBackgroundDone

SpriteEraseStage    ldu       dirtyobject,x
                    lda       7,u
                    ldb       #160
                    mul
                    addb      6,u
                    adca      #0
                    std       <pictureoutoffset
                    lda       9,u
                    sta       dirtyrows,x
                    leay      resourcecommands,x
SpriteEraseRow      ldu       dirtyobject,x
                    lda       8,u
                    sta       dirtycolumns,x
* Copy a row span without repeated per-pixel address reconstruction.
* Limit each span to this mapping's remaining bytes, then reconstruct U.
SpriteErasePixel    ldd       <pictureoutoffset
                    anda      #$1F
                    pshs      d
                    ldd       #8192
                    subd      ,s++
                    pshs      d
                    clra
                    ldb       dirtycolumns,x
                    cmpd      ,s
                    bls       SpriteEraseSpanSize
                    ldd       ,s
SpriteEraseSpanSize leas      2,s
                    pshs      d                   private count, never a foreign pointer
                    ldd       <pictureoutoffset
                    tst       gamecopydirection,x
                    bne       SpriteEraseWrite
                    lbsr      AssetPointer
                    tst       <asseterror
                    bne       SpriteEraseAssetError
                    ldb       1,s
SpriteEraseReadCopy lda       ,u+
                    sta       ,y+
                    decb
                    bne       SpriteEraseReadCopy
                    bra       SpriteErasePixelDone
SpriteEraseWrite    lbsr      PicturePointer
                    tst       <decodeerror
                    bne       SpriteEraseDecodeError
                    ldb       1,s
SpriteEraseWriteCopy lda      ,y+
                    sta       ,u+
                    decb
                    bne       SpriteEraseWriteCopy
SpriteErasePixelDone ldb      dirtycolumns,x
                    subb      1,s
                    stb       dirtycolumns,x
                    ldd       <pictureoutoffset
                    addd      ,s++
                    std       <pictureoutoffset
                    tst       dirtycolumns,x
                    bne       SpriteErasePixel
                    ldu       dirtyobject,x
                    clra
                    ldb       8,u
                    pshs      d
                    ldd       <pictureoutoffset
                    subd      ,s++
                    addd      #160
                    std       <pictureoutoffset
                    dec       dirtyrows,x
                    bne       SpriteEraseRow
                    clrb
                    rts
SpriteEraseAssetError leas    2,s
                    lbra      GameBackgroundAssetError
SpriteEraseDecodeError leas   2,s
                    lbra      GameBackgroundDecodeError
                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_PRESENT_DAMAGE
                    use platform/wildbits-graphics.asm

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_DECODER_CODE
* ===== wildbits-decoder-code =====
                    ifndef PLATFORM_WILDBITS_GRAPHICS_BINDINGS
                    use platform/wildbits-graphics-bindings.asm
                    endc
* DecodeLines: X=commands, Y=length, U=private base and matching DP.
* Returns a private physical combined buffer, U=private base, carry clear;
* otherwise carry/B error, with no successful result for unsupported opcodes.
* Picture storage uses one OS-managed window; PictureWrite exports its bytes.
DecodeLines         stu       <resourcebase
                    tst       <decodeerror
                    lbne      DecodeFailed
                    tfr       y,d
                    leay      d,x
                    sty       <decodeend
                    pshs      x
                    lbsr      PictureAllocate
                    bcs       DecodeInitFailed
                    lbsr      PictureClear
DecodeInitFailed    puls      x
                    tst       <decodeerror
                    lbne      DecodeFailed
                    lda       #$FF
                    sta       <DrawColor
                    clr       <DrawMask
                    clr       <PenStatus
                    clr       <ScratchA6
                    lbsr      ReadNext
DecodeCommand       tst       <decodeerror
                    bne       DecodeFailed
                    cmpa      #$FF
                    beq       DecodeFinished
                    suba      #$F0
                    blo       DecodeInvalid
                    cmpa      #10
                    bhi       DecodeInvalid
                    asla
                    leau      DecodeDispatch,pcr
                    ldd       a,u
                    leau      d,u
                    jsr       ,u
                    bra       DecodeCommand
DecodeFinished      cmpx      <decodeend
                    bne       DecodeInvalid
                    ldu       <resourcebase
                    clrb
                    rts
DecodeInvalid       ldb       #E$BMode
                    stb       <decodeerror
DecodeFailed        ldu       <resourcebase
                    ldb       <decodeerror
                    orcc      #1
                    rts

* Immutable offsets from the table base, not load addresses patched at runtime.
DecodeDispatch      equ       *
                    use       shared/picture-command-table.asm

* Preserve B: color/mask routines and coordinate helpers use it across reads.
ReadNext            tst       <decodeerror
                    bne       DecodeReadStop
                    cmpx      <decodeend
                    bhs       DecodeExhausted
                    ifne      GAME_PRESENTATION
                    pshs      b,y,u
                    tfr       x,d
                    anda      #$1F              offset in private input chunk
                    cmpd      #0
                    bne       DecodeBufferedByte
                    lbsr      GameReadPictureChunk
                    tst       <decodeerror
                    beq       DecodeBufferedByte
                    puls      b,y,u
                    bra       DecodeReadStop
DecodeBufferedByte  ldu       <resourcebase
                    leay      resourcecommands,u
                    lda       d,y
                    leax      1,x
                    else
                    lda       ,x+
                    endc
                    sta       <decodevalue      bounded callbacks retain the original byte
                    ifne      GAME_PRESENTATION
                    puls      b,y,u,pc
                    else
                    rts
                    endc
DecodeExhausted     pshs      b
                    ldb       #E$BMode
                    stb       <decodeerror
                    puls      b
DecodeReadStop      lda       #$FF
                    rts
ReadNextB           pshs      a
                    bsr       ReadNext
                    tfr       a,b
                    puls      a,pc
ReadColor           bsr       ReadNext
                    cmpa      #15
                    bls       ReadColorRet
                    pshs      b
                    ldb       #E$BMode
                    stb       <decodeerror
                    puls      b
ReadColorRet        rts
ReadInitialPos      lbsr      ReadXyPos
                    bcc       InitialPosRet
                    pshs      b
                    ldb       #E$BMode
                    stb       <decodeerror
                    puls      b
InitialPosRet       rts

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
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
