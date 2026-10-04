* CoCo platform boundary: timer-intercept.
* Included in place; see ../../PORTABILITY.md.

SigIntercept        cmpb      #$80      b gets the signal code if not $80 ignore
                    bne       SigInterceptRet $80 is user defined
                    tfr       u,d       copy U (data area ptr) into D
                    tfr       a,dp      set direct page register to data area base
                    dec       <IrqCountdown decrement IRQ countdown counter
                    bne       SigInterceptRet not yet time — return
                    bsr       SigHandlerCore call timer and game-clock handler
                    lda       #$03      reload countdown to 3 intervals
                    sta       <IrqCountdown reset IRQ countdown
SigInterceptRet     rti                 return from interrupt
