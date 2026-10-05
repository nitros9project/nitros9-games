* get.string/get.num use a modal bounded editor; pending game input is saved.
GameGetInput        ldu       <resourcebase
                    lda       #1
                    sta       dialoginputmode,u
                    lda       <vmopcode
                    cmpa      #118
                    beq       GameGetNumber
                    lda       vmarguments,u
                    cmpa      #12
                    lbhs      GameGetInvalid
                    lda       vmarguments+2,u
                    cmpa      #25
                    lbhs      GameGetInvalid
                    sta       inventoryrow,u
                    lda       vmarguments+3,u
                    cmpa      #40
                    lbhs      GameGetInvalid
                    sta       inventorykey,u
                    lda       vmarguments+4,u
                    cmpa      #39
                    lbhi      GameGetInvalid
                    sta       inventorypaint,u
                    ldb       vmarguments+1,u
                    bra       GameGetSave
GameGetNumber       lda       #2
                    sta       dialoginputmode,u
                    sta       inventorykey,u
                    lda       #10
                    sta       inventoryrow,u
                    lda       #3
                    sta       inventorypaint,u
                    ldb       vmarguments,u
GameGetSave         pshs      b
                    leax      parserline,u
                    leay      resourcecommands+2000,u
                    ldb       #40
GameGetSaveByte     lda       ,x+
                    sta       ,y+
                    decb
                    bne       GameGetSaveByte
                    lda       parserlength,u
                    sta       ,y
                    clr       parserlength,u
                    clr       parserline,u
                    puls      b
                    lbsr      GamePrintMessage
                    pshs      cc,b
                    bcs       GameGetRestore
                    ldu       <resourcebase
                    lda       dialoginputmode,u
                    cmpa      #2
                    beq       GameGetCommitNumber
                    lda       vmarguments,u
                    ldb       #40
                    mul
                    leay      vmstrings,u
                    leay      d,y
                    leax      parserline,u
GameGetCommitString lda      ,x+
                    sta       ,y+
                    bne       GameGetCommitString
                    bra       GameGetRestore
GameGetCommitNumber leax      parserline,u
                    lbsr      AtoI
                    tfr       a,b
GameGetNumberStore  leay      vmvariables,u
                    lda       vmarguments+1,u
                    pshs      b
                    tfr       a,b
                    clra
                    leay      d,y
                    puls      b
                    stb       ,y
GameGetRestore      ldu       <resourcebase
                    leax      resourcecommands+2000,u
                    leay      parserline,u
                    ldb       #40
GameGetRestoreByte  lda       ,x+
                    sta       ,y+
                    decb
                    bne       GameGetRestoreByte
                    lda       ,x
                    sta       parserlength,u
                    clr       dialoginputmode,u
                    puls      cc,b,pc
GameGetInvalid      clr       dialoginputmode,u
                    lbra      ObjectBadIndex
                    use       shared/decimal-byte.asm
* A=1 finished, A=0 continue; C/error B. No vocabulary submission here.
GameLineKey         ldu       <resourcebase
                    lda       parsercharacter,u
                    cmpa      #13
                    lbeq      GameLineDone
                    cmpa      #5
                    beq       GameLineCancel
                    cmpa      #27
                    bne       GameLineBackspaceTest
GameLineCancel      clr       parserline,u
                    clr       parserlength,u
                    lbra      GameLineDone
GameLineBackspaceTest cmpa    #8
                    bne       GameLinePrintable
                    ldb       parserlength,u
                    beq       GameLineDraw
                    decb
                    stb       parserlength,u
                    leax      parserline,u
                    clr       b,x
                    bra       GameLineDraw
GameLinePrintable   cmpa      #32
                    blo       GameLineDraw
                    cmpa      #126
                    bhi       GameLineDraw
                    ldb       dialoginputmode,u
                    cmpb      #2
                    bne       GameLineStore
                    cmpa      #'0
                    blo       GameLineDraw
                    cmpa      #'9
                    bhi       GameLineDraw
GameLineStore       ldb       parserlength,u
                    cmpb      inventorypaint,u
                    bhs       GameLineDraw
                    cmpb      #39
                    bhs       GameLineDraw
                    leax      parserline,u
                    sta       b,x
                    incb
                    stb       parserlength,u
                    clr       b,x
GameLineDraw        ldx       <resourcebase
                    lda       inventoryrow,x
                    sta       textrow,x
                    ldb       #40
                    mul
                    addb      inventorykey,x
                    adca      #0
                    std       textindex,x
                    leay      textcharacters,x
                    leay      d,y
                    lda       inventorykey,x
                    sta       textcolumn,x
                    ldb       #40
                    subb      inventorykey,x
GameLineBlank       lda       #32
                    sta       ,y
                    lda       #$0F
                    sta       1000,y
                    leay      1,y
                    decb
                    bne       GameLineBlank
                    ldd       textindex,x
                    leay      textcharacters,x
                    leay      d,y
                    leau      parserline,x
                    ldb       #40
                    subb      inventorykey,x
GameLineCopy        lda       ,u+
                    beq       GameLineCursor
                    sta       ,y+
                    decb
                    bne       GameLineCopy
                    bra       GameLineShow
GameLineCursor      lda       #'_
                    sta       ,y
GameLineShow        lda       inventoryrow,x
                    ldb       #40
                    mul
                    addd      #40
                    std       textend,x
                    lbsr      GameDrawTextRange
                    bcs       GameLineReturn
                    clra
GameLineReturn      rts
GameLineDone        lda       #1
                    clrb
                    rts

GameWordToString    ldu       <resourcebase
                    ldb       vmarguments,u
                    beq       GameWordInvalid
                    cmpb      #20
                    bhi       GameWordInvalid
                    lda       parsercount,u
                    tst       vmvariables+9,u
                    beq       GameWordBound
                    inca
GameWordBound       pshs      a
                    cmpb      ,s+
                    bhi       GameWordInvalid
                    lda       vmarguments+1,u
                    cmpa      #12
                    bhs       GameWordInvalid
                    pshs      b
                    ldb       #40
                    mul
                    leay      vmstrings,u
                    leay      d,y
                    puls      b
                    decb
                    leax      parseroffsets,u
                    leax      b,x
                    lda       ,x
                    ldb       20,x
                    leax      parserlastline,u
                    leax      a,x
GameWordCopy        tstb
                    beq       GameWordEnd
                    lda       ,x+
                    sta       ,y+
                    decb
                    bra       GameWordCopy
GameWordEnd         clr       ,y
                    clrb
                    rts
GameWordInvalid     lbra      ObjectBadIndex
