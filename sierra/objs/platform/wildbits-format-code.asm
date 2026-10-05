* Bounded formatter. Four 512-byte source frames and a 2048-byte output
* share the idle fill stack; recursion never retains a mapped message pointer.
                    use shared/nul-string-copy.asm
                    use platform/format-recursion-operands.asm
                    use shared/format-recursive-call.asm
NUL_FRAME_WRITE     macro
                    sta       ,y+
                    endm
GameFormatMessage   ldu       <resourcebase
                    clr       formatdepth,u
                    clr       parserreadlength,u
                    clr       parserreadlength+1,u
                    leay      fillstack+2048,u
                    sty       parserreadindex,u
                    clr       ,y
                    lbsr      FormatPart
                    lbcs      FormatReturn
                    leax      fillstack+2048,u
                    clrb
                    rts
FormatPart          lda       formatdepth,u
                    cmpa      #4
                    lbhs      FormatInvalid
                    ldb       #0
                    lsla
                    leay      fillstack,u
                    leay      d,y
                    pshs      y
                    NUL_STRING_COPY x,FormatCopy,1,NUL_FRAME_WRITE,NUL_COPY_NOOP,NUL_COPY_NOOP
                    puls      x
                    inc       formatdepth,u
FormatNext          equ *
                    use platform/format-scan-operands.asm
                    use shared/format-scan.asm
FormatDirective     lda       ,x+
                    cmpa      #'%
                    bne       FormatNumberStart
                    lbsr      FormatPut
                    lbcs      FormatPartError
                    bra       FormatNext
FormatNumberStart   sta       parsercharacter,u
                    clr       parserwordlength,u
                    clr       parserbestlength,u
FormatNumber        lbsr      ParseDecStr
                    lbcs      FormatPartError
FormatDispatch      lda       ,x
                    cmpa      #'|
                    beq       FormatUnsupported
                    tst       parserbestlength,u
                    lbeq      FormatPartInvalid
                    lda       parsercharacter,u
                    ldb       parserwordlength,u
                    use platform/format-directive-operands.asm
                    use shared/format-directives.asm
FormatUnsupported   ldb       #E$UnkSvc
                    orcc      #1
                    bra       FormatPartError
FormatDone          dec       formatdepth,u
                    clrb
FormatReturn        rts
FormatPartInvalid   ldb       #E$BMode
                    orcc      #1
FormatPartError     dec       formatdepth,u
                    rts
FormatInvalid       ldb       #E$BMode
                    orcc      #1
                    rts
FormatPut           pshs      d,y
                    ldd       parserreadlength,u
                    cmpd      #2047
                    bhs       FormatFull
                    addd      #1
                    std       parserreadlength,u
                    ldy       parserreadindex,u
                    lda       ,s
                    sta       ,y+
                    clr       ,y
                    sty       parserreadindex,u
                    andcc     #$FE
                    puls      d,y,pc
FormatFull          puls      d,y
                    ldb       #E$BMode
                    orcc      #1
                    rts
FormatWord          tstb
                    lbeq      FormatPartInvalid
                    cmpb      #20
                    lbhi      FormatPartInvalid
                    lda       parsercount,u
                    tst       vmvariables+9,u
                    beq       FormatWordBound
                    inca
FormatWordBound     pshs      a
                    cmpb      ,s+
                    lbhi      FormatPartInvalid
                    decb
                    leay      parseroffsets,u
                    leay      b,y
                    lda       ,y
                    ldb       20,y
                    leay      parserlastline,u
                    leay      a,y
FormatWordCopy      tstb
                    lbeq      FormatNext
                    lda       ,y+
                    lbsr      FormatPut
                    lbcs      FormatPartError
                    decb
                    bra       FormatWordCopy
FormatString        equ *
                    use platform/format-string-operands.asm
                    use shared/format-string-slot.asm
                    NUL_STRING_COPY y,FormatStringCopy,0,FORMAT_STRING_WRITE,FORMAT_STRING_DONE,FORMAT_STRING_ERROR
FormatMessage       pshs      x
                    lbsr      ReadLogicMessage
                    bcs       FormatMessageReturn
FormatMessageReturn equ FormatExpansionReturn
                    use shared/format-expansion.asm
FormatVariable      leay      vmvariables,u
                    clra
                    ldb       d,y
* Keep the source cursor/context and four numeric bytes on the caller stack.
* No copied message, source frame, or persistent argument buffer is reused.
                    pshs      u,x
                    leas      -4,s
                    leax      3,s
                    lbsr      UIntToDecStr
                    tfr       x,y
                    ldx       4,s
                    ldu       6,s
                    NUL_STRING_COPY y,FormatVariableCopy,0,FORMAT_STRING_WRITE,FORMAT_NUMBER_DONE,FORMAT_NUMBER_ERROR
FormatVariableDone  leas      8,s
                    lbra      FormatNext
FormatVariableError leas      8,s
                    lbra      FormatPartError

                    use       platform/decimal-output-operands.asm
                    use       shared/unsigned-decimal.asm
* Bind the common quotient/remainder ABI to the existing 8-bit divider.
* D <= 255, U=10; return U=quotient and D=remainder, preserving X/Y.
FormatByteDivide10  lda       #10
                    lbsr      Div8
                    pshs      a
                    clra
                    tfr       d,u
                    puls      b
                    rts

                    use       platform/decimal-index-operands.asm
                    use       shared/decimal-index.asm
DecimalIndexOverflow ldb     #E$BMode
                    orcc      #1
                    rts
