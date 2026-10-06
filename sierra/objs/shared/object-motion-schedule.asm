* Per-object eligibility, owner step schedule, and complete motion dispatch.
* Cursor U remains on the selected object. Owners supply iteration/error
* continuations and context restoration; no runtime platform dispatch exists.
MotionSchedule      lda       <$26,u
                    anda      #$51
                    cmpa      #$51
                    SCHEDULE_SKIP_INACTIVE
                    SCHEDULE_STEP_READY
                    lda       <$22,u
                    beq       MotionScheduleReady
                    cmpa      #1
                    bne       MotionScheduleNotWander
                    lbsr      ObjAnimStep
                    bra       MotionScheduleReady
MotionScheduleNotWander cmpa #2
                    bne       MotionScheduleNotFollow
                    lbsr      CalcFollowDir
                    SCHEDULE_FOLLOW_CONTEXT
                    bra       MotionScheduleReady
MotionScheduleNotFollow cmpa #3
                    SCHEDULE_UNKNOWN
                    SCHEDULE_TARGET_DIRECTION
MotionScheduleReady equ *
