* Common cel progression for cycle modes 0/1/2/3 and one-tick suppression.
* U=object. Owners bind the two adjacent DP scratch bytes,
* completion flag, cel selection and status return. No state is allocated.
AdvanceCelFrame     lda       <$25,u    load object animation flags
                    bita      #$10      test single-cycle-advance flag
                    beq       GetCelIndex branch if normal cycling
                    anda      #$EF      clear single-advance flag
                    sta       <$25,u    store updated flags
                    bra       AdvCelReturn done for this cycle
GetCelIndex         ldd       $0E,u     load current cel number (A) and last cel (B)
                    decb                decrement last-cel index for comparison
                    std       <CycleCurrent    save current and max cel indices
                    CYCLE_READ_MODE
                    cmpa      #$00      check if forward cycling
                    bne       CycleReverse branch if not forward cycle
                    ldb       <CycleCurrent    reload current cel index
                    incb                advance to next cel
                    cmpb      <CycleLast    compare to maximum cel index
                    bls       SetCelInLoop branch if still within range
                    clrb                wrap back to cel 0
                    bra       SetCelInLoop go set the new cel
CycleReverse        cmpa      #$03      check if reverse-cycle mode
                    bne       CycleRevEnd branch if not reverse cycling
                    ldb       <CycleCurrent    load current cel index
                    subb      #1        unsigned previous index; C marks wrap
                    bcc       SetCelInLoop
                    ldb       <CycleLast    wrap to last cel
                    bra       SetCelInLoop go set the new cel
CycleRevEnd         cmpa      #$02      check if end-of-loop mode
                    bne       CycleEnd  branch if not end-of-loop
                    ldb       <CycleCurrent    load current cel index
                    beq       NotifyEndOfLoop branch if already at cel 0
                    decb                step back one cel
                    bne       SetCelInLoop branch if not yet at cel 0
                    stb       <CycleCurrent    save cel index (0)
                    bra       NotifyEndOfLoop signal end of loop
CycleEnd            cmpa      #$01      check if end-of-forward-loop mode
                    bne       SetCelInLoop branch if none of the special modes
                    ldb       <CycleCurrent    load current cel index
                    cmpb      <CycleLast    compare to last cel
                    bcc       NotifyEndOfLoop branch if at or past last cel
                    incb                advance to next cel
                    cmpb      <CycleLast    compare to last cel again
                    bne       SetCelInLoop branch if not yet at end
                    stb       <CycleCurrent    save last cel index
NotifyEndOfLoop     CYCLE_NOTIFY_FLAG
                    lda       <$26,u    load object state flags
                    anda      #$DF      clear loop-active bit
                    sta       <$26,u    store updated state
                    clra                clear zero value
                    sta       <$21,u    halt object direction (stop)
                    sta       <$23,u    clear cycle mode
                    ldb       <CycleCurrent    reload final cel index
SetCelInLoop        CYCLE_SET_CEL
AdvCelReturn        CYCLE_RETURN
