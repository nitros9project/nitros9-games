* Collision eligibility on common records. Register selection preserves the
* owner's result accumulator; self identity/order is an owner interface.
* Ignore parameters: record pointer, value register, skip target.
COLLISION_IGNORE    macro
                    ld\2      <$25,\1
                    bit\2     #2
                    bne       \3
                    endm
* Candidate parameters: pointer, value register, skip target.
COLLISION_CANDIDATE macro
                    ifne      COLLISION_SELF_FIRST
                    COLLISION_SELF_SKIP \1,\2,\3
                    endc
                    ld\2      <$26,\1
                    and\2     #$41
                    cmp\2     #$41
                    bne       \3
                    COLLISION_IGNORE \1,\2,\3
                    ifeq      COLLISION_SELF_FIRST
                    COLLISION_SELF_SKIP \1,\2,\3
                    endc
                    endm
