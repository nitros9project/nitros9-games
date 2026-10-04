* Native F9/FA handlers. CoCo pen geometry and texture sequence retained.
* Command X is private; tables are immutable PCR-relative data.
ReadPenStatus       lbsr      ReadNext
                    cmpa      #cmd_start
                    lbhs      DecodeInvalid
                    sta       <PenStatus
                    lbsr      ReadNext
                    rts
PlotWithPen         lda       <PenStatus
                    bita      #$20
                    beq       PenSolidPosition
                    lbsr      ReadNext
                    cmpa      #cmd_start
                    bhs       PenCommandRet
                    sta       <ScratchA6
                    lbsr      ReadInitialPos
                    bra       PenPositionReady
PenSolidPosition    lbsr      ReadXyPos
PenPositionReady    bcs       PenCommandRet
                    std       <ScratchA2
                    pshs      x
                    lbsr      PlotWithPen2
                    puls      x
                    bra       PlotWithPen
PenCommandRet       rts

PlotWithPen2        ldb       <PenStatus pen_status
                    andb      #$07      mask to get pen size bits 0-2
                    stb       <ScratchA7 pen.size ?? save for pen_status & $07

                    clra                clear a and condition codes
                    lslb                multiply by 2
                    std       <ScratchA9 pen size x 2
                    leau      CircleList,pcr circle_list[]
                    ldd       b,u       d now holds one of the circle_list values
                    leau      CircleData,pcr circle_data[]
                    leau      d,u       use that to index to a circle_data item
*                      u now is circle_ptr

*  Set up x position
                    clra                zero a for double-byte x calc
                    ldb       <ScratchA2 load pen_x position
                    lslb                multiply by two
                    rola                carry high bit of b into a
                    subb      <ScratchA7 subtract the pen.size
                    bcc       PenXOk    outcome not less than zero move on
                    deca                borrow from high byte
                    bpl       PenXOk    if we still have pos must be 0 or >
                    ldd       #0000     clamp to zero
                    bra       PenXFinal use clamped zero value
PenXOk              std       <ScratchAB store pen_x at scratch

                    ldd       #$013E    start with 320
                    subd      <ScratchA9 subtract 2 x pen.size
                    cmpd      <ScratchAB pen_x to calc
                    bls       PenXFinal if pen_x is greater keep temp calc
                    ldd       <ScratchAB otherwise use pen_x

PenXFinal           lsra                divide by 2
                    rorb                complete 16-bit right shift of d
                    stb       <ScratchA2 stow at pen_x
                    stb       <ScratchA4 stow at pen_final_x

*  Set up y position
                    lda       <ScratchA3 pen_y
                    suba      <ScratchA7 pen.size
                    bcc       PenYOk    >= 0 Ok go stow it
                    clra                otherwise less than zero so set it to 0
                    bra       PenYStore go stow it
PenYOk              sta       <ScratchAB store pen_y at scratch

                    lda       #y_max    start with 167
                    suba      <ScratchAA subtract 2 x pen.size
                    cmpa      <ScratchAB compare to pen_y calced so far
                    bls       PenYStore if pen_y > calc use calc and save it
                    lda       <ScratchAB otherwise use pen_y
PenYStore           sta       <ScratchA3 pen_y
                    sta       <ScratchA5 pen_final_y

                    lda       <ScratchA6 texture_num
                    ora       #$01      ensure bit 0 set for t calculation
                    sta       <ScratchA8 t ??

                    ldb       <ScratchAA 2 x pen.size
                    incb                bump it by one
                    tfr       b,a       copy b into a
                    adda      <ScratchA5 add value to pen_final_y
                    sta       <ScratchA5 save new pen_final_y
                    lslb                shift b left (multiply by 2)

                    leax      BinaryList,pcr binary list[]
                    abx                 advance x to table entry at offset B
                    stx       <ScratchAD pen width pointer

*   this looks like it should have been nested for loops
*   but not coded that way in pic_render.c

*  new y
PenYLoop            leax      BinaryList,pcr binary_list[]

*  new x
PenXLoop            lda       <PenStatus pen_status
                    bita      #$10 and it with $10 but don't change
                    bne       PenStatusCheck not equal zero go on to next pen status test
                    ldd       ,u        otherwise  load data at circle_ptr
                    anda      ,x        and that with first element in binary_list
                    bne       PenStatusCheck if thats not zero go on to next pen status check

                    andb      $01,x     and the second bytes of data at circle_ptr
*                      and binary_list
                    beq       NextPenX  that outcome is equ zero head for next calcs

PenStatusCheck      lda       <PenStatus pen_status
                    bita      #$20      anded with $20 but don't change
                    beq       PlotPoint equals zero set up and plot buffer
                    lda       <ScratchA8 otherwise load t (texture_num | $01)
                    lsra                divide by 2
                    bcc       SaveTexture no remainder save that number as t
                    eora      #$b8      exclusive or t with $B8
SaveTexture         sta       <ScratchA8 save new t
                    bita      #$01  anded with 1 but don't change
                    bne       NextPenX  not equal zero don't plot
                    bita      #$02 anded with 2 but don't change
                    beq       NextPenX  does equal zero don't plot

PlotPoint           pshs      u         save current u sbuff_plot uses it
                    ldd       <ScratchA2 load pen_x/pen_y values
                    std       <PosInitX  save at pos_init_x/y positions
                    lbsr      SbuffPlot head for sbuff_plot()
                    puls      u         retrieve u from before call

NextPenX            inc       <ScratchA2 increment pen_x value

                    leax      $04,x     move four bytes in the binary_list
                    cmpx      <ScratchAD comapre that value to pen_width
                    bls       PenXLoop  less or same go again

                    leau      $02,u     bump circle_ptr to next location in circle_data[]

                    lda       <ScratchA4 load pen_final_x
                    sta       <ScratchA2 store at pen_x
                    inc       <ScratchA3 bump pen_y
                    lda       <ScratchA3 pen_y
                    cmpa      <ScratchA5 compare to pen_final_y
                    bne       PenYLoop  not equal go do the next row
                    rts                 all pen rows drawn return

BinaryList          fdb       $8000
                    fdb       $4000
                    fdb       $2000
                    fdb       $1000
                    fdb       $0800
                    fdb       $0400
                    fdb       $0200
                    fdb       $0100
                    fdb       $0080
                    fdb       $0040
                    fdb       $0020
                    fdb       $0010
                    fdb       $0008
                    fdb       $0004
                    fdb       $0002
                    fdb       $0001

* circle_data[] (pic_render.c)
CircleData          fdb       $8000
                    fdb       $4000
                    fdb       $e000
                    fdb       $4000
                    fdb       $7000
                    fdb       $f800
                    fdb       $f800
                    fdb       $f800
                    fdb       $7000
                    fdb       $3800
                    fdb       $7c00
                    fdb       $fe00
                    fdb       $fe00
                    fdb       $fe00
                    fdb       $7c00
                    fdb       $3800
                    fdb       $1c00
                    fdb       $7f00
                    fdb       $ff80
                    fdb       $ff80
                    fdb       $ff80
                    fdb       $ff80
                    fdb       $ff80
                    fdb       $7f00
                    fdb       $1c00
                    fdb       $0e00
                    fdb       $3f80
                    fdb       $7fc0
                    fdb       $7fc0
                    fdb       $ffe0
                    fdb       $ffe0
                    fdb       $ffe0
                    fdb       $7fc0
                    fdb       $7fc0
                    fdb       $3f80
                    fdb       $1f00
                    fdb       $0e00
                    fdb       $0f80
                    fdb       $3fe0
                    fdb       $7ff0
                    fdb       $7ff0
                    fdb       $fff8
                    fdb       $fff8
                    fdb       $fff8
                    fdb       $fff8
                    fdb       $fff8
                    fdb       $7ff0
                    fdb       $7ff0
                    fdb       $3fe0
                    fdb       $0f80
                    fdb       $07c0
                    fdb       $1ff0
                    fdb       $3ff8
                    fdb       $7ffc
                    fdb       $7ffc
                    fdb       $fffe
                    fdb       $fffe
                    fdb       $fffe
                    fdb       $fffe
                    fdb       $fffe
                    fdb       $7ffc
                    fdb       $7ffc
                    fdb       $3ff8
                    fdb       $1ff0
                    fdb       $07c0

* circle_list[] (pic_render.c)
* this data is different in the file
* { 0, 1, 4, 9, 16, 25, 37, 50 }
* These run like a set of numbers**2 {0,1,2,3,4,5,~6,~7}
* ah ha these are multiples 2*(0,1,2,3,4,5,~6,~7)**2)

CircleList          fcb       $00,$00   0
                    fcb       $00,$02   2
                    fcb       $00,$08   8
                    fcb       $00,$12   18
                    fcb       $00,$20   32
                    fcb       $00,$32   50
                    fcb       $00,$4a   74
                    fcb       $00,$64   100
