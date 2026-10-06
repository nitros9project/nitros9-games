                    ifne WILDBITS
                    use platform/wildbits-motion-operands.asm
                    else
                    use platform/coco-motion-operands.asm
                    endc

* Eligibility/countdown and continuation policy for the shared scheduler.
SCHEDULE_SKIP_INACTIVE macro
                    ifne WILDBITS
                    lbne      MotionNextObject
                    else
                    bne       NextMotionObj
                    endc
                    endm
SCHEDULE_STEP_READY macro
                    ifne WILDBITS
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
                    else
                    lda       1,u
                    cmpa      #1
                    bne       NextMotionObj
                    endc
                    endm
SCHEDULE_FOLLOW_CONTEXT macro
                    ifne WILDBITS
                    ldx       <resourcebase
                    ldu       motionobject,x
                    endc
                    endm
SCHEDULE_UNKNOWN macro
                    ifne WILDBITS
                    lbne      MotionUnsupported
                    else
                    bhi       MotionScheduleReady
                    endc
                    endm
SCHEDULE_TARGET_DIRECTION macro
                    ifne WILDBITS
                    lbsr      MotionMoveDirection
                    else
                    lbsr      SetObjMotion
                    endc
                    endm
