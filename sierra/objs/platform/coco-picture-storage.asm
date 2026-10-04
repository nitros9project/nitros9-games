* CoCo platform boundary: picture-storage.
* Included in place; see ../../PORTABILITY.md.

SbuffFill           pshs      x         save x as we use it for an index
                    ldu       #gbuffend address to write to
                    ldx       #picb_size $6900 bytes to write (26.25K)
*                      this would be picture buffer width x height
                    ldd       $04,s     since we pushed x pull our color input out of the stack
FillLoop            std       ,--u      store them and dec dest address
                    leax      -$02,x    dec counter
                    bne       FillLoop  loop till done
                    puls      x         fetch the x
                    rts                 return


* sbuff_xline()  sbuff_util.c
* gets called here with pos_final_x/y in accd
*
*  DrawColor = color
*  DrawMask = sbuff_drawmask
*  PosInitX = pos_init_x
*  PosInitY = pos_init_y
*  PosFinalX = pos_final_x
*  PosFinalY = pos_final_y
*  ScratchAC = x_orig

SbuffXLine          sta       ScratchAC stow as x_orig
                    cmpa      PosInitX  compare with pos_init_x position
                    bhs       XLineStart if pos_final_x same or greater branch

*                      otherwise init >  final so swap init and final
                    ldb       PosInitX  load pos_init_x position
                    stb       PosFinalX save pos_final_x position
                    sta       PosInitX  save pos_init_x position

XLineStart          bsr       SbuffPlot head for sbuff_plot() returns pointer in u

                    ldb       PosFinalX load pos_final_x
                    subb      PosInitX  subtract pos_init_x position
                    beq       XLineDone if they are the same move on
*                      b now holds the loop counter len
*                      u is the pointer returned from sbuff_plot
                    leau      $01,u     bump the pointer one byte right
XLineLoop           lda       ,u        get the the byte
                    ora       DrawMask  or it with sbuff_drawmmask
                    anda      DrawColor and it with the color
                    sta       ,u+       save it back and bump u to next byte
                    decb                decrememnt the loop counter
                    bne       XLineLoop done them all? Nope loop

XLineDone           lda       ScratchAC x_orig (pos_final_x)
                    sta       PosInitX  save at pos_init_x position
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

SbuffYLine          stb       ScratchAC stow as y_orig
                    cmpb      PosInitY  compare with pos_init_y
                    bhs       YLineStart if pos_final same or greater branch

*                           otherwise init > final so swap 'em
                    lda       PosInitY  load pos_init_y
                    sta       PosFinalY stow as pos_final_y
                    stb       PosInitY  stow as pos_init_y

YLineStart          bsr       SbuffPlot head for sbuff_plot() returns pointer in u
                    ldb       PosFinalY load pos_final_y
                    subb      PosInitY  subtract pos_init_y
                    beq       YLineDone if they are the same move on
*                           b now holds the loop counter len
*                           u is the pointer returned from sbuff_plot
YLineLoop           leau      PICBUFF_WIDTH,u bump ptr one line up
                    lda       ,u        get the byte
                    ora       DrawMask  or it with sbuff_drawmmask
                    anda      DrawColor and it with the color
                    sta       ,u        save it back out
                    decb                decrement the loop counter
                    bne       YLineLoop done them all ? Nope loop

YLineDone           ldb       ScratchAC load y_orig
                    stb       PosInitY  save it as pos_init_y
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

SbuffPlot           ldb       PosInitY  load pos_init_y
                    lda       #$A0      according to PBUF_MULT()
                    mul                 do the math
                    addb      PosInitX  add pos_init_x position
                    adca      #0000     this adds the carry bit in to a
                    addd      #gfx_picbuff add that to the start of the screen buf $6040
                    tfr       d,u       move this into u
                    lda       ,u        get the byte u points to
                    ora       DrawMask  or it with sbuff_drawmask
                    anda      DrawColor and it with the color
                    sta       ,u        and stow it back at the same place
                    rts                 return




* sbuff_picfill(u8 ypos, u8 xpos) sbuf_util.c
* DrawColor = color
* DrawMask = sbuff_drawmask
* PosInitX = pos_init_x
* PosInitY = pos_init_y
* PosFinalX = left
* PosFinalY = right
* ScratchA2 = old_direction
* ScratchA3 = direction
* ScratchA4 = old_initx
* ScratchA5 = old_inity
* ScratchA6 = old_left
* ScratchA7 = old_right
* ScratchA8 = stack_left
* ScratchA9 = stack_right
* ScratchAA = toggle
* ScratchAB = old_toggle
* FillColorBl = color_bl
* MaskDl = mask_dl
* OldBuff = old_buff (word)
* TempBuff = temp (buff)


colorbl             set       $4F
temp_stk            set       $E000

SbuffPicFill        pshs      x         save x
                    ldx       #temp_stk load addr to create a new stack
                    sts       ,--x      store current stack pointer there and decrement x
                    tfr       x,s       make that the stack
*                           s is now stack_ptr pointing to fill_stack

                    ldb       PosInitY  pos_init_y
                    lda       #$a0      set up PBUF_MULT
                    mul                 do the math
                    addb      PosInitX  add pos_init_x
                    adca      #0000     add in that carry bit
                    addd      #gfx_picbuff add the start of screen buffer $6040
                    tfr       d,u       move this to u
*                           u now is pointer to screen buffer b


                    ldb       DrawColor load color
                    lda       DrawMask  load sbuff_drawmask

*                           next 2 lines must have been a if (sbuff_drawmask > 0)
*                           not in the nagi source

                    lbeq      SbuffPicFillRet if sbuff_drawmask = 0 we're done
                    bpl       TestColorNibble if not negative branch to test color

                    cmpa      #cmd_start comp $F0 with sbuff_drawmask
                    bne       TestColorNibble not = go test color for $0F
                    andb      #$f0      and color with $F0
                    cmpb      #$40      compare that to $40 (input was $4x)
                    lbeq      SbuffPicFillRet if so were done
                    lda       #$f0      set up value for mask_dl
                    bra       SaveMaskDl go save it

TestColorNibble     andb      #$0f      and color with $0F
                    cmpb      #$0f      was it already $0F
                    lbeq      SbuffPicFillRet if so we're done
                    lda       #$0f      set up value for mask_dl

SaveMaskDl          sta       MaskDl    stow as mask_dl
                    anda      #colorbl  and that with $4F
                    sta       FillColorBl stow that as color_bl
                    lda       ,u        get byte at screen buffer
                    anda      MaskDl    and with mask_dl
                    cmpa      FillColorBl compare to color_bl
                    lbne      SbuffPicFillRet not equal were done

                    ldd       #$FFFF    push 7 $FF bytes on temp stack
                    pshs      a,b       and set stack_ptr accordingly
                    pshs      a,b       push two more FF bytes
                    pshs      a,b       push two more FF bytes
                    pshs      a         push final FF byte (7 total)

                    lda       #$a1      load a with 161
                    sta       PosFinalX stow it at left
                    clra                make a zero
                    sta       PosFinalY stow it at right
                    sta       ScratchAA stow it at toggle
                    inca                now we want a 1
                    sta       ScratchA3 stow it at direction

* fill a new line
FillNewLine         ldd       PosFinalX load left/right
                    std       ScratchA6 stow at old_left/right
                    lda       ScratchAA load toggle
                    sta       ScratchAB stow at old_toggle
                    ldb       PosInitX  load pos_init_x
                    stb       ScratchA4 store as old_initx
                    incb                accb now becomes counter
                    stu       OldBuff   stow current screen byte as old_buff

FillLeftLoop        lda       ,u        get the screen byte pointed to by u
                    ora       DrawMask  or it with sbuff_drawmmask
                    anda      DrawColor and that with the color
                    sta       ,u        stow that back
                    lda       ,-u       get the screen byte befor that one
                    anda      MaskDl    and that with mask_dl
                    cmpa      FillColorBl compare result with color_bl
                    bne       FillAdvance not equal move on
                    decb                otherwise decrement the counter
                    bne       FillLeftLoop if were not at zero go again

FillAdvance         leau      1,u       since cranked to zero bump the screen pointer by one
                    tfr       u,d       move that into d
                    subd      OldBuff   subtract old_buff
                    addb      PosInitX  add pos_init_x
                    stb       PosFinalX stow at left
                    lda       PosInitX  load pos_init_x
                    stb       PosInitX  store left at pos_init_x
                    stu       TempBuff  temp buff
                    ldu       OldBuff   load  old_buff
                    leau      1,u       bump to the next byte
                    nega                negate pos_init_x value
                    adda      #x_max    add that to 159 (subtract pos_init_x)
                    beq       ComputeRight that's the new counter and if zero move on

FillRightLoop       ldb       ,u        get that screen byte (color_old)
                    andb      MaskDl    and it with mask_dl
                    cmpb      FillColorBl check against color_bl
                    bne       ComputeRight not equal move on
                    ldb       ,u        load that byte again to do something with
                    orb       DrawMask  or it with sbuff_drawmmask
                    andb      DrawColor and it with color
                    stb       ,u+       stow it back and bump the pointer
                    deca                decrement the counter
                    bne       FillRightLoop if we haven't hit zero go again

ComputeRight        tfr       u,d       move the screen buff ptr to d
                    subd      TempBuff  subtract that saved old pointer
                    decb                sunbtract a 1
                    addb      PosFinalX add in the left
                    stb       PosFinalY store as the right
                    lda       ScratchA6 load old_left
                    cmpa      #$a1      compare to 161
                    beq       FillNextScan if it is move on

                    cmpb      ScratchA7 if the new right == old right
                    beq       EqualRightCheck then move on
                    bhi       UpdateOldRight not equal and right > old_right
*                           otherwise
                    stb       ScratchA4 stow right as old_initx
                    clr       ScratchAA clear toggle
                    bra       PushFillState head for next calc
*                           they were equal
EqualRightCheck     lda       PosFinalX load a with left
                    cmpa      ScratchA6 compare that to old_left
                    bne       UpdateOldRight move on
                    lda       #$01      set up a one
                    cmpa      ScratchAA compare toggle
                    beq       FillNextScan is a one ? go to locnext
                    sta       ScratchAA not one ? set it to 1
                    lda       PosFinalY load right
                    sta       ScratchA4 stow it as old_initx
                    bra       PushFillState head for the next calc
*                           right > old_right or left > old left
UpdateOldRight      clr       ScratchAA clear toggle
                    lda       ScratchA7 load old right
                    sta       ScratchA4 save as old_initx

*         push a bunch on our temp stack
PushFillState       ldy       ScratchA2 old_direction/direction
                    ldx       ScratchA4 old_initx/y
                    ldu       ScratchA6 old_left/right
                    lda       ScratchAB old_toggle
                    pshs      a,x,y,u   push them on the stack

locnext
FillNextScan        lda       ScratchA3 load direction
                    sta       ScratchA2 stow as old_direction
                    ldb       PosInitY  load pos_init_y
                    stb       ScratchA5 stow as old_inity

FillAdvanceDir      addb      ScratchA3 add direction to pos_init_y
                    stb       PosInitY  stow the updated pos_init_y
                    cmpb      #y_max    compare that to 167
                    bhi       FillTestDir greater than 167 go test direction

FillCalcAddr        ldb       PosInitY  load pos_init_y
                    lda       #$A0      according to PBUF_MULT
                    mul                 do the math
                    addb      PosInitX  add pos_init_x position
                    adca      #0000     this adds the carry bit into the answer
                    addd      #gfx_picbuff add that to the screen buff start addr $6040
                    tfr       d,u       move it into u
                    lda       ,u        get the byte pointed to
                    anda      MaskDl    and with mask_dl
                    cmpa      FillColorBl compare with color_bl
                    lbeq      FillNewLine if equal go fill a new line

                    lda       PosInitX  load pos_init_x
                    ldb       ScratchA3 load direction
                    cmpb      ScratchA2 compare to old_direction
                    beq       FillCheckRight go comapre pos_init_x and right
                    tst       ScratchAA test toggle
                    bne       FillCheckRight not zero go comapre pos_init_x and right
                    cmpa      ScratchA8 compare pos_init_x and stack_left
                    blo       FillCheckRight less than stack_left go comapre pos_init_x and right
                    cmpa      ScratchA9 compare it to stack_right
                    bhi       FillCheckRight greater than go comapre pos_init_x and right
                    lda       ScratchA9 load stack_right
                    cmpa      PosFinalY compare to right
                    bhs       FillTestDir greater or equal go check direction
                    inca                add one to stack_right
                    sta       PosInitX  stow as pos_init_x

FillCheckRight      cmpa      PosFinalY compare updated value to right
                    bhs       FillTestDir go check directions
                    inca                less than then increment by 1
                    sta       PosInitX  stow updated value pos_init_x
                    bra       FillCalcAddr loop for next byte

* test direction and toggle
FillTestDir         lda       ScratchA3 load direction
                    cmpa      ScratchA2 compare old_direction
                    bne       FillPopStack not equal go pull stacked values
                    tst       ScratchAA test toggle
                    bne       FillPopStack not zero go pull stack values
                    nega                negate direction
                    sta       ScratchA3 store back at direction
                    lda       PosFinalX load left
                    sta       PosInitX  stow as pos_init_x
                    ldb       ScratchA5 load old_inity
                    stb       PosInitY  stow at pos_init_y
                    bra       FillGetStackLR go grab off stack and move on

* directions not equal
FillPopStack        puls      a,x,y,u   grab the stuff off the stack
                    cmpa      #$FF      test toggle for $FF source has test of pos_init_y
                    beq       SbuffPicFillRet equal ? clean up stack and return
                    sty       ScratchA2 stow old_direction/direction
                    stx       PosInitX  stow pos_init_x/y
                    stu       PosFinalX stow left/right
                    sta       ScratchAA stow toggle

                    ldb       PosInitY  load pos_init_y
                    stb       ScratchA5 stow old_inity
FillGetStackLR      ldx       $05,s     gets left right  off stack
                    stx       ScratchA8 stow stack_left/right
                    bra       FillAdvanceDir always loop

SbuffPicFillRet     lds       ,s        reset stack
                    puls      x         retrieve our x
                    rts                 return
