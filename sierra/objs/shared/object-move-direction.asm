* Common target-direction classifier for both owners. Stack arguments are
* current X/Y, target X/Y, then a word-sized threshold. Native per-cycle
* stepping supplies threshold one for exact sign classification; move setup
* and CoCo stepping supply the actual step threshold.
CalcMoveDir         leas      -$03,s    allocate three local bytes
                    clra                clear A = 0
                    sta       $09,s     clear computed direction slot
                    ldb       $05,s     load target Y from args
                    std       ,s        save target Y
                    ldb       $07,s     load current Y from args
                    subd      ,s        compute Y delta (cur - target)
                    pshs      b,a       push Y delta
                    ldd       $0B,s     load step size
                    pshs      b,a       push step size
                    lbsr      CalcAxisDir compute Y-axis direction (0=same,1=pos,2=neg)
                    leas      $04,s     discard two arguments
                    sta       $02,s     save Y-axis direction (row index)
                    clra                clear A for X calc
                    sta       $05,s     clear X-comparison slot
                    ldb       $08,s     load current X from args
                    subd      $05,s     compute X delta
                    pshs      b,a       push X delta
                    ldd       $0B,s     load step size
                    pshs      b,a       push step size
                    lbsr      CalcAxisDir compute X-axis direction
                    leas      $04,s     discard two arguments
                    leax      >MoveTableData,pcr point to direction lookup table
                    ldb       #$03      table stride = 3 (per Y-dir group)
                    mul                 A × 3 = row offset
                    addb      $02,s     add X-axis direction index
                    lda       b,x       load final direction from table
                    leas      $03,s     release local frame
                    rts
CalcAxisDir         ldd       #$0000    compute negative of arg: -delta
                    subd      $02,s     subtract arg gives -arg in D
                    cmpd      $04,s     compare -delta to step size
                    blt       CalcAxisDirNeg branch if within negative range
                    clra                direction = 0 (at target)
                    bra       CalcAxisDirRet return zero direction
CalcAxisDirNeg      ldd       $02,s     load delta again
                    cmpd      $04,s     compare delta to step size
                    bgt       CalcAxisDirPos branch if positive delta
                    lda       #$02      direction = 2 (negative)
                    bra       CalcAxisDirRet return negative direction
CalcAxisDirPos      lda       #$01      direction = 1 (positive)
CalcAxisDirRet      rts
