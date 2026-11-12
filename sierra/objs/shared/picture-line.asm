* Shared AGI integer line algorithm; owner supplies DP state and SbuffPlot.
DrawLine            cmpb      <PosInitY  compare pos_final_y with pos_init_y
                    lbeq      SbuffXLine if equal call sbuff_xline() and don't return here
                    cmpa      <PosInitX  else compare with pos_init_x position
                    lbeq      SbuffYLine if equal call sbuff_yline() and don't return here

                    ldd       <PosInitX  load pos_init_x/y positions
                    std       <ScratchA4 store at pen_final ??? not in pic_render.c version

*  process y
                    lda       #$01      line_y_inc

                    ldb       <PosFinalY load pos_final_y
                    subb      <PosInitY  subtract pos_init_y
                    bcc       StoreLineYInc greater or equal zero don't negate
*                      less than zero
                    nega                flip the sign of line_y_inc
                    negb                flip the sign of y_component

StoreLineYInc       sta       <ScratchA7 store line_y_inc
                    stb       <ScratchA9 store y_component

* process x
                    lda       #$01      line_x_inc

                    ldb       <PosFinalX load pos_final_x
                    subb      <PosInitX  subtract pos_init_x
                    bcc       StoreLineXInc greater or equal zero don't negate
*                      less than zero
                    nega                flip the sign of line_x_inc
                    negb                flip the sign of x_component
StoreLineXInc       sta       <ScratchA6 store line_x_inc
                    stb       <ScratchA8 store x_component

* compare x/y components
                    cmpb      <ScratchA9 compare y_component to x_component
                    blo       YLarger   if x_component is smaller move on


*  x >= y
*                      x_component is in b
                    stb       <ScratchAB counter
                    stb       <ScratchAA largest_line
                    lsrb                divide by 2
                    stb       <ScratchA3 store y_count
                    clra                make a zero
                    sta       <ScratchA2 store x_count
                    bra       LineDrawLoop move on

*  x < y
YLarger             lda       <ScratchA9 load y_component
                    sta       <ScratchAB stow as counter
                    sta       <ScratchAA stow as largest line
                    lsra                divide by 2
                    sta       <ScratchA2 store x_count
                    clrb                make a zero
                    stb       <ScratchA3 store as y_count


* loops through the line and uses sbuff_plot to do the screen write
*                      y_count is in b
LineDrawLoop        addb      <ScratchA9 add in the y_component
                    stb       <ScratchA3 and stow back as y_count
                    cmpb      <ScratchAA compare that with line_largest
                    blo       XCountUpdate if y_count >= line_largest is not the case branch
                    subb      <ScratchAA subtract line_largest
                    stb       <ScratchA3 store as y_count
                    ldb       <ScratchA5 load pos_y
                    addb      <ScratchA7 add line_y_inc
                    stb       <ScratchA5 stow as pos_y

*                      x_count is in a
XCountUpdate        adda      <ScratchA8 add in x_component
                    sta       <ScratchA2 store as x_count
                    cmpa      <ScratchAA compare that with line_largest
                    blo       PlotNextPoint if x_count >= line_largest is not the case branch
                    suba      <ScratchAA subtract line_longest
                    sta       <ScratchA2 store at x_count
                    lda       <ScratchA4 load pos_x
                    adda      <ScratchA6 add line_x_inc
                    sta       <ScratchA4 stow as pos_x

PlotNextPoint       ldd       <ScratchA4 load computed pos_x/y
                    std       <PosInitX  store at pos_init_x/y positions
                    lbsr      SbuffPlot head for sbuff_plot()
                    ldd       <ScratchA2 reload x/y_count
                    dec       <ScratchAB decrement counter
                    bne       LineDrawLoop if counter not zero go again
                    rts                 line fully drawn return
