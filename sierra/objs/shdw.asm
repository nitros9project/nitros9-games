                    use       buffer-layout.d

********************************************************************
* shdw - Sierra AGI screen rendering module
*
* Note the header shows a data size of 0 called from the sierra
* module and accesses data set up in that module.
*
* Much credit and thanks is give to Nick Sonneveld and the other NAGI
* folks. Following his sources made it so much easier to document what
* was happening in here.
*
* Edt/Rev  YYYY/MM/DD  Modified by
* Comment
* ------------------------------------------------------------------
*   0      2003/03/14  Paul W. Zibaila
* Disassembly of original distribution using a combination of disasm
* v1.6 and the os9tools disassembler Os9disasm.
* Annotated by /annotate-asm (Claude Code) 2026-05-12:
*   - Renamed disassembled labels to meaningful names
*   - Added inline comments to every instruction
* Annotated by /annotate-asm (Claude Code) 2026-05-14:
*   - Renamed disassembled equates (Xffa9→GimeMmuReg, X01af→StateFlag, X0551→GivenPicDataPtr)
*   - Fixed module description (removed KQ3-specific title — module is game-generic)
*   - Added ====== section headers throughout code body

                    nam       shdw
                    ttl       program module

                  IFP1
                    use       defsfile
                  ENDC

tylg                set       Prgrm+Objct
atrv                set       ReEnt+rev
rev                 set       $01
                    mod       eom,name,tylg,atrv,start,size

size                equ       .

GimeMmuReg          equ       $FFA9     GIME task-1 MMU register (maps $2000–$3FFF)
StateFlag           equ       $01AE     Sierra state.flag byte (ego signal / water / invis)
GivenPicDataPtr     equ       $0551     given_pic_data pointer (set by pic_res.c)


* OS9 data area definitions

ShdwMmuBlock        equ       $001A     shdw MMU block data
LoadOffset          equ       $002E     Load offset
SierraPdBlk         equ       $0042     Sierra process descriptor block
Sierra2ndBlk        equ       $0043     Sierra 2nd 8K data block
DrawColor           equ       $005A     color
DrawMask            equ       $005B     sbuff_drawmask
FlagControl         equ       $005C     flag_control
PenStatus           equ       $006B     pen_status

* these look like gen purpose scratch vars

PosInitX            equ       $00A0
PosInitY            equ       $00A1
PosFinalX           equ       $00A2
PosFinalY           equ       $00A3
ScratchA2           equ       $00A4
ScratchA3           equ       $00A5
ScratchA4           equ       $00A6
ScratchA5           equ       $00A7
ScratchA6           equ       $00A8
ScratchA7           equ       $00A9
ScratchA8           equ       $00AA
ScratchA9           equ       $00AB
ScratchAA           equ       $00AC
ScratchAB           equ       $00AD
ScratchAC           equ       $00AE
ScratchAD           equ       $00AF
FillColorBl         equ       $00B0
MaskDl              equ       $00B1
OldBuff             equ       $00B2
TempBuff            equ       $00B4
PriHeight           equ       $00B5




* VIEW OBJECTS FLAGS

O_DRAWN             equ       $01       * 0  - object has been drawn
O_BLKIGNORE         equ       $02       * 1  - ignore blocks and condition lines
O_PRIFIXED          equ       $04       * 2  - fixes priority agi cannot change it based on position
O_HRZNIGNORE        equ       $08       * 3  - ignore horizon
O_UPDATE            equ       $10       * 4  - update every cycle
O_CYCLE             equ       $20       * 5  - the object cycles
O_ANIMATE           equ       $40       * 6  - animated
O_BLOCK             equ       $80       * 7  - resting on a block
O_WATER             equ       $100      * 8  - only allowed on water
O_OBJIGNORE         equ       $200      * 9  - ignore other objects when determining contacts
O_REPOS             equ       $400      * 10 - set whenever a obj is repositioned
*                                that way the interpeter doesn't check it's next movement for one cycle
O_LAND              equ       $800      * 11 - only allowed on land
O_SKIPUPDATE        equ       $1000     * 12 - does not update obj for one cycle
O_LOOPFIXED         equ       $2000     * 13 - agi cannot set the loop depending on direction
O_MOTIONLESS        equ       $4000     * 14 - no movement.
*                                if position is same as position in last cycle then this flag is set.
*                                follow/wander code can then create a new direction
*                                (ie, if it hits a wall or something)
O_UNUSED            equ       $8000

* Local Program Defines

PICBUFF_WIDTH       equ       AgiPictureWidth ($A0)
PICBUFF_HEIGHT      equ       AgiPictureHeight ($A8)

picb_size           equ       CocoPictureBytes $6900
x_max               equ       PICBUFF_WIDTH-1 159 ($9F)
y_max               equ       PICBUFF_HEIGHT-1 167 ($A7)

gfx_picbuff         equ       CocoPictureBase combined picture/priority buffer
gbuffend            equ       CocoPictureEnd exclusive end $C940

blit_end            equ       gfx_picbuff+$6860

cmd_start           equ       $F0       first command value


* ====== Module Header ======
name                equ       *
ShdwName            fcs       'shdw'
                    fcb       $00

* This module is linked to in sierra

* ====== Dispatch Table: Function Entry Vectors ======
start               equ       *
DispatchTable       lbra      PicBufUpdateRemap gfx_picbuff_update_remap
                    lbra      ObjChkControl obj_chk_control
                    lbra      RenderPic render_pic  (which calls pic_cmd_loop)
                    lbra      PicCmdLoop pic_cmd_loop
                    lbra      ObjBlit   obj_blit
                    lbra      ObjAddPicPri obj_add_pic_pri
                    lbra      BlitRestore blit_restore
                    lbra      BlitSave  blit_save
                    lbra      SbuffFill sbuff_fill
                    lbra      BlitListDraw blitlist_draw
                    lbra      BlitListErase blitlist_erase

                    fcc       'AGI (c) copyright 1988 SIERRA On-Line'
                    fcc       'CoCo3 version by Chris Iden'
                    fcb       C$NULL

* ====== TwiddleMmu: Switch MMU Context for Sierra Data Block ======
* Twiddles with MMU
* accd is loaded by calling program
*
*  ShdwMmuBlock = shdw mem block data
*  SierraPdBlk = sierra process descriptor block
*  Sierra2ndBlk = Sierra 2nd 8K data block

* Platform mapping implementation; retained at its original location.
                    use       platform/picture-map.asm

LoadOffsetsFlag     fcb       $00       load offsets updated flag

* ====== Static Data Tables: BinaryList, CircleData, CircleList, CmdDispatchTable ======
* binary_list[] (pic_render.c)
                    use       shared/picture-pen-tables.asm

* select case dispatch table for pic_cmd_loop()

CmdDispatchTable    fdb       EnablePicDraw enable_pic_draw()
                    fdb       DisablePicDraw disable_pic_draw()
                    fdb       EnablePriDraw enable_pri_draw()
                    fdb       DisablePriDraw disable_pri_draw()
                    fdb       DrawYCorner draw_y_corner()
                    fdb       DrawXCorner draw_x_corner()
                    fdb       AbsoluteLine absolute_line()
                    fdb       RelativeLine relative_line()
                    fdb       PicFill   pic_fill()
                    fdb       ReadPenStatus read_pen_status()
                    fdb       PlotWithPen plot_with_pen()


* ====== AddLoadOffsets: Patch Command Dispatch Table on First Call ======
* This code adds the load offsets to the program offsets above
*
*  ScratchAB = loop counter
*
AddLoadOffsets      tst       LoadOffsetsFlag,pcr test if we've loaded the offsets already
                    bne       AddOffsetsDone done once leave
                    inc       LoadOffsetsFlag,pcr not done set the flag
                    lda       #$0b      set our index to 11
                    sta       ScratchAB stow it in mem since we are going to clobber b
                    leau      >CmdDispatchTable,pcr load table head address
AddOffsetLoop       ldd       LoadOffset get load offset set in sierra
                    addd      ,u        add the load offset
                    std       ,u++      and stow it back, bump pointer
                    dec       ScratchAB decrement the index
                    bne       AddOffsetLoop ain't done go again
AddOffsetsDone      rts                 we're out of here


* ====== RenderPic / PicCmdLoop: Main Picture Rendering Loop ======
* The interaction between render_pic and pic_cmd_loop is divided
* differently in the NAGI source pic_render.c

* render_pic()
* 4 = proirity and color = F, so the note says
* so the priority is MSnibble and the color is LSnibble

RenderPic           ldd       #$4f4f    load the color
                    pshs      d         push it on the stack for the pass
                    lbsr      SbuffFill call sbuff_fill routine
                    leas      $02,s     reset stack to value at entry
                    ldd       $02,s     pull the next word
                    pshs      d         push it on top of the stack
                    lbsr      PicCmdLoop call pic_cmd_loop()
                    leas      $02,s     once we return clean up stack again
                    rts                 return

* pic_cmd_loop() (pic_render.c)
*
*  DrawColor = color
*  DrawMask = sbuff_drawmask
*  PenStatus = pen_status

PicCmdLoop          pshs      y
                    bsr       AddLoadOffsets ensure load offset has been added to table address
                    lbsr      TableInit sbuff_fill()
                    clra                make a zero
                    sta       DrawMask  sbuff_drawmask
                    sta       PenStatus pen_status
                    coma                make the complement FF
                    sta       DrawColor store color

                    ldu       4,s       get the word passed in to us on the stack
                    ldd       5,u       pull out the required info for the mmu twiddle
                    lbsr      TwiddleMmu twiddle mmu

* pic_cmd_loop()  (pic_render.c) starts here
                    ldx       GivenPicDataPtr given_pic_data  set in pic_res.c
GetPicByte          lda       ,x+       pic_byte

ProcessPicByte      cmpa      #$ff      if it's FF were done
                    beq       PicCmdLoopRet so head out
                    suba      #cmd_start first valid cmd = F0 so subtract to get index
                    blo       GetPicByte less than F0 ignore it get next byte
                    cmpa      #$0a      check for top end
                    bhi       GetPicByte greater than FA ignore it get next byte
                    leau      >CmdDispatchTable,pcr load the addr of the dispatch table
                    asla                sign extend multiply by two for double byte offset
                    jsr       [a,u]     make the call
                    bra       ProcessPicByte loop again

PicCmdLoopRet       puls      y         done then fetch the y back
                    rts                 and return

* ====== Picture Draw Commands ($F0-$F3): Color and Priority Control ======
* Command $F0 change picture color and enable picture draw
*  enable_pic_draw() pic_render.c
*  differs slightly with pic_render.c
*  does't have colour_render()
*  and setting of colour_picpart
*
*  DrawColor = color
*  DrawMask = sbuff_drawmask
*
*  x contains pointer to given_pic_data known as the pic_byte
*  after ldd
*  a contains color
*  b contains draw mask
*  returns the next pic_byte in a

EnablePicDraw       ldd       DrawColor pulls in color and sbuff_drawmask
                    anda      #$f0      and color with $F0
                    ora       ,x+       or that result with the pic_byte and bump to next
                    orb       #$0f      or the sbuff_drawmask with $0F
                    std       DrawColor store the updated values
                    lda       ,x+       return value ignored so this just bumps to next pic_byte
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

DisablePicDraw      ldd       DrawColor pulls in color and sbuff_drawmask
                    ora       #$0f      ors color with $0F (white ??)
                    andb      #$f0      ands draw mask with $F0
                    std       DrawColor store the updated values
                    lda       ,x+       return value ignored so this just bumps to next pic_byte
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

EnablePriDraw       ldd       DrawColor pulls in color and sbuff_drawmask
                    anda      #$0f      ands color with $0F
                    sta       DrawColor save color
                    lda       ,x+       loads pic_byte and bumps to next
                    asla                times 2 with sign extend
                    asla                again times 2
                    asla                and again times 2
                    asla                end result is multiply pic_byte by 16 ($10)
                    ora       DrawColor or that value with the modified color
                    orb       #$f0      or the sbuff_drawmask with $F0
                    std       DrawColor store the updated values
                    lda       ,x+       return value ignored so this just bumps to next pic_byte
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


DisablePriDraw      ldd       DrawColor pulls in color and sbuff_drawmask
                    ora       #$f0      or the color with $F0
                    andb      #$0f      and the sbuff_drawmask with $0F
                    std       DrawColor store the updated values
                    lda       ,x+       return value ignored so this just bumps to next pic_byte
                    rts                 return to pic_cmd_loop

* ====== PlotWithPen / PlotWithPen2 ($FA): Splatter and Solid Pen Plotting ======
* Command $FA plot with pen
* Logic is pic_byte >= 0xF0 in c source.
* Emailed Nick Sonneveld 3/14/ 03
*
*  PenStatus = pen_status
*  ScratchA2 = pen_x position
*  ScratchA3 = pen_y position
*  ScratchA6 = texture_num
*
*  x contains pointer to given_pic_data known as the pic_byte
*  returns the next pic_byte in a

* plot_with_pen()  (pic_render.c)
PlotWithPen         lda       PenStatus pen_status
                    bita      #$20      and but don't change check for pen type solid or splater ($20)
                    beq       PlotWithPenCalc is splater
                    lda       ,x+       load pic_byte (acca) from pic_code and bump pointer
                    cmpa      #cmd_start test against $F0 if a is less than
*                      based on discussions with Nick this must have been a bug
*                      in the earlier versions of software...
*                      if it is less than $F0 it's just a picture byte
*                      fix next rev.
                    lbcc      CmdReturn branch to a return statement miles away (could be fixed)
                    sta       ScratchA6 save our pic_byte in texture_num
PlotWithPenCalc     lbsr      ReadXyPos call read_xy_postion
                    lblo      CmdReturn far off rts
                    std       ScratchA2 pen x/y position
                    fcb       $34,$10,$8D,$0B,$35,$10,$20,$DF
*      bsr   PlotWithPen2      call plot_with_pen2()
*      bra   PlotWithPen       go again ...
*                      yes there is no rts here in the c source either


* Command $F9 Change pen size and style
*  read_pen_status() pic_render.c
*
*  PenStatus = pen_status
*
*  x contains pointer to given_pic_data known as the pic_byte
*  returns the next pic_byte in a

ReadPenStatus       lda       ,x+       get pic_byte
                    sta       PenStatus save as pen_status
                    lda       ,x+       return value ignored so this just bumps to next pic_byte
                    rts                 return to pic_cmd_loop


* plot_with_pen2()
* called from plot with pen
*  Sets up circle_ptr
*
*  PenStatus = pen_status
*  PosInitX = pos_init_x
*  PosInitY = pos_init_y
*  ScratchA2 = pen_x position
*  ScratchA3 = pen_y position
*  ScratchA4 = pen_final_x
*  ScratchA5 = pen_final_y
*  ScratchA7 = pen.size
*  ScratchA8 = t
*  ScratchA9 = pensize x 2
*  ScratchAA =  "
*  ScratchAB = scratch var
*  ScratchAC = scratch var
*  ScratchAD = penwidth
*  FillColorBl =  "

                    use       shared/picture-pen.asm

* ====== Corner and Line Drawing Commands ($F4-$F7) ======
* Command $F5 Draw an X corner
* draw_x_corner()  pic_render.c
*
*  PosInitX = pos_init_x
*  PosInitY = pos_init_y

DrawXCorner         lbsr      ReadXyPos call read_xy_pos
                    bcs       CmdReturn next subs rts
                    std       PosInitX  save pos_init_x/y positions
                    lbsr      SbuffPlot head for sbuff_plot()
                    bsr       DrawXEntry draw_corner(0)
                    rts                 corner drawn return


* Command $F4 Draw a Y corner
* draw_y_corner()  pic_render.c
*
*  PosInitX = pos_init_x
*  PosInitY = pos_init_y

DrawYCorner         lbsr      ReadXyPos call read_xy_pos
                    bcs       CmdReturn return
                    std       PosInitX  save at pos_init_x/y positions
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
                    sta       PosFinalX store as pos_final_x
                    ldb       PosInitY  load pos_init_y
                    stb       PosFinalY store as pos_final_y
                    lbsr      SbuffXLine call sbuff_xline()

draw_y
DrawYEntry          lbsr      GetYPos   get_y_pos
                    bcs       CmdReturn prior subs return
                    stb       PosFinalY save pos_final_y
                    lda       PosInitX  load pos_init_x
                    sta       PosFinalX save pos_final_x
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

AbsoluteLine        bsr       ReadXyPos call read_xy_pos
                    bcs       CmdReturn prior subs return
                    std       PosInitX  save at pos_init_x/y positions
                    lbsr      SbuffPlot head for sbuff_plot()
AbsLineLoop         bsr       ReadXyPos call read_xy_pos
                    bcs       CmdReturn prior subs return
                    std       PosFinalX save at pos_final_x/y and passed draw_line in d
                    lbsr      DrawLine  call draw_line()
                    bra       AbsLineLoop go again



* relative_line()
*
*  PosInitX = pos_init_x
*  PosInitY = pos_init_y
*  PosFinalX = pos_final_x
*  PosFinalY = pos_final_y

RelativeLine        bsr       ReadXyPos call read_xy_pos
                    bcs       CmdReturn prior subs return
                    std       PosInitX  save at pos_init_x/y positions
                    lbsr      SbuffPlot head for sbuff_plot()

* calc x
RelLineLoop         lda       ,x+       get next pic_byte
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
XStepOk             adda      PosInitX  add pos_init_x position
                    cmpa      #x_max    compare to 159
                    bls       StorePosX if it's less or same move on
                    lda       #x_max    else cap it at 159
StorePosX           sta       PosFinalX store as pos_final_x

* calc y
*                      not quite the same as pic_render.c almost
*                      we've go the pic_byte ... er pos_data ... now called y_step
*                      in b so lets calc the y_step
                    andb      #$0f      and with $0F (not in pic_render.c)
                    bitb      #$08      and that with $08 but don't change
                    beq       AddYStep  if result = 0 move on
                    andb      #$07      else and it with $07
                    negb                and negate it
AddYStep            addb      PosInitY  add calced value to pos_init_y
                    cmpb      #y_max    compare to 167
                    bls       StorePosY less or same move on
                    ldb       #y_max    greater ? cap it
StorePosY           stb       PosFinalY pos_final_y

*                      passes pos_final_x/y in d
                    lbsr      DrawLine  call draw_line()

                    bra       RelLineLoop go again exit is conditinals inside loop

* ====== PicFill ($F8) / ReadXyPos / GetXPos / GetYPos: Fill and Coordinate Helpers ======
* Command $F8 Fill
* pic_fill()
*
*  PosInitX = pos_init_x
*  PosInitY = pos_init_y

PicFill             bsr       ReadXyPos call read_xy_pos
                    bcs       CmdReturn returned a 1 head for prior subs return
                    std       PosInitX  save at pos_init_x/y position
                    lbsr      SbuffPicFill call sbuff_picfill()
                    bra       PicFill   loop till we get a 1 back from read_xy_pos

* read_xy_pos()
                    use       shared/picture-coordinates.asm

* ====== DrawLine: Bresenham Line Rasterizer ======
* draw_line()  pic_render.c
* while this is a void function() seems pos_final_x/y are passed in d
*
*  PosInitX = pos_init_x
*  PosInitY = pos_init_y
*  PosFinalX = pos_final_x
*  PosFinalY = pos_final_y
*  ScratchA2 = x_count
*  ScratchA3 = y_count
*  ScratchA4 = pos_x
*  ScratchA5 = pos_y
*  ScratchA6 = line_x_inc
*  ScratchA7 = line_y_inc
*  ScratchA8 = x_component
*  ScratchA9 = y_component
*  ScratchAA = largest_line
*  ScratchAB = counter

*  process straight lines
                    use       shared/picture-line.asm

***********************************************************************


* ====== Screen Buffer Utilities: SbuffFill, SbuffXLine, SbuffYLine, SbuffPlot, SbuffPicFill ======
* sbuff_fill() sbuf_util.c
* fill color is passed in s register

* Platform implementation; selection emits no dispatch code.
                    use       platform/picture-storage.asm

* ====== PicBufUpdateRemap: Nibble-Swap Pixel Buffer for CoCo3 Display ======
* this routine effective swaps postion of
* the two nibbles of the byte loaded
* and returns it to the screen
* it is the workhorse loop in gfx_picbuff_update gfx.c ???
* called via remap call in mnln

* Platform implementation; selection emits no dispatch code.
                    use       platform/picture-orientation.asm

*  our blit_struct is a bit different from the one in nagi
*
* struct blit_struct
* {
*	struct blit_struct *prev;	// 0-1
*	struct blit_struct *next;	// 2-3
*	struct view_struct *v;		// 4-5
*	s8 x;                       // 6
*	s8 y;                       // 7
*	s8 x_size;                  // 8
*	s8 y_size;                  // 9
*	u16 *buffer;                // A-B
*   u16 *view_data              // C-D info for mmu twiddler
*
* };


* ====== Blit List Operations: BlitListErase / BlitListDraw ======
* blitlist_draw(BLIT *b) obj_base.c
BlitListErase       leas      -$02,s    make room on the stack
                    ldx       $04,s     get the blit_struct pointer
                    ldu       $02,x     load u with pointer to next blit

BlitListEraseLoop   stu       ,s        stow it on the stack
                    beq       BlitListEraseDone if it's zero we're done
                    pshs      u         push the pointer on the stack
                    lbsr      BlitSave  call blit_save()
                    leas      $02,s     get the pointer back in s
                    ldu       ,s        put it in u
                    ldu       $04,u     get the pointer to view_struct
                    pshs      u         push that on the stack and
                    lbsr      ObjBlit   call obj_blit()
                    leas      $02,s     get the pointer back in s
                    ldu       ,s        put it in u
                    ldu       $02,u     get the pointer to the next one
                    bra       BlitListEraseLoop and go again

BlitListEraseDone   leas      $02,s     clean up stack and leave
                    rts                 blit list erase done return

* blitlist_erase(BLIT *b) obj_base.c
* nagi has a return blitlist_free at the end

BlitListDraw        leas      -$02,s    make room on the stack
                    ldx       $04,s     get the blit_struct pointer
                    ldu       ,x        load u with the prev pointer
                    beq       BlitListDrawDone if it's zero we're done
BlitListDrawLoop    stu       ,s        stow it on the stack
                    pshs      u         push the pointer
                    lbsr      BlitRestore call blit_restore()
                    leas      $02,s     get the pointer back in s
                    ldx       ,s        load x with the pointer
                    ldu       ,x        get the prev from that struct
                    bne       BlitListDrawLoop loop again

BlitListDrawDone    leas      $02,s     clean up stack and leave
                    rts                 blit list draw done return

* ====== Priority Table and TableInit: Object Priority Zone Data ======
* From obj_picbuff.c the pri_table[172]
* ours is only 168
pri_table
PriTableBase

* loops thru 48 bytes with a = 4
* bumps a by one load b with 12 this
* iterates thru ten sets of twelve bytes
* bumping acca by one as it goes.

* table_init()   obj_pic_buff.c
TableInit

                    fcb       $B6,$05,$EE lda $05EE (priority table address)
                    fcb       $81,$FF   cmpa #$FF
                    fcb       $26,$15   bne +21
                    fcb       $8E,$05,$EE ldx #$05EE (set x to table address)
                    ldb       #$30      load index 48
                    lda       #4        load acca = 4
TableInitLoop       sta       ,x+       save a in buffer
                    decb                dec the inner loop counter
                    bne       TableInitLoop go again if loop not finished
                    cmpa      #$0e      get here when inner loop is done
                    bcc       TableInitDone did we do 10 loops (e-4)
                    inca                nope bump data byte
                    ldb       #$0c      set new counter on loops 2-10
*                       to do 12 bytes and
                    bra       TableInitLoop have at it again
TableInitDone       rts                 priority table initialized return


* ====== ObjChkControl: Check Object Contacts with Priority Zones ======
* obj_chk_control(VIEW *x)  obj_picbuff.c
* our index reg x points to the view structure
* are 3 = x, 4 = y instead of 3-4 = x & 5-6 = y ???

* This routine is passed a pointer to a view_structure
* from agi.h in the nagi source
* struct view_struct
*{
*	u8 step_time;		// 0
*	u8 step_count;		// 1	// counts down until the next step
*	u8 num;				// 2

*	     s16 x;	        // 3-4  in nagi
*	     s16 y;         // 5-6  in nagi


*   u8 x;               // 3 in ours
*   u8 y:               // 4 the rest of the offsets hold true
*   u8 dummy1           // 5 who knows what these are
*   u8 dummy2           // 6 maybe just fillers


*	u8 view_cur;		// 7
*	u8 *view_data;		// 8-9
*
*	u8 loop_cur; 		// A
*	u8 loop_total;		// B
*	u8 *loop_data;		// C-D
*
*	u8 cel_cur;			// E
*	u8 cel_total;		// F
*	u8 *cel_data; 		// 10-11
*	u8 cel_prev_width;	// new ones added to prevent kq4 crashing
*	u8 cel_prev_height;
*	//u8 *cel_data_prev;// 12-13
*	BLIT *blit;			// 14-15
*
*	s16 x_prev;			// 16-17
*	s16 y_prev;			// 18-19
*	s16 x_size;			// 1A-1B
*	s16 y_size;			// 1C-1D
*	u8 step_size;		// 1E
*	u8 cycle_time; 		// 1F
*	u8 cycle_count;		// 20	// counts down till next cycle
*	u8 direction;		// 21
*	u8 motion;			// 22
*	u8 cycle;			// 23
*	u8 priority;		// 24
*	u16 flags;			// 25-26
*
*	//u8 unknown27;		// 27	// these variables depend on the motion
*	//u8 unknown28;		// 28	// type set by follow ego, move, obj.. stuff
*	//u8 unknown29;		// 29	// like that
*	//u8 unknown2A;		// 2A
*
*	union
*	{
*		struct	// move_ego move_obj
*		{
*			s16 x;			// 27
*			s16 y;			// 28
*			u8 step_size;	// 29	// original stepsize
*			u8 flag;		// 2A
*		} move;
*
*		struct	// follow_ego
*		{
*			u8 step_size;	// 27
*			u8 flag;		// 28
*			u8 count;		// 29
*		} follow;
*
*		// wander
*		u8 wander_count;	// 27
*
*		// reverse or end of loop
*		u8 loop_flag;		// 27
*	};
*};
*typedef struct view_struct VIEW;


*  ScratchA5 = flag_signal
*  ScratchA6 = flag_water
*  FlagControl = flag_control
*
*  StateFlag is location of state.flag
*  see agi.h for definition of state structure
* Platform implementation; selection emits no dispatch code.
                    use       platform/object-storage.asm

                    fcb       $00,$00,$00,$00
                    fcb       $00,$00,$00,$00
                    fcc       "shdw"
                    fcb       $00

                    emod
eom                 equ       *
                    end

