* A=target byte; X=NUL-terminated byte set. Returns X=match or zero, Z=not found.
* Preserves A, B, Y and U.
FindByte            tst       ,x        check for null terminator at current position
                    bne       FindByteLoop branch if not null (search continues)
                    ldx       #$0000    null found, return null pointer (not found)
                    bra       FindByteRet
FindByteLoop        cmpa      ,x+       compare search byte to current, advance X
                    bne       FindByte  branch if not matching (retry from top)
                    leax      -$01,x    back up to point at the matching byte
FindByteRet         rts
