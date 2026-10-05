* Native F9/FA handlers. CoCo pen geometry and texture sequence retained.
* Command X is private; tables are immutable PCR-relative data.
ReadPenStatus       lbsr      ReadNext
                    cmpa      #cmd_start
                    lbhs      DecodeInvalid
                    sta       <PenStatus
                    lbsr      ReadNext
                    rts
PlotWithPen         lda       <PenStatus
                    bita      #$20
                    beq       PenSolidPosition
                    lbsr      ReadNext
                    cmpa      #cmd_start
                    bhs       PenCommandRet
                    sta       <ScratchA6
                    lbsr      ReadInitialPos
                    bra       PenPositionReady
PenSolidPosition    lbsr      ReadXyPos
PenPositionReady    bcs       PenCommandRet
                    std       <ScratchA2
                    pshs      x
                    lbsr      PlotWithPen2
                    puls      x
                    bra       PlotWithPen
PenCommandRet       rts

                    use       shared/picture-pen.asm
                    use       shared/picture-pen-tables.asm
