* View/loop/cel selection and queries adapted from mnln. View records are
* mapped only while reading metadata. Object positions/indices are private;
* cel locations are logical offsets, never pointers into a foreign window.
ViewCommand         lbsr      ObjectAddress
                    lbcs      ViewReturn
                    stx       <viewobject
                    ldb       <vmopcode
                    cmpb      #49
                    lbhs      ViewQuery
                    ldu       <resourcebase
                    ldb       vmarguments+1,u
                    lda       <vmopcode
                    bita      #1
                    bne       ViewArgumentReady
                    lbsr      ObjectArgumentValue
ViewArgumentReady   lda       <vmopcode
                    cmpa      #42
                    bls       ViewSetResource
                    cmpa      #44
                    bls       ViewSetLoop
                    stb       $0E,x
                    bra       ViewSelect
ViewSetLoop         stb       $0A,x
                    bra       ViewSelect
ViewSetResource     stb       5,x
ViewSelect          ldb       5,x
                    lda       #2
                    lbsr      VmLoadResource
                    lbcs      ViewReturn
                    lbsr      VmRestoreAsset
                    ldd       #2
                    lbsr      AssetReadByte
                    lbcs      ViewRestore
                    tstb
                    lbeq      ViewInvalid
                    ldx       <viewobject
                    stb       $0B,x
                    clra
                    lslb
                    rola
                    addd      #5
                    std       <viewminoffset
                    cmpd      <resourcelength
                    lbhi      ViewInvalid
                    ldb       $0A,x
                    cmpb      $0B,x
                    blo       ViewLoopValid
                    lda       <vmopcode
                    cmpa      #42
                    lbhi      ViewInvalid
                    clr       $0A,x
                    clrb
ViewLoopValid       clra
                    lslb
                    rola
                    addd      #5
                    lbsr      AssetReadWord
                    lbcs      ViewRestore
                    cmpd      <viewminoffset
                    lblo      ViewInvalid
                    cmpd      <resourcelength
                    lbhs      ViewInvalid
                    std       <viewloopbase
                    lbsr      AssetReadByte
                    lbcs      ViewRestore
                    tstb
                    lbeq      ViewInvalid
                    ldx       <viewobject
                    stb       $0F,x
                    clra
                    lslb
                    rola
                    addd      #1
                    addd      <viewloopbase
                    lbcs      ViewInvalid
                    std       <viewminoffset
                    cmpd      <resourcelength
                    lbhi      ViewInvalid
                    ldb       $0E,x
                    cmpb      $0F,x
                    blo       ViewCelValid
                    lda       <vmopcode
                    cmpa      #44
                    lbhi      ViewInvalid
                    clr       $0E,x
                    clrb
ViewCelValid        clra
                    lslb
                    rola
                    addd      #1
                    addd      <viewloopbase
                    lbsr      AssetReadWord
                    lbcs      ViewRestore
                    addd      <viewloopbase
                    lbcs      ViewInvalid
                    cmpd      <viewminoffset
                    lblo      ViewInvalid
                    std       <viewcelbase
                    addd      #3
                    lbcs      ViewInvalid
                    cmpd      <resourcelength
                    lbhi      ViewInvalid
                    ldd       <viewcelbase
                    lbsr      AssetReadByte
                    lbcs      ViewRestore
                    tstb
                    lbeq      ViewInvalid
                    cmpb      #160
                    lbhi      ViewInvalid
                    ldx       <viewobject
                    stb       $1C,x
                    ldd       <viewcelbase
                    addd      #1
                    lbsr      AssetReadByte
                    lbcs      ViewRestore
                    tstb
                    lbeq      ViewInvalid
                    cmpb      #168
                    lbhi      ViewInvalid
                    ldx       <viewobject
                    stb       $1D,x
                    ldd       <viewcelbase
                    addd      #2
                    lbsr      AssetReadByte
                    bcs       ViewRestore
                    ldx       <viewobject
                    stb       $12,x
                    ldd       <viewcelbase
                    std       $10,x
                    clrb
ViewRestore         pshs      cc,b
                    lbsr      AssetUnmap
                    bcc       ViewUnmapped
                    leas      2,s
                    pshs      cc,b
ViewUnmapped        ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    puls      cc,b,pc
ViewInvalid         ldb       #E$BMode
                    orcc      #1
                    bra       ViewRestore
ViewReturn          rts
ViewQuery           cmpb      #49
                    lbeq      cmd_last_cel
                    cmpb      #50
                    lbeq      cmd_current_cel
                    cmpb      #51
                    lbeq      cmd_current_loop
                    cmpb      #52
                    lbeq      cmd_current_view
                    lbra      cmd_number_of_loops
* ObjectAddress already validated the object and left its record in X.
                    use       platform/object-view-query-operands.asm
                    use       shared/object-field-query.asm
                    use       shared/object-view-queries.asm
ViewInvalidQuery    ldb       #E$BMode
                    orcc      #1
                    rts
