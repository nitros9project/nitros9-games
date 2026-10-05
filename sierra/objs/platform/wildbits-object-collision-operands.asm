* Native context X owns motionobject; skip that pointer before flag reads.
COLLISION_SELF_FIRST equ 1
COLLISION_SELF_SKIP macro
                    cmp\1     motionobject,x
                    beq       \3
                    endm
