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
