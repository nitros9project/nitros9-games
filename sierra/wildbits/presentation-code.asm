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
                    lbcs      PresentFailure
                    lbsr      CheckTerminal
                    lbcs      PresentFailure
* Refuse an existing bitmap: it is not ours to modify or free.
                    lda       #1
                    ldb       #SS.AScrn
                    ldx       #0
                    ldy       #0
                    os9       I$SetStt
                    lbcs      PresentFailure
                    inc       <bitmapowned
* Query the actual first block,rather than relying on an old allocation ABI.
                    lda       #1
                    ldb       #WBBmBlk
                    ldy       #0
                    os9       I$GetStt
                    lbcs      PresentFailure
                    stx       <firstblock
                    lda       #0
                    ldb       #WBWSig
                    ldx       #SignalBg*256+SignalFg
                    os9       I$SetStt
                    lbcs      PresentFailure
                    inc       <registered
                    clr       <blockindex
clearblock          lbsr      foreground
                    lbcs      PresentFailure
                    lbsr      mapblock
                    lbcs      PresentFailure
                    ldx       #BlockBytes
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
                    lda       #PictureHeight
                    sta       <rows
PresentReadRow      lbsr      foreground
                    lbcs      PresentFailure
                    ldu       <dbase
                    leax      rowinput,u
                    stx       <sourceptr
                    ldd       #PictureWidth
                    std       <remaining
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
PresentCopySource   lda       ,u+
                    sta       ,x+
                    leay      -1,y
                    bne       PresentCopySource
                    stx       <sourceptr
                    lbsr      PictureUnmap
                    lbcs      PresentFailure
                    ldd       <presentoffset
                    addd      <chunk
                    std       <presentoffset
                    ldd       <remaining
                    subd      <chunk
                    std       <remaining
                    bne       PresentReadSpan
                    ldu       <dbase
                    leax      rowinput,u
                    leay      rowoutput,u
                    lbsr      ConvertRow
                    ldu       <dbase
                    leax      rowoutput,u
                    stx       <sourceptr
                    ldd       #320
                    std       <remaining
writespan           ldd       <frameoffset
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
                    pshs      d
                    ldd       #BlockBytes
                    subd      ,s++
                    cmpd      <remaining
                    bls       sized
                    ldd       <remaining
sized               std       <chunk
                    tfr       d,y
                    ldx       <sourceptr
copyspan            lda       ,x+
                    sta       ,u+
                    leay      -1,y
                    bne       copyspan
                    stx       <sourceptr
                    ldd       <frameoffset
                    addd      <chunk
                    std       <frameoffset
                    ldd       <remaining
                    subd      <chunk
                    std       <remaining
                    lbsr      unmap
                    lbcs      PresentFailure
                    tst       <aborted
                    lbne      PresentAbort
                    ldd       <remaining
                    bne       writespan
                    dec       <rows
                    lbne      PresentReadRow
                    lbsr      foreground
                    lbcs      PresentFailure
                    leax      palette,pcr
                    ldy       #0
                    ldu       #17
                    lda       #1
                    ldb       #WBClutWrite
                    os9       I$SetStt
                    lbcs      PresentFailure
                    lda       #1
                    ldb       #SS.Palet
                    ldx       #0
                    ldy       #0
                    os9       I$SetStt
                    lbcs      PresentFailure
                    lda       #1
                    ldb       #SS.PScrn
                    ldx       #0
                    ldy       #0
                    os9       I$SetStt
                    lbcs      PresentFailure
                    lda       #1
                    ldb       #SS.DScrn
                    ldx       #FX_BM+FX_GRF
                    ldy       #FT_OMIT
                    os9       I$SetStt
                    lbcs      PresentFailure
                    lda       #0
                    ldu       <dbase
                    leax      rowinput,u
                    ldy       #1
                    os9       I$Read    any key returns to text
                    bcs       PresentFailure
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
                    bcs       PresentReleaseError
                    clr       <registered
PresentReleaseBitmap tst      <bitmapowned
                    beq       PresentReleaseResult
                    lda       #1
                    ldb       #SS.DScrn
                    ldx       #FX_TXT
                    ldy       #FT_OMIT
                    os9       I$SetStt
                    bcs       PresentReleaseError
                    lda       #1
                    ldb       #SS.FScrn
                    ldy       #0
                    os9       I$SetStt
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
