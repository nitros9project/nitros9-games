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

                    use       shared/picture-coordinates.asm

                    use       shared/picture-line.asm
                    use       platform/picture-storage.asm
