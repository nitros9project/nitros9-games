* Cold save/restore operations. The game copies and unlinks this module before
* executing it in its private fill workspace. No formatting or flood-fill
* decoder may run while this code is active.
AUDIO_USER_COPY     equ 1
WILDBITS            equ 1
WILDBITS_LAYOUT_ONLY equ 1
                    use platform/wildbits-runtime.asm
                    org 0
                    mod StateEnd,StateName,Sbrtn+Objct,ReEnt+1,StateEntry,0
StateName           fcs /wbstate/
                    fcb 1
StateEntry          bra StateBegin
                    STATE_ABI
                    fdb AudioBlobEnd-AudioBlobStart,AudioInstall
* A=0 save, 1 validate/stage restore, 2 apply after nested logic unwinds.
* X=filename, Y=engine callback table, U=the game's private base.
StateBegin          stu StateBase,pcr
                    sty StateAPI,pcr
                    cmpa #2
                    lbeq StateApply
                    sta StateMode,pcr
                    stx StateFilename,pcr
                    clr StateOpen,pcr
                    clr StateCreated,pcr
                    clr StateMapped,pcr
                    clr StateOwned,pcr
                    clr StateReady,pcr
                    clr StateError,pcr
                    tst vmgameid,u
                    lbeq StateBad
                    tsta
                    lbne StatePrepare
StateSave           leax StateHeader,pcr
                    ldd #$5753
                    std ,x
                    lda #1
                    sta 2,x
                    clr 3,x
                    ldd #StateCoreBytes+160
                    std 4,x
                    leay vmgameid,u
                    ldb #8
StateSaveID         lda ,y+
                    sta 8,x
                    leax 1,x
                    decb
                    bne StateSaveID
                    ldu StateBase,pcr
                    ldb vmcache,u
                    stb StateHeader+16,pcr
                    clr StateHeader+17,pcr
                    tst gamebackgroundowned,u
                    beq StateSaveCurrentPicture
                    ldd gamebackgroundfirst,u
                    bra StateSavePicture
StateSaveCurrentPicture tst <pictureowned
                    beq StateSaveNoPicture
                    ldd <picturefirst
StateSavePicture    std StatePicture,pcr
                    lda #1
                    sta StateHeader+3,pcr
                    ldd #StateCoreBytes+160+26880
                    std StateHeader+4,pcr
StateSaveNoPicture  lbsr StateCaptureCache
                    ldx StateFilename,pcr
                    lda #WRITE.
                    ldb #3
                    os9 I$Create
                    lbcs StateFail
                    sta StatePath,pcr
                    inc StateOpen,pcr
                    inc StateCreated,pcr
                    ldd #$FFFF
                    std StateCRC,pcr
                    clr StateHeader+6,pcr
                    clr StateHeader+7,pcr
                    leax StateHeader,pcr
                    ldy #18
                    lbsr StateWriteExact
                    lbcs StateFail
                    leax StateRanges,pcr
                    stx StateRange,pcr
StateSaveRange      ldx StateRange,pcr
                    ldd ,x++
                    ldy ,x++
                    stx StateRange,pcr
                    cmpy #0
                    beq StateSaveCache
                    ldu StateBase,pcr
                    leax d,u
                    cmpd #inventoryloaded
                    bne StateSaveField
                    tst ,x
                    bne StateSaveField
* Unloaded inventory has no valid length/count; do not persist scratch bytes.
                    leax StateBuffer,pcr
                    clra
                    clrb
                    std ,x
                    std 2,x
                    sta 4,x
StateSaveField      lbsr StateChecksum
                    lbsr StateWriteExact
                    lbcs StateFail
                    bra StateSaveRange
StateSaveCache      leax StateCache,pcr
                    ldy #160
                    lbsr StateChecksum
                    lbsr StateWriteExact
                    lbcs StateFail
                    tst StateHeader+3,pcr
                    beq StateSaveHeader
                    ldd #0
                    std StateCursor,pcr
StateSavePixels     tst <aborted
                    lbne StateAbort
                    ldd #26880
                    subd StateCursor,pcr
                    beq StateSaveHeader
                    cmpd #512
                    bls StateSavePixelCount
                    ldd #512
StateSavePixelCount std StateCount,pcr
                    ldx StateCursor,pcr
                    ldd StatePicture,pcr
                    lbsr StateMapSpan
                    lbcs StateFail
                    leax StateBuffer,pcr
                    ldy StateCount,pcr
StateSavePixelCopy  lda ,u+
                    sta ,x+
                    leay -1,y
                    bne StateSavePixelCopy
                    lbsr StateUnmap
                    lbcs StateFail
                    leax StateBuffer,pcr
                    ldy StateCount,pcr
                    lbsr StateChecksum
                    lbsr StateWriteExact
                    lbcs StateFail
                    ldd StateCursor,pcr
                    addd StateCount,pcr
                    std StateCursor,pcr
                    bra StateSavePixels
StateSaveHeader     ldd StateCRC,pcr
                    std StateHeader+6,pcr
                    lda StatePath,pcr
                    clrb
                    ldx #0
                    ldu #0
                    os9 I$Seek
                    lbcs StateFail
                    leax StateHeader,pcr
                    ldy #18
                    lbsr StateWriteExact
                    lbcs StateFail
                    lbsr StateClose
                    lbcs StateFail
                    clr StateCreated,pcr
                    clrb
                    rts

* Read and check the entire file before changing any game state or cache.
StatePrepare        lda #READ.
                    ldx StateFilename,pcr
                    os9 I$Open
                    lbcs StateFail
                    sta StatePath,pcr
                    inc StateOpen,pcr
                    leax StateHeader,pcr
                    ldy #18
                    lbsr StateReadExact
                    lbcs StateFail
                    ldd StateHeader,pcr
                    cmpd #$5753
                    lbne StateBad
                    lda StateHeader+2,pcr
                    cmpa #1
                    lbne StateBad
                    lda StateHeader+3,pcr
                    cmpa #1
                    lbhi StateBad
                    ldd #StateCoreBytes+160
                    tst StateHeader+3,pcr
                    beq StatePrepareLength
                    addd #26880
StatePrepareLength  cmpd StateHeader+4,pcr
                    lbne StateBad
                    ldu StateBase,pcr
                    leax StateHeader+8,pcr
                    leay vmgameid,u
                    ldb #8
StateCheckID        lda ,x+
                    cmpa ,y+
                    lbne StateBad
                    decb
                    bne StateCheckID
                    ldb StateHeader+16,pcr
                    cmpb vmcache,u
                    lbne StateBad
                    tst StateHeader+17,pcr
                    lbne StateBad
                    ldd StateHeader+4,pcr
                    addd #8191
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    stb StateBlocks,pcr
                    os9 F$AllRAM
                    lbcs StateFail
                    std StateFirst,pcr
                    inc StateOwned,pcr
                    ldd #$FFFF
                    std StateCRC,pcr
                    ldd #0
                    std StateCursor,pcr
StateReadPayload    tst <aborted
                    lbne StateAbort
                    ldd StateHeader+4,pcr
                    subd StateCursor,pcr
                    beq StateReadEnd
                    cmpd #512
                    bls StateReadCount
                    ldd #512
StateReadCount      std StateCount,pcr
                    tfr d,y
                    leax StateBuffer,pcr
                    lbsr StateReadExact
                    lbcs StateFail
                    leax StateBuffer,pcr
                    ldy StateCount,pcr
                    lbsr StateChecksum
                    ldx StateCursor,pcr
                    ldd StateFirst,pcr
                    lbsr StateMapSpan
                    lbcs StateFail
                    leax StateBuffer,pcr
                    ldy StateCount,pcr
StateStageCopy      lda ,x+
                    sta ,u+
                    leay -1,y
                    bne StateStageCopy
                    lbsr StateUnmap
                    lbcs StateFail
                    ldd StateCursor,pcr
                    addd StateCount,pcr
                    std StateCursor,pcr
                    lbra StateReadPayload
StateReadEnd        ldd StateCRC,pcr
                    cmpd StateHeader+6,pcr
                    lbne StateBad
* Reject trailing bytes, not just short snapshots.
                    lda StatePath,pcr
                    leax StateBuffer,pcr
                    ldy #1
                    os9 I$Read
                    lbcc StateBad
                    cmpb #E$EOF
                    lbne StateFail
                    lbsr StateClose
                    lbcs StateFail
                    lbsr StateValidate
                    lbcs StateFail
                    inc StateReady,pcr
                    clrb
                    rts

* Capture only kind/id/scan metadata. Physical slab handles never enter files.
StateCaptureCache   ldu StateBase,pcr
                    leax vmcache,u
                    leay StateCache,pcr
                    ldb #32
StateCaptureSlot    pshs b
                    clra
                    clrb
                    std ,y
                    std 2,y
                    sta 4,y
                    tst 1,x
                    beq StateCaptureNext
                    lda 5,x
                    inca
                    sta ,y
                    lda ,x
                    sta 1,y
                    ldd 10,x
                    std 2,y
StateCaptureNext    leax 14,x
                    leay 5,y
                    puls b
                    decb
                    bne StateCaptureSlot
                    rts

* Payload metadata and all persistent text live in the first staged page.
StateValidate       ldd StateFirst,pcr
                    ldx #0
                    lbsr StateMapSpan
                    lbcs StateValidateReturn
                    ldb SavedKeyCount,u
                    cmpb #50
                    lbhi StateValidateBad
                    lda SavedMenuControl,u
                    cmpa #8
                    lbhi StateValidateBad
                    lda SavedMenuControl+1,u
                    cmpa #32
                    lbhi StateValidateBad
                    ldd SavedMenuControl+4,u
                    cmpd #768
                    lbhi StateValidateBad
                    lda SavedScreen+3,u
                    cmpa #4
                    lbhi StateValidateBad
                    lda SavedScreen+1,u
                    cmpa #15
                    lbhi StateValidateBad
                    lda SavedScreen+2,u
                    cmpa #15
                    lbhi StateValidateBad
                    lda SavedScreen+4,u
                    cmpa #25
                    lbhs StateValidateBad
                    lda SavedScreen+5,u
                    cmpa #25
                    lbhs StateValidateBad
                    ldd SavedInventoryControl+3,u
                    cmpd #256
                    lbhi StateValidateBad
                    ldd SavedReplay+1,u
                    bitb #1
                    lbne StateValidateBad
                    cmpd #510
                    lbhi StateValidateBad
                    cmpd SavedReplay+3,u
                    lblo StateValidateBad
                    leax SavedText,u
                    ldy #1000
StateCheckText      lda ,x+
                    cmpa #127
                    bhi StateValidateBad
                    leay -1,y
                    bne StateCheckText
                    leax StateCoreBytes,u
                    ldy #32
StateCheckSlot      lda ,x
                    cmpa #4
                    bhi StateValidateBad
                    tst 4,x
                    bne StateValidateBad
                    tst ,x
                    beq StateCheckEmpty
                    ldd 2,x
                    cmpd #2
                    blo StateValidateBad
                    bra StateCheckNext
StateCheckEmpty     ldd 1,x
                    bne StateValidateBad
                    tst 3,x
                    bne StateValidateBad
StateCheckNext      leax 5,x
                    leay -1,y
                    bne StateCheckSlot
                    lda StateCoreBytes,u
                    cmpa #1
                    bne StateValidateBad
                    lda StateCoreBytes+1,u
                    cmpa StateHeader+16,pcr
                    bne StateValidateBad
                    lbra StateUnmap
StateValidateBad    ldb #E$BMode
                    pshs b
                    lbsr StateUnmap
                    puls b
                    orcc #1
StateValidateReturn rts

* Apply only after every nested interpreter frame has returned. File validation
* precedes resource replacement; an allocation/resource failure exits cleanly.
STATE_CALL          macro
                    lbsr StateCallWarm
                    fcb \1
                    lbcs StateFail
                    endm
StateApply          tst StateReady,pcr
                    lbeq StateBad
                    tst StateOwned,pcr
                    lbeq StateBad
                    ldu StateBase,pcr
                    tst <vmdepth
                    lbne StateBad
                    tst <aborted
                    lbne StateAbort
                    clr <vmcleanup
                    STATE_CALL 4
                    ldu StateBase,pcr
                    STATE_CALL 6
                    ldu StateBase,pcr
                    STATE_CALL 8
                    clr <asseterror
                    clr <decodeerror
* Copy canonical cache recipes out of the staged block before loading assets.
                    ldx #StateCoreBytes
                    ldy #160
                    lbsr StateLoadBuffer
                    lbcs StateFail
                    leax StateBuffer,pcr
                    leay StateCache,pcr
                    ldb #160
StateRecipeCopy     lda ,x+
                    sta ,y+
                    decb
                    bne StateRecipeCopy
                    leax StateCache,pcr
                    stx StateRecipe,pcr
                    clr <vmcurrent
                    clr <vmdepth
* Resource loading must not append records to the snapshot's replay stream.
                    clr <replaylimit
StateLoadRecipe     ldx StateRecipe,pcr
                    lda ,x
                    beq StateNextRecipe
                    deca
                    ldb 1,x
                    ldu StateBase,pcr
                    STATE_CALL 10
                    stx StateSlot,pcr
                    ldu StateRecipe,pcr
                    ldd 2,u
                    std 10,x
                    tst 5,x
                    bne StateNextRecipe
                    cmpd 6,x
                    lbhs StateBad
* Only logic owns a scan position; a valid blank picture may be one byte.
* Derive logic bounds from newly loaded bytes, not a saved mapped pointer.
                    ldd 2,x
                    ldx #0
                    lbsr StateMapSpan
                    lbcs StateFail
                    lda 1,u
                    ldb ,u
                    addd #2
                    lbcs StateBad
                    std StateCodeEnd,pcr
                    lbsr StateUnmap
                    lbcs StateFail
                    ldx StateSlot,pcr
                    ldd StateCodeEnd,pcr
                    cmpd #2
                    lbls StateBad
                    cmpd 6,x
                    lbhi StateBad
                    cmpd 10,x
                    lbls StateBad
                    std 12,x
StateNextRecipe     ldx StateRecipe,pcr
                    leax 5,x
                    stx StateRecipe,pcr
                    leay StateCache+160,pcr
                    pshs y
                    cmpx ,s++
                    lblo StateLoadRecipe
* Restore private logical state. Cold code and owner/driver controls are excluded.
                    leax StateRanges,pcr
                    stx StateRange,pcr
                    ldd #0
                    std StateCursor,pcr
StateRestoreRange   ldx StateRange,pcr
                    ldd ,x++
                    ldy ,x++
                    stx StateRange,pcr
                    cmpy #0
                    beq StateRestorePixels
                    sty StateRemaining,pcr
                    addd StateBase,pcr
                    std StateDestination,pcr
StateRestoreChunk   ldx StateCursor,pcr
                    ldy StateRemaining,pcr
                    lbsr StateLoadBuffer
                    lbcs StateFail
                    leax StateBuffer,pcr
                    ldu StateDestination,pcr
                    ldy StateCount,pcr
StateRestoreCopy    lda ,x+
                    sta ,u+
                    leay -1,y
                    bne StateRestoreCopy
                    stu StateDestination,pcr
                    ldd StateCursor,pcr
                    addd StateCount,pcr
                    std StateCursor,pcr
                    ldd StateRemaining,pcr
                    subd StateCount,pcr
                    std StateRemaining,pcr
                    bne StateRestoreChunk
                    bra StateRestoreRange
StateRestorePixels  ldu StateBase,pcr
                    lda #$FF
                    sta gameclocklast,u
                    lda #1
                    sta gameclockreset,u
                    clr gameclockdelta,u
                    clr gamequit,u
                    clr <vmcurrent
                    clr <vmdepth
                    clr <vmroompending
                    clr <vmroomchanges
                    clr parserlength,u
                    clr parserline,u
                    clr vmflags+2,u
                    clr vmflags+4,u
                    clr vmflags+6,u
                    sta vmflags+12,u
                    leax vmcontrollers,u
                    ldy #32
StateClearControllers clr ,x+
                    leay -1,y
                    bne StateClearControllers
                    leax vmobjects,u
                    ldb #64
StateForgetSprites  clr 9,x
                    leax 43,x
                    decb
                    bne StateForgetSprites
                    tst StateHeader+3,pcr
                    lbeq StateRestoreRoot
                    STATE_CALL 16
                    ldd #0
                    std StatePictureOffset,pcr
StateRestorePicture ldx StatePictureOffset,pcr
                    ldd #26880
                    subd StatePictureOffset,pcr
                    beq StateSaveBackground
                    tfr d,y
* The staged stream and destination picture have different page alignment.
* Bound both windows before copying; a stage boundary alone is insufficient.
                    tfr x,d
                    anda #$1F
                    pshs d
                    ldd #8192
                    subd ,s++
                    pshs y
                    cmpd ,s
                    bhs StatePicturePageFits
                    tfr d,y
StatePicturePageFits leas 2,s
                    tfr x,d
                    addd #StateCoreBytes+160
                    tfr d,x
                    lbsr StateLoadBuffer
                    lbcs StateFail
                    ldu StateBase,pcr
                    ldd StatePictureOffset,pcr
                    STATE_CALL 18
                    tst <decodeerror
                    lbne StatePictureFailed
                    leax StateBuffer,pcr
                    ldy StateCount,pcr
StateRestorePictureCopy lda ,x+
                    sta ,u+
                    leay -1,y
                    bne StateRestorePictureCopy
                    ldu StateBase,pcr
                    STATE_CALL 2
                    ldd StatePictureOffset,pcr
                    addd StateCount,pcr
                    std StatePictureOffset,pcr
                    bra StateRestorePicture
StateSaveBackground lbsr StateFree
                    lbcs StateFail
* Static pixels and logical fields are now private/owned; release the temporary
* five-page stream before allocating the permanent background copy.
                    ldu StateBase,pcr
                    STATE_CALL 20
StateRestoreRoot    ldu StateBase,pcr
                    clrb
                    STATE_CALL 12
                    ldd 12,x
                    std <vmend
                    ldd 10,x
                    std <vmip
                    STATE_CALL 14
                    lbsr StateFree
                    lbcs StateFail
* These callbacks render cells/sprites but never invoke the message formatter
* or picture flood-fill decoder; the cold workspace remains intact until return.
                    ldu StateBase,pcr
                    STATE_CALL 22
                    ldu StateBase,pcr
                    STATE_CALL 24
                    clrb
                    rts
StatePictureFailed  ldb <decodeerror
                    lbra StateFail
StateAbort          ldb #E$PrcAbt
                    lbra StateFail

* Load one bounded stage span into the private transfer buffer. X/Y preserved.
StateLoadBuffer     pshs x,y
                    tfr y,d
                    cmpd #512
                    bls StateLoadCount
                    ldd #512
StateLoadCount      std StateCount,pcr
                    tfr x,d
                    anda #$1F
                    pshs d
                    ldd #8192
                    subd ,s++
                    cmpd StateCount,pcr
                    bhs StateLoadMap
                    std StateCount,pcr
StateLoadMap        ldd StateFirst,pcr
                    lbsr StateMapSpan
                    bcs StateLoadReturn
                    leax StateBuffer,pcr
                    ldy StateCount,pcr
StateLoadCopy       lda ,u+
                    sta ,x+
                    leay -1,y
                    bne StateLoadCopy
                    lbsr StateUnmap
StateLoadReturn     puls x,y,pc

* Inline byte selects a callback offset. Preserve input D/X/U; callbacks use
* the same private base/DP as the owner. No absolute link-time addresses occur.
StateCallWarm       pshs d,u
                    ldu 4,s
                    ldb ,u+
                    stu 4,s
                    clra
                    ldu StateAPI,pcr
                    ldd d,u
                    leau d,u
                    pshs u
                    ldd 2,s
                    ldu 4,s
                    jsr [,s]
                    leas 6,s
                    rts

* CRC-16/CCITT over the canonical payload. Preserve the caller's data pointer.
StateChecksum       pshs d,x,y
StateCRCByte        lda ,x+
                    eora StateCRC,pcr
                    sta StateCRC,pcr
                    lda #8
                    sta StateBits,pcr
                    ldd StateCRC,pcr
StateCRCBit         lslb
                    rola
                    bcc StateCRCNoXor
                    eora #$10
                    eorb #$21
StateCRCNoXor       dec StateBits,pcr
                    bne StateCRCBit
                    std StateCRC,pcr
                    leay -1,y
                    bne StateCRCByte
                    puls d,x,y,pc

* Handle partial file transfers without mapping foreign RAM across I/O.
StateWriteExact     pshs x,y
StateWriteMore      ldx ,s
                    ldy 2,s
                    lda StatePath,pcr
                    os9 I$Write
                    bcs StateTransferReturn
                    bra StateTransferCount
StateReadExact      pshs x,y
StateReadMore       ldx ,s
                    ldy 2,s
                    lda StatePath,pcr
                    os9 I$Read
                    bcs StateTransferReturn
StateTransferCount  tfr y,d
                    cmpd #0
                    beq StateTransferBad
                    cmpd 2,s
                    bhi StateTransferBad
                    std StateActual,pcr
                    ldd ,s
                    addd StateActual,pcr
                    std ,s
                    ldd 2,s
                    subd StateActual,pcr
                    std 2,s
                    beq StateTransferDone
* Save/read entry is selected by whether the path was created by this call.
                    tst StateCreated,pcr
                    bne StateWriteMore
                    bra StateReadMore
StateTransferDone   clrb
StateTransferReturn leas 4,s
                    rts
StateTransferBad    ldb #E$BMode
                    orcc #1
                    bra StateTransferReturn

* D=owned first physical block, X=byte offset. Returns one ephemeral pointer.
StateMapSpan        std StateMapFirst,pcr
                    pshs x
                    tfr x,d
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    lsra
                    rorb
                    addd StateMapFirst,pcr
                    tfr d,x
                    ldb #1
                    os9 F$MapBlk
                    bcs StateMapReturn
                    stu StateMapBase,pcr
                    inc StateMapped,pcr
                    ldd ,s
                    anda #$1F
                    leau d,u
StateMapReturn      puls x,pc
StateUnmap          tst StateMapped,pcr
                    beq StateUnmapped
                    ldu StateMapBase,pcr
                    ldb #1
                    os9 F$ClrBlk
                    bcs StateUnmapReturn
                    clr StateMapped,pcr
StateUnmapped       clrb
StateUnmapReturn    rts
StateClose          tst StateOpen,pcr
                    beq StateUnmapped
                    lda StatePath,pcr
                    os9 I$Close
                    bcs StateUnmapReturn
                    clr StateOpen,pcr
                    clrb
                    rts
StateFree           tst StateOwned,pcr
                    beq StateUnmapped
                    ldx StateFirst,pcr
                    ldb StateBlocks,pcr
                    os9 F$DelRAM
                    bcs StateUnmapReturn
                    clr StateOwned,pcr
                    clr StateReady,pcr
                    clrb
                    rts
StateBad            ldb #E$BMode
StateFail           stb StateError,pcr
                    lbsr StateUnmap
                    bcc StateFailClose
                    lbsr StateUnmap
StateFailClose      lbsr StateClose
                    lbsr StateFree
                    tst StateCreated,pcr
                    beq StateFailReturn
                    ldx StateFilename,pcr
                    os9 I$Delete
                    clr StateCreated,pcr
StateFailReturn     ldb StateError,pcr
                    orcc #1
                    rts

* One canonical field list supplies both the private ABI and stream order.
StateFieldOffset    set 0
STATE_COPY_FIELD    macro
\1                  equ StateFieldOffset
                    fdb \2,\3
StateFieldOffset    set StateFieldOffset+\3
                    endm
StateRanges         equ *
                    STATE_SCHEMA STATE_COPY_FIELD
StateCoreBytes      equ StateFieldOffset
                    fdb 0,0
                    ifgt StateCoreBytes+160-8192
                    error Snapshot metadata must fit the first staging block
                    endc
StateBase           fdb 0
StateAPI            fdb 0
StateFilename       fdb 0
StateMode           fcb 0
StatePath           fcb 0
StateOpen           fcb 0
StateCreated        fcb 0
StateMapped         fcb 0
StateOwned          fcb 0
StateReady          fcb 0
StateError          fcb 0
StateBlocks         fcb 0
StateBits           fcb 0
StateFirst          fdb 0
StatePicture        fdb 0
StateMapFirst       fdb 0
StateMapBase        fdb 0
StateRange          fdb 0
StateCursor         fdb 0
StateCount          fdb 0
StateActual         fdb 0
StateCRC            fdb 0
StateRecipe         fdb 0
StateSlot           fdb 0
StateCodeEnd        fdb 0
StateDestination    fdb 0
StateRemaining      fdb 0
StatePictureOffset  fdb 0
StateHeader         zmb 18
StateCache          zmb 160
StateBuffer         zmb 512
PLATFORM_SECTION    set PLATFORM_WILDBITS_SOUND_CODE
                    use platform/wildbits-audio.asm
                    emod
StateEnd            equ *
                    ifp2
                    ifgt AudioBlobEnd-AudioBlobStart-432
                    error Private audio adapter exceeds its reserved workspace
                    endc
                    ifgt StateEnd-4096
                    error Cold state helper exceeds its private workspace
                    endc
                    endc
