* CoCo identifies self by record ID after activity/ignore checks.
COLLISION_SELF_FIRST equ 0
COLLISION_SELF_SKIP macro
                    ld\2      $02,\1
                    cmp\2     $02,u
                    beq       \3
                    endm

COLLISION_WIDE      equ 0
COLLISION_RESULT_B  equ 0
COLLISION_SCAN_ACTOR macro
                    clra
                    COLLISION_IGNORE u,b,CollisionScanEmpty
                    endm
COLLISION_SCAN_INIT macro
                    ldx       <$0030
                    endm
COLLISION_SCAN_END  macro
                    cmpx      <$0032
                    bcc       CollisionScanEmpty
                    endm
COLLISION_SCAN_FILTER macro
                    COLLISION_CANDIDATE x,b,CollisionScanAdvance
                    endm
COLLISION_SCAN_OVERLAPS macro
                    COLLISION_HORIZONTAL u,x,1
                    COLLISION_HORIZONTAL x,u,0
                    endm
COLLISION_SCAN_BASELINE macro
                    COLLISION_BASELINE x,0
                    endm
COLLISION_SCAN_NEXT macro
                    leax      <$2B,x
                    bra       CollisionScanLoop
                    endm
