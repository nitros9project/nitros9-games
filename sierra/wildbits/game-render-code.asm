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
SpriteRenderObject  ldx       <resourcebase
                    stu       spriteobject,x
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
SpriteReadRow       ldx       <resourcebase
                    leay      spriterow,x
                    ldb       #160
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
SpriteRowReady      lbsr      AssetUnmap
                    lbcs      SpriteRestoreLogic
                    ldx       <resourcebase
                    ldd       spriterowy,x
                    cmpd      #168
                    lbhs      SpriteNextRow
                    clr       spritecolumn,x
SpritePlotNext      ldu       spriteobject,x
                    ldb       3,u
                    clra
                    addb      spritecolumn,x
                    adca      #0
                    cmpd      #160
                    lbhs      SpriteNextColumn
                    pshs      b
                    ldb       spritecolumn,x
                    tst       spritemirror,x
                    beq       SpriteSourceColumn
                    ldb       spritewidth,x
                    decb
                    subb      spritecolumn,x
SpriteSourceColumn  leay      spriterow,x
                    lda       b,y
                    puls      b
                    cmpa      #$FF
                    beq       SpriteNextColumn
                    sta       spritecolor,x
                    pshs      b
                    ldb       spriterowy+1,x
                    lda       #160
                    mul
                    addb      ,s+
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
                    bra       SpriteNextColumn
SpriteControlPixel  ldd       <pictureoffset
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
SpriteControlHidden equ       *
* Search success still has the original-offset word on the stack.
                    leas      2,s
                    bra       SpriteNextColumn
SpriteControlError  equ       *
SpriteControlRestoreError leas 2,s
                    lbra      SpriteDecodeError
SpriteNextColumn    inc       spritecolumn,x
                    ldb       spritecolumn,x
                    cmpb      spritewidth,x
                    lblo      SpritePlotNext
SpriteNextRow       lbsr      PictureUnmap
                    bcs       SpriteRestoreLogic
                    ldx       <resourcebase
                    ldd       spriterowy,x
                    addd      #1
                    std       spriterowy,x
                    dec       spriteheight,x
                    lbne      SpriteReadRow
                    clrb
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
