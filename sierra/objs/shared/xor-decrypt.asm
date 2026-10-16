* X=buffer start, U=exclusive end. In-place AGI XOR; Y/DP unchanged.
* Consumed spans return X=end and U=key cursor; empty/reversed spans do not write.
XorDecrypt          leas      -$02,s    allocate 2-byte stack slot for pointer
                    stu       ,s        save end-of-buffer pointer
                    leau      >XorKeyStr,pcr point U to start of XOR key string
XorDecryptLoop      cmpx      ,s        compare X (current pos) to end pointer
                    bcc       XorDecryptDone branch if past end of buffer
                    tst       ,u        check if key pointer at null terminator
                    bne       XorDecryptWrap branch if not at end of key
                    leau      >XorKeyStr,pcr wrap key pointer back to start
XorDecryptWrap      lda       ,x        load current ciphertext byte
                    eora      ,u+       XOR with key byte, advance key pointer
                    sta       ,x+       store decrypted byte, advance data pointer
                    bra       XorDecryptLoop loop until all bytes decrypted
XorDecryptDone      leas      $02,s     release stack pointer slot
                    rts

