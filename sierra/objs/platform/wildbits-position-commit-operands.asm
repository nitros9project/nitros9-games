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
                    lbra      MotionBlocked
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
