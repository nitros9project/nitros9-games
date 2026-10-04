* CoCo loader/memory backend: private-load.
* Included in place; see ../../PORTABILITY.md for ownership and constraints.

NMLoadModule        leas      -10,s
                    stu       ,s        remap-table base
                    stx       2,s       module name
                    lda       #Prgrm+Objct
                    os9       F$Link
                    bcc       PrivateLinked
                    ldx       2,s
                    lda       #Prgrm+Objct
                    os9       F$Load
                    bcs       PrivateLoadRet
PrivateLinked       stu       6,s
                    tfr       u,d
                    addd      M$Size,u
                    bcs       PrivateBadSize
                    subd      #1
                    bcs       PrivateBadSize
                    anda      #$E0
                    clrb
                    std       8,s       last occupied source page
                    cmpd      #$C000    relocated code must end below the I/O page
                    bhi       PrivateBadSize
                    tfr       u,d
                    anda      #$E0
                    clrb
                    cmpd      #$6000    $4000 is the private copy window
                    blo       PrivateBadSize
                    std       4,s       first occupied source page
PrivatePageLoop     lda       >PrivateNext
                    cmpa      >PrivateLimit
                    bhs       PrivateBadSize
                    ldd       4,s
                    ldb       #8
                    mul                 A = source logical slot
                    ldx       ,s
                    leax      a,x
                    lda       >PrivateNext
                    sta       ,x        save private page in the runtime remap table
                    ldx       4,s
                    lbsr      CopyPrivatePage
                    inc       >PrivateNext
                    ldd       4,s
                    cmpd      8,s
                    beq       PrivateCopyDone
                    addd      #$2000
                    std       4,s
                    bra       PrivatePageLoop
PrivateCopyDone     ldu       6,s
                    os9       F$UnLink  releases our template reference and mappings
                    bra       PrivateLoadRet
PrivateBadSize      ldu       6,s
                    os9       F$UnLink
                    comb
                    ldb       #E$MemFul
PrivateLoadRet      leas      10,s
                    rts

* X=source page, A=private destination block. The $4000 data alias is
* borrowed only while interrupts are masked; the process DAT image is
* unchanged and no system calls occur before the hardware map is restored.
CopyPrivatePage     pshs      cc,d,x,y,u
                    orcc      #IntMasks
                    ldb       <MmuBlk2Orig the copy window normally aliases private data
                    pshs      b
                    sta       >$FFAA
                    ldu       #$4000
                    ldy       #$1000
PrivateWordLoop     ldd       ,x++
                    std       ,u++
                    leay      -1,y
                    bne       PrivateWordLoop
                    puls      b
                    stb       >$FFAA
                    puls      cc,d,x,y,u,pc
