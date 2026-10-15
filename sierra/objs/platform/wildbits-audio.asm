* Wild Bits owned audio adapter: private state, resident entry points and
* position-independent user code exported by the existing cold state module.
                    ifndef AUDIO_TICK_OFFSET
AUDIO_TICK_OFFSET   equ 3
                    endc
                    ifndef AUDIO_USER_COPY
AUDIO_USER_COPY     equ 0
                    endc
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_SOUND_DATA
soundpath           rmb 1
soundflag           rmb 1
soundcache          rmb 1
soundready          rmb 1
soundchannel        rmb 1
soundrounds         rmb 1
soundoffsets        rmb 8
                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_SOUND_CODE
                    ifndef SS.PSG
SS.PSG              equ $C5
                    endc
                    ifne AUDIO_USER_COPY
* Two fixed-width public entry slots; the resident tick caller uses slot 3.
AudioBlobStart      lbra SoundCommandBody
AudioTickEntry      lbra SoundTickBody
                    ifne AudioTickEntry-AudioBlobStart-AUDIO_TICK_OFFSET
                    error Audio tick entry ABI moved
                    endc
SoundCommandBody    jsr [soundcalls+12,u]
                    lbcs SoundPrivateReturn
                    ldu <resourcebase
                    ldb vmarguments+1,u
                    stb <soundflag
                    jsr [soundcalls+18,u]    asynchronous requests clear their flag
                    tst vmflags+9,u
                    lbeq SoundMarkPrivate
                    ldb vmarguments,u
                    lda #3
                    jsr [soundcalls+0,u]
                    bcs GameSoundUnavailable
                    ldb <vmcacheindex
                    stb <soundcache
                    jsr [soundcalls+2,u]
* The repository's sound resources use CoCo notes, not PC four-track headers:
* tone, DAC amplitude, big-endian duration; then FF and an elapsed-time word.
                    ldd <resourcelength
                    subd #3
                    bcs GameSoundUnavailable
                    pshs d
                    andb #3
                    puls d
                    bne GameSoundUnavailable
                    std <soundoffsets+2
                    std <soundoffsets+4
                    std <soundoffsets+6
                    jsr [soundcalls+4,u]
                    tst <asseterror
                    bne GameSoundUnavailable
                    lda ,u
                    cmpa #$FF
                    bne GameSoundUnavailable
                    ldu <resourcebase
                    clra
                    clrb
                    std <soundoffsets
                    jsr [soundcalls+6,u]
                    bcs GameSoundUnavailable
                    leax GameSoundDevice,pcr
                    lda #UPDAT.
                    os9 I$Open
                    bcs GameSoundUnavailable
                    ldu <resourcebase
                    inca
                    sta <soundpath
                    ldx #0
                    lbsr SoundStatus
                    bcs GameSoundUnavailable
                    cmpx #4
                    bne GameSoundUnavailable
                    ldx #1
                    lbsr GameSoundSet
                    bcs SoundClaimFailed
                    ldx #4
SoundQueueStart     lbsr GameSoundSet
                    bcs GameSoundUnavailable
                    leax 1,x
                    cmpx #6
                    blo SoundQueueStart
                    bra SoundTickBody
SoundClaimFailed    cmpb #E$DevBsy
                    bne GameSoundUnavailable
                    bra SoundDropRequest   another owner must not disable future sound
GameSoundUnavailable ldu <resourcebase
                    clr vmflags+9,u
SoundDropRequest    jsr [soundcalls+6,u]
                    ldu <resourcebase
                    jsr [soundcalls+12,u]
                    pshs cc,b
                    jsr [soundcalls+16,u]
                    puls cc,b
                    bcs SoundPrivateReturn
SoundMarkPrivate    jmp [soundcalls+14,u]
SoundPrivateSuccess clrb
SoundPrivateReturn  rts
SoundStopPrivate    jmp [soundcalls+12,u]
GameSoundDevice     fcc |/fPSG|
                    fcb C$CR
* Preserve the running logic offsets while the shared bounded fetch reads notes.
SoundTickBody       tst vmflags+9,u
                    beq SoundStopPrivate
                    ldd <vmip
                    pshs d
                    ldd <vmend
                    pshs d
                    lda #8
                    sta <soundrounds
GameSoundPoll       ldx #1
                    lbsr SoundStatus
                    lbcs SoundTickBodyStop
                    bitb #$10
                    lbeq SoundTickBodyStop
                    andb #15
                    lbeq SoundTickBodyRestore
                    stb <soundready
                    clr <soundchannel
GameSoundChannel    lsr <soundready
                    lbcc GameSoundNextChannel
                    ldb <soundcache
                    jsr [soundcalls+8,u]
                    jsr [soundcalls+2,u]
                    leax soundoffsets,u
                    ldb <soundchannel
                    lslb
                    ldd b,x
                    std <vmip
                    ldd <resourcelength
                    std <vmend
                    ldd <vmend
                    subd #3
                    cmpd <vmip
                    beq SoundEndPacket
                    lda #1
                    sta <vmargindex
                    ldb #5
                    stb <vmargcount
                    jsr [soundcalls+10,u]
                    bcs SoundTickBodyStop
                    clr vmarguments+5,u
                    lda <soundchannel
                    ora #$80       driver translates a CoCo note at enqueue time
                    bra SoundPacketReady
SoundEndPacket      ldd #$FFFF
                    std vmarguments+1,u
                    clra
                    clrb
                    std vmarguments+3,u
                    stb vmarguments+5,u
                    lda <soundchannel
SoundPacketReady    sta vmarguments,u
                    jsr [soundcalls+6,u]
                    bcs SoundTickBodyStop
                    ldu <resourcebase
                    leax vmarguments,u
                    ldy #6
                    lda <soundpath
                    deca
                    os9 I$Write
                    bcs SoundTickBodyStop
                    cmpy #6
                    bne SoundTickBodyStop
                    leax soundoffsets,u
                    ldb <soundchannel
                    lslb
                    leax b,x
                    ldd <vmip
                    std ,x
GameSoundNextChannel inc <soundchannel
                    lda <soundchannel
                    cmpa #4
                    lblo GameSoundChannel
                    dec <soundrounds
                    lbne GameSoundPoll
                    bra SoundTickBodyRestore
SoundTickBodyStop   ldu <resourcebase
                    jsr [soundcalls+12,u]
SoundTickBodyRestore pshs cc,b
                    jsr [soundcalls+16,u]
                    ldd 2,s
                    std <vmend
                    ldd 4,s
                    std <vmip
                    puls cc,b
                    leas 4,s
                    rts
GameSoundSet        ldu <resourcebase
                    lda <soundpath
                    deca
                    ldb #SS.PSG
                    os9 I$SetStt
                    rts
SoundStatus         lda <soundpath
                    deca
                    ldb #SS.PSG
                    os9 I$GetStt
                    tfr u,d
                    ldu <resourcebase
                    rts
AudioBlobEnd        equ *
AudioInstall        pshs u
                    leax AudioBlobStart,pcr
                    leau soundcode,u
                    ldd #AudioBlobEnd-AudioBlobStart
AudioInstallCopy    pshs d
                    lda ,x+
                    sta ,u+
                    puls d
                    subd #1
                    bne AudioInstallCopy
                    ldu ,s
                    leax soundcalls,u
                    ldb #10
                    stb <soundrounds
AudioInstallCalls   ldd ,y
                    leau d,y
                    stu ,x++
                    leay 2,y
                    dec <soundrounds
                    bne AudioInstallCalls
                    clrb
                    puls u,pc

                    else
* Frontend entry points execute a per-process copy in reclaimed private space.
* No shared code is patched and the display/font/formatter buffers stay separate.
GameSoundCommand    ldu <resourcebase
                    ldb <vmopcode
                    cmpb #100
                    beq SoundStopBody
                    tst soundinstalled,u
                    bne SoundCommandReady
                    tst vmflags+9,u
                    beq SoundOffline
                    bsr GameSoundLoad
                    bcc SoundCommandReady
                    clr vmflags+9,u
SoundOffline        ldb vmarguments+1,u
                    stb <soundflag
                    bra GameSoundMarkDone
GameSoundSuccess    clrb
                    rts
SoundCommandReady   leax soundcode,u
                    jmp ,x
GameSoundTick       ldu <resourcebase
                    tst <soundpath
                    beq GameSoundSuccess
                    leax soundcode+AUDIO_TICK_OFFSET,u
                    jmp ,x
GameSoundStop       equ SoundStopBody
GameSoundLoad       lbsr StateLoadModule
                    bcs SoundLoadReturn
                    ldd 2,x
                    cmpd #13
                    blo SoundLoadBad
                    ldy M$Size,u
                    leay -3,y
                    pshs y
                    cmpd ,s
                    leas 2,s
                    bhs SoundLoadBad
                    pshs u
                    leax d,u
                    leay SoundMainCallbacks,pcr
                    ldu <resourcebase
                    jsr ,x
                    puls u
                    os9 F$UnLink
                    ldu <resourcebase
                    bcs SoundLoadReturn
                    inc soundinstalled,u
SoundLoadReturn     rts
SoundLoadBad        os9 F$UnLink
                    ldu <resourcebase
                    ldb #E$BMode
                    orcc #1
                    rts
GameSoundMarkDone   lda #1
SoundSetFlag        leax vmflags,u
                    ldb <soundflag
                    abx
                    sta ,x
                    bra GameSoundSuccess
SoundStopBody       ldu <resourcebase
                    lda <soundpath
                    beq GameSoundSuccess
                    deca
                    os9 I$Close
                    bcs SoundResidentReturn
                    clr <soundpath
                    bra GameSoundMarkDone
SoundRestoreRoot    lbsr AssetUnmap
                    bcs SoundResidentReturn
                    clr <asseterror
                    ldb <vmcurrent
                    lbsr VmSlotAddress
                    lbra VmRestoreAsset
SoundResidentReturn rts
SoundClearFlag      clra
                    bra SoundSetFlag
SoundMainCallbacks  fdb VmLoadResource-*
                    fdb VmRestoreAsset-*
                    fdb AssetPointer-*
                    fdb AssetUnmap-*
                    fdb VmSlotAddress-*
                    fdb VmArgumentLoop-*
                    fdb SoundStopBody-*
                    fdb GameSoundMarkDone-*
                    fdb SoundRestoreRoot-*
                    fdb SoundClearFlag-*
                    endc
                    else
                    error Unknown platform feature section
                    endc
                    endc
