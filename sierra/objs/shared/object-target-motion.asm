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
