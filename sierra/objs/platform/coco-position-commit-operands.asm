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
