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
SpriteErasePixel    ldd       <pictureoutoffset
                    tst       gamecopydirection,x
                    bne       SpriteEraseWrite
                    lbsr      AssetPointer
                    tst       <asseterror
                    lbne      GameBackgroundAssetError
                    ldb       ,u
                    stb       ,y+
                    bra       SpriteErasePixelDone
SpriteEraseWrite    ldb       ,y+
                    pshs      b
                    ldd       <pictureoutoffset
                    lbsr      PicturePointer
                    puls      b
                    tst       <decodeerror
                    lbne      GameBackgroundDecodeError
                    stb       ,u
SpriteErasePixelDone ldd      <pictureoutoffset
                    addd      #1
                    std       <pictureoutoffset
                    dec       dirtycolumns,x
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
                    use       platform/wildbits-present-damage.asm
