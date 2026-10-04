* Keep the decoded background separate from the sprite composition buffer.
* Copy through private 512-byte staging; only one foreign mapping is live.
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
                    lda       #1
                    sta       gamecopydirection,x
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
                    cmpd      #512
                    bls       GameBackgroundSize
                    ldd       #512
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
GameStageBackground leax      picturestage,x
GameBackgroundRead  lda       ,u+
                    sta       ,x+
                    leay      -1,y
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
GameWriteBackground leax      picturestage,x
                    ldy       <picturechunk
GameBackgroundWrite lda       ,x+
                    sta       ,u+
                    leay      -1,y
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
GameBackgroundDone  ldb       <vmcurrent
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
