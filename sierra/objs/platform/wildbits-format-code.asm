* Bounded formatter. Four 512-byte source frames and a 2048-byte output
* share the idle fill stack; recursion never retains a mapped message pointer.
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
FormatCopy          lda       ,x+
                    sta       ,y+
                    bne       FormatCopy
                    puls      x
                    inc       formatdepth,u
FormatNext          lda       ,x+
                    lbeq      FormatDone
                    cmpa      #'%
                    beq       FormatDirective
                    lbsr      FormatPut
                    lbcs      FormatPartError
                    bra       FormatNext
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
                    cmpa      #'w
                    lbeq      FormatWord
                    cmpa      #'v
                    lbeq      FormatVariable
                    cmpa      #'s
                    lbeq      FormatString
                    cmpa      #'m
                    lbeq      FormatMessage
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
FormatString        cmpb      #12
                    lbhs      FormatPartInvalid
                    lda       #40
                    mul
                    leay      vmstrings,u
                    leay      d,y
FormatStringCopy    lda       ,y+
                    lbeq      FormatNext
                    lbsr      FormatPut
                    lbcs      FormatPartError
                    bra       FormatStringCopy
FormatMessage       pshs      x
                    lbsr      ReadLogicMessage
                    bcs       FormatMessageReturn
                    ldu       <resourcebase
                    lbsr      FormatPart
FormatMessageReturn puls     x
                    lbcs      FormatPartError
                    lbra      FormatNext
FormatVariable      leay      vmvariables,u
                    clra
                    ldb       d,y
                    lda       #100
                    lbsr      Div8
                    sta       parserbestlength,u
                    stb       parserid,u
                    tstb
                    beq       FormatTens
                    tfr       b,a
                    adda      #'0
                    lbsr      FormatPut
                    lbcs      FormatPartError
FormatTens          ldb       parserbestlength,u
                    lda       #10
                    lbsr      Div8
                    sta       parserbestlength,u
                    tstb
                    bne       FormatTensPut
                    tst       parserid,u
                    beq       FormatOnes
FormatTensPut       tfr       b,a
                    adda      #'0
                    lbsr      FormatPut
                    lbcs      FormatPartError
FormatOnes          lda       parserbestlength,u
                    adda      #'0
                    lbsr      FormatPut
                    lbcs      FormatPartError
                    lbra      FormatNext

                    use       platform/decimal-index-operands.asm
                    use       shared/decimal-index.asm
DecimalIndexOverflow ldb     #E$BMode
                    orcc      #1
                    rts
