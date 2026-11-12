* Common follow-ego and wander command setup for 43-byte object records.
* Record pointer and branch labels are assembly-time parameters. Y is the
* remaining follow operand stream; adapters own flag/control/reset policies.
OBJECT_FOLLOW_SETUP macro
                    lda       #$02
                    sta       <$22,\1
                    lda       <$1E,\1
                    sta       <$27,\1
                    lda       ,y+
                    cmpa      <$1E,\1
                    bls       \2
                    sta       <$27,\1
\2                  lda       ,y+
                    sta       <$28,\1
                    MOTION_CLEAR_FLAG
                    lda       #$FF
                    sta       <$29,\1
                    lda       <$26,\1
                    ora       #$10
                    sta       <$26,\1
                    endm
OBJECT_WANDER_SETUP macro
                    lda       #$01
                    sta       <$22,\1
                    MOTION_RESET_WANDER \1
                    lda       <$26,\1
                    ora       #$10
                    sta       <$26,\1
                    MOTION_DISABLE_EGO \2
\2
                    endm
* Move-to finish after target assignment: saved speed, optional override,
* literal completion flag, update bit, ego ownership and direction callback.
* Parameters: record, variable operands, step label, direction label.
OBJECT_MOVE_SETUP   macro
                    lda       <$1E,\1
                    sta       <$29,\1
                    MOTION_FETCH_STEP \2
                    beq       \3
                    sta       <$1E,\1
\3                  MOTION_FETCH_MOVE_FLAG
                    sta       <$2A,\1
                    MOTION_CLEAR_FLAG
                    lda       <$26,\1
                    ora       #$10
                    sta       <$26,\1
                    MOTION_DISABLE_EGO \4
\4                  MOTION_START_MOVE
                    endm
