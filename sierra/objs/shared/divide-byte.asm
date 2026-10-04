* A=nonzero divisor, B=dividend; returns A=remainder, B=quotient.
Div8                sta       <DivideDivisor    ; save divisor
                    lda       #$08      ; 8 bits to shift
                    sta       <DivideBits    ; save bit counter
                    clra                ; A = 0 (accumulator for quotient)
Div8Loop            lslb                ; shift dividend left
                    rola                ; rotate carry into accumulator
                    cmpa      <DivideDivisor    ; accumulator >= divisor?
                    bcs       Div8Next  ; branch if not
                    suba      <DivideDivisor    ; subtract divisor
                    incb                ; set quotient bit
Div8Next            dec       <DivideBits    ; decrement bit counter
                    bne       Div8Loop  ; loop for all 8 bits
                    rts
