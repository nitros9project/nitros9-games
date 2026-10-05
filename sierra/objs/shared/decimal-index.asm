* Decimal substitution index scanner: X=input, B=parsed byte, X=first non-digit.
* The owner supplies byte-wrap or checked-overflow policy and return flags.
* Does not skip spaces. Each consumed decimal digit contributes value*10+digit.
ParseDecStr         clrb
ParseDecStrLoop     lda       ,x
                    cmpa      #$30
                    bcs       ParseDecStrRet
                    cmpa      #$39
                    bhi       ParseDecStrRet
                    lda       #$0A
                    mul
                    DECIMAL_INDEX_ADJUST
                    addb      ,x+
                    DECIMAL_INDEX_VALIDATE
                    bra       ParseDecStrLoop
ParseDecStrRet      DECIMAL_INDEX_RETURN
