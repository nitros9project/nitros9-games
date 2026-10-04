* Native plain AGI picture-resource boundary, shared by probe/future decoder.
* LoadPicture: X = CR/space-terminated game directory; Y = picture 0..255;
* U = private resource-data base; DP = high byte of that base.
* Success: X = private command buffer, Y = length, U = private data base,
* carry clear. Failure: carry set, B = OS-9 error. All opened paths are closed
* on normal success/error paths. No writable code, fixed buffers or hardware.
* Header format here is the existing CoCo game's seven-byte resource format.
LoadPicture         stu       <resourcebase
                    sty       <resourcenumber
                    clr       <resourceopen
                    cmpy      #255
                    lbhi      ResourceArgument
                    leay      resourcefilename,u
                    ldb       #128
ResourceCopyDir     lda       ,x+
                    cmpa      #C$SPAC
                    beq       ResourceDirEnd
                    cmpa      #C$CR
                    beq       ResourceDirEnd
                    tsta
                    beq       ResourceDirEnd
                    sta       ,y+
                    decb
                    bne       ResourceCopyDir
                    lbra      ResourceArgument
ResourceDirEnd      leax      resourcefilename,u
                    pshs      x
                    cmpy      ,s++
                    lbeq      ResourceArgument
                    lda       -1,y
                    cmpa      #'/
                    beq       ResourceDirSlash
                    lda       #'/
                    sta       ,y+
ResourceDirSlash    sty       <resourcenameend
                    leax      ResourcePicDir,pcr
                    lbsr      ResourceSuffix
                    lbsr      OpenPicturePath
                    lbcs      ResourceFailed
                    ldd       <resourcenumber
                    pshs      d
                    lslb
                    rola
                    addd      ,s++              directory entry = number * 3
                    tfr       d,u
                    ldx       #0                I$Seek position is X:U
                    lda       <resourcepath
                    os9       I$Seek
                    lbcs      ResourceFailed
                    ldu       <resourcebase
                    leax      resourceentry,u
                    ldy       #3
                    lbsr      ResourceReadExact
                    lbcs      ResourceFailed
                    ldu       <resourcebase
                    leax      resourceentry,u
                    lda       ,x
                    cmpa      #$FF
                    bne       DecodePictureEntry
                    ldd       1,x
                    cmpd      #$FFFF
                    lbeq      ResourceInvalid
DecodePictureEntry       lda       ,x
                    lsra
                    lsra
                    lsra
                    lsra
                    sta       <resourcevolume
                    clr       <resourceoffset
                    lda       ,x
                    anda      #$0F
                    sta       <resourceoffset+1
                    ldd       1,x
                    std       <resourceoffset+2
                    lbsr      ResourceClose
                    lbcs      ResourceFailed
                    ldy       <resourcenameend
                    leax      ResourceVol,pcr
                    lbsr      ResourceSuffix     ends at CR after "vol."
                    leay      -1,y
                    lda       <resourcevolume
                    cmpa      #10
                    blo       ResourceVolumeDigit
                    ldb       #'1
                    stb       ,y+
                    suba      #10
ResourceVolumeDigit adda      #'0
                    sta       ,y+
                    lda       #C$CR
                    sta       ,y
                    lbsr      OpenPicturePath
                    lbcs      ResourceFailed
                    ldx       <resourceoffset
                    ldu       <resourceoffset+2
                    lda       <resourcepath
                    os9       I$Seek
                    lbcs      ResourceFailed
                    ldu       <resourcebase
                    leax      resourceheader,u
                    ldy       #7
                    lbsr      ResourceReadExact
                    lbcs      ResourceFailed
                    ldu       <resourcebase
                    leax      resourceheader,u
                    ldd       ,x
                    cmpd      #$1234
                    lbne      ResourceInvalid
                    lda       2,x
                    bita      #$80              nibble-packed is not implemented
                    lbne      ResourceInvalid
                    anda      #$0F
                    cmpa      <resourcevolume
                    lbne      ResourceInvalid
                    ldb       3,x               decoded size is little endian
                    lda       4,x
                    std       <resourcelength
                    lbeq      ResourceInvalid
                    cmpd      #8192
                    lbhi      ResourceInvalid
                    ldb       5,x               stored size is little endian
                    lda       6,x
                    cmpd      <resourcelength    reject LZW, do not misdecode it
                    lbne      ResourceInvalid
                    leax      resourcecommands,u
                    ldy       <resourcelength
                    lbsr      ResourceReadExact
                    lbcs      ResourceFailed
                    ldu       <resourcebase
                    leax      resourcecommands,u
                    ldd       <resourcelength
                    leay      d,x
                    lda       -1,y
                    cmpa      #$FF
                    bne       ResourceInvalid
                    lbsr      ResourceClose
                    bcs       ResourceFailed
                    ldu       <resourcebase
                    leax      resourcecommands,u
                    ldy       <resourcelength
                    clrb
                    rts
ResourceArgument    ldb       #E$IllArg
                    bra       ResourceFailed
ResourceInvalid     ldb       #E$BMode
ResourceFailed      stb       <resourceerror
                    tst       <resourceopen
                    beq       ResourceReturnErr
                    lbsr      ResourceClose
ResourceReturnErr   ldu       <resourcebase
                    ldb       <resourceerror
                    orcc      #1
                    rts

ResourceSuffix      lda       ,x+
                    sta       ,y+
                    cmpa      #C$CR
                    bne       ResourceSuffix
                    rts
OpenPicturePath        ldu       <resourcebase
                    leax      resourcefilename,u
                    lda       #READ.
                    os9       I$Open
                    bcs       OpenPicturePathRet
                    sta       <resourcepath
                    inc       <resourceopen
OpenPicturePathRet     rts
ResourceClose       lda       <resourcepath
                    os9       I$Close
                    bcs       ResourceCloseRet
                    clr       <resourceopen
ResourceCloseRet    rts

* Exact reads retain partial progress; a zero-byte success is malformed input.
ResourceReadExact   stx       <resourcepointer
                    sty       <resourceremaining
ResourceReadMore    lda       <resourcepath
                    ldx       <resourcepointer
                    ldy       <resourceremaining
                    os9       I$Read
                    bcs       ResourceReadRet
                    cmpy      #0
                    beq       ResourceReadZero
                    cmpy      <resourceremaining
                    bhi       ResourceReadZero
                    tfr       y,d
                    addd      <resourcepointer
                    std       <resourcepointer
                    ldd       <resourceremaining
                    pshs      y
                    subd      ,s++
                    std       <resourceremaining
                    bne       ResourceReadMore
                    clrb
ResourceReadRet     rts
ResourceReadZero    ldb       #E$BMode
                    orcc      #1
                    rts

ResourcePicDir      fcc       /picDir/
                    fcb       C$CR
ResourceVol         fcc       /vol./
                    fcb       C$CR
