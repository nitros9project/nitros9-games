* Converted from objs/shdw.asm F0-F7 coordinate/line bodies and
* platform/coco-picture-storage.asm line/plot bodies. Original labels and
* Bresenham/clamping behavior retained. Private DP fields and relative buffer
* base replace CoCo addresses; command fetches go through bounded ReadNext.
* This file contains no module header, data allocation or hardware access.
EnablePicDraw       ldd       <DrawColor pulls in color and sbuff_drawmask
                    anda      #$f0      and color with $F0
                    pshs      d
                    lbsr      ReadColor
                    sta       <decodevalue
                    puls      d
                    ora       <decodevalue       or that result with the pic_byte and bump to next
                    orb       #$0f      or the sbuff_drawmask with $0F
                    std       <DrawColor store the updated values
                    lbsr      ReadNext       return value ignored so this just bumps to next pic_byte
                    rts                 return to pic_cmd_loop


* Command $F1 Disable picture draw
*  disable_pic_draw()
*
*  DrawColor = color
*  DrawMask = sbuff_drawmask
*  x contains pointer to given_pic_data known as the pic_byte
*  after ldd
*  a contains color
*  b contains draw mask
*  returns the next pic_byte in a

DisablePicDraw      ldd       <DrawColor pulls in color and sbuff_drawmask
                    ora       #$0f      ors color with $0F (white ??)
                    andb      #$f0      ands draw mask with $F0
                    std       <DrawColor store the updated values
                    lbsr      ReadNext       return value ignored so this just bumps to next pic_byte
                    rts                 return to pic_cmd_loop

* Command $F2 Changes priority color and enables priority draw
*  enable_pri_draw() pic_render.c
*
*  DrawColor = color
*  DrawMask = sbuff_drawmask
*  x contains pointer to given_pic_data known as the pic_byte
*  after ldd
*  a contains color
*  b contains draw mask
*  returns the next pic_byte in a

EnablePriDraw       ldd       <DrawColor pulls in color and sbuff_drawmask
                    anda      #$0f      ands color with $0F
                    sta       <DrawColor save color
                    lbsr      ReadColor       loads pic_byte and bumps to next
                    asla                times 2 with sign extend
                    asla                again times 2
                    asla                and again times 2
                    asla                end result is multiply pic_byte by 16 ($10)
                    ora       <DrawColor or that value with the modified color
                    orb       #$f0      or the sbuff_drawmask with $F0
                    std       <DrawColor store the updated values
                    lbsr      ReadNext       return value ignored so this just bumps to next pic_byte
                    rts                 return to pic_cmd_loop

* Command $F3 Disable priority draw
*  diasable_pri_draw() pic_render.c
*
*  DrawColor = color
*  DrawMask = sbuff_drawmask
*  x contains pointer to given_pic_data known as the pic_byte
*  after ldd
*  a contains color
*  b contains draw mask
*  returns the next pic_byte in a


DisablePriDraw      ldd       <DrawColor pulls in color and sbuff_drawmask
                    ora       #$f0      or the color with $F0
                    andb      #$0f      and the sbuff_drawmask with $0F
                    std       <DrawColor store the updated values
                    lbsr      ReadNext       return value ignored so this just bumps to next pic_byte
                    rts                 return to pic_cmd_loop

DrawXCorner         lbsr      ReadInitialPos call read_xy_pos
                    bcs       CmdReturn next subs rts
                    std       <PosInitX  save pos_init_x/y positions
                    lbsr      SbuffPlot head for sbuff_plot()
                    bsr       DrawXEntry draw_corner(0)
                    rts                 corner drawn return


* Command $F4 Draw a Y corner
* draw_y_corner()  pic_render.c
*
*  PosInitX = pos_init_x
*  PosInitY = pos_init_y

DrawYCorner         lbsr      ReadInitialPos call read_xy_pos
                    bcs       CmdReturn return
                    std       <PosInitX  save at pos_init_x/y positions
                    lbsr      SbuffPlot head for sbuff_plot()
                    bsr       DrawYEntry draw_corner(1)
CmdReturn           rts                 common return point for commands



* draw_corner(u8 type)  pic_render.c
*
*  PosInitX = pos_init_x
*  PosInitY = pos_init_y
*  PosFinalX = pos_final_x
*  PosFinalY = pos_final_y

draw_x
DrawXEntry          lbsr      GetXPos   get_x_pos()
                    bcs       CmdReturn prior subs return
                    sta       <PosFinalX store as pos_final_x
                    ldb       <PosInitY  load pos_init_y
                    stb       <PosFinalY store as pos_final_y
                    lbsr      SbuffXLine call sbuff_xline()

draw_y
DrawYEntry          lbsr      GetYPos   get_y_pos
                    bcs       CmdReturn prior subs return
                    stb       <PosFinalY save pos_final_y
                    lda       <PosInitX  load pos_init_x
                    sta       <PosFinalX save pos_final_x
                    lbsr      SbuffYLine sbuff_yline()
                    bra       DrawXEntry head for draw_x



* Command $F6 Absolute line
* absolute_line()
* This command is before Draw X corner in nagi source
*
*  PosInitX = pos_init_x
*  PosInitY = pos_init_y
*  PosFinalX = pos_final_x
*  PosFinalY = pos_final_y

AbsoluteLine        lbsr      ReadInitialPos call read_xy_pos
                    bcs       CmdReturn prior subs return
                    std       <PosInitX  save at pos_init_x/y positions
                    lbsr      SbuffPlot head for sbuff_plot()
AbsLineLoop         bsr       ReadXyPos call read_xy_pos
                    bcs       CmdReturn prior subs return
                    std       <PosFinalX save at pos_final_x/y and passed draw_line in d
                    lbsr      DrawLine  call draw_line()
                    bra       AbsLineLoop go again



* relative_line()
*
*  PosInitX = pos_init_x
*  PosInitY = pos_init_y
*  PosFinalX = pos_final_x
*  PosFinalY = pos_final_y

RelativeLine        lbsr      ReadInitialPos call read_xy_pos
                    bcs       CmdReturn prior subs return
                    std       <PosInitX  save at pos_init_x/y positions
                    lbsr      SbuffPlot head for sbuff_plot()

* calc x
RelLineLoop         lbsr      ReadNext       get next pic_byte
*                      and load it in pos_data in c source
                    cmpa      #cmd_start is that equal $F0 or greater
                    bcc       CmdReturn yep were done so return (we use prior subs return ??)
*                      that rascal in acca changes names again to x_step
*                      but it's still the same old data
                    anda      #$70      and that with $70
*                      (where these values are derived from I haven't a clue, as of yet :-))
                    lsra                divide by 2
                    lsra                and again
                    lsra                once more
                    lsra                and finally another for a /16
                    ldb       -$01,x    get the original value
                    bpl       XStepOk   if original value not negative move on
                    nega                else it was so flip the sign of the computed value
XStepOk             adda      <PosInitX  add pos_init_x position
                    cmpa      #x_max    compare to 159
                    bls       StorePosX if it's less or same move on
                    lda       #x_max    else cap it at 159
StorePosX           sta       <PosFinalX store as pos_final_x

* calc y
*                      not quite the same as pic_render.c almost
*                      we've go the pic_byte ... er pos_data ... now called y_step
*                      in b so lets calc the y_step
                    andb      #$0f      and with $0F (not in pic_render.c)
                    bitb      #$08      and that with $08 but don't change
                    beq       AddYStep  if result = 0 move on
                    andb      #$07      else and it with $07
                    negb                and negate it
AddYStep            addb      <PosInitY  add calced value to pos_init_y
                    cmpb      #y_max    compare to 167
                    bls       StorePosY less or same move on
                    ldb       #y_max    greater ? cap it
StorePosY           stb       <PosFinalY pos_final_y

*                      passes pos_final_x/y in d
                    lbsr      DrawLine  call draw_line()

                    bra       RelLineLoop go again exit is conditinals inside loop

ReadXyPos           lbsr      GetXPos   go get x position
                    lblo      CmdReturn prior subs return
                    lbsr      GetYPos   go get the y position
                    bcc       CoordPairRet
                    pshs      b
                    ldb       #E$BMode
                    stb       <decodeerror
                    puls      b
CoordPairRet        rts                 return with x/y in d


* get_x_pos()
GetXPos             lbsr      ReadNext       load pic_byte
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
GetYPos             lbsr      ReadNextB       load pic_byte
                    cmpb      #cmd_start is it a command
                    blo       YPosClamp nope less than command
                    lda       -$01,x    was a command load x back in acca
                    bra       RetSetCC  go set CC
YPosClamp           cmpb      #y_max    compare to 167
                    bls       YPosOk    is it less or same clear CC and return
                    ldb       #y_max    greater than load accb with 167
YPosOk              andcc     #$fe      clear CC and return
                    rts                 return carry clear = valid y coord


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

SbuffXLine          sta       <ScratchAC stow as x_orig
                    cmpa      <PosInitX  compare with pos_init_x position
                    bhs       XLineStart if pos_final_x same or greater branch

*                      otherwise init >  final so swap init and final
                    ldb       <PosInitX  load pos_init_x position
                    stb       <PosFinalX save pos_final_x position
                    sta       <PosInitX  save pos_init_x position

XLineStart          bsr       SbuffPlot head for sbuff_plot() returns pointer in u

                    ldb       <PosFinalX load pos_final_x
                    subb      <PosInitX  subtract pos_init_x position
                    beq       XLineDone if they are the same move on
*                      b now holds the loop counter len
*                      u is the pointer returned from sbuff_plot
                    leau      $01,u     bump the pointer one byte right
XLineLoop           lda       ,u        get the the byte
                    ora       <DrawMask  or it with sbuff_drawmmask
                    anda      <DrawColor and it with the color
                    sta       ,u+       save it back and bump u to next byte
                    decb                decrememnt the loop counter
                    bne       XLineLoop done them all? Nope loop

XLineDone           lda       <ScratchAC x_orig (pos_final_x)
                    sta       <PosInitX  save at pos_init_x position
                    rts                 horizontal line drawn return


* sbuff_yline() sbuf_util.c
* gets called here with pos_final_x/y in accd
*
*  DrawColor = color
*  DrawMask = sbuff_drawmask
*  PosInitX = pos_init_x
*  PosInitY = pos_init_y
*  PosFinalX = pos_final_x
*  PosFinalY = pos_final_y
*  ScratchAC = y_orig

SbuffYLine          stb       <ScratchAC stow as y_orig
                    cmpb      <PosInitY  compare with pos_init_y
                    bhs       YLineStart if pos_final same or greater branch

*                           otherwise init > final so swap 'em
                    lda       <PosInitY  load pos_init_y
                    sta       <PosFinalY stow as pos_final_y
                    stb       <PosInitY  stow as pos_init_y

YLineStart          bsr       SbuffPlot head for sbuff_plot() returns pointer in u
                    ldb       <PosFinalY load pos_final_y
                    subb      <PosInitY  subtract pos_init_y
                    beq       YLineDone if they are the same move on
*                           b now holds the loop counter len
*                           u is the pointer returned from sbuff_plot
YLineLoop           leau      PICBUFF_WIDTH,u bump ptr one line up
                    lda       ,u        get the byte
                    ora       <DrawMask  or it with sbuff_drawmmask
                    anda      <DrawColor and it with the color
                    sta       ,u        save it back out
                    decb                decrement the loop counter
                    bne       YLineLoop done them all ? Nope loop

YLineDone           ldb       <ScratchAC load y_orig
                    stb       <PosInitY  save it as pos_init_y
                    rts                 vertical line drawn return


* sbuff_plot()  from sbuf_util.c
* according to agi.h PBUF_MULT(width) ((( (width)<<2) + (width))<<5)
* which next 3 lines equate to so the $A0 is from 2 x 5
* pointer is returned in index reg u
*
*  DrawColor = color
*  DrawMask = sbuff_drawmask
*  PosInitX = pos_init_x
*  PosInitY = pos_init_y

SbuffPlot           ldb       <PosInitY  load pos_init_y
                    lda       #$A0      according to PBUF_MULT()
                    mul                 do the math
                    addb      <PosInitX  add pos_init_x position
                    adca      #0000     this adds the carry bit in to a
                    addd      <decodedbase add that to the start of the screen buf $6040
                    tfr       d,u       move this into u
                    lda       ,u        get the byte u points to
                    ora       <DrawMask  or it with sbuff_drawmask
                    anda      <DrawColor and it with the color
                    sta       ,u        and stow it back at the same place
                    rts                 return
