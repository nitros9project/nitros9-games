* Y=rectangle x1,y1,x2,y2; DP PositionLeftY=left X,Y, PositionRight=right X.
* Inclusive boundaries. Owner supplies RetTrue/RetFalse returning A=1/0.
TestPosnX           ldd       <PositionLeftY    load left/right X edge values
                    cmpa      ,y+       compare left edge to rect left boundary
                    bcc       TestPosnY branch if left edge >= rect left (inside or right)
                    leay      $03,y     skip remaining 3 boundary bytes
                    bra       RetFalse  object is left of rect
TestPosnY           cmpb      ,y+       compare Y to rect top boundary
                    bcc       TestPosnXRight branch if Y >= rect top (inside or below)
                    leay      $02,y     skip remaining 2 boundary bytes
                    bra       RetFalse  object is above rect
TestPosnXRight      lda       <PositionRight    load right X edge value
                    cmpa      ,y+       compare right edge to rect right boundary
                    bls       TestPosnYBot branch if right edge <= rect right (inside or left)
                    leay      $01,y     skip remaining 1 boundary byte
                    bra       RetFalse  object is right of rect
TestPosnYBot        cmpb      ,y+       compare Y to rect bottom boundary
                    bls       RetTrue   branch if Y <= rect bottom (inside)
                    bra       RetFalse  object is below rect
