* CoCo platform boundary: sound-elapsed.
* Included in place; see ../../PORTABILITY.md.

                    cmpd      #$0000    ; any elapsed time returned?
                    lbeq      TimeRestorePage ; skip time update if zero
                    pshs      b,a       ; save elapsed time
                    addb      $0C,s     ; add seconds field
                    bcc       TimeSecCarry ; branch if no second overflow
                    inca                ; carry into minutes
TimeSecCarry        ldu       #$003C    ; 60 seconds per minute
                    lbsr      UIntDivide ; divide to get minute carry
                    stb       $0C,s     ; store updated seconds
                    tfr       u,d       ; D = minute carry
                    cmpd      #$0000    ; any minutes to add?
                    beq       TimeSetSys ; skip if none
                    addb      $0B,s     ; add to minutes field
                    bcc       TimeMinCarry ; branch if no minute overflow
                    inca                ; carry into hours
TimeMinCarry        ldu       #$003C    ; 60 minutes per hour
                    lbsr      UIntDivide ; divide to get hour carry
                    stb       $0B,s     ; store updated minutes
                    tfr       u,d       ; D = hour carry
                    tstb                ; any hours to add?
                    beq       TimeSetSys ; skip if none
                    addb      $0A,s     ; add to hours field
                    lda       #$17      ; 24 hours per day
                    lbsr      Div8      ; divide to get day carry
                    sta       $0A,s     ; store updated hours
                    tstb                ; any days to add?
                    beq       TimeSetSys ; skip if none
                    inc       $09,s     ; increment day of month
                    ldd       $08,s     ; load month and year
                    leax      >MonthDayTable,pcr ; days-per-month table
                    cmpb      a,x       ; past end of month?
                    bls       TimeSetSys ; branch if still in month
                    ldb       a,x       ; days in this month
                    cmpa      #$02      ; is it February?
                    bne       TimeDayIncr ; branch if not Feb
                    ldb       $07,s     ; year value
                    beq       TimeDayIncr ; not a leap year
                    bitb      #$03      ; leap year check (divisible by 4)
                    bne       TimeDayIncr ; not divisible by 4
                    ldb       $09,s     ; current day
                    cmpb      #$1D      ; day 29?
                    beq       TimeSetSys ; allow Feb 29 on leap year
TimeDayIncr         ldb       #$01      ; reset to day 1
                    stb       $09,s     ; store day = 1
                    inca                ; advance month
                    cmpa      #$0C      ; past December?
                    bls       TimeMonthAdv ; branch if still in year
                    stb       $08,s     ; month = 1
                    inc       $07,s     ; increment year
                    bra       TimeSetSys ; apply to system
TimeMonthAdv        sta       $08,s     ; store updated month
TimeSetSys          leax      $07,s     ; point to updated time struct
                    os9       F$STime   ; set system time
                    puls      b,a       ; restore elapsed time
                    addb      >$043C    ; add to timer seconds field
                    bcc       TimeSec2Carry ; branch if no overflow
                    inca                ; carry into timer minutes
TimeSec2Carry       ldu       #$003C    ; 60 seconds per minute
                    lbsr      UIntDivide ; divide to get carry
                    stb       >$043C    ; store timer seconds
                    tfr       u,d       ; D = minute carry
                    cmpd      #$0000    ; any minutes?
                    beq       TimeRestorePage ; skip if none
                    addb      >$043D    ; add to timer minutes field
                    bcc       TimeMin2Carry ; branch if no overflow
                    inca                ; carry into hours
TimeMin2Carry       ldu       #$003C    ; 60 minutes per hour
                    lbsr      UIntDivide ; divide to get carry
                    stb       >$043D    ; store timer minutes
                    tfr       u,d       ; D = hour carry
                    tstb                ; any hours?
                    beq       TimeRestorePage ; skip if none
                    addb      >$043E    ; add to timer hours
                    lda       #$17      ; 24 hours per day
                    lbsr      Div8      ; get day carry in B
                    sta       >$043E    ; store timer hours
                    tstb                ; any day overflow?
                    beq       TimeRestorePage ; skip if none
                    inc       >$043F    ; increment timer day counter
TimeRestorePage     ldd       $03,s     ; saved logic page
                    lbsr      SetLogicPage ; restore logic page
