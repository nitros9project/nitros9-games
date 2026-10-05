* Signed direction vectors applied to word-sized candidate coordinates.
* Owners bind X/Y/step storage and direction lookup. No clamping or commit is
* performed here. JOIN_STORES preserves each owner's existing branch schedule.
                    STEP_X_DIRECTION
                    beq       StepCalculateY
                    bpl       StepAddX
                    STEP_X_D ldd
                    STEP_DISTANCE_D subd
                    ifne STEP_JOIN_STORES
                    bra       StepStoreX
                    else
                    STEP_X_D std
                    bra       StepCalculateY
                    endc
StepAddX            STEP_X_D ldd
                    STEP_DISTANCE_D addd
StepStoreX          STEP_X_D std
StepCalculateY      STEP_Y_DIRECTION
                    beq       StepCoordinatesDone
                    bpl       StepAddY
                    STEP_Y_D ldd
                    STEP_DISTANCE_D subd
                    ifne STEP_JOIN_STORES
                    bra       StepStoreY
                    else
                    STEP_Y_D std
                    bra       StepCoordinatesDone
                    endc
StepAddY            STEP_Y_D ldd
                    STEP_DISTANCE_D addd
StepStoreY          STEP_Y_D std
StepCoordinatesDone equ *
