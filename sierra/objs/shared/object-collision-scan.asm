* Complete collision traversal with shared filtering and overlap calculation.
* Actor is U. Owners bind table iteration, candidate register and return ABI.
* Horizontal arithmetic and baseline history retain explicit legacy policies.
* Horizontal parameter 3 preserves the first native comparison's high byte;
* the second comparison explicitly clears it, matching the previous code.
COLLISION_HORIZONTAL macro
                    ifne COLLISION_WIDE
                    clra
                    endc
                    ldb       3,\1
                    ifne COLLISION_WIDE
                    addb      $1C,\1
                    adca      #0
                    pshs      d
                    ldb       3,\2
                    ifeq \3
                    clra
                    endc
                    cmpd      ,s++
                    bhs       CollisionScanAdvance
                    else
                    addb      <$1C,\1
                    cmpb      3,\2
                    bcs       CollisionScanAdvance
                    endc
                    endm
COLLISION_BASELINE macro
                    ifne \2
                    lda       4,u
                    cmpa      4,\1
                    beq       CollisionScanHit
                    COLLISION_HISTORY_READ
                    cmpa      4,\1
                    blo       CollisionCrossDown
                    lda       4,u
                    cmpa      4,\1
                    blo       CollisionScanHit
                    bra       CollisionScanAdvance
CollisionCrossDown  lda       4,u
                    cmpa      4,\1
                    bhi       CollisionScanHit
                    else
                    ldb       4,\1
                    cmpb      4,u
                    beq       CollisionScanHit
                    bhi       CollisionPreviousHigher
                    ldb       <$1B,\1
                    cmpb      <$1B,u
                    bhi       CollisionScanHit
                    bra       CollisionScanAdvance
CollisionPreviousHigher ldb  <$1B,\1
                    cmpb      <$1B,u
                    bcs       CollisionScanHit
                    endc
                    endm
CollisionScan       COLLISION_SCAN_ACTOR
                    COLLISION_SCAN_INIT
CollisionScanLoop   COLLISION_SCAN_END
                    COLLISION_SCAN_FILTER
                    COLLISION_SCAN_OVERLAPS
                    COLLISION_SCAN_BASELINE
CollisionScanAdvance COLLISION_SCAN_NEXT
                    ifne COLLISION_RESULT_B
CollisionScanEmpty  clrb
                    rts
CollisionScanHit    ldb       #1
                    rts
                    else
CollisionScanHit    lda       #1
CollisionScanEmpty  rts
                    endc
