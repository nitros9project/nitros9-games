* Shared object command/state component. Macro definitions emit no code.
SHARED_OBJECT_COMMANDS_DEFINED equ 1

* ===== room-object-reset =====
* Room entry disables animation/drawing and resets cel/rate state in each
* 43-byte object record. Preserve owner zero-load encodings (CoCo LDD,
* native CLRA/CLRB), so sharing this transition does not change CoCo bytes.
* Parameters: record register, split-zero-load flag. Leaves A=1, B=0.
OBJECT_ROOM_RESET macro
                    lda       <$26,\1
                    anda      #$BE
                    ora       #$10
                    sta       <$26,\1
                    ifne      \2
                    clra
                    clrb
                    else
                    ldd       #0
                    endc
                    sta       <$25,\1
                    std       <$10,\1
                    std       6,\1
                    std       <$16,\1
                    inca
                    sta       <$1E,\1
                    sta       <$1F,\1
                    sta       <$20,\1
                    sta       1,\1
                    sta       ,\1
                    endm

* ===== object-animation-state =====
* Begin animation only once; repeated animate.obj preserves the live record.
* Parameters: record pointer register, owner's already-animated continuation.
OBJECT_ANIMATE_STATE macro
                    lda       <$26,\1
                    bita      #$40
                    bne       \2
                    lda       #$70
                    sta       <$26,\1
                    lda       #$00
                    sta       <$22,\1
                    sta       <$23,\1
                    sta       <$21,\1
                    endm

* ===== object-cycle-state =====
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

* ===== object-rate-state =====
* Store a step/cycle rate; optionally reset its countdown to the same value.
* Parameters: value accumulator, record register, rate field, countdown field
* (-1 omits countdown). Preserve owners' original indexed encodings.
OBJECT_RATE_STATE   macro
                    ifeq      \3
                    st\1      ,\2
                    else
                    st\1      \3,\2
                    endc
                    ifge      \4
                    st\1      \4,\2
                    endc
                    endm

* ===== object-motion-state =====
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

* ===== object-block-state =====
* Object U/control state: clear crossing bit, or stop after a crossing.
* The owner binds ego identity and its direction variable; no mapping occurs.
OBJECT_BLOCK_CLEAR  macro
                    lda       <$26,\1
                    anda      #$7F
                    sta       <$26,\1
                    endm
OBJECT_BLOCK_STOP   macro
                    lda       <$26,\1
                    ora       #$80
                    sta       <$26,\1
                    clr       <$21,\1
                    BLOCK_STATE_EGO \2
                    BLOCK_STATE_EGO_STOP
                    endm

* ===== object-unanimate =====
* Clear animated/visible bits in every owned 43-byte record, preserving
* all other fields. Owner supplies exclusive-end or positive-count traversal.
* Parameters: record register, loop label, completion label.
OBJECT_UNANIMATE_ALL macro
\2                  UNANIMATE_LIMIT \3
                    lda       <$26,\1
                    anda      #$BE
                    sta       <$26,\1
                    lea\1     <$2B,\1
                    UNANIMATE_NEXT \2
\3
                    endm

* ===== object-flag-mask =====
* Shared object flag mutation; compile out identity operations.
* Parameters: field offset, AND mask, OR mask, record pointer register.
OBJECT_FLAG_MASK    macro
                    lda       <\1,\4
                    ifne      (\2)-$FF
                    anda      #\2
                    endc
                    ifne      \3
                    ora       #\3
                    endc
                    sta       <\1,\4
                    endm

* ===== object-coordinate-state =====
* Shared position/get-position/reposition state on the common 43-byte record.
* Owners supply operand reads, output variable pointers and signed-delta storage.
* Coordinate arithmetic retains byte wrapping above 255 and clamps negative
* signed relative results to zero before platform-specific placement validation.
OBJECT_POSITION     macro
                    ifne      \2
                    OBJECT_FETCH_VARIABLE_X
                    OBJECT_FETCH_VARIABLE_Y
                    else
                    OBJECT_FETCH_POSITION
                    endc
                    std       $03,\1
                    ifne      \3
                    std       <$1A,\1
                    endc
                    endm
OBJECT_GET_POSITION macro
                    OBJECT_POSITION_RESULT_POINTER 1
                    lda       $03,\1
                    sta       ,\2
                    OBJECT_POSITION_RESULT_POINTER 2
                    lda       $04,\1
                    sta       ,\2
                    endm
OBJECT_SIGNED_DELTA macro
                    sex
                    OBJECT_DELTA_SAVE
                    clra
                    ldb       \2,\1
                    OBJECT_DELTA_ADD
                    bpl       \3
                    clrb
\3                  stb       \2,\1
                    endm

* ===== object-scalar-state =====
* Priority/direction assignment on a resolved 43-byte object record.
* Priority preloading is an ABI trait, preserving flags/read/write ordering.
* Parameters: record register and literal/variable source trait for priority;
* record register and loaded-value register for direction.
OBJECT_SET_PRIORITY macro
                    ifne      PRIORITY_PRELOADED
                    PRIORITY_VALIDATE
                    stb       <$24,\1
                    endc
                    lda       <$26,\1
                    ora       #4
                    sta       <$26,\1
                    ifeq      PRIORITY_PRELOADED
                    PRIORITY_READ \2
                    sta       <$24,\1
                    endc
                    endm
OBJECT_SET_DIRECTION macro
                    DIRECTION_READ
                    DIRECTION_VALIDATE
                    st\2      <$21,\1
                    DIRECTION_EGO_TEST \3
                    DIRECTION_EGO_STORE
                    endm

* ===== object-field-query =====
* Shared AGI object-field queries on an owner's object record.
* QUERY_OBJECT resolves the decoded object operand and consumes its byte.
* QUERY_LOAD reads a record field into A. QUERY_VARIABLE_TABLE supplies
* X=variable[0], preserving A/B/Y; QUERY_RETURN preserves owner ABI.
* QUERY_LAST_VALID retains each owner's empty-loop policy before decrement.
OBJECT_FIELD_QUERY   macro
\1                  QUERY_OBJECT
                    QUERY_LOAD \2
                    ifne      \3
                    QUERY_LAST_VALID
                    deca
                    endc
                    ldb       ,y+
                    QUERY_VARIABLE_TABLE
                    abx
                    sta       ,x
                    QUERY_RETURN
                    endm

* ===== View field query handlers =====
OBJECT_EMIT_VIEW_QUERIES macro
* View-state handlers use the common record-to-variable query implementation.
                    OBJECT_FIELD_QUERY cmd_last_cel,$0F,1
                    OBJECT_FIELD_QUERY cmd_current_cel,$0E,0
                    OBJECT_FIELD_QUERY cmd_current_loop,$0A,0
                    OBJECT_FIELD_QUERY cmd_current_view,$05,0
                    OBJECT_FIELD_QUERY cmd_number_of_loops,$0B,0
                    endm

* Resolve one little-endian view table entry (0=loop, 1=cel).
* B is the selected index. Providers supply pointer/offset addressing,
* bounded resource reads, validation and destination storage. The traversal
* preserves the CoCo byte index and native 16-bit offset arithmetic.
OBJECT_VIEW_TABLE_ENTRY macro
                    ifne VIEW_ENTRY_WIDE
                    clra
                    endc
                    lslb
                    ifne VIEW_ENTRY_WIDE
                    rola
                    ifne \1
                    addd      #1
                    else
                    addd      #5
                    endc
                    else
                    ifne \1
                    addb      #2
                    else
                    addb      #6
                    endc
                    endc
                    VIEW_ENTRY_BASE \1
                    VIEW_ENTRY_READ
                    VIEW_ENTRY_RESOLVE \1
                    endm

* Visibility is published only after a complete cel draw, and only for ego.
* Owners bind tracking storage and packed/byte AGI flag-1 representation.
OBJECT_SPRITE_VISIBILITY_BEGIN macro
                    lda       #1
                    SPRITE_VIS_STORE
                    endm
OBJECT_SPRITE_VISIBLE_PIXEL macro
                    SPRITE_VIS_CLEAR
                    endm
* Parameters: done and visible continuations (retain owner public labels).
OBJECT_SPRITE_VISIBILITY_FINISH macro
                    SPRITE_VIS_EGO_TEST
                    bne       \1
                    SPRITE_VIS_READ
                    beq       \2
                    SPRITE_VIS_PUBLISH_HIDDEN
                    bra       \1
\2                  SPRITE_VIS_PUBLISH_VISIBLE
\1                  equ *
                    endm

* Reconcile a newly selected cel with the existing position. A=width,
* B=height; owner supplies object register, horizon and right-add overflow
* policy. Retain the original height/horizon rule and clip-state bit.
* Parameters: object register, height continuation, done, right-clip label.
OBJECT_CEL_CLIP macro
                    adda      $03,\1
                    ifne CEL_CLIP_CHECK_CARRY
                    bcs       \4
                    endc
                    cmpa      #$A0
                    bls       \2
\4                  equ *
                    lda       <$25,\1
                    ora       #$04
                    sta       <$25,\1
                    lda       #$A0
                    suba      <$1C,\1
                    sta       $03,\1
\2                  decb
                    cmpb      $04,\1
                    bls       \3
                    lda       <$25,\1
                    ora       #$04
                    sta       <$25,\1
                    stb       $04,\1
                    CEL_CLIP_HORIZON cmpb
                    bhi       \3
                    lda       <$26,\1
                    bita      #$08
                    bne       \3
                    CEL_CLIP_HORIZON ldb
                    incb
                    stb       $04,\1
\3                  equ *
                    endm

* ===== room-entry-position =====
* Place ego on the opposite edge after a room transition. Side 0 or unknown
* values retain its coordinates. Width subtraction intentionally wraps as a
* byte, matching the legacy CoCo contract. No resources are acquired here.
* Parameters: ego record offset and owner base register. Side storage is bound
* by ROOM_ENTRY_READ_SIDE / ROOM_ENTRY_CLEAR_SIDE. A/flags are scratch;
* B/X/Y/U and all unrelated object fields are preserved.
OBJECT_ROOM_ENTRY macro
RoomEntryStart      ROOM_ENTRY_READ_SIDE
                    cmpa      #1
                    beq       RoomEntryTop
                    cmpa      #2
                    beq       RoomEntryRight
                    cmpa      #3
                    beq       RoomEntryBottom
                    cmpa      #4
                    bne       RoomEntryDone
                    lda       #160
                    suba      \1+$1C,\2
                    sta       \1+3,\2
                    bra       RoomEntryDone
RoomEntryTop        lda       #167
                    sta       \1+4,\2
                    bra       RoomEntryDone
RoomEntryRight      clr       \1+3,\2
                    bra       RoomEntryDone
RoomEntryBottom     lda       #37
                    sta       \1+4,\2
RoomEntryDone       ROOM_ENTRY_CLEAR_SIDE
RoomEntryFinished   equ *
                    endm

* Object-status diagnostic: owner supplies frame/buffer/storage bindings.
* Word-argument layout and cycle/motion selection match the CoCo command.
OBJECT_EMIT_STATUS_STRINGS macro
StrNormalCycle      fcc       /normal cycle/
                    fcb       0
StrEndOfLoop        fcc       /end of loop/
                    fcb       0
StrReverseLoop      fcc       /reverse loop/
                    fcb       0
StrReverseCycle     fcc       /reverse cycle/
                    fcb       0
StrNormalMotion     fcc       /normal motion/
                    fcb       0
StrWander           fcc       /wander/
                    fcb       0
StrFollow           fcc       /follow/
                    fcb       0
StrMoveTo           fcc       /move to (%d, %d)/
                    fcb       0
StrObjHeader        fcc       /Object %d:/
                    fcb       $0a
StrObjX             fcc       /x: %d  xsize: %d/
                    fcb       $0a
StrObjY             fcc       /y: %d  ysize: %d/
                    fcb       $0a
StrObjPri           fcc       /pri: %d/
                    fcb       $0a
StrObjStepSize      fcc       /stepsize: %d/
                    fcb       $0a
StrObjControl       fcc       /control: %x/
                    fcb       $0a
StrFmtNewline       fcc       /%s/
                    fcb       $0a
StrFmtNull          fcc       /%s/
                    fcb       0
                    endm
OBJECT_EMIT_STATUS macro
CmdObjStatusV       leas      >-OBJECT_STATUS_FRAME,s
                    OBJECT_STATUS_SELECT
                    std       >OBJECT_STATUS_OBJECT,s  save object address on stack
                    lda       <$23,u    load cycle type
                    cmpa      #$00      check if normal cycling
                    bne       CheckCycleType1 branch if not normal cycle
                    leax      >StrNormalCycle,pcr normal cycle
                    bra       GotCycleStr
CheckCycleType1     cmpa      #$01      check if end-of-loop mode
                    bne       CheckCycleType2 branch if not end-of-loop
                    leax      >StrEndOfLoop,pcr end of loop
                    bra       GotCycleStr
CheckCycleType2     cmpa      #$02      check if reverse-loop mode
                    bne       DefaultCycleStr branch if none of the above
                    leax      >StrReverseLoop,pcr reverse loop
                    bra       GotCycleStr
DefaultCycleStr     leax      >StrReverseCycle,pcr reverse cycle
GotCycleStr         stx       >OBJECT_STATUS_CYCLE,s  save cycle type string pointer
                    lda       <$22,u    load motion type
                    cmpa      #$00      check if normal motion
                    bne       CheckMotionType1 branch if not normal motion
                    leax      >StrNormalMotion,pcr normal motion
                    bra       GotMotionStr
CheckMotionType1    cmpa      #$01      check if wander motion
                    bne       CheckMotionType2 branch if not wander
                    leax      >StrWander,pcr wander
                    bra       GotMotionStr
CheckMotionType2    cmpa      #$02      check if follow-ego motion
                    bne       BuildMoveToStr branch if not follow (must be move-to)
                    leax      >StrFollow,pcr follow
                    bra       GotMotionStr
BuildMoveToStr      clra                clear A for word construction
                    ldb       <$28,u    load target Y position
                    pshs      b,a       push Y arg for format
                    ldb       <$27,u    load target X position
                    pshs      b,a       push X arg for format
                    leax      >StrMoveTo,pcr load "move to (%d, %d)" format string
                    pshs      x         push format string pointer
                    OBJECT_STATUS_MOTION_BUFFER
                    pshs      x         push output buffer pointer
                    OBJECT_STATUS_MOTION_FORMAT
MoveToFormatDone    leas      $08,s     release 4 pushed arguments
GotMotionStr        pshs      x         push motion string pointer
                    ldx       >OBJECT_STATUS_CYCLE+2,s  load saved cycle string
                    pshs      x         push object address for format
                    ldu       >OBJECT_STATUS_OBJECT+4,s  reload object address
                    ldd       <$25,u    load animation flags (both bytes)
                    pshs      b,a       push flags
                    clra                clear A for word construction
                    ldb       <$1E,u    load step size
                    pshs      b,a       push step size
                    ldb       <$24,u    load priority
                    pshs      b,a       push priority
                    ldb       <$1D,u    load Y size
                    pshs      b,a       push Y size
                    ldb       $04,u     load Y position
                    pshs      b,a       push Y position
                    ldb       <$1C,u    load X size
                    pshs      b,a       push X size
                    ldb       $03,u     load X position
                    pshs      b,a       push X position
                    ldb       $02,u     load object number
                    pshs      b,a       push object number
                    leau      >StrObjHeader,pcr load address of object header format string
                    pshs      u         push format string pointer
                    OBJECT_STATUS_OUTPUT_BUFFER
                    pshs      x         push output buffer pointer
                    lbsr      PrintFmtStr
                    leas      <$18,s    release all pushed arguments
                    OBJECT_STATUS_DISPLAY
                    leas      >OBJECT_STATUS_FRAME,s
                    rts
                    endm
