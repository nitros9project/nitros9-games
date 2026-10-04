* LoadAsset: same directory/number ABI as LoadPicture. resourcekind selects
* logic=0, picture=1, view=2, sound=3. Success retains an owned physical slab:
* X=first block, B=block count, Y=expanded length, U=private base. Caller must
* release/adopt it. Compressed input uses LZW; nibble-packed pictures rejected.
LoadAsset           lbsr      ResourceLocate     common header locator, leaves path open
                    lbcs      AssetReturn
                    lbsr      AssetAllocate
                    lbcs      AssetLoadError
                    ldd       <resourcestored
                    std       <assetinputleft
                    ldu       <resourcebase
                    leax      assetinput,u
                    stx       <assetinputpointer
                    stx       <assetinputend
                    clr       <assetoutoffset
                    clr       <assetoutoffset+1
                    ldd       <resourcestored
                    cmpd      <resourcelength
                    beq       AssetPlain
                    leax      resourcecommands,u
                    ldy       <resourcelength
                    lbsr      DecodeLzw
                    bra       AssetDecoded
AssetPlain          lbsr      LzwReadByte
                    bcs       AssetLoadError
                    lbsr      LzwWriteByte
                    bcs       AssetLoadError
                    ldd       <assetoutoffset
                    cmpd      <resourcelength
                    blo       AssetPlain
AssetDecoded        bcs       AssetLoadError
                    lbsr      AssetUnmap
                    bcs       AssetLoadError
                    lbsr      ResourceClose
                    bcs       AssetLoadError
                    ldu       <resourcebase
                    ldx       <assetfirst
                    ldy       <resourcelength
                    ldb       <assetblocks
                    andcc     #$FE
AssetReturn         rts
AssetLoadError      stb       <asseterror
                    tst       <resourceopen
                    beq       AssetLoadClosed
                    lbsr      ResourceClose
AssetLoadClosed     ldu       <resourcebase
                    ldb       <asseterror
                    orcc      #1
                    rts

* Disk reads use private staging with no output mapping live; partial reads
* are consumed correctly. Neither padding nor unbounded reads are accepted.
LzwReadByte         pshs      x,y,u
                    tst       <asseterror
                    lbne      AssetReadFailure
                    ldx       <assetinputpointer
                    cmpx      <assetinputend
                    blo       AssetReadBuffered
                    lbsr      AssetUnmap
                    lbcs      AssetReadFailure
                    ldd       <assetinputleft
                    lbeq      AssetReadEOF
                    cmpd      #512
                    bls       AssetReadSize
                    ldd       #512
AssetReadSize       tfr       d,y
                    ldu       <resourcebase
                    leax      assetinput,u
                    lda       <resourcepath
                    os9       I$Read
                    lbcs      AssetReadService
                    cmpy      #0
                    lbeq      AssetReadInvalid
                    cmpy      #512
                    lbhi      AssetReadInvalid
                    cmpy      <assetinputleft
                    lbhi      AssetReadInvalid
                    tfr       y,d
                    pshs      d
                    ldd       <assetinputleft
                    subd      ,s
                    std       <assetinputleft
                    ldu       <resourcebase
                    leax      assetinput,u
                    puls      d
                    leay      d,x
                    sty       <assetinputend
AssetReadBuffered   ldb       ,x+
                    stx       <assetinputpointer
                    andcc     #$FE
                    puls      x,y,u,pc
AssetReadEOF        ldb       #E$EOF
                    bra       AssetReadService
AssetReadInvalid    ldb       #E$BMode
AssetReadService    stb       <asseterror
AssetReadFailure    ldb       <asseterror
                    orcc      #1
                    puls      x,y,u,pc
LzwWriteByte        pshs      x,y,u
                    stb       <assetbyte
                    ldd       <assetoutoffset
                    cmpd      <resourcelength
                    bhs       AssetReadInvalid
                    lbsr      AssetPointer
                    tst       <asseterror
                    bne       AssetReadFailure
                    ldb       <assetbyte
                    stb       ,u
                    ldd       <assetoutoffset
                    addd      #1
                    std       <assetoutoffset
                    andcc     #$FE
                    puls      x,y,u,pc

AssetAllocate       ldu       <resourcebase
                    leax      assetinput,u
                    lda       #0
                    ldb       #SS.Opt
                    os9       I$GetStt
                    lbcs      AssetSetError
                    ldu       <resourcebase
                    tst       assetinput,u
                    bne       AssetBadMode
                    ldd       <resourcelength
                    subd      #1
                    lsra
                    lsra
                    lsra
                    lsra
                    lsra
                    inca
                    sta       <assetblocks
                    tfr       a,b
                    clra
                    tfr       d,x
                    lda       #0
                    ldb       #$D4
                    os9       I$SetStt
                    bcs       AssetSetError
                    stx       <assetfirst
                    inc       <assetowned
                    clrb
                    rts
AssetBadMode        ldb       #E$BMode
AssetSetError          stb       <asseterror
                    orcc      #1
                    rts
AssetUnmap          tst       <assetmapped
                    beq       AssetUnmapped
                    ldu       <assetmapbase
                    ldb       #1
                    os9       F$ClrBlk
                    bcs       AssetSetError
                    clr       <assetmapped
AssetUnmapped       clrb
                    rts
AssetRelease        lbsr      AssetUnmap
                    bcs       AssetReleaseDone
                    tst       <assetowned
                    beq       AssetUnmapped
                    ldb       <assetblocks
                    clra
                    tfr       d,u
                    ldx       <assetfirst
                    lda       #0
                    ldb       #$D5
                    os9       I$SetStt
                    bcs       AssetSetError
                    clr       <assetowned
                    clrb
AssetReleaseDone    rts
* D=logical offset -> ephemeral U; preserve D/X/Y. Error in asseterror.
AssetPointer        pshs      d,x,y
                    std       <assetoffset
                    tst       <asseterror
                    bne       AssetPointerDone
                    lsra
                    lsra
                    lsra
                    lsra
                    lsra
                    tst       <assetmapped
                    beq       AssetMap
                    cmpa      <assetpage
                    beq       AssetAddress
AssetMap            pshs      a
                    lbsr      AssetUnmap
                    puls      a
                    bcs       AssetPointerDone
                    sta       <assetpage
                    tfr       a,b
                    clra
                    addd      <assetfirst
                    tfr       d,x
                    ldb       #1
                    os9       F$MapBlk
                    bcs       AssetMapError
                    stu       <assetmapbase
                    inc       <assetmapped
AssetAddress        ldd       <assetoffset
                    anda      #$1F
                    ldu       <assetmapbase
                    leau      d,u
AssetPointerDone    puls      d,x,y,pc
AssetMapError       lbsr      AssetSetError
                    bra       AssetPointerDone
AssetIntercept      cmpb      #S$Abort
                    blo       AssetSignalDone
                    cmpb      #S$Intrpt
                    bhi       AssetSignalDone
                    ldb       #E$PrcAbt
                    stb       asseterror,u
AssetSignalDone     rti
