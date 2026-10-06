* wildbits-audio feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_SOUND_CODE
* ===== wildbits-sound-code =====
* Native AGI sound gate. No direct hardware writes or global tone ownership.
* This backend currently advertises sound-off at startup. With AGI flag 9 off,
* sound completes immediately, matching CoCo SoundSetFlagDone. Enabling sound
* emits one diagnostic and disables sound until an owned audio driver exists.
GameSoundCommand    ldu       <resourcebase
                    ldb       <vmopcode
                    cmpb      #100
                    beq       GameSoundStopped
                    tst       vmflags+9,u
                    bne       GameSoundUnavailable
GameSoundComplete
                    leax      vmflags,u
                    clra
                    ldb       vmarguments+1,u
                    abx
                    lda       #1
                    sta       ,x
GameSoundStopped    clrb
                    rts
GameSoundUnavailable clr      vmflags+9,u
                    tst       gamesoundwarned,u
                    bne       GameSoundComplete
                    lda       #1
                    sta       gamesoundwarned,u
                    lbsr      AssetUnmap
                    bcs       GameSoundReturn
                    lbsr      PictureUnmap
                    bcs       GameSoundReturn
                    leax      GameSoundNotice,pcr
                    ldy       #GameSoundNoticeEnd-GameSoundNotice
                    lda       #2
                    os9       I$Write
                    bcs       GameSoundReturn
                    ldu       <resourcebase
                    bra       GameSoundComplete
GameSoundReturn     rts
GameSoundNotice     fcc       /Wild Bits audio unavailable; sound disabled./
                    fcb       C$CR
GameSoundNoticeEnd  equ       *

                    else
                    error Unknown platform feature section
                    endc
