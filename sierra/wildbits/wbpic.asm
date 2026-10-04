* First native Wild Bits presentation milestone,not the AGI interpreter.
* Input is 160*168 combined bytes: low nibble color,high nibble priority.
                    nam       wbpic
                    ttl       Wild Bits AGI combined-buffer viewer
                    use       defsfile
                    use       presentation.d

                    use       presentation-data.asm
                    use       presentation-buffers.asm
                    rmb       $2000-.
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbpic/
                    fcb       1
start               pshs      x
                    leax      ,u
                    ldb       #nearend
init                clr       ,x+
                    decb
                    bne       init
                    stu       <dbase
                    leax      intercept,pcr
                    os9       F$Icpt
                    lbcs      fail
                    lbsr      CheckTerminal
                    lbcs      fail
                    puls      x
skipspace           lda       ,x+
                    cmpa      #C$SPAC
                    beq       skipspace
                    cmpa      #C$CR
                    lbeq      usage
                    leax      -1,x
                    lda       #READ.
                    os9       I$Open
                    lbcs      fail
                    sta       <filepath
                    inc       <fileopen
* Refuse an existing bitmap: it is not ours to modify or free.
                    lda       #1
                    ldb       #SS.AScrn
                    ldx       #0
                    ldy       #0
                    os9       I$SetStt
                    lbcs      fail
                    inc       <bitmapowned
* Query the actual first block,rather than relying on an old allocation ABI.
                    lda       #1
                    ldb       #WBBmBlk
                    ldy       #0
                    os9       I$GetStt
                    lbcs      fail
                    stx       <firstblock
                    lda       #0
                    ldb       #WBWSig
                    ldx       #SignalBg*256+SignalFg
                    os9       I$SetStt
                    lbcs      fail
                    inc       <registered
                    clr       <blockindex
clearblock          lbsr      foreground
                    lbcs      fail
                    lbsr      mapblock
                    lbcs      fail
                    ldx       #BlockBytes
                    lda       #1        opaque black,not transparent index zero
clearbyte           sta       ,u+
                    leax      -1,x
                    bne       clearbyte
                    lbsr      unmap
                    lbcs      fail
                    tst       <aborted
                    lbne      cancelled
                    inc       <blockindex
                    lda       <blockindex
                    cmpa      #10
                    blo       clearblock
                    lda       #PictureHeight
                    sta       <rows
readrow             lbsr      foreground
                    lbcs      fail
                    ldu       <dbase
                    leax      rowinput,u
                    stx       <sourceptr
                    ldy       #PictureWidth
                    sty       <remaining
readmore            lda       <filepath
                    ldx       <sourceptr
                    ldy       <remaining
                    os9       I$Read
                    lbcs      fail
                    cmpy      #0
                    lbeq      badfile
                    tfr       y,d
                    addd      <sourceptr
                    std       <sourceptr
                    ldd       <remaining
                    pshs      y
                    subd      ,s++
                    std       <remaining
                    bne       readmore
                    ldu       <dbase
                    leax      rowinput,u
                    leay      rowoutput,u
                    lbsr      ConvertRow
                    ldu       <dbase
                    leax      rowoutput,u
                    stx       <sourceptr
                    ldd       #320
                    std       <remaining
writespan           ldd       <frameoffset
                    anda      #$1F
                    pshs      d         offset inside mapped block
                    ldd       <frameoffset
                    lsra
                    lsra
                    lsra
                    lsra
                    lsra
                    sta       <blockindex
                    lbsr      mapblock
                    lbcs      fail
                    puls      d
                    leau      d,u
                    pshs      d
                    ldd       #BlockBytes
                    subd      ,s++
                    cmpd      <remaining
                    bls       sized
                    ldd       <remaining
sized               std       <chunk
                    tfr       d,y
                    ldx       <sourceptr
copyspan            lda       ,x+
                    sta       ,u+
                    leay      -1,y
                    bne       copyspan
                    stx       <sourceptr
                    ldd       <frameoffset
                    addd      <chunk
                    std       <frameoffset
                    ldd       <remaining
                    subd      <chunk
                    std       <remaining
                    lbsr      unmap
                    lbcs      fail
                    tst       <aborted
                    lbne      cancelled
                    ldd       <remaining
                    bne       writespan
                    dec       <rows
                    lbne      readrow
* Exact input size: reject trailing bytes and distinguish EOF from other errors.
                    lda       <filepath
                    ldu       <dbase
                    leax      rowinput,u
                    ldy       #1
                    os9       I$Read
                    bcc       badfile
                    cmpb      #E$EOF
                    lbne      fail
                    lbsr      foreground
                    lbcs      fail
                    leax      palette,pcr
                    ldy       #0
                    ldu       #17
                    lda       #1
                    ldb       #WBClutWrite
                    os9       I$SetStt
                    lbcs      fail
                    lda       #1
                    ldb       #SS.Palet
                    ldx       #0
                    ldy       #0
                    os9       I$SetStt
                    lbcs      fail
                    lda       #1
                    ldb       #SS.PScrn
                    ldx       #0
                    ldy       #0
                    os9       I$SetStt
                    lbcs      fail
                    lda       #1
                    ldb       #SS.DScrn
                    ldx       #FX_BM+FX_GRF
                    ldy       #FT_OMIT
                    os9       I$SetStt
                    lbcs      fail
                    lda       #0
                    ldu       <dbase
                    leax      rowinput,u
                    ldy       #1
                    os9       I$Read    any key returns to text
                    bcs       fail
                    clrb
                    bra       finish
badfile             ldb       #E$BMode
                    bra       fail
cancelled           ldb       #E$PrcAbt
fail                stb       <errorcode
                    bra       cleanup
usage               leax      help,pcr
                    ldy       #80
                    lda       #2
                    os9       I$WritLn
                    ldb       #E$IllArg
finish              stb       <errorcode
cleanup             tst       <mapped
                    beq       closefile
                    lbsr      unmap
closefile           tst       <fileopen
                    beq       freebitmap
                    lda       <filepath
                    os9       I$Close
freebitmap          tst       <registered
                    beq       releasescreen
                    lda       #0
                    ldb       #WBWSig
                    ldx       #0
                    os9       I$SetStt
releasescreen       tst       <bitmapowned
                    beq       exit
                    lda       #1
                    ldb       #SS.DScrn
                    ldx       #FX_TXT
                    ldy       #FT_OMIT
                    os9       I$SetStt
                    lda       #1
                    ldb       #SS.FScrn
                    ldy       #0
                    os9       I$SetStt
exit                ldb       <errorcode
                    os9       F$Exit

                    use       platform/wildbits-presentation-helpers.asm

help                fcc       /Usage: wbpic <26880-byte combined picture>; any key exits/
                    fcb       C$CR
                    use       platform/wildbits-presentation-palette.asm
                    emod
eom                 equ       *
                    end
