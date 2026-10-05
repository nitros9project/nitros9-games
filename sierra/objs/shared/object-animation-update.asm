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
