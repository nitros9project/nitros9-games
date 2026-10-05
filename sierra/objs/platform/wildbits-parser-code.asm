* Streaming original words.tok; no slab is held across file or terminal I/O.
* Private line/IDs survive assetinput being reused by subsequent logic loads.
ParserInitialize    ldu       <resourcebase
                    clr       parserlength,u
                    clr       parserline,u
                    clr       parsercount,u
                    clr       dialogactive,u
                    clr       dialogwordstart,u
                    clr       dialoginputmode,u
                    rts
ParserCommand       ldu       <resourcebase
                    lda       vmarguments,u
                    cmpa      #12
                    lbhs      ParserInvalid
                    ldb       #40
                    mul
                    leax      vmstrings,u
                    leax      d,x
                    leay      parserline,u
                    clr       parserlength,u
ParserCopy          lda       ,x+
                    beq       ParserCopyDone
                    lbsr      ParserLower
                    sta       ,y+
                    inc       parserlength,u
                    ldb       parserlength,u
                    cmpb      #39
                    blo       ParserCopy
ParserCopyDone      clr       ,y
                    lbra      ParserParse
ParserLower         equ       LowercaseByte
ParserLowerDone     equ       LowercaseReturn
                    use       shared/ascii-lower.asm
ParserParse         lbsr      ParserNormalize
                    lbsr      AssetUnmap
                    lbcs      ParserReturn
                    lbsr      PictureUnmap
                    lbcs      ParserReturn
                    ldu       <resourcebase
                    leax      parserline,u
                    leay      parserlastline,u
                    ldb       #40
ParserSaveLine      lda       ,x+
                    sta       ,y+
                    decb
                    bne       ParserSaveLine
                    clr       parsercount,u
                    clr       parserposition,u
                    clr       vmflags+2,u
                    clr       vmflags+4,u
                    clr       vmvariables+9,u
                    ldy       <resourcenameend
                    leax      ParserFilename,pcr
                    lbsr      ResourceSuffix
                    lbsr      OpenPicturePath
                    lbcs      ResourceFailed
* Validate complete 26-letter index, then scan entries from offset 52.
                    ldu       <resourcebase
                    leax      assetinput,u
                    ldy       #52
                    lbsr      ResourceReadExact
                    lbcs      ResourceFailed
                    ldu       <resourcebase
                    leax      assetinput,u
                    ldy       #26
                    ldd       #$FFFF
                    std       parserstart,u
ParserIndex         ldd       ,x++
                    beq       ParserIndexNext
                    cmpd      #52
                    lblo      ParserMalformed
                    cmpd      parserstart,u
                    bhs       ParserIndexNext
                    std       parserstart,u
ParserIndexNext     leay      -1,y
                    bne       ParserIndex
                    ldd       parserstart,u
                    cmpd      #$FFFF
                    bne       ParserNextInput
                    ldd       #52
                    std       parserstart,u
ParserNextInput     ldu       <resourcebase
                    leax      parserline,u
                    ldb       parserposition,u
                    lda       b,x
                    lbeq      ParserComplete
                    cmpa      #32
                    bne       ParserSearch
                    inc       parserposition,u
                    bra       ParserNextInput
ParserSearch        clr       parserbestlength,u
                    clr       parserwordlength,u
                    clr       parserreadindex,u
                    clr       parserreadindex+1,u
                    clr       parserreadlength,u
                    clr       parserreadlength+1,u
                    lda       <resourcepath
                    ldx       #0
                    ldu       parserstart,u
                    os9       I$Seek
                    lbcs      ResourceFailed
ParserEntry         lbsr      ParserByte
                    bcc       ParserPrefix
                    cmpb      #E$EOF
                    lbne      ResourceFailed
                    lbra      ParserSearchDone
ParserPrefix        cmpb      parserwordlength,u
                    lbhi      ParserMalformed
                    stb       parserwordlength,u
ParserSuffix        lbsr      ParserByte
                    bcc       ParserSuffixByte
                    cmpb      #E$EOF
                    lbne      ResourceFailed
                    tst       parserwordlength,u
                    lbeq      ParserSearchDone
                    lbra      ParserMalformed
ParserSuffixByte
                    stb       parsercharacter,u
                    andb      #$7F
                    eorb      #$7F
                    cmpb      #32
                    lblo      ParserMalformed
                    lda       parserwordlength,u
                    cmpa      #39
                    lbhs      ParserMalformed
                    leax      parserword,u
                    stb       a,x
                    inc       parserwordlength,u
                    tst       parsercharacter,u
                    bpl       ParserSuffix
                    lbsr      ParserByte
                    lbcs      ParserTruncated
                    stb       parserid,u
                    lbsr      ParserByte
                    lbcs      ParserTruncated
                    stb       parserid+1,u
* Compare dictionary phrases at a word boundary; prefer the longest match.
                    leax      parserword,u
                    leay      parserline,u
                    ldb       parserposition,u
                    leay      b,y
                    ldb       parserwordlength,u
ParserCompare       lda       ,x+
                    cmpa      ,y+
                    lbne      ParserEntry
                    decb
                    bne       ParserCompare
                    lda       ,y
                    beq       ParserCandidate
                    cmpa      #32
                    lbne      ParserEntry
ParserCandidate     lda       parserwordlength,u
                    cmpa      parserbestlength,u
                    lbls      ParserEntry
                    sta       parserbestlength,u
                    ldd       parserid,u
                    std       parserbestid,u
                    lbra      ParserEntry
ParserSearchDone    lda       parserbestlength,u
                    beq       ParserUnknown
                    adda      parserposition,u
                    sta       parserposition,u
                    ldd       parserbestid,u
                    lbeq      ParserNextInput
                    ldb       parsercount,u
                    cmpb      #20
                    bhs       ParserMalformed
                    leay      parseroffsets,u
                    lda       parserposition,u
                    suba      parserbestlength,u
                    sta       b,y
                    lda       parserbestlength,u
                    leay      b,y
                    sta       20,y
                    lslb
                    leax      parserids,u
                    leax      b,x
                    ldd       parserbestid,u
                    std       ,x
                    inc       parsercount,u
                    lbra      ParserNextInput
ParserUnknown       ldb       parsercount,u
                    cmpb      #20
                    lbhs      ParserMalformed
                    leay      parseroffsets,u
                    leay      b,y
                    lda       parserposition,u
                    sta       ,y
                    leax      parserlastline,u
                    leax      a,x
                    clrb
ParserUnknownLength lda      ,x+
                    beq       ParserUnknownEnd
                    cmpa      #32
                    beq       ParserUnknownEnd
                    incb
                    bra       ParserUnknownLength
ParserUnknownEnd    stb       20,y
                    lda       parsercount,u
                    inca
                    sta       vmvariables+9,u
ParserComplete      lda       parserlength,u
                    beq       ParserClose
                    lda       #1
                    sta       vmflags+2,u
ParserClose         lbra      ResourceClose
ParserTruncated     cmpb      #E$EOF
                    lbne      ResourceFailed
ParserMalformed     ldb       #E$BMode
                    lbra      ResourceFailed
ParserInvalid       ldb       #E$IllArg
                    orcc      #1
ParserReturn        rts
ParserFilename      fcc       /words.tok/
                    fcb       C$CR
* Buffered partial reads, with EOF accepted only between complete entries.
ParserByte          ldu       <resourcebase
                    ldd       parserreadindex,u
                    cmpd      parserreadlength,u
                    blo       ParserBuffered
                    lda       <resourcepath
                    leax      assetinput,u
                    ldy       #512
                    os9       I$Read
                    bcs       ParserReturn
                    ldu       <resourcebase
                    cmpy      #0
                    beq       ParserReadInvalid
                    cmpy      #512
                    bhi       ParserReadInvalid
                    sty       parserreadlength,u
                    ldd       #0
                    std       parserreadindex,u
ParserBuffered      leax      assetinput,u
                    leax      d,x
                    ldb       ,x
                    pshs      b
                    ldd       parserreadindex,u
                    addd      #1
                    std       parserreadindex,u
                    puls      b
                    andcc     #$FE
                    rts
ParserReadInvalid   ldb       #E$BMode
                    orcc      #1
                    rts
* said words are little endian in bytecode; dictionary IDs are big endian.
ParserSaid          ldu       <resourcebase
                    tst       vmflags+2,u
                    beq       ParserFalse
                    tst       vmflags+4,u
                    bne       ParserFalse
                    leax      parserids,u
                    leay      vmarguments,u
                    lda       parsercount,u
                    sta       <vmright
                    lda       <vmargcount
                    lsra
                    sta       <vmleft
SaidExpected        equ       vmleft
SaidParsed          equ       vmright
                    use       shared/said-match.asm
SaidCheckDone       ldd       <SaidExpected
                    bne       SaidNoMatch
SaidSetMatch        lda       #1
                    sta       vmflags+4,u
                    ldb       #1
                    andcc     #$FE
                    rts
SaidNoMatch         lsla
                    leay      a,y
ParserFalse         clrb
                    rts
* Unbound printable keys feed the input line; controllers retain precedence.
ParserKey           ldu       <resourcebase
                    tst       <vminputenabled
                    lbeq      GameCycleSuccess
                    lda       <vmkeybyte
                    cmpa      #13
                    beq       ParserSubmit
                    cmpa      #8
                    beq       ParserBackspace
                    cmpa      #32
                    lblo      GameCycleSuccess
                    cmpa      #126
                    lbhi      GameCycleSuccess
                    ldb       parserlength,u
                    cmpb      #38
                    lbhs      GameCycleSuccess
                    cmpb      vmvariables+24,u
                    lbhs      GameCycleSuccess
                    lbsr      ParserLower
                    leax      parserline,u
                    sta       b,x
                    incb
                    clr       b,x
                    stb       parserlength,u
                    lbra      GameCycleSuccess
ParserBackspace     ldb       parserlength,u
                    lbeq      GameCycleSuccess
                    decb
                    stb       parserlength,u
                    leax      parserline,u
                    clr       b,x
                    lbra      GameCycleSuccess
ParserSubmit        lbsr      ParserParse
                    lbcs      ParserReturn
                    ldu       <resourcebase
                    clr       parserlength,u
                    clr       parserline,u
                    clrb
                    rts
* Rebuild the input row before ordinary presentation, never in modal screens.
ParserDrawInput     ldu       <resourcebase
                    tst       <vminputenabled
                    lbeq      GameCycleSuccess
                    tst       vmstrings,u
                    bne       ParserInputVisible
                    tst       parserlength,u
                    lbeq      GameCycleSuccess
ParserInputVisible  lda       <vminputrow
                    ldb       #40
                    mul
                    leax      textcharacters,u
                    leax      d,x
                    pshs      x
                    ldb       #40
ParserBlankInput    lda       #32
                    sta       ,x
                    lda       <vmtextforeground
                    lsla
                    lsla
                    lsla
                    lsla
                    ora       <vmtextbackground
                    sta       1000,x
                    leax      1,x
                    decb
                    bne       ParserBlankInput
                    puls      x
                    leay      vmstrings,u     string zero is the AGI prompt
                    ldb       #40
ParserPrompt        lda       ,y+
                    beq       ParserInputText
                    sta       ,x+
                    decb
                    bne       ParserPrompt
                    lbra      GameCycleSuccess
ParserInputText     leay      parserline,u
ParserInputCopy     lda       ,y+
                    beq       ParserCursor
                    sta       ,x+
                    decb
                    bne       ParserInputCopy
                    lbra      GameCycleSuccess
ParserCursor        lda       <vmcursor
                    sta       ,x
                    lbra      GameCycleSuccess

* Match CoCo punctuation classes: delimiters become spaces; quotes/hyphens
* disappear. Normalize in place, collapsing delimiters and trimming ends.
ParserNormalize     ldu       <resourcebase
                    leax      parserline,u
                    tfr       x,y
                    clr       parserlength,u
                    lda       #1
                    sta       parserseen,u
ParserNormalizeByte lda      ,x+
                    beq       ParserNormalizeEnd
                    lbsr      ParserLower
                    pshs      x
                    leax      ParserDelimiters,pcr
ParserDelimiterTest tst      ,x
                    beq       ParserDropTestStart
                    cmpa      ,x+
                    bne       ParserDelimiterTest
                    puls      x
                    tst       parserseen,u
                    bne       ParserNormalizeByte
                    lda       #1
                    sta       parserseen,u
                    lda       #32
                    bra       ParserNormalizeStore
ParserDropTestStart leax     ParserDropChars,pcr
ParserDropTest      tst       ,x
                    beq       ParserKeepChar
                    cmpa      ,x+
                    bne       ParserDropTest
                    puls      x
                    bra       ParserNormalizeByte
ParserKeepChar      puls      x
                    clr       parserseen,u
ParserNormalizeStore sta     ,y+
                    inc       parserlength,u
                    bra       ParserNormalizeByte
ParserNormalizeEnd  tst       parserlength,u
                    beq       ParserNormalizeZero
                    tst       parserseen,u
                    beq       ParserNormalizeZero
                    leay      -1,y
                    dec       parserlength,u
ParserNormalizeZero clr      ,y
                    rts
ParserDelimiters    fcc       / ,.?!();:[]{}/
                    fcb       0
ParserDropChars     fcb       39,96,45,34,0
