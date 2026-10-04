* Start a loaded logic slab. The two-byte header is the little-endian code
* length; messages follow it and must never be executed as instructions.
StartLogic          ldu       <resourcebase
                    leax      vmvariables,u
                    ldy       #512
                    clra
VmClearState        sta       ,x+
                    leay      -1,y
                    bne       VmClearState
                    lbsr      VmInitializeCache
                    clr       <vmip
                    clr       <vmip+1
                    ldd       <resourcelength
                    std       <vmend
                    lbsr      VmReadWord
                    bcs       VmNativeReturn
                    cmpd      #$FFFD
                    bhi       VmNativeInvalid
                    addd      #2
                    cmpd      <resourcelength
                    bhi       VmNativeInvalid
                    cmpd      #2
                    bls       VmNativeInvalid
                    std       <vmend
                    lbsr      ExecuteLogic
VmNativeReturn      pshs      b,cc
                    lbsr      AssetUnmap
                    bcs       VmNativeUnmapError
                    puls      cc,b,pc
VmNativeUnmapError  leas      2,s
                    rts
VmNativeInvalid     lbsr      VmInvalid
                    bra       VmNativeReturn
VmFetchByte         pshs      x,y,u
                    tst       <asseterror
                    bne       VmFetchFailed
                    ldd       <vmip
                    cmpd      <vmend
                    bhs       VmFetchEOF
                    lbsr      AssetPointer
                    tst       <asseterror
                    bne       VmFetchFailed
                    ldb       ,u
                    pshs      b
                    ldd       <vmip
                    addd      #1
                    std       <vmip
                    puls      b
                    andcc     #$FE
                    puls      x,y,u,pc
VmFetchEOF          ldb       #E$EOF
                    orcc      #1
                    puls      x,y,u,pc
VmFetchFailed       ldb       <asseterror
                    orcc      #1
                    puls      x,y,u,pc
