* coco-objects-bindings feature bindings. Included once; emits no code.
PLATFORM_COCO_OBJECTS_BINDINGS equ 1

* ===== coco-motion-operands =====
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

* ===== coco-motion-setup =====
* CoCo packed completion flags and ego input-control bindings.
MOTION_CLEAR_FLAG   macro
                    lbsr      ClearFlag
                    endm
MOTION_RESET_WANDER macro
                    endm
MOTION_DISABLE_EGO  macro
                    cmpu      <$0030
                    bne       \1
                    clr       >$0250
                    endm
MOTION_FETCH_STEP  macro
                    ifne      \1
                    ldb       ,y+
                    ldx       #$0431
                    abx
                    lda       ,x
                    else
                    lda       ,y+
                    endc
                    endm
MOTION_FETCH_MOVE_FLAG macro
                    lda       ,y+
                    endm
MOTION_START_MOVE    macro
                    lbsr      SetObjMotion
                    endm

* ===== coco-object-bounds-operands =====
* CoCo permits zero width and retains A as the Boolean result accumulator.
BOUNDS_REJECT_ZERO_WIDTH equ 0
BOUNDS_HORIZON_COMPARE macro
                    cmpb      >$01D6
                    endm
BOUNDS_HORIZON_FLAGS macro
                    ldb       <$26,\1
                    bitb      #8
                    endm

* ===== coco-object-collision-operands =====
* CoCo identifies self by record ID after activity/ignore checks.
COLLISION_SELF_FIRST equ 0
COLLISION_SELF_SKIP macro
                    ld\2      $02,\1
                    cmp\2     $02,u
                    beq       \3
                    endm

COLLISION_WIDE      equ 0
COLLISION_RESULT_B  equ 0
COLLISION_SCAN_ACTOR macro
                    clra
                    COLLISION_IGNORE u,b,CollisionScanEmpty
                    endm
COLLISION_SCAN_INIT macro
                    ldx       <$0030
                    endm
COLLISION_SCAN_END  macro
                    cmpx      <$0032
                    bcc       CollisionScanEmpty
                    endm
COLLISION_SCAN_FILTER macro
                    COLLISION_CANDIDATE x,b,CollisionScanAdvance
                    endm
COLLISION_SCAN_OVERLAPS macro
                    COLLISION_HORIZONTAL u,x,1
                    COLLISION_HORIZONTAL x,u,0
                    endm
COLLISION_SCAN_BASELINE macro
                    COLLISION_BASELINE x,0
                    endm
COLLISION_SCAN_NEXT macro
                    leax      <$2B,x
                    bra       CollisionScanLoop
                    endm

* ===== coco-object-control-operands =====
* CoCo ego is the first record; direction is variable six.
BLOCK_STATE_EGO     macro
                    cmpu      <$0030
                    bne       \1
                    endm
BLOCK_STATE_EGO_STOP macro
                    clr       >$0437
                    endm
UNANIMATE_LIMIT     macro
                    cmpu      <$0032
                    bcc       \1
                    endm
UNANIMATE_NEXT      macro
                    bra       \1
                    endm

* ===== coco-object-coordinate-operands =====
* Owner operand/storage bindings for shared object coordinate commands.
OBJECT_FETCH_POSITION macro
                    ldd       ,y++
                    endm
OBJECT_FETCH_VARIABLE_X macro
                    ldx       #$0431
                    ldb       ,y+
                    abx
                    lda       ,x
                    endm
OBJECT_FETCH_VARIABLE_Y macro
                    ldx       #$0431
                    ldb       ,y+
                    abx
                    ldb       ,x
                    endm
OBJECT_POSITION_RESULT_POINTER macro
                    ldx       #$0431
                    ldb       ,y+
                    abx
                    endm
OBJECT_DELTA_SAVE   macro
                    std       ,s
                    endm
OBJECT_DELTA_ADD    macro
                    addd      ,s
                    endm

* ===== coco-object-placement-operands =====
* CoCo frame: object pointer, run length, direction, remaining steps.
SPIRAL_DIRECTION   equ 3
SPIRAL_LENGTH      equ 2
SPIRAL_REMAINING   equ 4
SPIRAL_CHECK_LENGTH equ 0
SPIRAL_CANDIDATE   equ FindObjPosIter
SPIRAL_RESUME      macro
                    bra       FindObjPosIter
                    endm
SPIRAL_REPEAT      macro
                    bne       FindObjPosIter
                    endm

* ===== coco-object-scalar-operands =====
* CoCo reads priority after setting its fixed-priority bit.
PRIORITY_PRELOADED  equ 0
PRIORITY_READ       macro
                    ifne \1
                    ldx       #$0431
                    ldb       ,y+
                    abx
                    lda       ,x
                    else
                    lda       ,y+
                    endc
                    endm
DIRECTION_READ     macro
                    ldb       ,y+
                    ldx       #$0431
                    abx
                    lda       ,x
                    endm
DIRECTION_VALIDATE macro
                    endm
DIRECTION_EGO_TEST macro
                    endm
DIRECTION_EGO_STORE macro
                    endm

* ===== coco-object-view-query-operands =====
* CoCo script operands, object pointer in U, and fixed variable storage.
QUERY_OBJECT        macro
                    lda       ,y+
                    ldb       #$2B
                    mul
                    addd      <$0030
                    tfr       d,u
                    endm
QUERY_LOAD          macro
                    lda       \1,u
                    endm
QUERY_VARIABLE_TABLE macro
                    ldx       #$0431
                    endm
QUERY_LAST_VALID    macro
                    endm
QUERY_RETURN        macro
                    rts
                    endm

* ===== coco-terrain-operands =====
* Packed mapped picture bytes, X=object, U=baseline cursor, B=width countdown.
TERRAIN_WATER_FIRST equ 1
TERRAIN_WATER equ $30
TERRAIN_CONTROL equ $10
TERRAIN_SIGNAL equ $20
TERRAIN_PIXEL_READ macro
                    lda       ,u+
                    anda      #$F0
                    endm
TERRAIN_BLOCK macro
                    \1       ClearFlagControl
                    endm
TERRAIN_CLEAR_WATER macro
                    clr       ScratchA6
                    endm
TERRAIN_IGNORE_CONTROL macro
                    lda       $26,x
                    bita      #2
                    endm
TERRAIN_SET_SIGNAL macro
                    sta       ScratchA5
                    endm
TERRAIN_ADVANCE macro
                    decb
                    bne       TerrainPixelLoop
                    endm
TERRAIN_STATUS_READ macro
                    lda       $25,x
                    endm
TERRAIN_TEST_WATER macro
                    tst       ScratchA6
                    endm

* View table addressing: little-endian entries in the mapped owner buffer.
VIEW_ENTRY_WIDE equ 0
VIEW_ENTRY_BASE macro
                    ifne \1
                    ldx       $0C,u
                    else
                    ldx       $06,u
                    endc
                    endm
VIEW_ENTRY_READ macro
                    lda       b,x
                    decb
                    ldb       b,x
                    endm
VIEW_ENTRY_RESOLVE macro
                    leax      d,x
                    ifne \1
                    stx       <$10,u
                    else
                    stx       $0C,u
                    endc
                    endm

* Sprite visibility tracker and packed ego-hidden flag.
SPRITE_VIS_STORE macro
                    sta       ScratchAC
                    endm
SPRITE_VIS_CLEAR macro
                    clr       ScratchAC
                    endm
SPRITE_VIS_READ macro
                    lda       ScratchAC
                    endm
SPRITE_VIS_EGO_TEST macro
                    ldx       2,s
                    lda       2,x
                    endm
SPRITE_VIS_PUBLISH_HIDDEN macro
                    lda       StateFlag
                    ora       #$40
                    sta       StateFlag
                    endm
SPRITE_VIS_PUBLISH_VISIBLE macro
                    lda       StateFlag
                    anda      #$BF
                    sta       StateFlag
                    endm
