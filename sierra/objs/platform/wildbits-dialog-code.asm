* print/print.v: modal text with private screen backup and no mapped wait.
* The picture/LZW command workspace is idle until the window is dismissed.
GamePrintCommand    ldu       <resourcebase
                    clr       dialoginputmode,u
                    ldb       vmarguments,u
                    lda       <vmopcode
                    cmpa      #102
                    bne       GamePrintMessage
                    leax      vmvariables,u
                    clra
                    ldb       d,x
GamePrintMessage    lbsr      ReadLogicMessage
                    lbcs      GameTextReturn
GamePrintText       ldu       <resourcebase
                    stx       textpointer,u
                    leax      textcharacters,u
                    leay      resourcecommands,u
                    ldd       #1000
                    pshs      d
GamePrintSave       ldd       ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       GamePrintSave
                    leas      2,s
                    lda       <vmtextforeground
                    ldb       <vmtextbackground
                    pshs      d
                    clr       <vmtextforeground
                    lda       #15
                    sta       <vmtextbackground
                    leax      textcharacters,u
                    ldy       #1000
GamePrintClear      lda       #32
                    sta       ,x
                    lda       #$0F
                    sta       1000,x
                    leax      1,x
                    leay      -1,y
                    bne       GamePrintClear
                    lda       #1
                    sta       dialogactive,u
                    sta       dialogwordstart,u
                    lda       #8
                    sta       textrow,u
                    lda       #2
                    sta       textcolumn,u
                    ldx       textpointer,u
                    lbsr      GameTextValidate
                    bcs       GamePrintRestore
GamePrintWait       lbsr      foreground
                    bcs       GamePrintRestore
                    lda       #0
                    ldb       #SS.Ready
                    os9       I$GetStt
                    bcc       GamePrintKey
                    cmpb      #E$NotRdy
                    bne       GamePrintRestore
                    ldx       #2
                    os9       F$Sleep
                    bra       GamePrintWait
GamePrintKey        lda       #0
                    ldu       <resourcebase
                    leax      parsercharacter,u
                    ldy       #1
                    os9       I$Read
                    lbcs      GamePrintRestore
                    ldu       <resourcebase
                    tst       dialoginputmode,u
                    beq       GamePrintRestore
                    lbsr      GameLineKey
                    lbcs      GamePrintRestore
                    tsta
                    lbeq      GamePrintWait
                    clrb
GamePrintRestore    pshs      cc,b
                    ldu       <resourcebase
                    clr       dialogactive,u
                    ldu       <resourcebase
                    leax      resourcecommands,u
                    leay      textcharacters,u
                    ldd       #1000
                    pshs      d
GamePrintCopyBack   ldd       ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       GamePrintCopyBack
                    leas      2,s
                    puls      cc,b
                    puls      a
                    sta       <vmtextforeground
                    puls      a
                    sta       <vmtextbackground
                    lbcs      GameTextReturn
                    lbsr      GameComposeScene
                    lbcs      GameTextReturn
                    lbra      RefreshPicture
