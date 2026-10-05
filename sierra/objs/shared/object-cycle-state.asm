* Common cycle mode and enable/single-loop transitions.
* Mode 0/3: continuous forward/reverse; mode 1/2: stop at a loop endpoint.
* Parameters: mode, record pointer register, endpoint completion enabled.
OBJECT_CYCLE_STATE  macro
                    lda       #\1
                    sta       <$23,\2
                    ifne      \3
                    ldd       <$25,\2
                    ora       #$10
                    orb       #$30
                    std       <$25,\2
                    else
                    lda       <$26,\2
                    ora       #$20
                    sta       <$26,\2
                    endc
                    endm
