* AGI LZW, adapted from mnln.asm PicRenderSetup. No file, hardware or
* destination-address assumptions. Input bits are least significant first.
*
* DecodeLzw: X = private 8192-byte workspace, Y = exact expanded length,
* U = private data base, DP = its high byte. Returns C clear on success;
* C set/B = error otherwise. U and DP retained; D/X/Y may change.
* Callbacks LzwReadByte and LzwWriteByte take/return B, carry/error in B,
* and preserve X/Y/U/DP. The writer must not retain mapped pointers.
* Dictionary width grows from 9 to 11 bits; clear=256, end=257.
DecodeLzw           stu       <lzwbase
                    stx       <lzwwork
                    sty       <lzwexpected
                    clr       <lzwerror
                    clr       <lzwbits
                    clr       <lzwproduced
                    clr       <lzwproduced+1
                    cmpy      #0
                    lbeq      LzwInvalid
                    lbsr      LzwReset
LzwLoop             lbsr      LzwReadCode
                    lbcs      LzwReturn
                    cmpd      #256
                    beq       LzwClear
                    cmpd      #257
                    lbeq      LzwEnd
                    std       <lzwcurrent
                    tst       <lzwhasprevious
                    bne       LzwString
                    cmpd      #256
                    lbhs      LzwInvalid
                    stb       <lzwfirst
                    lbsr      LzwEmit
                    lbcs      LzwReturn
                    lbra      LzwRemember
LzwClear            lbsr      LzwReset
                    bra       LzwLoop
LzwString           clr       <lzwtop
                    clr       <lzwtop+1
                    cmpd      <lzwnext
                    lbhi      LzwInvalid
                    bne       LzwWalk
                    ldb       <lzwpreviousfirst
                    lbsr      LzwPush
                    lbcs      LzwReturn
                    ldd       <lzwprevious
LzwWalk             cmpd      #256
                    blo       LzwLiteral
                    cmpd      #258
                    lblo      LzwInvalid
                    cmpd      <lzwnext
                    lbhs      LzwInvalid
                    std       <lzwchain
                    addd      <lzwchain
                    addd      <lzwchain
                    ldx       <lzwwork
                    leax      d,x
                    ldb       2,x
                    lbsr      LzwPush
                    lbcs      LzwReturn
                    ldd       ,x
                    bra       LzwWalk
LzwLiteral          stb       <lzwfirst
                    lbsr      LzwPush
                    lbcs      LzwReturn
LzwPop              ldd       <lzwtop
                    subd      #1
                    std       <lzwtop
                    ldx       <lzwwork
                    leax      6144,x
                    ldb       d,x
                    lbsr      LzwEmit
                    lbcs      LzwReturn
                    ldd       <lzwtop
                    bne       LzwPop
                    ldd       <lzwnext
                    cmpd      #2048
                    bhs       LzwRemember
                    std       <lzwchain
                    addd      <lzwchain
                    addd      <lzwchain
                    ldx       <lzwwork
                    leax      d,x
                    ldd       <lzwprevious
                    std       ,x
                    ldb       <lzwfirst
                    stb       2,x
                    ldd       <lzwnext
                    addd      #1
                    std       <lzwnext
                    cmpd      <lzwthreshold
                    blo       LzwRemember
                    lda       <lzwwidth
                    cmpa      #11
                    bhs       LzwRemember
                    inc       <lzwwidth
                    lsl       <lzwthreshold+1
                    rol       <lzwthreshold
LzwRemember         ldd       <lzwcurrent
                    std       <lzwprevious
                    ldb       <lzwfirst
                    stb       <lzwpreviousfirst
* The flag is Boolean; do not let long resources wrap it to zero.
                    lda       #1
                    sta       <lzwhasprevious
                    lbra      LzwLoop
LzwEnd              ldd       <lzwproduced
                    cmpd      <lzwexpected
                    bne       LzwInvalid
                    clrb
                    andcc     #$FE
LzwReturn           ldu       <lzwbase
                    rts
LzwReset            ldd       #258
                    std       <lzwnext
                    ldd       #512
                    std       <lzwthreshold
                    lda       #9
                    sta       <lzwwidth
                    clr       <lzwhasprevious
                    rts
LzwPush             pshs      x,b
                    ldd       <lzwtop
                    cmpd      #2048
                    bhs       LzwPushBad
                    ldx       <lzwwork
                    leax      6144,x
* Saved B precedes X on the 6809 stack.
                    ldd       <lzwtop
                    leax      d,x
                    ldb       ,s
                    stb       ,x
                    ldd       <lzwtop
                    addd      #1
                    std       <lzwtop
                    puls      b,x
                    andcc     #$FE
                    rts
LzwPushBad          puls      b,x
                    bra       LzwInvalid
LzwEmit             pshs      b
                    ldd       <lzwproduced
                    cmpd      <lzwexpected
                    bhs       LzwEmitBad
                    addd      #1
                    std       <lzwproduced
                    puls      b
                    lbsr      LzwWriteByte
                    rts
LzwEmitBad          puls      b
LzwInvalid          ldb       #E$BMode
                    stb       <lzwerror
                    orcc      #1
                    rts
LzwReadCode         clr       <lzwcode
                    clr       <lzwcode+1
                    ldd       #1
                    std       <lzwweight
                    lda       <lzwwidth
                    sta       <lzwcount
LzwReadBit          tst       <lzwbits
                    bne       LzwHaveBit
                    lbsr      LzwReadByte
                    bcs       LzwReadError
                    stb       <lzwbyte
                    lda       #8
                    sta       <lzwbits
LzwHaveBit          lsr       <lzwbyte
                    bcc       LzwZeroBit
                    ldd       <lzwcode
                    addd      <lzwweight
                    std       <lzwcode
LzwZeroBit          dec       <lzwbits
                    lsl       <lzwweight+1
                    rol       <lzwweight
                    dec       <lzwcount
                    bne       LzwReadBit
                    ldd       <lzwcode
                    andcc     #$FE
                    rts
LzwReadError        stb       <lzwerror
                    rts
