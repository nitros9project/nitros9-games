* Shared CoCo follow-ego direction, blocked wander and completion semantics.
CalcFollowDir       leas      -$05,s    allocate 5-byte local frame on stack
                    ldb       <$27,u    load follow-object's step size
                    pshs      b,a       save step size and A
                    ifne      FOLLOW_PRIVATE_STATE
                    ldx       <resourcebase
                    leax      vmobjects,x
                    else
                    ldx       <$0030    load ego object pointer
                    endc
                    lda       <$1C,x    load ego width
                    lsra                halve width to get center offset
                    adda      $03,x     add X position to get ego center X
                    ldb       $04,x     load ego Y position
                    std       $03,s     save ego center position on stack
                    pshs      b,a       push ego center as CalcMoveDir arg
                    lda       <$1C,u    load follower width
                    lsra                halve width to get center offset
                    adda      $03,u     add X position to get follower center X
                    sta       $07,s     save follower center X
                    ldb       $04,u     load follower Y position
                    pshs      b,a       push follower position as CalcMoveDir arg
                    lbsr      CalcMoveDir compute direction toward ego
                    leas      $06,s     release CalcMoveDir arguments
                    sta       ,s        save computed direction
                    bne       FollowCheckStop branch if direction is non-zero (not yet there)
                    sta       <$21,u    arrived: stop follower (direction = 0)
                    sta       <$22,u    clear motion type (no special motion)
                    lda       <$28,u    load "follow complete" flag number
                    ifne      FOLLOW_PRIVATE_STATE
                    lbsr      GameFollowSetFlag
                    else
                    lbsr      SetFlag   set the follow-complete flag
                    endc
                    bra       FollowRet
FollowCheckStop     lda       <$29,u    load follow delay counter
                    cmpa      #$FF      check for "wander first" sentinel
                    bne       FollowCheckWander branch if not in wander mode
                    clr       <$29,u    clear wander mode
                    bra       FollowSetDir go set the follow direction
FollowCheckWander   lda       <$25,u    load follower animation flags
                    bita      #$40      test "wander allowed" flag
                    beq       FollowDecTimer branch if not in wander mode
FollowSetWander     lbsr      InitRandSeed get random value
                    lda       #$09      random range 0-8 (9 directions)
                    lbsr      Div8      compute random direction
                    sta       <$21,u    store new random direction
                    beq       FollowSetWander loop if direction was 0 (stopped)
                    ldb       $03,s     load ego center X
                    subb      $01,s     subtract follower X to get delta X
                    bcc       FollowCalcDir branch if delta positive
                    negb                negate to get absolute delta X
FollowCalcDir       stb       $04,s     save absolute delta X
                    ldb       $04,u     load follower Y
                    subb      $02,s     subtract ego Y to get delta Y
                    bcc       FollowCalcStep branch if delta positive
                    negb                negate to get absolute delta Y
FollowCalcStep      clra                clear A for word construction
                    addb      $04,s     add delta X to delta Y (Manhattan distance)
                    adca      #$00      propagate carry
                    lsra                divide sum by 2 (A)
                    rorb                shift into B
                    incb                round up
                    stb       $04,s     save computed step distance
                    lda       <$1E,u    load follower step size
                    sta       <$29,u    save as follow timer
                    cmpa      $04,s     compare step size to distance
                    bcc       FollowRet branch if step size >= distance (no random needed)
FollowRandomStep    lbsr      InitRandSeed get random value for step delay
                    lda       $04,s     load computed distance
                    lbsr      Div8      compute random step within distance
                    cmpa      <$1E,u    compare to minimum step size
                    bcs       FollowRandomStep loop if random step too small
                    sta       <$29,u    store random step delay
                    bra       FollowRet
FollowDecTimer      lda       <$29,u    load follow delay counter
                    beq       FollowSetDir branch if counter is zero (time to move)
                    clr       <$29,u    clear counter temporarily
                    suba      <$1E,u    subtract step size from counter
                    bcs       FollowRet branch if underflowed (past time)
                    sta       <$29,u    store updated counter
                    bra       FollowRet
FollowSetDir        lda       ,s        load computed direction from stack
                    sta       <$21,u    store as follower's movement direction
FollowRet           leas      $05,s     release local stack frame
                    rts
