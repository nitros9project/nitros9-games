* Shared said matching. Y=little-endian script IDs; X=big-endian parsed IDs.
* Adjacent DP counters SaidExpected/SaidParsed hold remaining word counts.
* Owner callbacks SaidCheckDone/SaidSetMatch handle input flags and results.
* ID 1 consumes one parsed word; ID 9999 accepts the rest of the input.
SaidMatchLoop       lda       <SaidExpected    load remaining words to match
                    beq       SaidCheckDone branch if all words matched (success)
                    ldb       ,y+       load first byte of word ID
                    lda       ,y+       load second byte of word ID
                    dec       <SaidExpected    decrement remaining word count
                    cmpd      #$270F    check for "any word" wildcard ($270F)
                    bne       SaidCheckWild branch if not wildcard
                    lda       <SaidExpected    load remaining count after wildcard
                    beq       SaidSetMatch branch if at end of word list (match)
                    lsla                multiply remaining count by 2
                    leay      a,y       skip remaining word IDs in script
                    lbra      SaidSetMatch signal match
SaidCheckWild       tst       <SaidParsed    check if any parsed words remain
                    bne       SaidWordCompare branch if more parsed words to check
                    inc       <SaidParsed    indicate out of parsed words (no match)
                    lbra      SaidCheckDone
SaidWordCompare     cmpd      ,x++      compare word ID to parsed word (advance X)
                    beq       SaidWordMatch branch if word matches
                    cmpd      #$0001    check for "any/rest" wildcard ($0001)
                    bne       SaidCheckDone branch if no match and not wildcard
SaidWordMatch       dec       <SaidParsed    decrement remaining parsed word count
                    bra       SaidMatchLoop loop to match next word
