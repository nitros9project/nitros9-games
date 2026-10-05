* Common normal-motion state; owners handle ego input-control side effects.
* Parameters: record pointer register, clear direction (stop motion).
OBJECT_MOTION_STATE macro
                    lda       #0
                    sta       <$22,\1
                    ifne      \2
                    clra
                    sta       <$21,\1
                    endc
                    endm
