* wildbits motion bindings. No code is emitted by this include.

* ===== coordinate-step =====
* X is the private motion context, U the object; Y is the table scratch cursor.
STEP_JOIN_STORES    equ 1
STEP_X_D            macro
                    \1       motionx,x
                    endm
STEP_Y_D            macro
                    \1       motiony,x
                    endm
STEP_DISTANCE_D     macro
                    \1       motionstep,x
                    endm
STEP_X_DIRECTION    macro
                    leay      MotionXDelta,pcr
                    ldb       $21,u
                    lda       b,y
                    endm
STEP_Y_DIRECTION    macro
                    leay      MotionYDelta,pcr
                    ldb       $21,u
                    lda       b,y
                    endm

* ===== coordinate-clamp =====
* Checked dimensions and word-sized candidates in private context X.
CLAMP_CHECK_DIMENSIONS equ 1
CLAMP_CANDIDATE_FIRST equ 1
CLAMP_VERTICAL_EXIT equ 0
CLAMP_BYTE_HORIZON equ 0
CLAMP_LEFT_READ     macro
                    ldd       motionx,x
                    endm
CLAMP_WIDTH_READ    macro
                    ldb       $1C,u
                    endm
CLAMP_HEIGHT_READ   macro
                    ldb       $1D,u
                    endm
CLAMP_NEGATE_HIGH   macro
                    coma
                    endm
CLAMP_EDGE_STORE    macro
                    sta       motionedge,x
                    endm
CLAMP_HORIZON_READ  macro
                    ldb       <vmhorizon
                    endm
CLAMP_REJECT       macro
                    l\1       MotionInvalid
                    endm

* ===== position-commit =====
* Private word candidates; terrain has already passed before this transaction.
POSITION_TERRAIN_PRECHECKED equ 1
POSITION_STORE_CANDIDATE macro
                    ldu       motionobject,x
                    ldb       motionx+1,x
                    stb       3,u
                    ldb       motiony+1,x
                    stb       4,u
                    endm
POSITION_TEST_COLLISION macro
                    lbsr      MotionObjectCollision
                    endm
POSITION_COLLISION_RESULT macro
                    tstb
                    endm
POSITION_RESTORE_OLD macro
                    ldd       motionoldposition,x
                    std       3,u
                    endm
POSITION_RECOVER macro
                    lbra      MotionBlocked
                    endm
POSITION_ACCEPT_STATE macro
                    lda       $25,u
                    anda      #$BF
                    sta       $25,u
                    endm
POSITION_BOUNDARY_READ macro
                    lda       motionedge,x
                    endm
POSITION_BOUNDARY_EMPTY macro
                    beq       MotionCheckDestination
                    endm
POSITION_OBJECT_ID macro
                    ldb       motionid,x
                    endm
POSITION_EGO_BOUNDARY macro
                    sta       vmvariables+2,x
                    endm
POSITION_BOUNDARY_CONTINUE macro
                    bra       MotionCheckDestination
                    endm
POSITION_OTHER_BOUNDARY macro
                    stb       vmvariables+4,x
                    sta       vmvariables+5,x
                    endm

* ===== target-motion =====
* Native stepping classifies exact signs; target clamp uses the real step.
TARGET_COMPLETE_ZERO equ 0
TARGET_STOP_FIRST equ 1
TARGET_PREPARE macro
                    pshs      x
                    endm
TARGET_STEP_READ macro
                    ldd       #1
                    endm
TARGET_DIRECTION_CONTEXT macro
                    puls      x
                    endm
TARGET_DIRECTION_STORE macro
                    tfr       a,b
                    stb       $21,u
                    endm
TARGET_STEP_STORE macro
                    sta       $1E,u
                    endm
TARGET_STOP macro
                    clr       $21,u
                    clr       $22,u
                    endm
TARGET_FLAG_SET macro
                    ldb       $2A,u
                    leay      vmflags,x
                    clra
                    leay      d,y
                    lda       #1
                    sta       ,y
                    endm
TARGET_EGO_TEST macro
                    tst       motionid,x
                    endm
TARGET_EGO_STATE macro
                    clr       vmvariables+6,x
                    sta       <vmplayercontrol
                    endm
