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
                    cmpd      #8192
                    bhi       GamePictureInvalid
                    std       <gamepicturelength
                    ldd       #0
                    lbsr      AssetPointer
                    tst       <asseterror
                    bne       GamePictureAssetError
                    ldx       <resourcebase
                    leax      resourcecommands,x
                    ldy       <gamepicturelength
GameCopyCommands    lda       ,u+
                    sta       ,x+
                    leay      -1,y
                    bne       GameCopyCommands
                    lbsr      AssetUnmap
                    bcs       GamePictureReturn
                    ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    lbsr      PictureRelease
                    bcs       GamePictureReturn
                    ldu       <resourcebase
                    leax      resourcecommands,u
                    ldy       <gamepicturelength
                    lbsr      DecodeLines
                    bcs       GamePictureReturn
                    lbsr      PictureUnmap
                    bcs       GamePictureReturn
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
GameShowPicture     lbsr      AssetUnmap
                    bcs       GamePictureReturn
                    tst       <pictureowned
                    beq       GamePictureInvalid
                    lbsr      PresentPicture
                    rts
