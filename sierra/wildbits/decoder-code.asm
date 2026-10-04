* DecodeLines: X=commands, Y=length, U=private base and matching DP.
* Returns a private physical combined buffer, U=private base, carry clear;
* otherwise carry/B error, with no successful result for unsupported opcodes.
* Picture storage uses one OS-managed window; PictureWrite exports its bytes.
DecodeLines         stu       <resourcebase
                    tst       <decodeerror
                    lbne      DecodeFailed
                    tfr       y,d
                    leay      d,x
                    sty       <decodeend
                    pshs      x
                    lbsr      PictureAllocate
                    bcs       DecodeInitFailed
                    lbsr      PictureClear
DecodeInitFailed    puls      x
                    tst       <decodeerror
                    lbne      DecodeFailed
                    lda       #$FF
                    sta       <DrawColor
                    clr       <DrawMask
                    clr       <PenStatus
                    clr       <ScratchA6
                    lbsr      ReadNext
DecodeCommand       tst       <decodeerror
                    bne       DecodeFailed
                    cmpa      #$FF
                    beq       DecodeFinished
                    suba      #$F0
                    blo       DecodeInvalid
                    cmpa      #10
                    bhi       DecodeInvalid
                    asla
                    leau      DecodeDispatch,pcr
                    ldd       a,u
                    leau      d,u
                    jsr       ,u
                    bra       DecodeCommand
DecodeFinished      cmpx      <decodeend
                    bne       DecodeInvalid
                    ldu       <resourcebase
                    clrb
                    rts
DecodeInvalid       ldb       #E$BMode
                    stb       <decodeerror
DecodeFailed        ldu       <resourcebase
                    ldb       <decodeerror
                    orcc      #1
                    rts

* Immutable offsets from the table base, not load addresses patched at runtime.
DecodeDispatch      fdb       EnablePicDraw-DecodeDispatch
                    fdb       DisablePicDraw-DecodeDispatch
                    fdb       EnablePriDraw-DecodeDispatch
                    fdb       DisablePriDraw-DecodeDispatch
                    fdb       DrawYCorner-DecodeDispatch
                    fdb       DrawXCorner-DecodeDispatch
                    fdb       AbsoluteLine-DecodeDispatch
                    fdb       RelativeLine-DecodeDispatch
                    fdb       PicFill-DecodeDispatch
                    fdb       ReadPenStatus-DecodeDispatch
                    fdb       PlotWithPen-DecodeDispatch

* Preserve B: color/mask routines and coordinate helpers use it across reads.
ReadNext            tst       <decodeerror
                    bne       DecodeReadStop
                    cmpx      <decodeend
                    bhs       DecodeExhausted
                    lda       ,x+
                    rts
DecodeExhausted     pshs      b
                    ldb       #E$BMode
                    stb       <decodeerror
                    puls      b
DecodeReadStop      lda       #$FF
                    rts
ReadNextB           pshs      a
                    bsr       ReadNext
                    tfr       a,b
                    puls      a,pc
ReadColor           bsr       ReadNext
                    cmpa      #15
                    bls       ReadColorRet
                    pshs      b
                    ldb       #E$BMode
                    stb       <decodeerror
                    puls      b
ReadColorRet        rts
ReadInitialPos      lbsr      ReadXyPos
                    bcc       InitialPosRet
                    pshs      b
                    ldb       #E$BMode
                    stb       <decodeerror
                    puls      b
InitialPosRet       rts
