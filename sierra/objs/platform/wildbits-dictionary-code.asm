* Random-access encoded byte provider over the existing 512-byte file buffer.
* X=file offset, U=input cursor; A=byte/C clear or B=OS error/C set.
* X/Y/U are preserved, B is scratch. No mapped slab crosses file I/O.
DictionaryReadAt    pshs      x,y,u
                    ldu       <resourcebase
                    tfr       x,d
                    subd      dictionarycachebase,u
                    cmpd      parserreadlength,u
                    blo       DictionaryReadCached
                    ldx       ,s
                    stx       dictionarycachebase,u
                    ldd       #0
                    std       parserreadindex,u
                    std       parserreadlength,u
                    tfr       x,u
                    ldx       #0
                    lda       <resourcepath
                    os9       I$Seek
                    bcs       DictionaryReadReturn
                    lbsr      ParserByte
                    bcs       DictionaryReadReturn
                    tfr       b,a
                    andcc     #$FE
DictionaryReadReturn puls    x,y,u,pc
DictionaryReadCached leay    assetinput,u
                    lda       d,y
                    andcc     #$FE
                    puls      x,y,u,pc
DictionaryPrefix    pshs      a
                    lbsr      DictionaryReadAt
                    bcs       DictionaryPrefixError
                    tfr       a,b
                    puls      a
                    leax      1,x
                    andcc     #$FE
                    rts
DictionaryPrefixError puls   a,pc
DictionaryReadID    pshs      x
                    leax      1,x
                    lbsr      DictionaryReadAt
                    bcs       DictionaryIDReturn
                    pshs      a
                    leax      1,x
                    lbsr      DictionaryReadAt
                    bcs       DictionaryIDError
                    tfr       a,b
                    puls      a
                    andcc     #$FE
DictionaryIDReturn  puls     x,pc
DictionaryIDError   leas     1,s
                    puls      x,pc
* Validation already established EOF only at an entry boundary or trailing zero.
* Restore the common frame before propagating a real seek/read error.
DictionaryReadFailure cmpb   #E$EOF
                    lbeq      LookupWordNotFound
                    leas      6,s
                    orcc      #1
                    rts
