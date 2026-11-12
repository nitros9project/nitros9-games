* Left/down/right/up spiral step on a resolved record U and owner frame S.
* Valid direction is 0..3. One leg implementation is expanded four times to
* retain CoCo's existing branch/instruction schedule. Checked owners bind
* long continuations and reject a wrapped run length; candidate/budget policy
* remains outside this step. Parameters: coordinate operation/offset, grow
* the run after this leg, reset direction instead of incrementing it.
SPIRAL_LEG         macro
                    \1       \2,u
                    dec       SPIRAL_REMAINING,s
                    SPIRAL_REPEAT
                    ifne      \4
                    clr       SPIRAL_DIRECTION,s
                    else
                    inc       SPIRAL_DIRECTION,s
                    endc
                    ifne      \3
                    inc       SPIRAL_LENGTH,s
                    endc
                    lda       SPIRAL_LENGTH,s
                    ifne      SPIRAL_CHECK_LENGTH
                    SPIRAL_LENGTH_ERROR
                    endc
                    sta       SPIRAL_REMAINING,s
                    SPIRAL_RESUME
                    endm
SpiralStep          lda       SPIRAL_DIRECTION,s
                    bne       SpiralDirOne
                    SPIRAL_LEG dec,3,0,0
SpiralDirOne        cmpa      #1
                    bne       SpiralDirTwo
                    SPIRAL_LEG inc,4,1,0
SpiralDirTwo        cmpa      #2
                    bne       SpiralDirThree
                    SPIRAL_LEG inc,3,0,0
SpiralDirThree      SPIRAL_LEG dec,4,1,1
