* U=object; InitRandSeed returns a random byte in B; Div8 returns remainder A.
* Native X=private base. Coordinate stepping is separate from direction choice.
ObjAnimStep         lda       <$27,u    ; cel animation delay counter
                    beq       AnimStepRoll ; zero = time to advance cel
                    dec       <$27,u    ; decrement delay
                    lda       <$25,u    ; object flags
                    bita      #$40      ; random animation flag set?
                    beq       AnimStepRet ; skip random if not set
AnimStepRoll        lbsr      InitRandSeed ; seed/advance random generator
                    lda       #$09      ; range: 0-8 (9 possible values)
                    lbsr      Div8      ; random modulo: B = random % 9
                    sta       <$21,u    ; store random direction in object
                    ifne      WANDER_PRIVATE_STATE
                    tst       2,u
                    else
                    cmpu      <$0030    ; is this the ego object?
                    endc
                    bne       AnimStepCheckDelay ; branch if not ego
                    ifne      WANDER_PRIVATE_STATE
                    sta       vmvariables+6,x
                    else
                    sta       >$0437    ; set ego direction variable
                    endc
AnimStepCheckDelay  lda       <$27,u    ; reload delay counter
AnimStepDelayLoop   cmpa      #$06      ; delay >= 6?
                    bcc       AnimStepRet ; return if delay is already high
                    lbsr      InitRandSeed ; advance random state
                    lda       #$33      ; range: 0-50 (51 values)
                    lbsr      Div8      ; random modulo
                    sta       <$27,u    ; store new random delay
                    bra       AnimStepDelayLoop ; check if high enough
AnimStepRet         rts
