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
                    bne       ViewNotLast
                    lda       $0F,x
                    beq       ViewInvalidQuery
                    deca
                    bra       ViewStoreQuery
ViewNotLast         cmpb      #50
                    bne       ViewNotCel
                    lda       $0E,x
                    bra       ViewStoreQuery
ViewNotCel          cmpb      #51
                    bne       ViewNotLoop
                    lda       $0A,x
                    bra       ViewStoreQuery
ViewNotLoop         cmpb      #52
                    bne       ViewLoops
                    lda       5,x
                    bra       ViewStoreQuery
ViewLoops           lda       $0B,x
ViewStoreQuery      pshs      a
                    ldu       <resourcebase
                    leay      vmvariables,u
                    clra
                    ldb       vmarguments+1,u
                    leay      d,y
                    puls      a
                    sta       ,y
                    clrb
                    rts
ViewInvalidQuery    ldb       #E$BMode
                    orcc      #1
                    rts
