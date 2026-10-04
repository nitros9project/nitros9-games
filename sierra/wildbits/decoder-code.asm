* DecodeLines: X=commands, Y=length, U=private base and matching DP.
* Returns X=combined buffer, Y=26880, U=private base, carry clear;
* otherwise carry/B error, with no successful result for unsupported opcodes.
* This probe uses a resident combined buffer. A mapped backend is still needed
* before integrating it into the full engine's smaller resident state budget.
DecodeLines         stu       <resourcebase
                    clr       <decodeerror
                    tfr       y,d
                    leay      d,x
                    sty       <decodeend
                    pshs      x
                    leau      decodedbuffer,u
                    stu       <decodedbase
                    ldx       #13440
                    ldd       #$4F4F
DecodeClear         std       ,u++
                    leax      -1,x
                    bne       DecodeClear
                    puls      x
                    lda       #$FF
                    sta       <DrawColor
                    clr       <DrawMask
                    lbsr      ReadNext
DecodeCommand       tst       <decodeerror
                    bne       DecodeFailed
                    cmpa      #$FF
                    beq       DecodeFinished
                    suba      #$F0
                    blo       DecodeInvalid
                    cmpa      #7
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
                    leax      decodedbuffer,u
                    ldy       #26880
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

* Preserve B: color/mask routines and coordinate helpers use it across reads.
ReadNext            cmpx      <decodeend
                    bhs       DecodeExhausted
                    lda       ,x+
                    rts
DecodeExhausted     pshs      b
                    ldb       #E$BMode
                    stb       <decodeerror
                    puls      b
                    lda       #$FF
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
