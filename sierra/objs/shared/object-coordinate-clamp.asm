* Candidate screen clamping; storage comes from coordinate-step operands.
* Traits preserve checked/native dimensions, comparison widths and CoCo's
* early vertical exits. Horizon equality and zero-width policies are explicit.
ClampCoordinates    CLAMP_LEFT_READ
                    ifne CLAMP_CANDIDATE_FIRST
                    bpl       ClampRightLimit
                    ldd       #0
                    else
                    ble       ClampRightLimit
                    endc
                    STEP_X_D std
                    lda       #4
                    CLAMP_EDGE_STORE
                    bra       ClampTopLimit
ClampRightLimit     equ *
                    ifne CLAMP_CHECK_DIMENSIONS
                    clra
                    endc
                    CLAMP_WIDTH_READ
                    ifne CLAMP_CHECK_DIMENSIONS
                    CLAMP_REJECT beq
                    cmpb      #160
                    CLAMP_REJECT bhi
                    endc
                    negb
                    CLAMP_NEGATE_HIGH
                    addd      #160
                    STEP_X_D cmpd
                    ifne CLAMP_CHECK_DIMENSIONS
                    bhs       ClampTopLimit
                    else
                    bge       ClampTopLimit
                    endc
                    STEP_X_D std
                    lda       #2
                    CLAMP_EDGE_STORE
ClampTopLimit       clra
                    CLAMP_HEIGHT_READ
                    ifne CLAMP_CHECK_DIMENSIONS
                    CLAMP_REJECT beq
                    endc
                    decb
                    STEP_Y_D cmpd
                    ble       ClampBottomLimit
                    STEP_Y_D std
                    lda       #1
                    CLAMP_EDGE_STORE
                    ifne CLAMP_VERTICAL_EXIT
                    bra       ClampCoordinatesDone
                    endc
ClampBottomLimit    equ *
                    ifne CLAMP_CANDIDATE_FIRST
                    STEP_Y_D ldd
                    cmpd      #167
                    ble       ClampHorizon
                    ldd       #167
                    else
                    ldd       #167
                    STEP_Y_D cmpd
                    bge       ClampHorizon
                    endc
                    STEP_Y_D std
                    lda       #3
                    CLAMP_EDGE_STORE
                    ifne CLAMP_VERTICAL_EXIT
                    bra       ClampCoordinatesDone
                    endc
ClampHorizon        lda       <$26,u
                    bita      #8
                    bne       ClampCoordinatesDone
                    ifeq CLAMP_BYTE_HORIZON
                    clra
                    CLAMP_HORIZON_READ
                    addd      #1
                    STEP_Y_D cmpd
                    ble       ClampCoordinatesDone
                    STEP_Y_D std
                    else
                    CLAMP_HORIZON_READ
                    CLAMP_HORIZON_COMPARE
                    bls       ClampCoordinatesDone
                    inca
                    CLAMP_HORIZON_STORE
                    endc
                    lda       #1
                    CLAMP_EDGE_STORE
ClampCoordinatesDone equ *
