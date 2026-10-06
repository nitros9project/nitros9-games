* coco motion bindings. No code is emitted by this include.

* ===== coordinate-step =====
* Candidate coordinates and step are in UpdateAllMotion's private stack frame.
STEP_JOIN_STORES    equ 0
STEP_X_D            macro
                    \1       $03,s
                    endm
STEP_Y_D            macro
                    \1       $05,s
                    endm
STEP_DISTANCE_D     macro
                    \1       $09,s
                    endm
STEP_X_DIRECTION    macro
                    leax      >x_dir_mult,pcr
                    lda       <$21,u
                    lda       a,x
                    endm
STEP_Y_DIRECTION    macro
                    leax      >y_dir_mult,pcr
                    lda       <$21,u
                    lda       a,x
                    endm

* ===== coordinate-clamp =====
* Legacy frame and byte-horizon semantics, including early vertical exits.
CLAMP_CHECK_DIMENSIONS equ 0
CLAMP_CANDIDATE_FIRST equ 0
CLAMP_VERTICAL_EXIT equ 1
CLAMP_BYTE_HORIZON equ 1
CLAMP_LEFT_READ     macro
                    ldd       #0
                    cmpd      $03,s
                    endm
CLAMP_WIDTH_READ    macro
                    ldb       <$1C,u
                    endm
CLAMP_HEIGHT_READ   macro
                    ldb       <$1D,u
                    endm
CLAMP_NEGATE_HIGH   macro
                    lda       #$FF
                    endm
CLAMP_EDGE_STORE    macro
                    sta       $02,s
                    endm
CLAMP_HORIZON_READ  macro
                    lda       >$01D6
                    endm
CLAMP_HORIZON_COMPARE macro
                    cmpa      $06,s
                    endm
CLAMP_HORIZON_STORE macro
                    sta       $06,s
                    endm

* ===== position-commit =====
* Stack-frame candidate/old coordinates; banked terrain service and recovery.
POSITION_TERRAIN_PRECHECKED equ 0
POSITION_STORE_CANDIDATE macro
                    lda       $04,s
                    ldb       $06,s
                    std       $03,u
                    endm
POSITION_TEST_COLLISION macro
                    lbsr      CheckObjCollision
                    endm
POSITION_VALIDATE_TERRAIN macro
                    stu       ,s
                    pshs      u
                    lda       #3
                    sta       <$0021
                    ldx       <$0028
                    jsr       >$0701
                    leas      2,s
                    ldu       ,s
                    lda       <$005C
                    endm
POSITION_COLLISION_RESULT macro
                    tsta
                    endm
POSITION_RESTORE_OLD macro
                    ldd       $07,s
                    std       $03,u
                    endm
POSITION_RECOVER macro
                    clr       $02,s
                    lbsr      FindObjPos
                    endm
POSITION_ACCEPT_STATE macro
                    endm
POSITION_BOUNDARY_READ macro
                    lda       $02,s
                    endm
POSITION_BOUNDARY_EMPTY macro
                    beq       UpdateObjFlags
                    endm
POSITION_OBJECT_ID macro
                    ldb       $02,u
                    endm
POSITION_EGO_BOUNDARY macro
                    sta       >$0433
                    endm
POSITION_BOUNDARY_CONTINUE macro
                    bra       CheckMoveTarget
                    endm
POSITION_OTHER_BOUNDARY macro
                    stb       >$0435
                    sta       >$0436
                    endm

* ===== target-motion =====
* CoCo direction threshold is the actual step. Completion uses packed flags.
TARGET_COMPLETE_ZERO equ 1
TARGET_STOP_FIRST equ 0
TARGET_PREPARE macro
                    endm
TARGET_STEP_READ macro
                    ldb       $1E,u
                    endm
TARGET_DIRECTION_CONTEXT macro
                    cmpu      <$0030
                    bne       TargetStoreDirection
                    sta       >$0437
                    endm
TARGET_DIRECTION_STORE macro
                    sta       <$21,u
                    endm
TARGET_STEP_STORE macro
                    sta       <$1E,u
                    endm
TARGET_STOP macro
                    lda       #0
                    sta       <$22,u
                    endm
TARGET_FLAG_SET macro
                    lda       <$2A,u
                    lbsr      SetFlag
                    endm
TARGET_EGO_TEST macro
                    cmpu      <$0030
                    endm
TARGET_EGO_STATE macro
                    lda       #1
                    sta       >$0250
                    clr       >$0437
                    endm
