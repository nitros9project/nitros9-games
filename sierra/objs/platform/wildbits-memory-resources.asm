* wildbits-memory-resources feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_ASSET_CODE
* ===== wildbits-asset-code =====
* LoadAsset: same directory/number ABI as LoadPicture. resourcekind selects
* logic=0, picture=1, view=2, sound=3. Success retains an owned physical slab:
* X=first block, B=block count, Y=expanded length, U=private base. Caller must
* release/adopt it. LZW and nibble-packed pictures use bounded byte callbacks.
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
                    lda       resourceheader+2,u
                    bita      #$80
                    bne       AssetPackedPicture
                    ldd       <resourcestored
                    cmpd      <resourcelength
                    beq       AssetPlain
                    leax      resourcecommands,u
                    ldy       <resourcelength
                    lbsr      DecodeLzw
                    lbra      AssetDecoded
AssetPlain          lbsr      LzwReadByte
                    lbcs      AssetLoadError
                    lbsr      LzwWriteByte
                    lbcs      AssetLoadError
                    ldd       <assetoutoffset
                    cmpd      <resourcelength
                    blo       AssetPlain
                    bra      AssetDecoded
* Picture bytes are high-nibble first; F0/F2 take one color nibble.
* Reuse LZW scratch: the two codecs never execute concurrently.
AssetPackedPicture  clr       <lzwbits
AssetPackedCommand  bsr      AssetReadNibble
                    bcs      AssetLoadError
                    lslb
                    lslb
                    lslb
                    lslb
                    pshs      b
                    bsr      AssetReadNibble
                    bcs       AssetPackedPopError
                    orb       ,s+
                    stb       <lzwfirst
                    lbsr      LzwWriteByte
                    bcs      AssetLoadError
                    ldb       <lzwfirst
                    cmpb      #$FF
                    beq       AssetPackedEnd
                    cmpb      #$F0
                    beq       AssetPackedColor
                    cmpb      #$F2
                    bne       AssetPackedCommand
AssetPackedColor    bsr      AssetReadNibble
                    bcs      AssetLoadError
                    lbsr      LzwWriteByte
                    bcs      AssetLoadError
                    bra       AssetPackedCommand
AssetPackedPopError leas      1,s
                    bra      AssetLoadError
AssetPackedEnd      ldd       <assetoutoffset
                    cmpd      <resourcelength
                    bne       AssetPackedInvalid
* A final unused low nibble is padding; extra whole bytes are malformed.
                    ldx       <assetinputpointer
                    cmpx      <assetinputend
                    bne       AssetPackedInvalid
                    ldd       <assetinputleft
                    bne       AssetPackedInvalid
                    andcc     #$FE
                    bra      AssetDecoded
AssetPackedInvalid  ldb       #E$BMode
                    bra      AssetLoadError
AssetReadNibble     tst       <lzwbits
                    bne       AssetReadLowNibble
                    bsr      LzwReadByte
                    bcs       AssetNibbleReturn
                    stb       <lzwbyte
                    inc       <lzwbits
                    lsrb
                    lsrb
                    lsrb
                    lsrb
                    andcc     #$FE
AssetNibbleReturn   rts
AssetReadLowNibble  clr       <lzwbits
                    ldb       <lzwbyte
                    andb      #$0F
                    andcc     #$FE
                    rts
AssetDecoded        bcs      AssetLoadError
                    lbsr      AssetUnmap
                    bcs      AssetLoadError
                    lbsr      ResourceClose
                    bcs      AssetLoadError
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
                    bne      AssetReadFailure
                    ldx       <assetinputpointer
                    cmpx      <assetinputend
                    blo       AssetReadBuffered
                    lbsr      AssetUnmap
                    bcs      AssetReadFailure
                    ldd       <assetinputleft
                    beq      AssetReadEOF
                    cmpd      #512
                    bls       AssetReadSize
                    ldd       #512
AssetReadSize       tfr       d,y
                    ldu       <resourcebase
                    leax      assetinput,u
                    lda       <resourcepath
                    os9       I$Read
                    bcs      AssetReadService
                    cmpy      #0
                    beq      AssetReadInvalid
                    cmpy      #512
                    bhi      AssetReadInvalid
                    cmpy      <assetinputleft
                    bhi      AssetReadInvalid
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
                    bcs      AssetSetError
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
AssetRelease        bsr      AssetUnmap
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
AssetPointer        pshs      d
                    tst       <asseterror
                    bne       AssetPointerDone
* Cache the encoded 8K page; shift only when a mapping changes.
                    anda      #$E0
                    tst       <assetmapped
                    beq       AssetMap
                    cmpa      <assetpage
                    beq       AssetAddress
AssetMap            pshs      x,y
                    pshs      a
                    bsr      AssetUnmap
                    puls      a
                    bcs       AssetMapDone
                    sta       <assetpage
                    lsra
                    lsra
                    lsra
                    lsra
                    lsra
                    tfr       a,b
                    clra
                    addd      <assetfirst
                    tfr       d,x
                    ldb       #1
                    os9       F$MapBlk
                    bcs       AssetMapError
                    stu       <assetmapbase
                    inc       <assetmapped
AssetMapDone        puls      x,y
                    bcs       AssetPointerDone
AssetAddress        ldd       ,s
                    anda      #$1F
                    ldu       <assetmapbase
                    leau      d,u
AssetPointerDone    puls      d,pc
AssetMapError       bsr      AssetSetError
                    bra       AssetMapDone
AssetIntercept      cmpb      #S$Abort
                    blo       AssetSignalDone
                    cmpb      #S$Intrpt
                    bhi       AssetSignalDone
                    ldb       #E$PrcAbt
                    stb       asseterror,u
AssetSignalDone     rti

* Bounded random byte/word reads from the current slab. D=offset; U/X/Y
* retained. Word result is little endian; byte result is B.
AssetReadWord         pshs      x
                    tfr       d,x
                    bsr      AssetReadByte
                    bcs       AssetReadWordFailed
                    pshs      b
                    leax      1,x
                    tfr       x,d
                    bsr      AssetReadByte
                    bcs       AssetReadWordLowFailed
                    tfr       b,a
                    puls      b,x
                    andcc     #$FE
                    rts
AssetReadWordLowFailed leas     1,s
AssetReadWordFailed   puls      x,pc
AssetReadByte         pshs      x,y,u
                    cmpd      <resourcelength
                    bhs       AssetReadByteInvalid
                    bsr      AssetPointer
                    tst       <asseterror
                    bne       AssetReadByteError
                    ldb       ,u
                    andcc     #$FE
                    puls      x,y,u,pc
AssetReadByteInvalid  ldb       #E$BMode
                    orcc      #1
                    puls      x,y,u,pc
AssetReadByteError    ldb       <asseterror
                    orcc      #1
                    puls      x,y,u,pc

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_ASSET_DATA
* ===== wildbits-asset-data =====
* Owned expanded-resource slab. One mapping at a time, private I/O staging.
assetfirst          rmb       2
assetblocks         rmb       1
assetowned          rmb       1
assetmapped         rmb       1
assetpage           rmb       1
assetmapbase        rmb       2
assetoutoffset      rmb       2
assetchunk          rmb       2
assetinputleft      rmb       2
assetinputpointer   rmb       2
assetinputend       rmb       2
asseterror          rmb       1
assetexiterror      rmb       1
assetbyte           rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_ASSET_WRITE
* ===== wildbits-asset-write =====
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

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_LZW_CODE
* ===== wildbits-lzw-code =====
* AGI LZW, adapted from mnln.asm PicRenderSetup. No file, hardware or
* destination-address assumptions. Input bits are least significant first.
*
* DecodeLzw: X = private 8192-byte workspace, Y = exact expanded length,
* U = private data base, DP = its high byte. Returns C clear on success;
* C set/B = error otherwise. U and DP retained; D/X/Y may change.
* Callbacks LzwReadByte and LzwWriteByte take/return B, carry/error in B,
* and preserve X/Y/U/DP. The writer must not retain mapped pointers.
* Dictionary width grows from 9 to 11 bits; clear=256, end=257.
                    ifndef PLATFORM_WILDBITS_MEMORY_RESOURCES_BINDINGS
                    use platform/wildbits-memory-resources-bindings.asm
                    endc
                    ifndef SHARED_RESOURCE_LZW_DEFINED
                    use shared/resource-lzw.asm
                    endc
DecodeLzw           stu       <lzwbase
                    stx       <lzwwork
                    sty       <lzwexpected
                    clr       <lzwerror
                    clr       <lzwbits
                    clr       <lzwproduced
                    clr       <lzwproduced+1
                    cmpy      #0
                    lbeq      LzwInvalid
                    lbsr      LzwReset
LzwLoop             lbsr      LzwReadCode
                    lbcs      LzwReturn
                    cmpd      #256
                    beq       LzwClear
                    cmpd      #257
                    lbeq      LzwEnd
                    std       <lzwcurrent
                    tst       <lzwhasprevious
                    bne       LzwString
                    cmpd      #256
                    lbhs      LzwInvalid
                    stb       <lzwfirst
                    lbsr      LzwEmit
                    lbcs      LzwReturn
                    lbra      LzwRemember
LzwClear            lbsr      LzwReset
                    bra       LzwLoop
LzwString           clr       <lzwtop
                    clr       <lzwtop+1
                    cmpd      <lzwnext
                    lbhi      LzwInvalid
                    bne       LzwWalk
                    ldb       <lzwpreviousfirst
                    lbsr      LzwPush
                    lbcs      LzwReturn
                    ldd       <lzwprevious
                    RESOURCE_LZW_WALK LzwWalk,LzwLiteral,x
LzwLiteral          stb       <lzwfirst
                    bsr      LzwPush
                    bcs      LzwReturn
LzwPop              ldd       <lzwtop
                    subd      #1
                    std       <lzwtop
                    ldx       <lzwwork
                    leax      6144,x
                    ldb       d,x
                    lbsr      LzwEmit
                    bcs      LzwReturn
                    ldd       <lzwtop
                    bne       LzwPop
                    ldd       <lzwnext
                    cmpd      #2048
                    bhs       LzwRemember
                    RESOURCE_LZW_INSERT x,lzwnext,lzwprevious,lzwfirst,lzwchain,0
                    cmpd      <lzwthreshold
                    blo       LzwRemember
                    lda       <lzwwidth
                    cmpa      #11
                    bhs       LzwRemember
                    inc       <lzwwidth
                    lsl       <lzwthreshold+1
                    rol       <lzwthreshold
LzwRemember         ldd       <lzwcurrent
                    std       <lzwprevious
                    ldb       <lzwfirst
                    stb       <lzwpreviousfirst
* The flag is Boolean; do not let long resources wrap it to zero.
                    lda       #1
                    sta       <lzwhasprevious
                    lbra      LzwLoop
LzwEnd              ldd       <lzwproduced
                    cmpd      <lzwexpected
                    bne       LzwInvalid
                    clrb
                    andcc     #$FE
LzwReturn           ldu       <lzwbase
                    rts
LzwReset            RESOURCE_LZW_RESET lzwnext,lzwthreshold,lzwwidth,0,0
                    clr       <lzwhasprevious
                    rts
LzwPush             pshs      x,b
                    ldd       <lzwtop
                    cmpd      #2048
                    bhs       LzwPushBad
                    ldx       <lzwwork
                    leax      6144,x
* Saved B precedes X on the 6809 stack.
                    ldd       <lzwtop
                    leax      d,x
                    ldb       ,s
                    stb       ,x
                    ldd       <lzwtop
                    addd      #1
                    std       <lzwtop
                    puls      b,x
                    andcc     #$FE
                    rts
LzwPushBad          puls      b,x
                    bra       LzwInvalid
LzwEmit             pshs      b
                    ldd       <lzwproduced
                    cmpd      <lzwexpected
                    bhs       LzwEmitBad
                    addd      #1
                    std       <lzwproduced
                    puls      b
                    lbsr      LzwWriteByte
                    rts
LzwEmitBad          puls      b
LzwInvalid          ldb       #E$BMode
                    stb       <lzwerror
                    orcc      #1
                    rts
* Keep the raw last byte plus its remaining-bit count. Fetch only the
* bytes needed for this code; a valid final code must not require padding
* beyond the compressed source. Align/mask the window with the CoCo core.
LzwReadCode         tst       <lzwbits
                    bne       LzwWindowFirst
                    lbsr      LzwReadByte
                    bcs       LzwReadError
                    stb       <lzwbyte
                    lda       #8
                    sta       <lzwbits
LzwWindowFirst      ldb       <lzwbyte
                    stb       <lzwcode+1
                    lda       #8
                    suba      <lzwbits
                    sta       <lzwcount
                    lbsr      LzwReadByte
                    bcs       LzwReadError
                    stb       <lzwcode
                    stb       <lzwbyte
                    lda       <lzwwidth
                    adda      <lzwcount
                    cmpa      #16
                    bls       LzwWindowTwo
                    lbsr      LzwReadByte
                    bcs       LzwReadError
                    stb       <lzwweight
                    stb       <lzwbyte
                    lda       #24
                    bra       LzwWindowCount
LzwWindowTwo        clr       <lzwweight
                    lda       #16
LzwWindowCount      suba      <lzwcount
                    suba      <lzwwidth
                    sta       <lzwbits
                    ldb       <lzwcount
                    RESOURCE_LZW_EXTRACT lzwweight,lzwcode,lzwwidth,LzwCodeMasks,LzwWindowShift,LzwWindowMask
                    andcc     #$FE
                    rts
LzwReadError        stb       <lzwerror
                    rts
LzwCodeMasks        RESOURCE_LZW_MASKS

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_LZW_DATA
* ===== wildbits-lzw-data =====
* Private control state. The caller supplies 8192 bytes of workspace in X:
* 2048 three-byte dictionary entries, followed by a 2048-byte string stack.
lzwbase             rmb       2
lzwwork             rmb       2
lzwnext             rmb       2
lzwthreshold        rmb       2
lzwprevious         rmb       2
lzwcurrent          rmb       2
lzwchain            rmb       2
lzwtop              rmb       2
lzwcode             rmb       2
lzwweight           rmb       2        ; first byte is the window high byte
lzwexpected         rmb       2
lzwproduced         rmb       2
lzwwidth            rmb       1
lzwbyte             rmb       1        ; raw last source byte
lzwbits             rmb       1        ; remaining bits in raw byte
lzwcount            rmb       1        ; window alignment (0..7)
lzwhasprevious      rmb       1
lzwfirst            rmb       1
lzwpreviousfirst    rmb       1
lzwerror            rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_RESOURCE_CLI
* ===== wildbits-resource-cli =====
* Shared probe argument/output body. Owning module supplies state and help.
start               stu       <resourcebase
                    ifne      GAME_TRACE
                    clr       gametracestagebyte,u
                    clr       gametracekeybyte,u
                    clr       gametracemenuhit,u
                    endc
                    ifne      GAME_PRESENTATION
                    lda       #$FF
                    sta       gameclockpath,u
                    clr       gameclockmuted,u
                    clr       terminalchanged,u
                    clr       gamebackgroundowned,u
                    clr       <soundpath
                    clra
                    clrb
                    std       textstoremodule,u
                    std       textstoreentry,u
                    std       textwaitentry,u
                    std       textrectentry,u
                    std       restartentry,u
                    pshs      x
                    lbsr      GameTextInitialize
                    puls      x
                    endc
                    clr       <resourceopen
                    ifne      AGI_ASSET
                    ifne      DECODE_PICTURE
                    clr       <pictureowned
                    clr       <picturemapped
                    clr       <decodeerror
                    ifne      PRESENT_PICTURE
                    pshs      x
                    lbsr      PresentationInitialize
                    puls      x
                    endc
                    endc
                    endc
                    ifne      AGI_ASSET
                    clr       <assetowned
                    clr       <assetmapped
                    clr       <asseterror
                    clr       <resourcekind
                    ifne      AGI_VM
                    pshs      x
                    clr       <replaylimit
                    clr       <replayused
                    clr       <replayused+1
                    clr       <replaycheckpoint
                    clr       <replaycheckpoint+1
                    clr       <vmroompending
                    clr       <vmroomchanges
                    lda       #36
                    sta       <vmhorizon
                    lda       #1
                    sta       <vmplayercontrol
                    lbsr      InputInitialize
                    lbsr      ScreenInitialize
                    lbsr      StringsInitialize
                    lbsr      MenuInitialize
                    lbsr      VmClearCache
                    puls      x
                    endc
                    pshs      x
                    leax      AssetIntercept,pcr
                    os9       F$Icpt
                    puls      x
                    lbcs      Exit
                    endc
                    ifne      DECODE_PICTURE
                    ifeq      AGI_ASSET
                    clr       <pictureowned
                    clr       <picturemapped
                    clr       <decodeerror
                    endc
                    pshs      x
                    ifne      PRESENT_PICTURE
                    ifeq      AGI_ASSET
                    lbsr      PresentationInitialize
                    endc
                    leax      intercept,pcr
                    else
                    leax      DecodeIntercept,pcr
                    endc
                    os9       F$Icpt
                    lbcs      Exit
                    puls      x
                    endc
                    lbsr      SkipSpaces
                    stx       <argdirectory
FindNumber          lda       ,x+
                    cmpa      #C$CR
                    lbeq      ArgumentsBad
                    cmpa      #C$SPAC
                    bne       FindNumber
                    lbsr      SkipSpaces
                    clr       <argnumber
                    clr       <argnumber+1
                    lda       ,x
                    cmpa      #'0
                    lblo      ArgumentsBad
                    cmpa      #'9
                    lbhi      ArgumentsBad
NumberDigit         lda       ,x+
                    cmpa      #'0
                    blo       NumberEnd
                    cmpa      #'9
                    bhi       NumberEnd
                    suba      #'0
                    sta       <argdigit
                    ldd       <argnumber
                    lda       #10
                    mul
                    addb      <argdigit
                    adca      #0
                    cmpd      #255
                    lbhi      ArgumentsBad
                    std       <argnumber
                    bra       NumberDigit
NumberEnd           cmpa      #C$CR
                    beq       LoadResource
                    cmpa      #C$SPAC
                    lbne      ArgumentsBad
                    lbsr      SkipSpaces
                    lda       ,x
                    cmpa      #C$CR
                    lbne      ArgumentsBad
LoadResource        equ       *
                    ifne      GAME_PRESENTATION
                    lbsr      GameFontLoad
                    bcs      Exit
                    lbsr      GameTerminalEnter
                    bcs      Exit
                    endc
                    ldx       <argdirectory
                    ldy       <argnumber
                    ldu       <resourcebase
                    ifne      AGI_ASSET
                    lbsr      LoadAsset
                    bcs       Exit
                    ifne      AGI_VM
                    lbsr      StartLogic
                    bcs       Exit
                    ifne      GAME_PRESENTATION
                    clrb
                    bra      Exit
                    else
                    ldu       <resourcebase
                    leax      vmvariables,u
                    ldy       #512
                    stx       <resourcepointer
                    sty       <resourceremaining
                    bra      WriteMore
                    endc
                    else
                    lbsr      AssetWrite
                    endc
                    bra      Exit
                    else
                    bsr      LoadPicture
                    bcs       Exit
                    endc
                    ifne      DECODE_PICTURE
                    lbsr      DecodeLines
                    bcs       Exit
                    ifne      PRESENT_PICTURE
                    lbsr      PresentPicture
                    else
                    lbsr      PictureWrite
                    endc
                    bra      Exit
                    endc
                    ifeq      GAME_PRESENTATION
                    stx       <resourcepointer
                    sty       <resourceremaining
WriteMore           lda       #1
                    ldx       <resourcepointer
                    ldy       <resourceremaining
                    os9       I$Write
                    bcs       Exit
                    cmpy      #0
                    beq      WriteBad
                    cmpy      <resourceremaining
                    bhi      WriteBad
                    tfr       y,d
                    addd      <resourcepointer
                    std       <resourcepointer
                    ldd       <resourceremaining
                    pshs      y
                    subd      ,s++
                    std       <resourceremaining
                    bne       WriteMore
                    clrb
                    endc
Exit                equ       *
                    ifne      GAME_PRESENTATION
                    pshs      b
                    lbsr      GameUnmapForExit
                    bcc       GameExitMappingsReady
                    tst       ,s
                    bne       GameExitMappingsReady
                    stb       ,s
GameExitMappingsReady lbsr    GameClockClose
                    bcc       GameClockExitDone
                    tst       ,s
                    bne       GameClockExitRetry
                    stb       ,s
GameClockExitRetry  lbsr      GameClockClose
GameClockExitDone   lbsr      GameSoundStop
                    bcc       GameSoundExitDone
                    tst       ,s
                    bne       GameSoundExitRetry
                    stb       ,s
GameSoundExitRetry  lbsr      GameSoundStop
GameSoundExitDone   lbsr      GameTextUnlink
                    bcc       GameTextExitDone
                    tst       ,s
                    bne       GameTextExitRetry
                    stb       ,s
GameTextExitRetry   lbsr      GameTextUnlink
GameTextExitDone    puls      b
                    endc
                    ifne      AGI_ASSET
                    stb       <assetexiterror
                    ifne      AGI_VM
                    lbsr      VmReleaseResources
                    else
                    lbsr      AssetRelease
                    endc
                    bcc       AssetExitDone
                    tst       <assetexiterror
                    bne       AssetExitRetry
                    stb       <assetexiterror
AssetExitRetry      lbsr      AssetRelease
AssetExitDone       ldb       <assetexiterror
                    endc
                    ifne      DECODE_PICTURE
                    stb       <pictureexiterror
                    lbsr      PictureRelease
                    bcc       PictureExitResult
                    tst       <pictureexiterror
                    bne       PictureExitRetry
                    stb       <pictureexiterror
PictureExitRetry    lbsr      PictureRelease
PictureExitResult   equ       *
                    ifne      GAME_PRESENTATION
                    lbsr      GameReleaseBackground
                    bcc       GameBackgroundExitDone
                    tst       <pictureexiterror
                    bne       GameBackgroundExitRetry
                    stb       <pictureexiterror
GameBackgroundExitRetry lbsr  GameReleaseBackground
GameBackgroundExitDone equ   *
                    endc
                    ifne      PRESENT_PICTURE
                    lbsr      PresentationRelease
                    bcc       PresentationExitResult
                    tst       <pictureexiterror
                    bne       PresentationExitResult
                    stb       <pictureexiterror
PresentationExitResult equ    *
                    endc
                    ldb       <pictureexiterror
                    endc
                    ifne      GAME_PRESENTATION
                    pshs      b
                    lbsr      GameTerminalRestore
                    bcc       GameTerminalExitDone
                    tst       ,s
                    bne       GameTerminalExitRetry
                    stb       ,s
GameTerminalExitRetry lbsr    GameTerminalRestore
GameTerminalExitDone puls     b
                    endc
                    ifne      GAME_TRACE
                    lbsr      GameTraceError
                    endc
                    os9       F$Exit
                    ifeq      GAME_PRESENTATION
WriteBad            ldb       #E$BMode
                    bra      Exit
                    endc
ArgumentsBad        leax      help,pcr
                    ldy       #80
                    lda       #2
                    os9       I$WritLn
                    ldb       #E$IllArg
                    lbra      Exit
SkipSpaces          lda       ,x+
                    cmpa      #C$SPAC
                    beq       SkipSpaces
                    leax      -1,x
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_RESOURCE_CODE
* ===== wildbits-resource-code =====
* Native plain AGI picture-resource boundary, shared by probe/future decoder.
* LoadPicture: X = CR/space-terminated game directory; Y = picture 0..255;
* U = private resource-data base; DP = high byte of that base.
* Success: X = private command buffer, Y = length, U = private data base,
* carry clear. Failure: carry set, B = OS-9 error. All opened paths are closed
* on normal success/error paths. No writable code, fixed buffers or hardware.
* Header format here is the existing CoCo game's seven-byte resource format.
                    ifne      AGI_ASSET
* Generic header locator returns an open volume positioned at stored bytes.
ResourceLocate      equ       *
                    else
LoadPicture         equ       *
                    endc
                    stu       <resourcebase
                    sty       resourcenumber,u
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
ResourceDirSlash    sty       resourcenameend,u
                    ifne      AGI_ASSET
                    ldb       <resourcekind
                    cmpb      #3
                    lbhi      ResourceArgument
                    leax      ResourceDirectoryTable,pcr
                    lslb
                    ldd       b,x
                    leax      d,x
                    else
                    leax      ResourcePicDir,pcr
                    endc
                    lbsr      ResourceSuffix
                    lbsr      OpenPicturePath
                    lbcs      ResourceFailed
                    ldd       resourcenumber,u
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
                    sta       resourcevolume,u
                    clr       resourceoffset,u
                    lda       ,x
                    anda      #$0F
                    sta       resourceoffset+1,u
                    ldd       1,x
                    std       resourceoffset+2,u
                    lbsr      ResourceClose
                    lbcs      ResourceFailed
                    ldy       resourcenameend,u
                    leax      ResourceVol,pcr
                    lbsr      ResourceSuffix     ends at CR after "vol."
                    leay      -1,y
                    lda       resourcevolume,u
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
                    ldx       resourceoffset,u
                    ldu       resourceoffset+2,u
                    lda       <resourcepath
                    os9       I$Seek
                    bcs      ResourceFailed
                    ldu       <resourcebase
                    leax      resourceheader,u
                    ldy       #7
                    lbsr      ResourceReadExact
                    bcs      ResourceFailed
                    ldu       <resourcebase
                    leax      resourceheader,u
                    ldd       ,x
                    cmpd      #$1234
                    bne      ResourceInvalid
                    lda       2,x
                    bita      #$80
                    ifne      AGI_ASSET
                    beq       ResourceHeaderFlagsOK
                    ldb       <resourcekind
                    cmpb      #1                packed encoding applies only to pictures
                    bne      ResourceInvalid
ResourceHeaderFlagsOK equ     *
                    else
                    bne      ResourceInvalid   plain-resource probe only
                    endc
                    anda      #$0F
                    cmpa      resourcevolume,u
                    bne      ResourceInvalid
                    ldb       3,x               decoded size is little endian
                    lda       4,x
                    std       <resourcelength
                    beq      ResourceInvalid
                    ifne      AGI_ASSET
                    ldb       5,x
                    lda       6,x
                    std       <resourcestored
                    beq      ResourceInvalid
                    ldu       <resourcebase
                    clrb
                    rts
                    else
                    cmpd      #8192
                    bhi      ResourceInvalid
                    ldb       5,x               stored size is little endian
                    lda       6,x
                    cmpd      <resourcelength    reject LZW, do not misdecode it
                    bne      ResourceInvalid
                    leax      resourcecommands,u
                    ldy       <resourcelength
                    bsr      ResourceReadExact
                    bcs      ResourceFailed
                    ldu       <resourcebase
                    leax      resourcecommands,u
                    ldd       <resourcelength
                    leay      d,x
                    lda       -1,y
                    cmpa      #$FF
                    bne       ResourceInvalid
                    bsr      ResourceClose
                    bcs       ResourceFailed
                    ldu       <resourcebase
                    leax      resourcecommands,u
                    ldy       <resourcelength
                    clrb
                    rts
                    endc
ResourceArgument    ldb       #E$IllArg
                    bra       ResourceFailed
ResourceInvalid     ldb       #E$BMode
ResourceFailed      stb       <resourceerror
                    tst       <resourceopen
                    beq       ResourceReturnErr
                    bsr      ResourceClose
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
                    ifne      AGI_ASSET
ResourceDirectoryTable fdb    ResourceLogDir-ResourceDirectoryTable
                    fdb       ResourcePicDir-ResourceDirectoryTable
                    fdb       ResourceViewDir-ResourceDirectoryTable
                    fdb       ResourceSoundDir-ResourceDirectoryTable
ResourceLogDir      fcc       /logDir/
                    fcb       C$CR
ResourceViewDir     fcc       /viewDir/
                    fcb       C$CR
ResourceSoundDir    fcc       /sndDir/
                    fcb       C$CR
                    endc

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_RESOURCE_DATA
* ===== wildbits-resource-data =====
* Private picture-resource state. Include once in the owning module's RMB area.
                    ifne      AGI_ASSET
resourcekind        rmb       1
resourcestored      rmb       2
                    endc
resourcebase        rmb       2
resourcepath        rmb       1
resourceopen        rmb       1
resourceerror       rmb       1
                    ifeq GAME_PRESENTATION
resourcevolume      rmb       1
resourcenumber      rmb       2
resourceoffset      rmb       4
                    endc
resourcelength      rmb       2
resourcepointer     rmb       2
resourceremaining   rmb       2
                    ifeq GAME_PRESENTATION
resourcenameend     rmb       2
                    endc
                    ifeq      AGI_ASSET
resourceentry       rmb       3
resourceheader      rmb       7
                    endc
                    ifgt      .-$100
                    error     Picture resource control fields must fit the private direct page
                    endc
                    ifne GAME_PRESENTATION
resourcevolume      rmb       1
resourcenumber      rmb       2
resourceoffset      rmb       4
resourcenameend     rmb       2
                    endc
resourcefilename    rmb       160
                    ifne      AGI_ASSET
resourceentry       rmb       3
resourceheader      rmb       7
                    endc
resourcecommands    rmb       8192

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_ROOM_CODE
* ===== wildbits-room-code =====
* Room requests adapted from mnln NewRoomSetup. Resource reset runs only
* after the call stack unwinds. Keep the root logic and private menu labels.
RequestRoom         stb       <vmnewroom
                    lda       #1
                    sta       <vmroompending
                    clrb
                    rts
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
ApplyRoomChange     tst       <vmdepth
                    lbne      VmInvalid
                    inc       <vmroomchanges
                    lda       <vmroomchanges
                    cmpa      #64
                    lbhs      VmInvalid
                    lbsr      AssetUnmap
                    lbcs      RoomReturn
                    ifne      GAME_PRESENTATION
* Release foreign mappings before owned audio I/O and cancel only the
* software command line. SCF's queued keys remain available to the player.
                    lbsr      PictureUnmap
                    lbcs      RoomReturn
                    lbsr      GameSoundStop
                    lbcs      RoomReturn
                    lbsr      GameCancelLine
                    endc
                    lda       #1
                    sta       <vmcacheindex
RoomFreeNext        ldb       <vmcacheindex
                    lbsr      VmSlotAddress
                    tst       1,x
                    beq       RoomFreeAdvance
                    stx       <vmslot
                    lbsr      VmRestoreAsset
                    inc       <assetowned
                    lbsr      AssetRelease
                    lbcs      RoomFreeFailure
                    ldx       <vmslot
                    clr       1,x
RoomFreeAdvance     inc       <vmcacheindex
                    ldb       <vmcacheindex
                    cmpb      #32
                    blo       RoomFreeNext
                    ldu       <resourcebase
                    leax      vmobjects,u
                    ldy       #64
RoomResetObject     OBJECT_ROOM_RESET x,1
                    leax      43,x
                    leay      -1,y
                    bne       RoomResetObject
                    leax      vmvariables,u
                    AGI_ROOM_VARIABLES
                    clr       4,x
                    clr       5,x
                    lda       #36
                    sta       <vmhorizon
                    lda       vmobjects+5,u
                    sta       16,x
* Place ego on the opposite edge of the room, retaining its view width.
                    OBJECT_ROOM_ENTRY vmobjects,u
RoomEnterTop        equ RoomEntryTop
RoomEnterRight      equ RoomEntryRight
RoomEnterBottom     equ RoomEntryBottom
                    lda       #1
* Like CoCo NewRoomSetup, release program/stop-motion control on entry.
* The destination logic may explicitly take control again afterwards.
                    sta       <vmplayercontrol
                    ifne      GAME_PRESENTATION
                    clr       gameblockenabled,u
                    endc
                    sta       vmflags+5,u
                    clr       <replayused
                    clr       <replayused+1
                    clr       <replaycheckpoint
                    clr       <replaycheckpoint+1
                    ldb       <vmnewroom
                    lbsr      VmLoadLogic
                    bcs       RoomReturn
                    clr       <vmcurrent
                    clrb
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    ldd       10,x
                    std       <vmip
                    clr       <vmroompending
                    clrb
RoomReturn          rts
RoomFreeFailure     clr       <assetowned
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_ROOM_DATA
* ===== wildbits-room-data =====
* Room transitions are requests; nested logic unwinds before resource teardown.
vmroompending       rmb       1
vmnewroom           rmb       1
vmroomchanges       rmb       1
vmhorizon           rmb       1
vmplayercontrol     rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_VIEW_CODE
* ===== wildbits-view-code =====
* View/loop/cel selection and queries adapted from mnln. View records are
* mapped only while reading metadata. Object positions/indices are private;
* cel locations are logical offsets, never pointers into a foreign window.
                    ifndef PLATFORM_WILDBITS_OBJECTS_BINDINGS
                    use platform/wildbits-objects-bindings.asm
                    endc
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
ViewCommand         lbsr      ObjectAddress
                    lbcs      ViewReturn
                    stx       <viewobject
                    ldb       <vmopcode
                    cmpb      #49
                    lbhs      ViewQuery
                    ldu       <resourcebase
                    ldb       vmarguments+1,u
                    lda       <vmopcode
                    bita      #1
                    bne       ViewArgumentReady
                    lbsr      ObjectArgumentValue
ViewArgumentReady   lda       <vmopcode
                    cmpa      #42
                    bls       ViewSetResource
                    cmpa      #44
                    bls       ViewSetLoop
                    stb       $0E,x
                    bra       ViewSelect
ViewSetLoop         stb       $0A,x
                    bra       ViewSelect
ViewSetResource     stb       5,x
ViewSelect          ldb       5,x
                    lda       #2
                    lbsr      VmLoadResource
                    lbcs      ViewReturn
                    lbsr      VmRestoreAsset
                    ldd       #2
                    lbsr      AssetReadByte
                    lbcs      ViewRestore
                    tstb
                    lbeq      ViewInvalid
                    ldx       <viewobject
                    stb       $0B,x
                    clra
                    lslb
                    rola
                    addd      #5
                    std       <viewminoffset
                    cmpd      <resourcelength
                    lbhi      ViewInvalid
                    ldb       $0A,x
                    cmpb      $0B,x
                    blo       ViewLoopValid
                    lda       <vmopcode
                    cmpa      #42
                    lbhi      ViewInvalid
                    clr       $0A,x
                    clrb
ViewLoopValid equ *
                    OBJECT_VIEW_TABLE_ENTRY 0
                    lbsr      AssetReadByte
                    lbcs      ViewRestore
                    tstb
                    lbeq      ViewInvalid
                    ldx       <viewobject
                    stb       $0F,x
                    clra
                    lslb
                    rola
                    addd      #1
                    addd      <viewloopbase
                    lbcs      ViewInvalid
                    std       <viewminoffset
                    cmpd      <resourcelength
                    lbhi      ViewInvalid
                    ldb       $0E,x
                    cmpb      $0F,x
                    blo       ViewCelValid
                    lda       <vmopcode
                    cmpa      #44
                    lbhi      ViewInvalid
                    clr       $0E,x
                    clrb
ViewCelValid equ *
                    OBJECT_VIEW_TABLE_ENTRY 1
                    addd      #3
                    lbcs      ViewInvalid
                    cmpd      <resourcelength
                    lbhi      ViewInvalid
                    ldd       <viewcelbase
                    lbsr      AssetReadByte
                    bcs      ViewRestore
                    tstb
                    lbeq      ViewInvalid
                    cmpb      #160
                    lbhi      ViewInvalid
                    ldx       <viewobject
                    stb       $1C,x
                    ldd       <viewcelbase
                    addd      #1
                    lbsr      AssetReadByte
                    bcs      ViewRestore
                    tstb
                    beq      ViewInvalid
                    cmpb      #168
                    bhi      ViewInvalid
                    ldx       <viewobject
                    stb       $1D,x
                    ldd       <viewcelbase
                    addd      #2
                    lbsr      AssetReadByte
                    bcs       ViewRestore
                    ldx       <viewobject
                    stb       $12,x
                    ldd       <viewcelbase
                    std       $10,x
ViewPositionCel     ldd       <$1C,x
                    OBJECT_CEL_CLIP x,ViewCelHeightClip,ViewCelClipDone,ViewCelRightClip
                    clrb
ViewRestore         pshs      cc,b
                    lbsr      AssetUnmap
                    bcc       ViewUnmapped
                    leas      2,s
                    pshs      cc,b
ViewUnmapped        ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    puls      cc,b,pc
ViewInvalid         ldb       #E$BMode
                    orcc      #1
                    bra       ViewRestore
ViewReturn          rts
ViewQuery           cmpb      #49
                    beq      cmd_last_cel
                    cmpb      #50
                    beq      cmd_current_cel
                    cmpb      #51
                    beq      cmd_current_loop
                    cmpb      #52
                    beq      cmd_current_view
                    bra      cmd_number_of_loops
* ObjectAddress already validated the object and left its record in X.
* Assembly-time object query operand/storage interface; no runtime dispatch.
                    ifne      WILDBITS
                    ifndef PLATFORM_WILDBITS_OBJECTS_BINDINGS
                    use platform/wildbits-objects-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_OBJECTS_BINDINGS
                    use platform/coco-objects-bindings.asm
                    endc
                    endc
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
                    OBJECT_EMIT_VIEW_QUERIES
ViewInvalidQuery    ldb       #E$BMode
                    orcc      #1
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_VIEW_DATA
* ===== wildbits-view-data =====
* Transient mapped view lookup controls; object records store offsets.
viewobject          rmb       2
viewloopbase        rmb       2
viewcelbase         rmb       2
viewminoffset       rmb       2

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
