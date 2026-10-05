* Native context X owns motionobject; skip that pointer before flag reads.
COLLISION_SELF_FIRST equ 1
COLLISION_SELF_SKIP macro
                    cmp\1     motionobject,x
                    beq       \3
                    endm

COLLISION_WIDE      equ 1
COLLISION_RESULT_B  equ 1
COLLISION_SCAN_ACTOR macro
                    COLLISION_IGNORE u,a,CollisionScanEmpty
                    endm
COLLISION_SCAN_INIT macro
                    clr       motioncollision,x
                    leay      vmobjects,x
                    endm
COLLISION_SCAN_END  macro
                    endm
COLLISION_SCAN_FILTER macro
                    COLLISION_CANDIDATE y,a,CollisionScanAdvance
                    endm
COLLISION_SCAN_OVERLAPS macro
                    COLLISION_HORIZONTAL u,y,1
                    COLLISION_HORIZONTAL y,u,0
                    endm
COLLISION_HISTORY_READ macro
                    lda       motionoldposition+1,x
                    endm
COLLISION_SCAN_BASELINE macro
                    COLLISION_BASELINE y,1
                    endm
COLLISION_SCAN_NEXT macro
                    leay      43,y
                    inc       motioncollision,x
                    lda       motioncollision,x
                    cmpa      #64
                    blo       CollisionScanLoop
                    endm
