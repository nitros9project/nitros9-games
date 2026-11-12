* A=X, B=baseline Y; returns A=1 strictly inside, else 0.
* Native owner supplies X=private base; CoCo binds absolute state aliases.
InBlockRect         leas      -$01,s    allocate one byte result on stack
                    clr       ,s        assume not in block rect
                    ifne      BLOCK_PRIVATE_STATE
                    cmpa      BlockLeft,x
                    else
                    cmpa      >BlockLeft    compare X to left edge
                    endc
                    bls       InBlockRectReturn branch if X is left of rect (not inside)
                    ifne      BLOCK_PRIVATE_STATE
                    cmpa      BlockRight,x
                    else
                    cmpa      >BlockRight    compare X to right edge
                    endc
                    bcc       InBlockRectReturn branch if X is right of rect (not inside)
                    ifne      BLOCK_PRIVATE_STATE
                    cmpb      BlockTop,x
                    else
                    cmpb      >BlockTop    compare Y to top edge
                    endc
                    bls       InBlockRectReturn branch if Y is above rect (not inside)
                    ifne      BLOCK_PRIVATE_STATE
                    cmpb      BlockBottom,x
                    else
                    cmpb      >BlockBottom    compare Y to bottom edge
                    endc
                    bcc       InBlockRectReturn branch if Y is below rect (not inside)
                    inc       ,s        inside rect: set result to 1
InBlockRectReturn   lda       ,s        load result byte
                    leas      $01,s     release stack byte
                    rts
