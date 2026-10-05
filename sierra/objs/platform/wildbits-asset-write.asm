* Expanded resource export via private staging.
AssetWrite        clr       <assetoutoffset
                    clr       <assetoutoffset+1
AssetWriteChunk   ldd       <resourcelength
                    subd      <assetoutoffset
                    beq       AssetWriteDone
                    cmpd      #512
                    bls       AssetWriteSize
                    ldd       #512
AssetWriteSize    std       <assetchunk
                    tfr       d,y
                    ldd       <assetoutoffset
                    lbsr      AssetPointer
                    tst       <asseterror
                    bne       AssetWriteFail
                    ldx       <resourcebase
                    leax      assetinput,x
AssetStageCopy    lda       ,u+
                    sta       ,x+
                    leay      -1,y
                    bne       AssetStageCopy
                    lbsr      AssetUnmap
                    bcs       AssetWriteFail
                    ldx       <resourcebase
                    leax      assetinput,x
                    stx       <resourcepointer
                    ldy       <assetchunk
                    sty       <resourceremaining
AssetStageWrite   lda       #1
                    ldx       <resourcepointer
                    ldy       <resourceremaining
                    os9       I$Write
                    lbcs      AssetSetError
                    cmpy      #0
                    beq       AssetWriteInvalid
                    cmpy      <resourceremaining
                    bhi       AssetWriteInvalid
                    tfr       y,d
                    addd      <resourcepointer
                    std       <resourcepointer
                    ldd       <resourceremaining
                    pshs      y
                    subd      ,s++
                    std       <resourceremaining
                    bne       AssetStageWrite
                    ldd       <assetoutoffset
                    addd      <assetchunk
                    std       <assetoutoffset
                    bra       AssetWriteChunk
AssetWriteDone    clrb
                    rts
AssetWriteInvalid ldb       #E$BMode
                    lbra      AssetSetError
AssetWriteFail    ldb       <asseterror
                    orcc      #1
                    rts
