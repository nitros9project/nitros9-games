* Animation component: per-object update, cel progression and direction tables.
* Definitions emit code only at the named expansion sites.

* ===== object-animation-update =====
ANIMATION_EMIT_UPDATE macro
* Per-object direction-driven loop selection and cycle countdown.
* U is the object record. Platform policy is selected at assembly time;
* metadata acquisition and return/iteration conventions remain owner bindings.
                    ifeq WILDBITS
                    ldb       #4
                    endc
AnimationUpdate     lda       <$25,u
                    bita      #$20
                    bne       AnimationCycleTick
                    lda       $0B,u
                    ifne WILDBITS
                    cmpa      #2
                    blo       AnimationCycleTick
                    cmpa      #4
                    bhi       AnimationCycleTick
                    leay      DirTableFwd,pcr
                    cmpa      #4
                    bne       MotionChooseLoop
                    leay      DirTableRev,pcr
MotionChooseLoop    ldb       $21,u
                    cmpb      #8
                    lbhi      MotionInvalid
                    ldb       b,y
                    else
                    cmpa      #$03      compare to 3 loops
                    bhi       CheckCycleType4 branch if more than 3 loops
                    cmpa      #$02      compare to 2 loops
                    bcs       AnimationCycleTick branch if fewer than 2 loops
                    lda       <$21,u    load current movement direction
                    leay      >DirTableFwd,pcr point to forward direction table
                    ldb       a,y       look up loop index from direction
                    bra       CheckObjVisible go validate the loop index
CheckCycleType4     cmpa      #$04      check if exactly 4 loops
                    beq       LookupRevDirTable branch if 4 loops (use reverse table)
                    ANIMATION_REVERSE_ENABLE
                    beq       AnimationCycleTick branch if reverse dir not enabled
LookupRevDirTable   lda       <$21,u    load current movement direction
                    leay      >DirTableRev,pcr point to reverse direction table
                    ldb       a,y       look up reverse loop index
CheckObjVisible     lda       $01,u     load legacy step countdown
CheckObjIsEgo       cmpa      #$01      require countdown equal to one
                    bne       AnimationCycleTick branch if countdown differs
                    endc
                    cmpb      #4
                    beq       AnimationCycleTick
                    cmpb      $0A,u
                    beq       AnimationCycleTick
                    ANIMATION_SELECT_LOOP
AnimationCycleTick  lda       <$26,u
                    bita      #$20
                    beq       AnimationCycleDone
                    lda       <$20,u
                    beq       AnimationCycleDone
                    dec       <$20,u
                    bne       AnimationCycleDone
                    ifeq WILDBITS
                    lbsr      AdvanceCelFrame
                    endc
                    lda       <$1F,u
                    sta       <$20,u
                    ifne WILDBITS
                    lbra      AdvanceCelFrame
                    endc
AnimationCycleDone equ *
                    ANIMATION_FINISH
                    endm

* ===== object-cel-advance =====
ANIMATION_EMIT_CEL_ADVANCE macro
* Common cel progression for cycle modes 0/1/2/3 and one-tick suppression.
* U=object. Owners bind the two adjacent DP scratch bytes,
* completion flag, cel selection and status return. No state is allocated.
AdvanceCelFrame     lda       <$25,u    load object animation flags
                    bita      #$10      test single-cycle-advance flag
                    beq       GetCelIndex branch if normal cycling
                    anda      #$EF      clear single-advance flag
                    sta       <$25,u    store updated flags
                    bra       AdvCelReturn done for this cycle
GetCelIndex         ldd       $0E,u     load current cel number (A) and last cel (B)
                    decb                decrement last-cel index for comparison
                    std       <CycleCurrent    save current and max cel indices
                    CYCLE_READ_MODE
                    cmpa      #$00      check if forward cycling
                    bne       CycleReverse branch if not forward cycle
                    ldb       <CycleCurrent    reload current cel index
                    incb                advance to next cel
                    cmpb      <CycleLast    compare to maximum cel index
                    bls       SetCelInLoop branch if still within range
                    clrb                wrap back to cel 0
                    bra       SetCelInLoop go set the new cel
CycleReverse        cmpa      #$03      check if reverse-cycle mode
                    bne       CycleRevEnd branch if not reverse cycling
                    ldb       <CycleCurrent    load current cel index
                    subb      #1        unsigned previous index; C marks wrap
                    bcc       SetCelInLoop
                    ldb       <CycleLast    wrap to last cel
                    bra       SetCelInLoop go set the new cel
CycleRevEnd         cmpa      #$02      check if end-of-loop mode
                    bne       CycleEnd  branch if not end-of-loop
                    ldb       <CycleCurrent    load current cel index
                    beq       NotifyEndOfLoop branch if already at cel 0
                    decb                step back one cel
                    bne       SetCelInLoop branch if not yet at cel 0
                    stb       <CycleCurrent    save cel index (0)
                    bra       NotifyEndOfLoop signal end of loop
CycleEnd            cmpa      #$01      check if end-of-forward-loop mode
                    bne       SetCelInLoop branch if none of the special modes
                    ldb       <CycleCurrent    load current cel index
                    cmpb      <CycleLast    compare to last cel
                    bcc       NotifyEndOfLoop branch if at or past last cel
                    incb                advance to next cel
                    cmpb      <CycleLast    compare to last cel again
                    bne       SetCelInLoop branch if not yet at end
                    stb       <CycleCurrent    save last cel index
NotifyEndOfLoop     CYCLE_NOTIFY_FLAG
                    lda       <$26,u    load object state flags
                    anda      #$DF      clear loop-active bit
                    sta       <$26,u    store updated state
                    clra                clear zero value
                    sta       <$21,u    halt object direction (stop)
                    sta       <$23,u    clear cycle mode
                    ldb       <CycleCurrent    reload final cel index
SetCelInLoop        CYCLE_SET_CEL
AdvCelReturn        CYCLE_RETURN
                    endm

* ===== object-direction-tables =====
ANIMATION_EMIT_DIRECTION_TABLES macro
* AGI loop selection for movement directions 0..8; value 4 keeps the loop.
DirTableFwd         fcb       4,4,0,0,0,4,1,1,1
DirTableRev         fcb       4,3,0,0,0,2,1,1,1
                    endm
