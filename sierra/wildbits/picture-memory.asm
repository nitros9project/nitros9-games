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
PicturePointer      pshs      d,x,y
                    std       <pictureoffset
                    tst       <decodeerror
                    bne       PicturePointerRet
                    lsra
                    lsra
                    lsra
                    lsra
                    lsra
                    tst       <picturemapped
                    beq       PictureMap
                    cmpa      <picturepage
                    beq       PictureAddress
PictureMap          pshs      a
                    lbsr      PictureUnmap
                    puls      a
                    bcs       PicturePointerRet
                    sta       <picturepage
                    tfr       a,b
                    clra
                    addd      <picturefirst
                    tfr       d,x
                    ldb       #1
                    os9       F$MapBlk
                    bcs       PictureMapError
                    stu       <picturemapbase
                    inc       <picturemapped
PictureAddress      ldd       <pictureoffset
                    anda      #$1F
                    ldu       <picturemapbase
                    leau      d,u
PicturePointerRet   puls      d,x,y,pc
PictureMapError     lbsr      PictureError
                    bra       PicturePointerRet
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
