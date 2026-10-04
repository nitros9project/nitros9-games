* Shared coordinate clamping and command-byte detection.
* PICTURE_BOUNDED_READ selects bounded ReadNext/ReadNextB callbacks; otherwise
* X is a contiguous command stream. It does not select hardware or add runtime
* dispatch. The bounded stream also records incomplete coordinate-pair errors.
ReadXyPos           lbsr      GetXPos   go get x position
                    lblo      CmdReturn prior subs return
                    lbsr      GetYPos   go get the y position
                    ifne      PICTURE_BOUNDED_READ
                    bcc       CoordPairRet
                    pshs      b
                    ldb       #E$BMode
                    stb       <decodeerror
                    puls      b
                    endc
CoordPairRet        rts                 return with x/y in d


* get_x_pos()
GetXPos             equ       *
                    ifne      PICTURE_BOUNDED_READ
                    lbsr      ReadNext       load pic_byte
                    else
                    lda       ,x+
                    endc
                    cmpa      #cmd_start is it a command?
                    bhs       RetSetCC  if so set CC
                    cmpa      #x_max    compare to 159
                    bls       RetClearCC is it less or same clear CC and return
                    lda       #x_max    greater than load acca with 159
RetClearCC          andcc     #$fe      clear CC ad return
                    rts                 return carry clear = valid coord


RetSetCC            orcc      #1        returns a "1"
                    rts                 return carry set = command byte seen

* get_y_pos()
GetYPos             equ       *
                    ifne      PICTURE_BOUNDED_READ
                    lbsr      ReadNextB       load pic_byte
                    else
                    ldb       ,x+
                    endc
                    cmpb      #cmd_start is it a command
                    blo       YPosClamp nope less than command
                    lda       -$01,x    was a command load x back in acca
                    bra       RetSetCC  go set CC
YPosClamp           cmpb      #y_max    compare to 167
                    bls       YPosOk    is it less or same clear CC and return
                    ldb       #y_max    greater than load accb with 167
YPosOk              andcc     #$fe      clear CC and return
                    rts                 return carry clear = valid y coord
