* Definitions may be reused without emitting another decimal converter.
                    ifndef SHARED_WORD_CONVERSION
SHARED_WORD_CONVERSION equ 1
WORD_EMIT_HEX_DIVIDE macro
UIntToHexStr        WORD_HEX_OUTPUT_END
                    clr       ,x        null-terminate the buffer
UIntToHexLoop       ldu       #$0010    divide by 16 for hex conversion
                    bsr       UIntDivide divide D by 16 for hex digit
                    addb      #$30      convert remainder to ASCII
                    cmpb      #$39      check if digit is 0-9
                    ble       UIntToHexStore branch if in '0'-'9' range
                    addb      #$07      adjust for 'A'-'F' range
UIntToHexStore      stb       ,-x       store hex digit left of current position
                    tfr       u,d       transfer quotient to D
                    cmpd      #$0000    check if quotient is zero
                    bhi       UIntToHexLoop loop if more digits to convert
                    rts
UIntDivide          leas      -$05,s    allocate 5-byte local frame on stack
                    std       ,s        save dividend (D)
                    stu       $02,s     save divisor (U)
                    lda       #$10      16 iterations for 16-bit divide
                    sta       $04,s     save iteration count
                    ldd       #$0000    clear quotient accumulator
UIntDivideLoop      lsl       $01,s     shift dividend left (LSB of dividend)
                    rol       ,s        shift dividend MSB with carry
                    rolb                roll bit into quotient LSB
                    rola                roll quotient MSB
                    cmpd      $02,s     compare partial remainder to divisor
                    bcs       UIntDivideShift branch if remainder < divisor (no subtract)
                    subd      $02,s     subtract divisor from partial remainder
                    inc       $01,s     set quotient bit (LSB of dividend was 1)
UIntDivideShift     dec       $04,s     decrement iteration count
                    bne       UIntDivideLoop loop for all 16 bits
                    ldu       ,s        load final quotient into U
                    leas      $05,s     release local stack frame
                    rts
                    endm
                    endc
                    ifndef SHARED_DECIMAL_EMIT
SHARED_DECIMAL_EMIT equ 1
UNSIGNED_DECIMAL_EMIT macro
\1                  \3
                    clr       ,x
\2                  ldu       #$000A
                    \4
                    addb      #$30
                    stb       ,-x
                    tfr       u,d
                    cmpd      #$0000
                    bhi       \2
                    rts
                    endm
                    endc
                    ifndef WORD_CONVERSION_DEFINITIONS_ONLY
* Unsigned decimal conversion; input D in the owner's supported domain.
* DECIMAL_OUTPUT_END supplies X=last buffer byte; caller owns enough space
* for the number plus NUL. DECIMAL_OUTPUT_DIVIDE takes D/U and returns
* quotient U and remainder D, preserving X/Y. Return X=first digit, D/U=0.
                    UNSIGNED_DECIMAL_EMIT UIntToDecStr,UIntToDecLoop,DECIMAL_OUTPUT_END,DECIMAL_OUTPUT_DIVIDE
                    endc
