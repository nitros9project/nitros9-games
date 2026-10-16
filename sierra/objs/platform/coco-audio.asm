* coco-audio feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_COCO_SOUND_CODE
* ===== coco-sound-code =====
* CoCo blocking DAC sound backend. See ../../PORTABILITY.md for contract.
* Keep instruction order and addressing widths: delay loops are calibrated.

PlaySound           pshs      y         ; save logic script pointer
                    clrb                ; B = 0 (initial silence)
                    ldu       $03,u     ; follow pointer to sound data
                    bsr       SoundPIASave ; configure PIA for sound output
PlaySoundLoop       ldb       ,u+       ; read note byte (0xFF = end)
                    cmpb      #$FF      ; end of sound?
                    beq       PlaySoundEnd ; branch to finish
                    lslb                ; double B for freq table index
                    lda       ,u+       ; read amplitude byte
                    ora       #2        ; force RS-232 line high
                    sta       >$FF20    ; write amplitude to PIA DAC
                    ldy       ,u++      ; load duration in Y
                    leax      >NoteFreqTable,pcr ; base of frequency table
                    abx                 ; index to this note's frequency
                    ldd       ,x        ; load half-period count
                    std       <$008E    ; store half-period in DP
                    leax      >$007A,x  ; offset to wave-count table
                    ldd       ,x        ; load wave-count entry
                    std       <$0090    ; store wave count in DP
* The RS-232 line is now masked and forced high.
* Therefore $FF20 can't be tested for $00 but we can test the actual
* data stream. RG
*         tst   $FF20	old
                    tst       -3,u      new
                    beq       PlaySoundWaveLow ; branch if low amplitude (silent)
PlaySoundWaveHigh   ldx       <$0090    ; wave repetition count
PlaySoundHighLoop   ldd       <$008E    ; half-period delay
PlaySoundHighDelay  subd      #$0001    ; count down delay
                    bne       PlaySoundHighDelay ; loop until delay elapsed
*         com   $FF20
                    lda       $ff20     patch RG
                    coma                ; invert DAC output (toggle wave)
                    ora       #2        ; keep RS-232 line high
                    sta       $ff20     ; write toggled value
                    leax      -1,x      ; decrement wave count
                    bne       PlaySoundHighLoop ; loop for all waves
                    leay      -$01,y    ; decrement duration counter
                    bne       PlaySoundWaveHigh ; loop for full duration
                    bra       PlaySoundLoop ; next note
PlaySoundWaveLow    ldx       <$0090    ; wave repetition count
PlaySoundLowLoop    ldd       <$008E    ; half-period delay
PlaySoundLowDelay   subd      #$0001    ; count down delay
                    bne       PlaySoundLowDelay ; loop until delay elapsed
* This is a meaningless test and must be here to balance cycles. RG
                    tst       >$FF20    ; cycle-balance test (no-op)
                    leax      -$01,x    ; decrement wave count
                    bne       PlaySoundLowLoop ; loop for all waves
                    leay      -$01,y    ; decrement duration counter
                    bne       PlaySoundWaveLow ; loop for full duration
                    bra       PlaySoundLoop ; next note
PlaySoundEnd        bsr       SoundPIARestore ; restore PIA to pre-sound state
                    ldd       ,u        ; load elapsed time word
                    puls      y         ; restore logic script pointer
                    rts

*Sound on
* RS-232 toggle change. RG

SoundPIASave        orcc      #IntMasks ; disable interrupts during sound
*        clr   $FF20		this would trash the RS-232 line while zeroing the DAC
                    lda       #2        patch RG
                    sta       $ff20     ; set DAC to zero (RS-232 safe)
                    lda       >$FF01    save PIA setting
                    sta       >SoundPIA1Ctrl,pcr ; save PIA1 control byte
                    anda      #$F7      set MUX to 0
                    sta       >$FF01    ; write MUX=0 to PIA1
                    lda       >$FF03    save PIA setting
                    sta       >SoundPIA2Ctrl,pcr ; save PIA2 control byte
                    anda      #$F7      set MUX to 0
                    sta       >$FF03    DAC now selected
                    lda       >$FF23    save Sound setting
                    sta       >SoundEnableReg,pcr ; save sound-enable register
                    ora       #$08      turn sound on
                    sta       >$FF23    ; enable sound output
                    rts

*Sound off
* RS-232 toggle change. RG
SoundPIARestore     lda       >SoundPIA1Ctrl,pcr get saved PIA HSYNC setting
                    sta       >$FF01    restore it
                    lda       >SoundPIA2Ctrl,pcr get saved PIA VSYNC setting
                    sta       >$FF03    restore it
                    lda       >SoundEnableReg,pcr get Sound setting (presumably off)
                    sta       >$FF23    restore it
                    lda       #2        patch RG
                    sta       $FF20     ; reset DAC to RS-232-safe value
                    lda       $FF02     ; clear PIA1 interrupt latch
                    lda       $FF22     ; clear PIA2 interrupt latch
                    andcc     #$AF      ; re-enable interrupts
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_SOUND_DATA
* ===== coco-sound-data =====
* CoCo sound state and CPU-calibrated tables. Included at the original
* engine location to preserve all addresses. State remains in the private
* engine copy; it must not be shared between concurrent processes.

SoundPIA1Ctrl       fcb       0
SoundPIA2Ctrl       fcb       0
SoundEnableReg      fcb       0

NoteFreqTable       fcb       $07,$78
                    fcb       $07,$0C
                    fcb       $06,$A8
                    fcb       $06,$48
                    fcb       $05,$EC
                    fcb       $05,$98
                    fcb       $05,$48
                    fcb       $04,$FC
                    fcb       $04,$B4
                    fcb       $04,$70
                    fcb       $04,$30
                    fcb       $03,$F4
                    fcb       $03,$BC
                    fcb       $03,$86
                    fcb       $03,$54
                    fcb       $03,$24
                    fcb       $02,$F6
                    fcb       $02,$CC
                    fcb       $02,$A4
                    fcb       $02,$7E
                    fcb       $02,$5A
                    fcb       $02,$38
                    fcb       $02,$18
                    fcb       $01,$FA
                    fcb       $01,$DE
                    fcb       $01,$C2
                    fcb       $01,$AA
                    fcb       $01,$92
                    fcb       $01,$7A
                    fcb       $01,$66
                    fcb       $01,$52
                    fcb       $01,$3E
                    fcb       $01,$2C
                    fcb       $01,$1C
                    fcb       $01,$0C
                    fcb       $00,$FC
                    fcb       $00,$EE
                    fcb       $00,$E2
                    fcb       $00,$D4
                    fcb       $00,$C8
                    fcb       $00,$BE
                    fcb       $00,$B2
                    fcb       $00,$A8
                    fcb       $00,$9C
                    fcb       $00,$96
                    fcb       $00,$8E
                    fcb       $00,$86
                    fcb       $00,$7E
                    fcb       $00,$78
                    fcb       $00,$70
                    fcb       $00,$6A
                    fcb       $00,$64
                    fcb       $00,$5E
                    fcb       $00,$5A
                    fcb       $00,$54
                    fcb       $00,$50
                    fcb       $00,$4C
                    fcb       $00,$46
                    fcb       $00,$42
                    fcb       $00,$3E
                    fcb       $00,$3C
                    fcb       $00,$02
                    fcb       $00,$02
                    fcb       $00,$02
                    fcb       $00,$03
                    fcb       $00,$03
                    fcb       $00,$03
                    fcb       $00,$03
                    fcb       $00,$03
                    fcb       $00,$03
                    fcb       $00,$04
                    fcb       $00,$04
                    fcb       $00,$04
                    fcb       $00,$04
                    fcb       $00,$05
                    fcb       $00,$05
                    fcb       $00,$05
                    fcb       $00,$05
                    fcb       $00,$06
                    fcb       $00,$06
                    fcb       $00,$06
                    fcb       $00,$07
                    fcb       $00,$07
                    fcb       $00,$08
                    fcb       $00,$08
                    fcb       $00,$09
                    fcb       $00,$09
                    fcb       $00,$0A
                    fcb       $00,$0A
                    fcb       $00,$0B
                    fcb       $00,$0C
                    fcb       $00,$0C
                    fcb       $00,$0D
                    fcb       $00,$0E
                    fcb       $00,$0E
                    fcb       $00,$0F
                    fcb       $00,$10
                    fcb       $00,$11
                    fcb       $00,$12
                    fcb       $00,$13
                    fcb       $00,$14
                    fcb       $00,$15
                    fcb       $00,$17
                    fcb       $00,$19
                    fcb       $00,$1A
                    fcb       $00,$1B
                    fcb       $00,$1D
                    fcb       $00,$1E
                    fcb       $00,$20
                    fcb       $00,$22
                    fcb       $00,$24
                    fcb       $00,$26
                    fcb       $00,$28
                    fcb       $00,$2B
                    fcb       $00,$2D
                    fcb       $00,$30
                    fcb       $00,$33
                    fcb       $00,$35
                    fcb       $00,$39
                    fcb       $00,$3D
                    fcb       $00,$40
                    fcb       $00,$42

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_SOUND_ELAPSED
* ===== coco-sound-elapsed =====
* CoCo platform boundary: sound-elapsed.
* Included in place; see ../../PORTABILITY.md.

                    cmpd      #$0000    ; any elapsed time returned?
                    lbeq      TimeRestorePage ; skip time update if zero
                    pshs      b,a       ; save elapsed time
                    addb      $0C,s     ; add seconds field
                    bcc       TimeSecCarry ; branch if no second overflow
                    inca                ; carry into minutes
TimeSecCarry        ldu       #$003C    ; 60 seconds per minute
                    lbsr      UIntDivide ; divide to get minute carry
                    stb       $0C,s     ; store updated seconds
                    tfr       u,d       ; D = minute carry
                    cmpd      #$0000    ; any minutes to add?
                    beq       TimeSetSys ; skip if none
                    addb      $0B,s     ; add to minutes field
                    bcc       TimeMinCarry ; branch if no minute overflow
                    inca                ; carry into hours
TimeMinCarry        ldu       #$003C    ; 60 minutes per hour
                    lbsr      UIntDivide ; divide to get hour carry
                    stb       $0B,s     ; store updated minutes
                    tfr       u,d       ; D = hour carry
                    tstb                ; any hours to add?
                    beq       TimeSetSys ; skip if none
                    addb      $0A,s     ; add to hours field
                    lda       #$17      ; 24 hours per day
                    lbsr      Div8      ; divide to get day carry
                    sta       $0A,s     ; store updated hours
                    tstb                ; any days to add?
                    beq       TimeSetSys ; skip if none
                    inc       $09,s     ; increment day of month
                    ldd       $08,s     ; load month and year
                    leax      >MonthDayTable,pcr ; days-per-month table
                    cmpb      a,x       ; past end of month?
                    bls       TimeSetSys ; branch if still in month
                    ldb       a,x       ; days in this month
                    cmpa      #$02      ; is it February?
                    bne       TimeDayIncr ; branch if not Feb
                    ldb       $07,s     ; year value
                    beq       TimeDayIncr ; not a leap year
                    bitb      #$03      ; leap year check (divisible by 4)
                    bne       TimeDayIncr ; not divisible by 4
                    ldb       $09,s     ; current day
                    cmpb      #$1D      ; day 29?
                    beq       TimeSetSys ; allow Feb 29 on leap year
TimeDayIncr         ldb       #$01      ; reset to day 1
                    stb       $09,s     ; store day = 1
                    inca                ; advance month
                    cmpa      #$0C      ; past December?
                    bls       TimeMonthAdv ; branch if still in year
                    stb       $08,s     ; month = 1
                    inc       $07,s     ; increment year
                    bra       TimeSetSys ; apply to system
TimeMonthAdv        sta       $08,s     ; store updated month
TimeSetSys          leax      $07,s     ; point to updated time struct
                    os9       F$STime   ; set system time
                    puls      b,a       ; restore elapsed time
                    addb      >$043C    ; add to timer seconds field
                    bcc       TimeSec2Carry ; branch if no overflow
                    inca                ; carry into timer minutes
TimeSec2Carry       ldu       #$003C    ; 60 seconds per minute
                    lbsr      UIntDivide ; divide to get carry
                    stb       >$043C    ; store timer seconds
                    tfr       u,d       ; D = minute carry
                    cmpd      #$0000    ; any minutes?
                    beq       TimeRestorePage ; skip if none
                    addb      >$043D    ; add to timer minutes field
                    bcc       TimeMin2Carry ; branch if no overflow
                    inca                ; carry into hours
TimeMin2Carry       ldu       #$003C    ; 60 minutes per hour
                    lbsr      UIntDivide ; divide to get carry
                    stb       >$043D    ; store timer minutes
                    tfr       u,d       ; D = hour carry
                    tstb                ; any hours?
                    beq       TimeRestorePage ; skip if none
                    addb      >$043E    ; add to timer hours
                    lda       #$17      ; 24 hours per day
                    lbsr      Div8      ; get day carry in B
                    sta       >$043E    ; store timer hours
                    tstb                ; any day overflow?
                    beq       TimeRestorePage ; skip if none
                    inc       >$043F    ; increment timer day counter
TimeRestorePage     ldd       $03,s     ; saved logic page
                    lbsr      SetLogicPage ; restore logic page

                    else
                    error Unknown platform feature section
                    endc
                    endc
                    endc
