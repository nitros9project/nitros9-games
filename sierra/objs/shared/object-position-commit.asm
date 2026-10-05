* Candidate-position transaction and boundary publication.
* Owners bind coordinates, collision ABI, terrain lifecycle, rejected recovery
* and the next movement stage. No new storage or runtime dispatch is introduced.
PositionCommit      POSITION_STORE_CANDIDATE
                    POSITION_TEST_COLLISION
                    POSITION_COLLISION_RESULT
                    ifne POSITION_TERRAIN_PRECHECKED
                    beq       PositionAccepted
                    else
                    bne       PositionRejected
                    POSITION_VALIDATE_TERRAIN
                    bne       PositionAccepted
                    endc
PositionRejected    POSITION_RESTORE_OLD
                    POSITION_RECOVER
PositionAccepted    POSITION_ACCEPT_STATE
                    POSITION_BOUNDARY_READ
                    POSITION_BOUNDARY_EMPTY
                    POSITION_OBJECT_ID
                    bne       PositionOtherBoundary
                    POSITION_EGO_BOUNDARY
                    POSITION_BOUNDARY_CONTINUE
PositionOtherBoundary POSITION_OTHER_BOUNDARY
PositionCommitDone  equ *
