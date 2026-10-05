* CoCo identifies self by record ID after activity/ignore checks.
COLLISION_SELF_FIRST equ 0
COLLISION_SELF_SKIP macro
                    ld\2      $02,\1
                    cmp\2     $02,u
                    beq       \3
                    endm
