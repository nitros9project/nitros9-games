* wildbits-objects-bindings feature bindings. Included once; emits no code.
PLATFORM_WILDBITS_OBJECTS_BINDINGS equ 1

* ===== wildbits-motion-operands =====
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
                    bra       MotionBlocked
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

* ===== wildbits-motion-setup =====
* Native private completion flags, wander reset and ego input control.
* U=private base; X=record; preserve X while clearing the literal flag in A.
MOTION_CLEAR_FLAG   macro
                    leay      vmflags,u
                    tfr       a,b
                    clra
                    clr       d,y
                    endm
MOTION_RESET_WANDER macro
                    clr       $27,\1
                    endm
MOTION_DISABLE_EGO  macro
                    tst       2,x
                    bne       \1
                    clr       <vmplayercontrol
                    endm
* One native handler selects literal/variable step from the staged opcode.
MOTION_FETCH_STEP   macro
                    ldb       <vmopcode
                    cmpb      #82
                    beq       GameMoveVariableStep
                    lda       vmarguments+3,u
                    bra       GameMoveStepRead
GameMoveVariableStep leay     vmvariables,u
                    clra
                    ldb       vmarguments+3,u
                    lda       d,y
GameMoveStepRead
                    endm
MOTION_FETCH_MOVE_FLAG macro
                    lda       vmarguments+4,u
                    endm
MOTION_START_MOVE    macro
                    stx       motionobject,u
                    lda       2,x
                    sta       motionid,u
                    tfr       x,y
                    tfr       u,x
                    tfr       y,u
                    lbsr      MotionMoveDirection
                    endm

* ===== wildbits-object-bounds-operands =====
* Native rejects zero width; A is scratch and horizon belongs to the process.
BOUNDS_REJECT_ZERO_WIDTH equ 1
BOUNDS_HORIZON_COMPARE macro
                    cmpb      <vmhorizon
                    endm
BOUNDS_HORIZON_FLAGS macro
                    lda       <$26,\1
                    bita      #8
                    endm

* ===== wildbits-object-collision-operands =====
* Native context X owns motionobject; skip that pointer before flag reads.
COLLISION_SELF_FIRST equ 1
COLLISION_SELF_SKIP macro
                    cmp\1     motionobject,x
                    beq       \3
                    endm

COLLISION_WIDE      equ 1
COLLISION_RESULT_B  equ 1
COLLISION_SCAN_ACTOR macro
                    COLLISION_IGNORE u,a,CollisionScanEmpty
                    endm
COLLISION_SCAN_INIT macro
                    clr       motioncollision,x
                    leay      vmobjects,x
                    endm
COLLISION_SCAN_END  macro
                    endm
COLLISION_SCAN_FILTER macro
                    COLLISION_CANDIDATE y,a,CollisionScanAdvance
                    endm
COLLISION_SCAN_OVERLAPS macro
                    COLLISION_HORIZONTAL u,y,1
                    COLLISION_HORIZONTAL y,u,0
                    endm
COLLISION_HISTORY_READ macro
                    lda       motionoldposition+1,x
                    endm
COLLISION_SCAN_BASELINE macro
                    COLLISION_BASELINE y,1
                    endm
COLLISION_SCAN_NEXT macro
                    leay      43,y
                    inc       motioncollision,x
                    lda       motioncollision,x
                    cmpa      #64
                    blo       CollisionScanLoop
                    endm

* ===== wildbits-object-control-operands =====
* Native record U and private context X; motionid zero identifies ego.
BLOCK_STATE_EGO     macro
                    tst       motionid,x
                    bne       \1
                    endm
BLOCK_STATE_EGO_STOP macro
                    clr       vmvariables+6,x
                    endm
* Native unanimate receives X=first record and positive Y=record count.
UNANIMATE_LIMIT     macro
                    endm
UNANIMATE_NEXT      macro
                    leay      -1,y
                    bne       \1
                    endm

* ===== wildbits-object-coordinate-operands =====
* Owner operand/storage bindings for shared object coordinate commands.
OBJECT_FETCH_POSITION macro
                    ldd       vmarguments+1,u
                    endm
OBJECT_FETCH_VARIABLE_X macro
                    leay      vmvariables,u
                    ldb       vmarguments+1,u
                    clra
                    lda       d,y
                    endm
OBJECT_FETCH_VARIABLE_Y macro
                    pshs      a
                    clra
                    ldb       vmarguments+2,u
                    ldb       d,y
                    puls      a
                    endm
OBJECT_POSITION_RESULT_POINTER macro
                    leay      vmvariables,u
                    clra
                    ldb       vmarguments+\1,u
                    leay      d,y
                    endm
OBJECT_DELTA_SAVE   macro
                    pshs      d
                    endm
OBJECT_DELTA_ADD    macro
                    addd      ,s++
                    endm

* ===== wildbits-object-placement-operands =====
* Native frame: direction, run length, remaining steps, 16-bit budget.
SPIRAL_DIRECTION   equ 0
SPIRAL_LENGTH      equ 1
SPIRAL_REMAINING   equ 2
SPIRAL_CHECK_LENGTH equ 1
SPIRAL_CANDIDATE   equ RepositionCandidate
SPIRAL_EXHAUSTED   equ RepositionExhausted
SPIRAL_RESUME      macro
                    lbra      RepositionCandidate
                    endm
SPIRAL_REPEAT      macro
                    lbne      RepositionCandidate
                    endm
SPIRAL_LENGTH_ERROR macro
                    beq       RepositionExhausted
                    endm

* ===== wildbits-object-scalar-operands =====
* Native priority is preloaded in B; reject before mutating the record.
PRIORITY_PRELOADED equ 1
PRIORITY_VALIDATE macro
                    cmpb      #15
                    lbhi      ObjectBadIndex
                    endm
DIRECTION_READ     macro
                    bsr       ObjectArgumentValue
                    endm
DIRECTION_VALIDATE macro
                    cmpb      #8
                    lbhi      ObjectBadIndex
                    endm
DIRECTION_EGO_TEST macro
                    tst       vmarguments,u
                    lbne      \1
                    endm
DIRECTION_EGO_STORE macro
                    stb       vmvariables+6,u
                    endm

* ===== wildbits-object-view-query-operands =====
* Validated private record in X, decoded arguments, and native return ABI.
QUERY_OBJECT        macro
                    leay      vmarguments+1,u
                    endm
QUERY_LOAD          macro
                    lda       \1,x
                    endm
QUERY_VARIABLE_TABLE macro
                    leax      vmvariables,u
                    endm
QUERY_LAST_VALID    macro
                    beq       ViewInvalidQuery
                    endm
QUERY_RETURN        macro
                    clrb
                    rts
                    endm

* ===== wildbits-terrain-operands =====
* Private context X and object U. Picture provider may map one owned block.
TERRAIN_WATER_FIRST equ 0
TERRAIN_WATER equ 3
TERRAIN_CONTROL equ 1
TERRAIN_SIGNAL equ 2
TERRAIN_PIXEL_READ macro
                    ldb       motiony+1,x
                    lda       #160
                    mul
                    addd      motionx,x
                    addb      motioncolumn,x
                    adca      #0
                    lbsr      PicturePointer
                    tst       <decodeerror
                    lbne      MotionTerrainError
                    lda       ,u
                    lsra
                    lsra
                    lsra
                    lsra
                    ldu       motionobject,x
                    tsta
                    endm
TERRAIN_BLOCK macro
                    \1       MotionTerrainBlocked
                    endm
TERRAIN_CLEAR_WATER macro
                    clr       motionwater,x
                    endm
TERRAIN_IGNORE_CONTROL macro
                    ldb       $26,u
                    bitb      #2
                    endm
TERRAIN_SET_SIGNAL macro
                    inc       motiontrigger,x
                    endm
TERRAIN_ADVANCE macro
                    inc       motioncolumn,x
                    ldb       motioncolumn,x
                    cmpb      $1C,u
                    blo       TerrainPixelLoop
                    endm
TERRAIN_STATUS_READ macro
                    lda       $25,u
                    endm
TERRAIN_TEST_WATER macro
                    tst       motionwater,x
                    endm

* ===== wildbits-object-code local macros =====
OBJECT_FLAG_RULE    macro
                    ifne      OBJECT_FLAG_TABLE
                    fcb       \2
                    fdb       \1-ObjectFlagTable
                    else
\1                  equ       *
                    OBJECT_FLAG_MASK \3,\4,\5,x
                    clrb
                    rts
                    endc
                    endm

* View table addressing: checked logical offsets with no retained mapping.
VIEW_ENTRY_WIDE equ 1
VIEW_ENTRY_BASE macro
                    ifne \1
                    addd      <viewloopbase
                    endc
                    endm
VIEW_ENTRY_READ macro
                    lbsr      AssetReadWord
                    lbcs      ViewRestore
                    endm
VIEW_ENTRY_RESOLVE macro
                    ifne \1
                    addd      <viewloopbase
                    lbcs      ViewInvalid
                    endc
                    cmpd      <viewminoffset
                    lblo      ViewInvalid
                    ifne \1
                    std       <viewcelbase
                    else
                    cmpd      <resourcelength
                    lbhs      ViewInvalid
                    std       <viewloopbase
                    endc
                    endm

* Sprite visibility tracker and byte-valued AGI ego-hidden flag 1.
SPRITE_VIS_STORE macro
                    sta       spriteinvisible,x
                    endm
SPRITE_VIS_CLEAR macro
                    clr       spriteinvisible,x
                    endm
SPRITE_VIS_READ macro
                    lda       spriteinvisible,x
                    endm
SPRITE_VIS_EGO_TEST macro
                    ldx       <resourcebase
                    ldu       spriteobject,x
                    lda       2,u
                    endm
SPRITE_VIS_PUBLISH_HIDDEN macro
                    lda       #1
                    sta       vmflags+1,x
                    endm
SPRITE_VIS_PUBLISH_VISIBLE macro
                    clr       vmflags+1,x
                    endm

* Selected-cel clipping uses the owner object register and horizon storage.
CEL_CLIP_CHECK_CARRY equ 1
CEL_CLIP_HORIZON macro
                    \1       <vmhorizon
                    endm

* Room-entry side storage; object placement is shared.
ROOM_ENTRY_READ_SIDE macro
                    lda       2,x
                    endm
ROOM_ENTRY_CLEAR_SIDE macro
                    clr       2,x
                    endm


* Motion scheduler interface: native owns cel advancement and step countdown.
SCHEDULE_SKIP_INACTIVE macro
                    lbne      MotionNextObject
                    endm
SCHEDULE_STEP_READY macro
                    lbsr      MotionAdvanceCel
                    lbcs      MotionReturn
                    ldx       <resourcebase
                    ldu       motionobject,x
                    lda       1,u
                    cmpa      #1
                    bls       MotionStepReady
                    dec       1,u
                    lbra      MotionNextObject
MotionStepReady     lda       ,u
                    sta       1,u
                    endm
SCHEDULE_FOLLOW_CONTEXT macro
                    ldx       <resourcebase
                    ldu       motionobject,x
                    endm
SCHEDULE_UNKNOWN macro
                    lbne      MotionUnsupported
                    endm
SCHEDULE_TARGET_DIRECTION macro
                    lbsr      MotionMoveDirection
                    endm
