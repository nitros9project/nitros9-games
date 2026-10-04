* CoCo platform boundary: keyboard-input.
* Included in place; see ../../PORTABILITY.md.

ReadStdinByte       leas      -$03,s    allocate three local bytes
                    sty       ,s        save Y register
                    lda       #$00      path 0 = stdin
                    ldb       #$01      GetStt code 1 = check char avail
                    os9       I$GetStt  check if char is available
                    bcs       ReadStdinByteErr branch if error (no char)
                    lda       #$00      path 0 = stdin
                    ldy       #$0001    read 1 byte
                    leax      $02,s     point X to local read buffer
                    os9       I$Read    read one byte from stdin
                    bcs       ReadStdinByteErr branch if read failed
                    lda       $02,s     load the byte we just read
                    bra       ReadStdinByteRet return with character in A
                    cmpa      #$F4      (unreachable — dead code)
                    bne       ReadStdinByteRet branch if not $F4
                    lda       <$0068    load trace-mode flag
                    bne       ReadStdinByteAlt branch if trace mode on
                    lda       >$01AF    load misc-flags byte
                    ora       #$20      set trace-active bit
                    sta       >$01AF    store updated flags
                    lbsr      TraceInit initialize trace display
                    bra       ReadStdinByteErr return error
ReadStdinByteAlt    lda       >$01AF    load misc-flags byte
                    anda      #$DF      clear trace-active bit
                    sta       >$01AF    store updated flags
                    lbsr      TraceErase erase trace display
ReadStdinByteErr    clra                return zero = no char / error
ReadStdinByteRet    ldy       ,s        restore Y register
                    leas      $03,s     release local frame
                    rts
