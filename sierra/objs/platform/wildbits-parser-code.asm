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
ParserSearch        clr       parserwordlength,u
                    clr       parserreadindex,u
                    clr       parserreadindex+1,u
                    clr       parserreadlength,u
                    clr       parserreadlength+1,u
                    leax      parserline,u
                    ldb       parserposition,u
                    lda       b,x
                    sta       parserseen,u
                    ldd       #$FFFF
                    std       dictionaryentry,u
                    ldd       parserstart,u
                    std       dictionarycachebase,u
                    lda       <resourcepath
                    ldx       #0
                    ldu       parserstart,u
                    os9       I$Seek
                    lbcs      ResourceFailed
                    ldu       <resourcebase
                    lbra      DictionaryValidateEntry
ParserLookup        leax      parserline,u
                    ldb       parserposition,u
                    leau      b,x
                    pshs      u
                    lbsr      LookupWord
                    bcc       ParserLookupResult
                    leas      2,s
                    lbra      ResourceFailed
ParserLookupResult  pshs      d
                    tfr       u,d
                    subd      2,s
                    cmpb      #0
                    beq       ParserLookupLength
                    lda       -1,u
                    cmpa      #32
                    bne       ParserLookupLength
                    decb
ParserLookupLength  ldu       <resourcebase
                    stb       parserbestlength,u
                    puls      d
                    std       parserbestid,u
                    leas      2,s
                    lbra      ParserSearchDone
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
DictionaryValidateEntry ldd dictionarycachebase,u
                    addd      parserreadindex,u
                    std       parserbestid,u
                    lbsr      ParserByte
                    bcc       ParserPrefix
                    cmpb      #E$EOF
                    lbne      ResourceFailed
                    lbra      DictionaryValidateDone
ParserPrefix        cmpb      parserwordlength,u
                    lbhi      ParserMalformed
                    stb       parserwordlength,u
ParserSuffix        lbsr      ParserByte
                    bcc       ParserSuffixByte
                    cmpb      #E$EOF
                    lbne      ResourceFailed
                    tst       parserwordlength,u
                    lbeq      DictionaryValidateDone
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
                    lbsr      ParserByte
                    lbcs      ParserTruncated
                    lda       parserword,u
                    cmpa      parserseen,u
                    lbne      DictionaryValidateEntry
                    ldd       dictionaryentry,u
                    cmpd      #$FFFF
                    lbne      DictionaryValidateEntry
                    ldd       parserbestid,u
                    std       dictionaryentry,u
                    lbra      DictionaryValidateEntry
DictionaryValidateDone ldd  #0
                    std       parserreadlength,u
                    clrb
                    lbra      ParserLookup

                    use platform/dictionary-operands.asm
                    use shared/dictionary-lookup.asm
                    use platform/wildbits-dictionary-code.asm

* Buffered partial reads, with EOF accepted only between complete entries.
ParserByte          ldu       <resourcebase
                    ldd       parserreadindex,u
                    cmpd      parserreadlength,u
                    blo       ParserBuffered
                    ldd       dictionarycachebase,u
                    addd      parserreadlength,u
                    std       dictionarycachebase,u
                    lda       <resourcepath
                    leax      assetinput,u
                    ldy       #512
                    os9       I$Read
                    lbcs      ParserReturn
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

* In-place adapter to the same sentence tokenizer assembled by CoCo.
ParserNormalize     ldu       <resourcebase
                    leau      parserline,u
                    lbsr      TokenizeString
                    ldu       <resourcebase
                    rts
TOKENIZE_OUTPUT     macro
                    ldx       <resourcebase
                    leax      parserline,x
                    endm
TOKENIZE_FOLD       macro
                    lbsr      ParserLower
                    endm
TOKENIZE_FINISH     macro
                    ldu       <resourcebase
                    leax      parserline,u
                    pshs      x
                    ldd       2,s
                    subd      ,s++
                    stb       parserlength,u
                    endm
                    use       shared/tokenize-string.asm
                    use       shared/find-byte.asm
                    use       shared/parser-punctuation.asm
