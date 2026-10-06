* Object-Motion component. Definitions emit no code until invoked.
* Named expansion sites preserve module layout and direct branch/call targets.

* ===== object-motion-schedule =====
MOTION_EMIT_SCHEDULE macro
* Per-object eligibility, owner step schedule, and complete motion dispatch.
* Cursor U remains on the selected object. Owners supply iteration/error
* continuations and context restoration; no runtime platform dispatch exists.
MotionSchedule      lda       <$26,u
                    anda      #$51
                    cmpa      #$51
                    SCHEDULE_SKIP_INACTIVE
                    SCHEDULE_STEP_READY
                    lda       <$22,u
                    beq       MotionScheduleReady
                    cmpa      #1
                    bne       MotionScheduleNotWander
                    lbsr      ObjAnimStep
                    bra       MotionScheduleReady
MotionScheduleNotWander cmpa #2
                    bne       MotionScheduleNotFollow
                    lbsr      CalcFollowDir
                    SCHEDULE_FOLLOW_CONTEXT
                    bra       MotionScheduleReady
MotionScheduleNotFollow cmpa #3
                    SCHEDULE_UNKNOWN
                    SCHEDULE_TARGET_DIRECTION
MotionScheduleReady equ *
                    endm

* ===== object-coordinate-step =====
MOTION_EMIT_COORDINATE_STEP macro
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
                    endm

* ===== object-coordinate-clamp =====
MOTION_EMIT_CLAMP macro
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
                    endm

* ===== object-position-commit =====
MOTION_EMIT_COMMIT macro
* Candidate-position transaction and boundary publication.
* Owners bind coordinates, collision ABI, terrain lifecycle, rejected recovery
* and the next movement stage. No new storage or runtime dispatch is introduced.
PositionCommit      POSITION_STORE_CANDIDATE
                    POSITION_TEST_COLLISION
                    POSITION_COLLISION_RESULT
                    ifne POSITION_TERRAIN_PRECHECKED
                    beq       PositionAccepted
                    else
                    bne       PositionRejected
                    POSITION_VALIDATE_TERRAIN
                    bne       PositionAccepted
                    endc
PositionRejected    POSITION_RESTORE_OLD
                    POSITION_RECOVER
PositionAccepted    POSITION_ACCEPT_STATE
                    POSITION_BOUNDARY_READ
                    POSITION_BOUNDARY_EMPTY
                    POSITION_OBJECT_ID
                    bne       PositionOtherBoundary
                    POSITION_EGO_BOUNDARY
                    POSITION_BOUNDARY_CONTINUE
PositionOtherBoundary POSITION_OTHER_BOUNDARY
PositionCommitDone  equ *
                    endm

* ===== object-target-motion =====
MOTION_EMIT_TARGET macro
* Target direction and arrival state transition. U is the object cursor.
* Owners bind step threshold, context/result ABI, flag storage and ego state.
TargetDirection     TARGET_PREPARE
                    TARGET_STEP_READ
                    pshs      b,a
                    ldd       <$27,u
                    pshs      b,a
                    ldd       3,u
                    pshs      b,a
                    lbsr      CalcMoveDir
                    leas      6,s
                    TARGET_DIRECTION_CONTEXT
TargetStoreDirection TARGET_DIRECTION_STORE
                    ifne TARGET_COMPLETE_ZERO
                    bne       TargetDirectionReturn
                    bsr       TargetReached
                    endc
TargetDirectionReturn rts
TargetReached       lda       <$29,u
                    TARGET_STEP_STORE
                    ifne TARGET_STOP_FIRST
                    TARGET_STOP
                    endc
                    TARGET_FLAG_SET
                    ifeq TARGET_STOP_FIRST
                    TARGET_STOP
                    endc
                    TARGET_EGO_TEST
                    bne       TargetReachedReturn
                    TARGET_EGO_STATE
TargetReachedReturn rts
                    endm
