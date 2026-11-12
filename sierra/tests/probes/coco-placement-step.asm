* Frozen original CoCo placement step from e6cef9d; CPU differential fixture.
* Not included by either production owner. Stop at FindObjPosIter before RTS.
FindObjPosIter      rts
FindObjPosDirNone   lda       $03,s     load current search direction
                    bne       FindObjPosDirOne branch if trying non-zero direction
                    dec       $03,u     shift object up by 1 (try above)
                    dec       $04,s     decrement remaining step count
                    bne       FindObjPosIter branch if more steps in this direction
                    inc       $03,s     advance to next direction
                    lda       $02,s     load step size
                    sta       $04,s     reset step counter
                    bra       FindObjPosIter try next position
FindObjPosDirOne    cmpa      #$01      check if direction 1 (down)
                    bne       FindObjPosDirTwo branch if not direction 1
                    inc       $04,u     shift object down by 1
                    dec       $04,s     decrement remaining step count
                    bne       FindObjPosIter branch if more steps in this direction
                    inc       $03,s     advance to next direction
                    inc       $02,s     increase step size
                    lda       $02,s     load new step size
                    sta       $04,s     reset step counter
                    bra       FindObjPosIter try next position
FindObjPosDirTwo    cmpa      #$02      check if direction 2 (right)
                    bne       FindObjPosDirThree branch if not direction 2
                    inc       $03,u     shift object right by 1
                    dec       $04,s     decrement remaining step count
                    bne       FindObjPosIter branch if more steps in this direction
                    inc       $03,s     advance to next direction
                    lda       $02,s     load step size
                    sta       $04,s     reset step counter
                    bra       FindObjPosIter try next position
FindObjPosDirThree  dec       $04,u     shift object left by 1
                    dec       $04,s     decrement remaining step count
                    bne       FindObjPosIter branch if more steps in this direction
                    clr       $03,s     reset direction to 0
                    inc       $02,s     increase step size for next spiral ring
                    lda       $02,s     load new step size
                    sta       $04,s     reset step counter
                    bra       FindObjPosIter try next position
FindObjPosDone      rts
