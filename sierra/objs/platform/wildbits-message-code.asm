* ReadLogicMessage: B=1-based message number. X=private messagebuffer,
* Y=length excluding NUL on success; C/error B otherwise. U/DP retained.
* Message offsets are little endian relative to the length word following
* the count. Plain AGI logic strings use Avis Durgan; LZW strings are plain.
* Every table/string access is checked against the owned expanded slab.
ReadLogicMessage    stb       <messagenumber
                    ldd       <vmend
                    lbsr      AssetReadByte
                    lbcs      MessageReturn
                    stb       <messagecount
                    tst       <messagenumber
                    lbeq      MessageInvalid
                    ldb       <messagenumber
                    cmpb      <messagecount
                    lbhi      MessageInvalid
                    ldd       <vmend
                    addd      #1
                    std       <messagebase
                    lbsr      AssetReadWord
                    lbcs      MessageReturn
                    cmpd      #2
                    lblo      MessageInvalid
                    addd      <messagebase
                    lbcs      MessageInvalid
                    cmpd      <resourcelength
                    lbhi      MessageInvalid
                    std       <messageend
                    clra
                    ldb       <messagecount
                    lslb
                    rola
                    addd      #2
                    addd      <messagebase
                    lbcs      MessageInvalid
                    std       <messagestart
                    cmpd      <messageend
                    lbhi      MessageInvalid
                    clra
                    ldb       <messagenumber
                    lslb
                    rola
                    addd      <messagebase
                    lbsr      AssetReadWord
                    lbcs      MessageReturn
                    cmpd      #0
                    lbeq      MessageInvalid
                    addd      <messagebase
                    lbcs      MessageInvalid
                    cmpd      <messagestart
                    lblo      MessageInvalid
                    cmpd      <messageend
                    lbhs      MessageInvalid
                    std       <messageposition
                    subd      <messagestart
MessageKeyModulo    cmpd      #11
                    blo       MessageKeyReady
                    subd      #11
                    bra       MessageKeyModulo
MessageKeyReady     stb       <messagekey
                    clr       <messagelength
                    clr       <messagelength+1
MessageCopyNext     ldd       <messageposition
                    cmpd      <messageend
                    lbhs      MessageInvalid
                    lbsr      AssetReadByte
                    lbcs      MessageReturn
                    pshs      b
                    ldd       <messageposition
                    addd      #1
                    std       <messageposition
                    ldd       <resourcestored
                    cmpd      <resourcelength
                    puls      b
                    bne       MessagePlainByte
                    leax      MessageXorKey,pcr
                    lda       <messagekey
                    eorb      a,x
                    inc       <messagekey
                    lda       <messagekey
                    cmpa      #11
                    blo       MessagePlainByte
                    clr       <messagekey
MessagePlainByte    pshs      b
                    ldu       <resourcebase
                    leax      messagebuffer,u
                    ldd       <messagelength
                    leax      d,x
                    puls      b
                    stb       ,x
                    tstb
                    beq       MessageDone
                    ldd       <messagelength
                    addd      #1
                    std       <messagelength
                    cmpd      #512
                    blo       MessageCopyNext
                    ldb       #E$MemFul
                    orcc      #1
                    bra       MessageReturn
MessageDone         ldu       <resourcebase
                    leax      messagebuffer,u
                    ldy       <messagelength
                    clrb
MessageReturn       rts
MessageInvalid      ldb       #E$BMode
                    orcc      #1
                    rts

MessageXorKey       equ       XorKeyStr
                    use shared/agi-xor-key.asm
