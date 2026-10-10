* coco-graphics feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_COCO_GAME_PALETTE_DATA
* ===== coco-game-palette-data =====
* CoCo screen backend: game-palette-data.
* Included in place; see ../../PORTABILITY.md for the current contract.

PaletteData         fcb       $00       composite
                    fcb       $0C
                    fcb       $02
                    fcb       $2E
                    fcb       $06
                    fcb       $09
                    fcb       $04
                    fcb       $20
                    fcb       $10
                    fcb       $1B
                    fcb       $11
                    fcb       $3D
                    fcb       $17
                    fcb       $29
                    fcb       $33
                    fcb       $3F

                    fcb       $00       rgb
                    fcb       $08
                    fcb       $14
                    fcb       $18
                    fcb       $20
                    fcb       $28
                    fcb       $22
                    fcb       $38
                    fcb       $07
                    fcb       $0B
                    fcb       $16
                    fcb       $1F
                    fcb       $27
                    fcb       $2D
                    fcb       $37
                    fcb       $3F

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_GAME_PALETTE_SET
* ===== coco-game-palette-set =====
* CoCo screen backend: game-palette-set.
* Included in place; see ../../PORTABILITY.md for the current contract.

cmd_toggle_monitor  leas      -$04,s    ; allocate 4-byte local frame
                    pshs      y         ; save script pointer
                    leax      >PaletteData,pcr ; point to palette table
                    ldb       >$0553    ; get current monitor mode
                    eorb      #$01      ; toggle between composite and RGB
                    stb       >$0553    ; store new mode
                    lda       #$10      ; 16 entries per palette
                    mul                 ; A*16 = palette offset
                    abx                 ; X = pointer to selected palette
                    lda       #$1B
                    sta       $02,s     ; ESC char for palette command
                    lda       #$31
                    sta       $03,s     ; '1' palette command byte
                    clra                ; A = 0 (initial color index)
                    sta       $04,s     ; color index start = 0
                    ldy       #$0004    ; path number 4 (screen)
PaletteWriteLoop    ldb       ,x+       ; fetch palette entry
                    stb       $05,s     ; store for write
                    pshs      x         ; save palette pointer
                    lda       #$01      ; write 1 byte
                    leax      $04,s     ; X = pointer to color byte
                    os9       I$Write   ; write palette command byte
                    bcs       PaletteWriteRet ; write failed
                    puls      x         ; restore palette pointer
                    inc       $04,s     ; increment color index
                    lda       $04,s     ; load color index
                    cmpa      #$10      ; compare to 16 (all colors)
                    bcs       PaletteWriteLoop ; not done, continue
PaletteWriteRet     puls      y         ; restore script pointer
                    leas      $04,s     ; release local frame
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_MONITOR_SELECT
* ===== coco-monitor-select =====
* CoCo screen backend: monitor-select.
* Included in place; see ../../PORTABILITY.md for the current contract.

ConfigureMonitor
*  get current montype
*  GetStat Function Code $92
*          Allocates and maps high res screen
*          into application address space
* entry:
*       a -> path number
*       b -> function code $92 (SS.Montr)
*
* exit:
*       x -> monitor type
*
* error:
*       CC -> Carry set on error
*       b  -> error code (if any)
*
                    lda       #StdOut   $01 path number
                    ldb       #SS.Montr monitor type code (not listed for getstat $92
                    os9       I$GetStt  make the call
                    bcs       ConfigureMonitorRet
                    tfr       x,d       save in d appears he expects montype returned
                    lda       >RgbRequested
                    beq       UseOriginalMonitor
                    ldb       #RGB
UseOriginalMonitor  andb      #$01      mask out mono type only RGB or COMP
                    stb       >$0553    save that value off as display_type

                    clrb                success; global monitor mode is untouched

ConfigureMonitorRet rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_PICTURE_MAP
* ===== coco-picture-map =====
* CoCo memory backend: picture-map.
* Included in place to preserve code addresses and instruction timing.
* See ../../PORTABILITY.md for dependencies and current contract.

TwiddleMmu          cmpa      ShdwMmuBlock compare to shdw mem block
                    beq       TwiddleMmuDone equal ?? no work to be done move on
                    orcc      #IntMasks turn off interupts
                    sta       ShdwMmuBlock store the value passed in by a
                    lda       SierraPdBlk get sierra process descriptor map block
                    sta       GimeMmuReg map it in to $2000-$3FFF
                    ldu       Sierra2ndBlk 2nd 8K data block in Sierra
                    lda       ShdwMmuBlock load my mem block value
                    sta       ,u        save my values at address held in Sierra2ndBlk
                    stb       $02,u     save block value byte 2
                    std       GimeMmuReg map it to task 1 block 2
                    andcc     #^IntMasks restore the interupts
TwiddleMmuDone      rts                 we done

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_PICTURE_ORIENTATION
* ===== coco-picture-orientation =====
* CoCo platform boundary: picture-orientation.
* Included in place; see ../../PORTABILITY.md.

gfx_picbuff_update_remap
PicBufUpdateRemap   ldx       #gfx_picbuff starting low address of srceen mem
NibbleSwapLoop      lda       ,x        get the first byte  bit order 0,1,2,3,4,5,6,7
                    clrb                empty b
                    lsra                shift one bit from a
                    rorb                into b
                    lsra                shift second bit from a
                    rorb                rotate into b
                    lsra                and again
                    rorb                rotate into b
                    lsra                and finally once more
                    rorb                nibble swap complete in b
                    stb       ,x        were changing x anyway so use it for temp storage
                    ora       ,x        or that with acca so now bit order from orig
*                        is 4,5,6,7,0,1,2,3
                    sta       ,x+       put it back at x and go for the next one
                    cmpx      #gbuffend ending high address of screen mem
                    bcs       NibbleSwapLoop loop until entire buffer remapped
                    rts                 buffer remap complete return

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_PICTURE_STORAGE
* ===== coco-picture-storage =====
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

                    PICTURE_FILL_SELECT b,SbuffPicFillRet,TestColorNibble,SaveMaskDl,0,1

                    sta       MaskDl    stow as mask_dl
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

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_PRESENTATION
* ===== coco-presentation =====
* CoCo platform boundary: presentation.
* Included in place; see ../../PORTABILITY.md.

gfx_picbuff_update  tst       >GfxPicBufRotate test UI nibble-swap mode
                    beq       GfxUpdateBlit skip swap in normal picture mode
                    lda       #$00      shdw dispatch 0: swap combined-byte nibbles in place
                    sta       <$0021    store twiddle opcode
                    ldx       <$0028    load shadow copy context ptr
                    jsr       >$0701    execute in-place nibble swap; not a buffer copy
*
*======================================================================
* SCREEN BLIT
*   Triggers a full-screen blit from the shadow buffer to the display by
*   calling the scrn module's update routine.
*======================================================================
*
GfxUpdateBlit       ldd       #$A8A0    blit destination row/col
                    pshs      b,a       push destination argument
                    ldd       #$00A7    blit source descriptor
                    pshs      b,a       push source argument
                    lda       #$00      MMU twiddle opcode $00 = blit
                    sta       <$0019    store twiddle opcode
                    ldx       <$0026    load blit context pointer
                    jsr       >$0701    execute screen blit
                    leas      $04,s     discard two arguments
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_PRIORITY_ADDRESS
* ===== coco-priority-address =====
* CoCo platform boundary: priority-address.
* Included in place; see ../../PORTABILITY.md.

CalcPriAddr         suba      <$005F    subtract priority base row offset
                    ldb       #$20      bytes per priority strip = 32
                    mul                 A×32 = byte offset into strip
                    exg       b,a       swap bytes (shift left 8)
                    subd      #$2000    subtract $2000 for final addr
                    leau      d,u       advance U by computed offset
                    rts
*
*======================================================================
* PRIORITY COORDINATE CALCULATION
*   Converts a screen Y coordinate to a priority value and maps a view's
*   logic page into the address space.
*======================================================================
*
CalcPriCoord        tfr       u,d       transfer priority address to D
                    anda      #$1F      isolate column within strip
                    adda      #$20      add $20 base column
                    exg       d,u       swap D and U
                    lsra                shift right (divide by 2)
                    lsra                shift right
                    lsra                shift right
                    lsra                shift right
                    lsra                shift right (divide by 32)
                    adda      <$005F    add priority base row to result
                    tfr       a,b       copy row to B
                    incb                increment for 1-based row
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_RENDER_SPANS
* ===== coco-render-spans =====
* CoCo packed-pixel renderer: render-spans.
* Keep optimized loops intact. See ../../PORTABILITY.md.

CocoViewPal         fcb       $00
                    fcb       $11
                    fcb       $22
                    fcb       $33
                    fcb       $44
                    fcb       $55
                    fcb       $66
                    fcb       $77
                    fcb       $88
                    fcb       $99
                    fcb       $AA
                    fcb       $BB
                    fcb       $CC
                    fcb       $DD
                    fcb       $EE
                    fcb       $FF


* Clears the area allocated to the screen in sierra
* entry:
*      d -> value to be written to screen
*      x -> may contain a value so we save it
* exit:
*      d -> preserved
*      x -> restored to initial value
*      u -> contains starting address of the screen

ClearScreen         pshs      x         save the x values as this routine uses it
ClearScreenInit     ldu       #CocoFrameEnd    end address of high res screen
                    ldx       #CocoFrameBytes    Scrn is from $6000 to $D800
ClearWordLoop       std       ,--u      set it to value passed us in d & dec d
                    leax      -$02,x    decrement x
                    bne       ClearWordLoop keep going till all of screen is cleared
                    puls      x         restore x`
                    rts                 move on

* Loads D to clear screen
ZeroClearScreen     ldd       #$0000    zeros screen bytes
                    bsr       ClearScreen go clear it
                    rts

ClearScreenBlack    bsr       ZeroClearScreen clear screen to black
                    ldd       #$A8A0    Y2=$A8, Y1=$A0 (screen rows)
                    pshs      d         push row args onto stack
                    ldd       #$00A7    X2=$00, X1=$A7 (screen columns)
                    pshs      d         push column args onto stack
                    lbsr      DrawStrip
                    leas      $04,s     pop 4 bytes of args
                    rts

ClearWithPalette    lda       >SierraPalette load palette color byte
                    tfr       a,b       duplicate into both bytes of D
                    bsr       ClearScreen fill screen with that color word
                    ldd       #$0000    clears value at SprCurRow
                    std       <SprCurRow reset sprite row/col position
                    rts

DrawBorder          ldd       $06,s     load top-left row arg
                    pshs      d         push row start
                    ldd       $06,s     reload arg (stack shifted)
                    pshs      d         push row end
                    ldd       $06,s     reload arg (stack shifted)
                    pshs      d         push color arg
                    lbsr      FillSolidRect draw top edge
                    leas      $06,s     pop 6 bytes of args
                    clra                A=0 for column start
                    ldb       $06,s     load height arg
                    pshs      d         push row params
                    lda       #$01      col start = 1
                    ldb       $07,s     load height (stack adjusted)
                    subb      #$02      subtract 2 to skip top/bottom
                    pshs      d         push height-2
                    ldd       $06,s     load position arg
                    inca                advance row by 1
                    decb                reduce column by 1
                    pshs      d         push adjusted position
                    lbsr      FillSolidRect draw left edge
                    leas      $06,s     pop 6 bytes of args
                    clra                A=0 for column start
                    ldb       $06,s     load next arg
                    pshs      d         push row
                    lda       $06,s     load X position
                    suba      #$04      subtract 4 for right edge position
                    ldb       #$01      column width = 1
                    pshs      d         push right edge position
                    ldd       $06,s     load base position
                    adda      $09,s     add height to get bottom
                    suba      #$02      adjust for edges
                    subb      #$02      adjust column
                    pshs      d         push bottom position
                    lbsr      FillSolidRect draw right edge
                    leas      $06,s     pop 6 bytes of args
                    clra                A=0
                    ldb       $06,s     load arg
                    pshs      d
                    lda       #$01      col start = 1
                    ldb       $07,s
                    subb      #$02      height - 2
                    pshs      d
                    ldd       $06,s
                    inca                advance row
                    subb      $08,s     subtract width
                    addb      #$02      adjust for border
                    pshs      d
                    lbsr      FillSolidRect draw bottom-left corner edge
                    leas      $06,s     pop 6 bytes of args
                    clra
                    ldb       $06,s
                    pshs      d
                    lda       $06,s
                    suba      #$04
                    ldb       #$01
                    pshs      d
                    ldd       $06,s
                    inca
                    subb      #$02
                    pshs      d
                    lbsr      FillSolidRect draw bottom edge
                    leas      $06,s     pop 6 bytes of args
                    rts

SetupDrawStrip      ldd       $04,s     load row args from caller's frame
                    pshs      d         push first arg
                    ldd       $04,s     reload same arg (stack shifted)
                    pshs      d         push second arg
                    lbsr      DrawStrip
                    leas      $04,s     pop 4 bytes of args
                    rts

* first call in module is here
* who put what on the stack for us ?
DrawStrip           pshs      y         save Y (module entry absolute address)

                    ldd       $04,s     load row/column args
                    sta       <ScrAddrLo save row as screen address low byte
                    incb                B = bottom row + 1
                    subb      $06,s     B = height of strip in rows
                    lda       #CocoFrameStride A = 160 (bytes per screen row)
                    mul                 D = height × 160
                    addd      <ScrAddrHi add hi-res screen high byte
                    tfr       d,x       X = source pixel address
                    addd      <HiResBase add screen base offset
                    tfr       d,y       Y = destination screen address
                    leax      <$40,x    advance X by $40 (source offset)
                    ldd       $06,s     load strip dimension
                    std       <RowCount save row count and strip width

                    ldb       #CocoFrameStride B = 160 (full row width)
                    subb      <StripWidth B = stride = 160 - strip pixel width
                    clra                clear A for full D
                    std       <RowStride save row stride
                    sta       <MmuBlkNum clear MMU block tracking variable

                    orcc      #IntMasks disable interrupts
                    lda       <SierraPdBlk load Sierra process descriptor block#
                    sta       >DatTask1Slot1 second block in task 1
                    cmpx      #$A000    check if X is in high 8K window
                    bcs       MapBlockLow branch if X < $A000 (low window)

                    ldd       <BlkMapHigh load high-address block map entry
                    leax      >-$8000,x adjust X for high window (-$8000)
                    bra       MapBlockAndRender
MapBlockLow         ldd       <BlkMapLow load low-address block map entry
                    leax      >-$4000,x adjust X for low window (-$4000)
MapBlockAndRender   ldu       <Sierra2ndBlk load Sierra 2nd 8K data block ptr
                    sta       ,u        store block A at slot 0
                    stb       $02,u     store block B at slot 2
                    std       >DatTask1Slot1 map block into task 1
                    andcc     #^IntMasks re-enable interrupts

                    leau      >CocoViewPal,pcr point U to CoCo view palette table
DrawRowOuter        ldb       <StripWidth load pixel count for this row
DrawPixelInner      lda       ,x+       fetch source pixel byte, advance X
                    anda      #$0F      mask to 4-bit palette index
                    lda       a,u       translate through CoCo palette
                    sta       ,y+       write translated pixel, advance Y
                    decb                one fewer pixel this row
                    bne       DrawPixelInner loop until row complete
                    dec       <RowCount one fewer row remaining
                    beq       DrawStripDone pull our y and exit routine
                    ldd       <RowStride load row stride
                    leay      d,y       advance Y to next screen row
                    abx                 advance X by B (stride)
                    cmpx      #CocoFrameBase    check if X wrapped below screen base
                    bcs       DrawRowOuter branch if still in range

                    orcc      #IntMasks disable interrupts for block remap
                    lda       <SierraPdBlk reload Sierra PD block#
                    sta       >DatTask1Slot1 second block in task 1
                    ldd       <BlkMapHigh load high block map for remap
                    leax      >-$4000,x adjust X by -$4000 for new window
                    bra       MapBlockAndRender remap and continue rendering
DrawStripDone       puls      y         restore Y
                    rts


FillSolidRect       ldd       $02,s     load row/column args from stack
                    sta       <ScrAddrLo save row as screen address low
                    incb                B = bottom row + 1
                    subb      $04,s     B = strip height
                    lda       #CocoFrameStride A = 160
                    mul                 D = height × 160
                    addd      <ScrAddrHi Hi res screen mem address ($6000)
                    addd      <HiResBase add base screen offset
                    tfr       d,x       X = starting screen address
                    ldd       $04,s     load dimension arg
                    std       <RowCount save row count / strip width
                    ldb       #CocoFrameStride B = 160
                    subb      <StripWidth B = stride = 160 - strip width
                    stb       <RowStride save row stride
                    leau      >CocoViewPal,pcr point U to CoCo palette table
                    lda       $07,s     load fill color index
                    anda      #$0F      mask to 4-bit palette index
                    lda       a,u       look up translated fill color

FillRowOuter        ldb       <StripWidth pixels to fill in this row
FillPixelInner      sta       ,x+       write fill color, advance X
                    decb                one fewer pixel this row
                    bne       FillPixelInner loop until row filled

                    dec       <RowCount one fewer row remaining
                    beq       FillRectDone done when all rows filled
                    ldb       <RowStride load row stride
                    abx                 advance X to next row
                    bra       FillRowOuter fill next row
FillRectDone        rts


CopyStrip           leas      -$04,s    allocate 4 scratch bytes on stack
                    ldd       $0A,s     load destination arg (shifted by alloc)
                    std       $02,s     stash destination in scratch[2]
                    ldd       $08,s     load source arg
                    std       ,s        stash source in scratch[0]
                    lda       $07,s     load destination row
                    lsla                row × 2
                    lsla                row × 4
                    lsla                row × 8
                    ldb       #CocoFrameStride B = 160
                    mul                 D = row × 8 × 160 = row × 1280
                    std       <DrawY1   save Y pixel offset for destination
                    clra                clear A
                    ldb       $01,s     load scratch[1]
                    lslb                × 2
                    lslb                × 4 (column × 4 bytes per glyph col)
                    addd      <DrawY1   add Y offset to screen address
                    tfr       d,u       transfer result to U (source pointer)
                    leau      >CocoFrameBase,u  add screen base $6000
                    ldb       $02,s     load scratch[2]
                    lslb                × 2
                    lslb                × 4
                    lslb                × 8 (source col × 8)
                    lda       #CocoFrameStride A = 160
                    mul                 D = source col × 8 × 160
                    leax      d,u       X = source screen address
                    lda       $03,s     load source row
                    lsla
                    lsla
                    lsla                source row × 8
                    ldb       ,s        load scratch[0] (src col)
                    subb      $01,s     subtract scratch[1] (dest col)
                    incb                +1 for pixel width
                    lslb                × 2
                    lslb                × 4
                    abx                 advance X by col delta
                    exg       u,x       swap src/dst pointers
                    abx                 advance X (was U) by col delta
                    exg       u,x       swap back
CopyRowOuter        pshs      u,x,b,a   save pointers, col count, row count
CopyPixelInner      lda       ,-x       read source pixel (reverse scan)
                    sta       ,-u       write to destination (reverse scan)
                    decb                step back one pixel
                    bne       CopyPixelInner loop until col count zero
                    puls      u,x,b,a   restore pointers and counts
                    leau      >$00A0,u  advance U to next source row
                    leax      >$00A0,x  advance X to next dest row
                    cmpx      #CocoFrameEnd    check if X reached screen end
                    bcc       CopyStripDone done if past end of screen
                    deca                one fewer row
                    bne       CopyRowOuter loop while rows remain
CopyStripDone       leas      $04,s     free scratch bytes
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_RENDER_VIEW
* ===== coco-render-view =====
* CoCo packed-pixel renderer: render-view.
* Keep optimized loops intact. See ../../PORTABILITY.md.

DrawView            lda       >PicVisible pic_visible
                    lbeq      DrawViewDone skip draw if picture not visible
                    ldu       $02,s     load view structure pointer
                    ldd       $08,u     load block number from view struct
                    lbsr      SetMapBlock map the block for source data
                    ldx       <$10,u    load pointer from view struct offset $10
                    ldd       ,x        load word at that pointer (view width)
                    std       <RowStride save as row stride
                    ldd       <$14,u    load block number from view+$14
                    lbsr      SetMapBlock map the second block
                    ldx       <$12,u    load pointer from view struct offset $12
                    ldd       ,x        load word at that pointer (view height)
                    std       <RowCount save as row count
                    ldd       <$10,u    reload view+$10
                    std       <$12,u    update view+$12 with it
                    ldd       $08,u     reload view block number
                    std       <$14,u    update view+$14 with it
                    lda       $04,u     load view X position
                    ldb       <ViewRightX load right-edge clip X
                    cmpa      <$1B,u    compare X with view's prev X
                    bcs       ClipXSmall branch if cur X < prev X
                    sta       <ClipLeft save X as left clip boundary
                    stb       <ClipRight save right-edge as clip right
                    lda       <$1B,u    load previous X
                    ldb       <StripWidth load strip pixel width
                    bra       ComputeClipWidth
ClipXSmall          ldb       <$1B,u    load previous X as left clip
                    stb       <ClipLeft save as left boundary
                    ldb       <StripWidth load strip width
                    stb       <ClipRight save as right boundary
                    ldb       <ViewRightX load right-edge X
ComputeClipWidth    stb       <OverlapLeft save overlap left boundary
                    inca                A = cur X + 1
                    suba      <OverlapLeft A = overlap width candidate
                    ldb       <ClipLeft load clip left
                    incb                B = ClipLeft + 1
                    subb      <ClipRight B = clip width
                    stb       <ClipWidth save clip width
                    cmpa      <ClipWidth compare overlap vs clip width
                    bcs       AdjustClipWidth use clip width if overlap is smaller
                    lda       <ClipWidth use clip width as limit
AdjustClipWidth     nega                negate to invert
                    adda      <ClipLeft A = ClipLeft - overlap width
                    inca                adjust for final right clip
                    sta       <ClipRight save computed clip right
                    lda       $03,u     load view Y position
                    ldb       <RowStride load row stride
                    cmpa      <$1A,u    compare Y with view's prev Y
                    bhi       ClipYGreater branch if cur Y > prev Y
                    sta       <DrawY1   save Y as top of draw region
                    stb       <OverlapTop save row stride as overlap top
                    lda       <$1A,u    load previous Y
                    ldb       <RowCount load row count
                    bra       ComputeClipHeight
ClipYGreater        ldb       <$1A,u    load previous Y as draw start
                    stb       <DrawY1   save as top of draw region
                    ldb       <RowCount load row count
                    stb       <OverlapTop save as overlap top
                    ldb       <RowStride load row stride
ComputeClipHeight   stb       <OverlapSize save overlap size
                    adda      <OverlapSize A = Y + overlap = bottom extent
                    sta       <ClipBottom save as clip bottom
                    lda       <DrawY1   load draw start Y
                    adda      <OverlapTop add overlap top to get draw bottom
                    cmpa      <ClipBottom compare against clip bottom
                    bhi       SetupDrawCall use draw bottom if it exceeds clip
                    lda       <ClipBottom use clip bottom as limit
SetupDrawCall       suba      <DrawY1   height = bottom - top
                    sta       <ClipHeight save computed clip height
                    ldd       <ClipRight load clip right/left pair
                    pshs      b,a       push column args for DrawStrip
                    ldd       <DrawY1   load draw Y start / clip height
                    pshs      b,a       push row args for DrawStrip
                    lbsr      DrawStrip render clipped view to screen
                    leas      $04,s     pop 4 bytes of args
DrawViewDone        rts

* This jumbled mass of bytes disassembles
* but looks like a data block
* or probably a bit map ???
* BitmapFont - DrawSprites is 1024 bytes of data

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_SCREEN_COLORS
* ===== coco-screen-colors =====
* CoCo screen backend: screen-colors.
* Included in place; see ../../PORTABILITY.md for the current contract.

ColorTable          fcb       $00       composite
                    fcb       $0C
                    fcb       $02
                    fcb       $2E
                    fcb       $06
                    fcb       $09
                    fcb       $04
                    fcb       $20
                    fcb       $10
                    fcb       $1B
                    fcb       $11
                    fcb       $3D
                    fcb       $17
                    fcb       $29
                    fcb       $33
                    fcb       $3F

                    fcb       $00       rgb
                    fcb       $08
                    fcb       $14
                    fcb       $18
                    fcb       $20
                    fcb       $28
                    fcb       $22
                    fcb       $38
                    fcb       $07
                    fcb       $0B
                    fcb       $16
                    fcb       $1F
                    fcb       $27
                    fcb       $2D
                    fcb       $37
                    fcb       $3F

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_SCREEN_MAP
* ===== coco-screen-map =====
* CoCo memory backend: screen-map.
* Included in place to preserve code addresses and instruction timing.
* See ../../PORTABILITY.md for dependencies and current contract.

SetMapBlock         cmpa      <MmuBlkNum check MMU block
                    beq       MapBlockOk if block 0  OK to leave
                    orcc      #IntMasks Turn off interrupts
                    sta       <MmuBlkNum store the value passed in by a
                    lda       <SierraPdBlk get sierra process descriptor map block
                    sta       >DatTask1Slot1 map it in to $2000-$3FFF
                    ldx       <Sierra2ndBlk 2nd 8K data block in Sierra
                    lda       <MmuBlkNum get mmu block num
                    sta       ,x        store block number at slot 0
                    stb       $02,x     store block number at slot 2
                    std       >DatTask1Slot1 Map it into task 1 block 2
                    andcc     #^IntMasks turn on interrupts $AF
MapBlockOk          rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_SCREEN_RESTORE
* ===== coco-screen-restore =====
* CoCo screen backend: screen-restore.
* Included in place; see ../../PORTABILITY.md for the current contract.

RestoreScreen       leas      -2,s      Make temp buffer to hold write data
*         tst   >$0174       Any hi-res screen # allocated?
                    tst       >HiResScrnNum any hi-res screen number allocated?
                    beq       RestoreScreenRet No, restore stack & return
                    tst       >OptionsChanged
                    beq       RestoreScreenDisplay
                    lbsr      DisableKbdInt restore original keyboard options
                    clr       >OptionsChanged
RestoreScreenDisplay equ      *
                    lda       #$1B      Setup DefColr sequence in temp buffer
                    sta       ,s        store escape byte in write buffer
                    lda       #$30      Sets palettes back to default color
                    sta       1,s       store palette-reset code in buffer
                    ldy       #$0002    number of bytes to write
                    lda       #StdOut   path to write to $01
                    leax      ,s        point x a buffer
                    os9       I$Write   write

*  Display a screen allocated by SS.AScrn
*  SetStat Function Code $8C
*
* entry:
*       a -> path number
*       b -> function code $8C (SS.DScrn)
*       y -> screen numbe
*            0 = text screen (32 x 16)
*            1-3 = high resolution screen
*
* error:
*       CC -> Carry set on error
*       b  -> error code (if any)

*                           a is still set to stdout from above
                    ldb       #SS.DScrn Display screen function code
                    ldy       #$0000    Display screen #0 (lo-res or 32x16 text)
                    os9       I$SetStt  make the call

*  Frees the memory of a screen allocated by SS.AScrn
*  SetStat Function Code $8C
*
* entry:
*       a -> path number
*       b -> function code $8D (SS.FScrn)
*       y -> screen number 1-3 = high resolution screen
*
* error:
*       CC -> Carry set on error
*       b  -> error code (if any)

                    clra                clear high byte
                    ldb       >HiResScrnNum get hi-res screen number again
                    tfr       d,y       move it to Y=screen #
                    lda       #StdOut   set the path $01
                    ldb       #SS.FSCrn Return screen memory to system
                    os9       I$SetStt  amke the call
                    bcs       RestoreScreenRet
                    clr       >HiResScrnNum

RestoreScreenRet    leas      2,s       Eat stack & return
                    rts                 return from RestoreScreen

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_SCREEN_SETUP
* ===== coco-screen-setup =====
* CoCo screen backend: screen-setup.
* Included in place; see ../../PORTABILITY.md for the current contract.

SetupScreen         leas      -$04,s    mamke room om stack 2 words
                    lda       #$01      Std out
                    ldb       #SS.AScrn Allocate & map in hi-res screen (VDGINT)
                    ldx       #$0004    320x192x16 screen
                    os9       I$SetStt  Map it in
                    bcs       ScreenSetupRet Error, Restore stack & exit
                    tfr       y,d       Move screen # returned to D
*         stb   >$0174      Save screen #
                    stb       >HiResScrnNum save allocated hi-res screen number
                    pshs      x         preserve screen mapping across monitor calls
                    lbsr      ConfigureMonitor
                    puls      x
                    bcs       ScreenSetupRet

* call with application address of screen in x
* returns with values in u
                    lbsr      mmuini2   get current MMU values
                    lbsr      TwiddleAddr twiddle addresses
                    stu       <ScrStartAddr stow it two places
                    stu       <ScrStart2 also save as second screen start reference

                    leax      >CocoFramePairBytes,x  end address ???
                    lbsr      TwiddleAddr twiddle addresses
                    stu       <ScrEndAddr stow it in two places
                    stu       <ScrEnd2  also save as second screen end reference

* TFM for 6309
                    ldu       #CocoFrameEnd    Clear hi-res screen to color 0
                    ldx       #CocoFrameBytes    Screen is from $6000 to $D800
                    ldd       #$0000    (U will end up pointing to beginning of screen)
ClearScreenLoop     std       ,--u      writes 0000 to screen address and decrements
                    leax      -2,x      decrement x loop counter
                    bne       ClearScreenLoop keep going till all of screen is cleared

*  Display a screen allocated by SS.AScrn
*  SetStat Function Code $8C
*
* entry:
*       a -> path number
*       b -> function code $8C (SS.DScrn)
*       y -> screen numbe
*            0 = text screen (32 x 16)
*            1-3 = high resolution screen
*
* error:
*       CC -> Carry set on error
*       b  -> error code (if any)

                    clra                Get screen # to display
                    ldb       >HiResScrnNum load allocated screen number
                    tfr       d,y       Y=screen # to display
                    lda       #StdOut   $01  Std out path
                    ldb       #SS.DScrn Display 320x192x16 screen
                    os9       I$SetStt  make the call
                    bcs       ScreenSetupRet bail on screen display error

                    leax      >ColorTable,pc get color table values
                    ldb       >$0553    display_type 0 = comp / 1 = rgb
                    lda       #$10      16 palette entries per color table
                    mul                 first sixteen comp, second rgb
                    abx                 add b to x reset the pointer as required


* This loads up the control sequence to set the pallete 1B 31 PRN CTN
*  PRN palette register 0 - 15, CTN color table 0 - 63
                    lda       #$1B      Escape code
                    sta       ,s        push on stack
                    lda       #$31      Palette code
                    sta       $01,s     push on stack
                    clra                make a zero palette reg value
                    sta       $02,s     push it `
                    ldy       #$0004    sets up # of bytes to write
PaletteLoop         ldb       ,x+       get value computed above for color table and bump it
                    stb       $03,s     push it
                    pshs      x         save it
                    lda       #StdOut   $01      Std Out path
                    leax      $02,s     start of data to write
                    os9       I$Write   write it
                    puls      x         balance the palette-loop save on errors too
                    bcs       ScreenSetupRet error during write clean up stack and leave
*                   puls      x         retrieve our x
                    inc       $02,s     this is our palette register value
                    lda       $02,s     we bumped it by one
                    cmpa      #$10      we loop 15 times to set them all
                    blo       PaletteLoop loop

                    clr       <PaletteFlag clear a flag in memory
                    lbsr      DisableKbdInt go disable keyboard interrupts
                    bcs       ScreenSetupRet
                    inc       >OptionsChanged
                    clrb
ScreenSetupRet      leas      $04,s     clean up stack
                    rts                 return

                    else
                    error Unknown platform feature section
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
