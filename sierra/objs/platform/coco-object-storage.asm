* CoCo platform boundary: object-storage.
* Included in place; see ../../PORTABILITY.md.

ObjChkControl       pshs      y         save y

                    ldx       $04,s     sets up mmu info
                    ldd       $08,x     load view_data passed to mmu twiddler
                    lbsr      TwiddleMmu twiddle mmu

                    ldb       $04,x     load y
                    lda       $26,x     load flags
                    bita      #O_PRIFIXED and with $04 but don't change
                    bne       SkipPriCalc not zero move on
*                         it is zero then
                    fcb       $ce,$05,$ee load buffer address
*      leau  PriTableBase,pcr    load buffer address
                    clra                clear a since we will use d as an index
                    lda       d,u       fetch the data from pri_table
                    sta       $24,x     save as priority

SkipPriCalc         lda       #$A0      set up PBUF_MULT()
                    mul                 do the math
                    addb      $03,x     add in x
                    adca      #0000     add in the carry bit
                    addd      #gfx_picbuff add it to the start of the screen buff addr 6040
                    tfr       d,u       move the pointer pb to u

                    ldy       $10,x     load y with cel_data ptr
                    clra                make a zero
                    sta       ScratchA6 stow it at flag_water
                    sta       ScratchA5 stow it at flag_signal
                    inca                make a 1
                    sta       FlagControl stow it at flag_contro1
                    ldb       $24,x     load priority
                    cmpb      #$0F      compare it with 15
                    beq       CheckFinish If it equals 15 move on
*                         otherwise if not equal 15
                    sta       ScratchA6 stow that 1 at flag_water
                    ldb       ,y        cx  first byte of cel_data  (cel_width)

*  do while cx != 0

PriLoop             lda       ,u+       (pri) put byte at pb in acca and bump pointer
                    anda      #$F0      and that with $F0  (obstacle ??)
                    beq       ClearFlagControl if it equals 0 set flag_control =0 and check_finish

                    cmpa      #$30      compare pri to 48 (water ??)
                    beq       PriLoopNext not equal  move to end of loop
                    clr       ScratchA6 clear the water flag
                    cmpa      #$10      compare it with 16 (conditional ??)
                    beq       TestObserveBlocks if equal go test for observe blocks
                    cmpa      #$20      compare with 32
                    beq       StoreFlagSignal pri=$20 signal this object

PriLoopNext         decb                decrement cx
                    bne       PriLoop   not zero yet loop again

                    lda       $25,x     load flags in  acca
                    tst       ScratchA6 test flag_water
                    bne       TestHrznIgnore not zero next test
                    bita      #O_DRAWN  should be O_WATER Looks like a BUG in ours
                    beq       CheckFinish if it equals one head for check_finish
                    bra       ClearFlagControl clear that flag control first and leave
TestHrznIgnore      bita      #O_HRZNIGNORE should be O_LAND  Looks like a BUG in ours
                    beq       CheckFinish horizon-ignore clear go check finish

ClearFlagControl    clr       FlagControl clear flag_control
                    bra       CheckFinish head for check_finish

TestObserveBlocks   lda       $26,x     load flags in acca
                    bita      #O_BLKIGNORE and with $02 but don't change
                    beq       ClearFlagControl equals zero clear flag_control and go check_finish
                    bra       PriLoopNext then  head back in the loop

StoreFlagSignal     sta       ScratchA5 store acca at flag signal (obj_picbuff.c has =1)
                    bra       PriLoopNext continue with loop



CheckFinish         lda       $02,x     load num
                    bne       ObjChkDone if not zero were done head out

* flag signal test
                    lda       ScratchA5 load flag_signal
*                         operates on F03_EGOSIGNAL
                    beq       ResetSignalFlag if its zero go reset the signal
*                         otherwise set the flag
                    lda       StateFlag load the state.flag element
                    ora       #$10      set the bits
                    sta       StateFlag save it back
                    bra       TestWaterFlag go test the water flag
ResetSignalFlag     lda       StateFlag load the state.flag element
                    anda      #$ef      reset the bits
                    sta       StateFlag save it back

* flag_water test
TestWaterFlag       lda       ScratchA6 load flag_water
                    beq       ResetWaterFlag if zero go reset the flag
*                         otherwise set it
                    lda       StateFlag load the state.flag element
                    ora       #$80      set the bits
                    sta       StateFlag save it back
                    bra       ObjChkDone baby we're out of here
ResetWaterFlag      lda       StateFlag load the state.flag element
                    anda      #$7f      reset the bits
                    sta       StateFlag save it back

ObjChkDone          puls      y         retrieve our y and leave
                    rts                 object control check done return


* ====== ObjBlit: Render Object Cel to Screen Buffer ======
*  obj_blit(VIEW *v)   obj_blit.c
*  our index reg x points to the view structure
*  are 3 = x, 4 = y instead of 3-4 = x & 5-6 = y ???
*  ScratchA2 = cel_height
*  ScratchA7 = cel_trans
*  ScratchA8 = init (pb)
*  ScratchAC = cel_invis
*  ScratchAD = pb_pri
*  PosInitX = view_pri
*  PosInitY = col

ObjBlit             ldx       $02,s     pull our x pointer off the stack
                    ldd       $08,x     load d with view_data
                    lbsr      TwiddleMmu twiddle mmu

                    ldu       $10,x     u now is a pointer to cel_data
                    lda       $02,u     cel_data[$02] loaded
                    bita      #O_Block  are we testing against a block or does $80 mean something else here?
                    beq       ProcessCelData if zero skip next instruction

                    lbsr      ObjCelMirror otherwise call obj_cell_mirror

ProcessCelData      ldd       ,u++      load the first 2 bytes of cel_data and bump to next word
*                        cel_width is in acca we ignore
                    stb       ScratchA2 save as cel_height
*                        obj_blit.c has and $0F which is a divide by 16
*                        we do a multiply x 16 ???
                    lda       ,u+       cel_trans
                    asla                shift trans color left 4 bits
                    asla                shift trans color left step 2
                    asla                shift trans color left step 3
                    asla                now in upper nibble
                    sta       ScratchA7 save as cel_tran

                    lda       $24,x     priority
                    asla                shift left 4
                    asla                priority to upper nibble step 2
                    asla                priority to upper nibble step 3
                    asla                priority now in upper nibble
                    sta       PosInitX  view_pri

                    ldb       $04,x     load the y value
                    subb      ScratchA2 subtract the cel_height
                    incb                add 1
                    lda       #$a0      set up PBUF_MULT()
                    mul                 do the math
                    addb      $03,x     add in the x value
                    adca      #0000     add in the carry from multiply
                    addd      #gfx_picbuff add this to the start of the screen buff addr $6040
                    std       ScratchA8 pb pointer to the pic buffer
                    ldx       ScratchA8 load it in an index reg

                    lda       #$01      set cel_invis flag initially
                    sta       ScratchAC set cel_invis to 1 and save

                    bra       ChunkLoop start processing cel chunk data
BumpPbPtr           abx                 bump the pb pointer

ChunkLoop           lda       ,u+       get the next "chunk"
                    beq       NextCelRow if zero
                    ldb       -$01,u    not zero load the same byte in accb
                    anda      #$f0      and chunk with $F0 (col)
                    andb      #$0f      and chunk with $0F (chunk_len)
                    cmpa      ScratchA7 compare with cel_trans
                    beq       BumpPbPtr set up and go again color is trasnparent
                    lsra                shift right 4
                    lsra                extract color nibble step 2
                    lsra                extract color nibble step 3
                    lsra                color now in lower nibble
                    sta       PosInitY  save the color

ChunkInnerLoop      lda       ,x        get the byte pointed to by pb
                    anda      #$f0      get the priority portion
                    cmpa      #$20      compare to $20
                    bls       SavePbPri less or equal
                    cmpa      PosInitX  compare to view_pri
                    bhi       SkipChunkPixel pb_pri > view_pri
*                        otherwise
                    lda       PosInitX  load view_pri
StoreChunkColor     ora       PosInitY  or it with col
                    sta       ,x+       store that at pb and bump the pointer
                    clr       ScratchAC zero cel_invis
                    decb                decrement chunk_len
                    bne       ChunkInnerLoop not equal zero go again inner loop
                    bra       ChunkLoop go again outer loop

NextCelRow          dec       ScratchA2 decrement cel_height
                    beq       CelDone   equal zero move on out of cel_height loop
                    ldx       ScratchA8 load init
                    leax      >PICBUFF_WIDTH,x move 160 into screen
                    stx       ScratchA8 stow that back as init/pb
                    bra       ChunkLoop go again

SavePbPri           stx       ScratchAD save the pointer
                    clra                set up ch

SearchPriLoop       cmpx      #blit_end compare to gfx_picbuff+$6860
                    bhs       GotPriority not less than then branch out
*                             less than the end
                    leax      >PICBUFF_WIDTH,x bump the pointer by 160
                    lda       ,x        get that byte
                    anda      #$f0      and it with $F0
                    cmpa      #$20      test against $20
                    bls       SearchPriLoop less or equal go again

GotPriority         ldx       ScratchAD load pb_pri
                    cmpa      PosInitX  compare with view_pri
                    bhi       SkipChunkPixel pb_pri > view_pri
                    lda       ,x        make the next
                    anda      #$f0      pb_pri
                    bra       StoreChunkColor go or it with the color

SkipChunkPixel      leax      $01,x     bump the pb pointer
                    decb                decrement chunk_len
                    bne       ChunkInnerLoop not equal do middle loop again
                    bra       ChunkLoop go again

CelDone             ldx       $02,s     pull our view pointer back off the stack
                    lda       $02,x     get the num
                    bne       ObjBlitDone if not zero exit routine
                    lda       ScratchAC get the cel_invis value
                    beq       ResetInvisFlag reset the flag

* set the flag
                    lda       StateFlag load the state.flag
                    ora       #$40      set it
                    sta       StateFlag stow it back
                    bra       ObjBlitDone exit routine

* reset the flag
ResetInvisFlag      lda       StateFlag load state.flag
                    anda      #$bf      clear it
                    sta       StateFlag stow it
ObjBlitDone         rts                 object blit complete return


* ====== ObjCelMirror: Mirror a Cel Horizontally ======
* obj_cel_mirror(View *v) in obj_picbuff.c
* we use different values from those shown nagi files
* on entry
*    a contains cell_data[$02] in call from obj_blit()
*    x contains pointer to view data
*    u contains pointer to cel_data
*
*    saves and restores x,y,u regs on exit
*
*  PosFinalY = width
*  ScratchA2 = height_count
*  ScratchA7 = trans transparent color left shifted 4
*  ScratchAA = tran_size ??
*  ScratchAB = meat_size
*  MaskDl = loop_cur << 4
*  OldBuff = al


ObjCelMirror        anda      #$30      and that with $30  (nagi has $70)
                    lsra                shift right 4
                    lsra                extract mirror type bits step 2
                    lsra                extract mirror type bits step 3
                    lsra                mirror type now in lower nibble
                    cmpa      $0A,x     compare that with loop_cur
                    lbeq      ObjCelMirrorDone if equal we're done

                    pshs      x,y,u     save our view (x) what ever (y) and cel_data (u) pointers

                    lda       $0A,x     load loop_cur
                    asla                and shift it 4 left
                    asla                loop_cur to upper nibble step 2
                    asla                loop_cur to upper nibble step 3
                    asla                loop_cur now in upper nibble
                    sta       MaskDl    stow it as ??
                    lda       #$cf      load a with with $CF  (nagi has $8F)
                    anda      $02,u     and that with cel[2]
                    ora       MaskDl    or with loop_cur<<4
                    sta       $02,u     stow it back at cel[2]

                    ldy       #gbuffend point y to temp mirror buffer

                    ldd       ,u++      load d with width and hieght
                    std       PosFinalY stow that
                    lda       ,u+       load a with trans color
                    asla                and shift left 4
                    asla                trans color to upper nibble step 2
                    asla                trans color to upper nibble step 3
                    asla                trans color now in upper nibble
                    sta       ScratchA7 stow as trans
                    stu       OldBuff   stow u as al
MirrorRowLoop       clrb                make a zero
                    stb       ScratchAB stow it as meat_size

*                      nagi code has tran_size set to width and
*                      al&$0F subtracted from it.
*                      in this loop

ScanTransLoop       stb       ScratchAA and tran_size

                    lda       ,u+       load in the next cel_data byte
                    beq       MirrorEndOfRow if its a zero leave loop
                    ldb       -$01,u    otherwise fetch the same data into b
*                      at this point a & b both have the same data byte
                    anda      #$f0      and the a copy with $F0
                    andb      #$0f      and the b copy with $0F
                    cmpa      ScratchA7 compare byte&$F0 with trans
                    bne       MirrorNonTrans not equal branch out of loop
                    addb      ScratchAA otherwise add in tran_size
                    bra       ScanTransLoop and loop

MirrorNextByte      ldb       ,u+       load the nbext byte and bump the pointer
                    beq       MirrorRemaining if it was zero move on
                    andb      #$0f      otherwise and it with $0F
MirrorNonTrans      addb      ScratchAA add in tran_size
                    stb       ScratchAA save it as tran_size
                    inc       ScratchAB bump meat_size
                    bra       MirrorNextByte loop to the next byte

MirrorRemaining     lda       ScratchAA load tran_size
                    nega                negate it
                    adda      PosFinalY add in the width
                    beq       MirrorReverseCopy if that is zero move on

MirrorFillTrans     suba      #$0f      subtract 15 from it
                    bls       MirrorLastTrans less or same move on
                    sta       ScratchAA otherwise stow that back as tran_size
                    lda       ScratchA7 fetch trans
                    ora       #$0f      or it with 15
                    sta       ,y+       store it at buff (gbuffend) and bump pointer
                    lda       ScratchAA fetch tra_size
                    bra       MirrorFillTrans loop again

MirrorLastTrans     adda      #$0f      add 15 back into a (tran_size)
                    ora       ScratchA7 or that with trans
                    sta       ,y+       stow that at buff and bump the pointer

MirrorReverseCopy   leax      -$01,u    set x to the last cel_data byte processed
                    ldb       ScratchAB load b with the meat_size (the loop counter)
MirrorCopyLoop      lda       ,-x       copy from the cel_data end
                    sta       ,y+       to the buff front
                    decb                dec the counter
                    bne       MirrorCopyLoop not done loop again

MirrorEndOfRow      stb       ,y+       on entry b should always = 0 stow that at the next buff location
                    dec       ScratchA2 decrement the height_count
                    bne       MirrorRowLoop not zero go again

* now we are going to copy the backward temp buffer back to the cel
                    tfr       y,d       get the buff pointer in d
                    subd      #gbuffend subtract the starting value of the buffer
                    stb       TempBuff  save that as the buffer size
                    andb      #$fe      make it an even number
                    tfr       d,x       transfer that to x
                    ldu       OldBuff   al cel_data pointer
                    ldy       #gbuffend load y start of our temp buffer

MirrorWriteBack     ldd       ,y++      get a word
                    std       ,u++      stow a word
                    leax      -$02,x    dec the counter by a word
                    bne       MirrorWriteBack not zero go again
*                      so we've moved an even number of bytes
                    lda       TempBuff  load the actual byte count
                    lsra                divide by 2
                    bcc       MirrorDone no remainder (not odd) we're done
                    lda       ,y        otherwise move the last
                    sta       ,u        byte
MirrorDone          puls      x,y,u     retrieve our x,y,u values

ObjCelMirrorDone    rts                 and return to caller



* ====== ObjAddPicPri: Stamp Object Priority Box Onto Screen Buffer ======
* obj_add_pic_pri(VIEW *v)  obj_picbuff.c
* our index reg x points to the view structure
*
*  PosInitX = priority&$F0
*  ScratchA3 = pri_table[y]
*  ScratchA4 = pri_table[y]
*  ScratchA8 = pb (word)
*  ScratchA9 = "
*  PriHeight = pri_height/height

ObjAddPicPri        pshs      y         save the y
                    ldx       $04,s     get the the pointer to our view
                    ldd       $08,x     load d with view_data ?
                    lbsr      TwiddleMmu twiddle mmu

*                      set up d as pointer to pri_table value
                    clra                zero a
                    ldb       $04,x     load view y value
                    fcb       $CE,$05,$EE load pri_table address
*      leau  PriTableBase,pcr    load pri_table address
                    lda       d,u       fetch the pri_table y data
                    std       ScratchA3 stow it in a temp
                    ldb       $24,x     load priority
                    andb      #$0f      and that with $0F
                    bne       SkipPriAdjust if that equals zero move on
                    ora       $24,x     otherwise or the pri_table[y] with priority
                    sta       $24,x     stow that back as priority

SkipPriAdjust       pshs      x         push the pointer to the view on the stack
                    lbsr      ObjBlit   call obj_blit()
                    leas      $02,s     reset the stack
                    ldx       $04,s     get the pointer to our view
                    lda       $24,x     load priority
                    cmpa      #$3F      compare to $3F
                    lbhi      ObjAddPicPriDone if greater then nothing to do head out

                    fcb       $CE,$05,$EE load pri_table address
*      leau  PriTableBase,pcr    load pri_table address
                    ldb       ScratchA4 fetch pri_table[y] (cx)
                    clr       PriHeight clear pri_height
PriHeightLoop       clra                zero acca
                    inc       PriHeight bump pri_hieght
                    tstb                is pri_table[y]
                    beq       CalcPbPtr equal zero if so move on
                    decb                dec our counter cx
                    lda       d,u       load pri_table[cx]
                    cmpa      ScratchA3 compare to pri_table[y]
                    beq       PriHeightLoop if they are equal loop again

* set up and execute PBUF_MULT call
CalcPbPtr           ldb       $04,x     load the view->y in
                    lda       #$a0      from pbuf mult
                    mul                 do the math
                    addb      $03,x     add in the x value
                    adca      #0000     add in the carry
                    addd      #gfx_picbuff add in the base address $6040
                    tfr       d,u       move that to an index reg (pb)
                    stu       ScratchA8 stow it as pb

                    ldy       $10,x     load y with cel_data pointer
                    ldb       $01,y     get the second byte (height)
                    cmpb      PriHeight compare to pri_height
                    bhi       SetupPriNibble greater move on
                    stb       PriHeight otherwise save the largest as pri_height
SetupPriNibble      lda       $24,x     load the priority again
                    anda      #$f0      and it with $F0
                    sta       PosInitX  stow that for later use

* bottom line
                    ldb       ,y        load b with the first byte in cel_data (cx)
BottomLineLoop      lda       ,u        get the byte at our pic buff pb
                    anda      #$0f      and it with $0F
                    ora       PosInitX  or it with priority&F0
                    sta       ,u+       stow it back and bump the pointer
                    decb                dec the loop counter cx
                    bne       BottomLineLoop not zero go again

* it has a height
                    dec       PriHeight test "height" for > 1
                    beq       ObjAddPicPriDone wasn't head no more to do so head out
                    ldu       ScratchA8 reset u to our pb pic buff pointer

* the sides
                    ldb       ,y        get the first byte of cel_data
                    decb                subtract 1 (sideoff)
SidesLoop           leau      -$A0,u    decrement pb by 160
                    tfr       u,x       move that value into x
                    lda       ,u        get the data
                    anda      #$0f      and it with $0F
                    ora       PosInitX  or it priority&$F0
                    sta       ,u        stow it back
                    clra                zero a so we can use d as a pointer
                    lda       d,u       use "sideoff" as an index into pb
                    anda      #$0f      and that with $0F
                    ora       PosInitX  or that rascal with priority&$F0
                    abx                 add that value to our x pointer
                    sta       ,x        and store it there
                    dec       PriHeight dec the height
                    bne       SidesLoop greater than zero go again

* the top of the box

                    ldb       ,y        get the cel_data first byte in b
                    subb      #$02      subtract 2
                    leau      $01,u     bump the pb pointer
TopLineLoop         lda       ,u        grab the byte
                    anda      #$0f      and that with $0F
                    ora       PosInitX  or it with priority &$F0
                    sta       ,u+       stow it back and bump the pointer
                    decb                dec our counter
                    bne       TopLineLoop loop if not finished

ObjAddPicPriDone    puls      y         return the y value
                    rts                 return



* ====== BlitSave / BlitRestore: Save and Restore Screen Background Under Object ======
* blit_save(BLIT *b) obj_blit.c
*  our blit_struct is a bit different from the one in nagi
*
* PosFinalX = zeroed and never changed cause we use the next byte :-)
* PosFinalY = x_count (x_size)         when cmpx ha ha
* ScratchA2 = y_count (y_size)
* ScratchA8 = pic buffer start pic_cur
* ScratchAD = pic_cur + offset

BlitSave            ldu       $02,s     get the pointer to the blit_struct
                    ldd       $0C,u     get the pointer to the view_data for mmu twiddler
                    lbsr      TwiddleMmu twiddle mmu

                    ldu       $02,s     get the pointer to the blit_struct data back in u
                    ldd       $08,u     load the x/y_size
                    std       PosFinalY stow that at x/y_count
                    clr       PosFinalX zero some adder
                    ldb       $07,u     get the y value
                    lda       #$a0      set up PBUF_MULT
                    mul                 do the math
                    addb      $06,u     add in x
                    adca      #0        add in the carry bit
                    addd      #gfx_picbuff add in pic buff base $6040

                    ldu       $0A,u     load u with with the buffer pointer blit_cur
BlitSaveLoop        std       ScratchA8 save the buffer start pointer pic_cur
                    addd      PosFinalX add in the offset x_size
                    std       ScratchAD stow that at pic_cur + offset
                    ldx       ScratchA8 load x with pic_cur
CopyPixelsLoop      ldd       ,x++      copy 2 bytes at a time
                    std       ,u++      to the buffer at blit_cur
                    cmpx      ScratchAD have we copied it all ??
                    blo       CopyPixelsLoop nope loop again

                    ldd       ScratchA8 load with pic buffer start
                    addd      #PICBUFF_WIDTH add 160
                    dec       ScratchA2 dec y_count
                    bne       BlitSaveLoop not zero loop again
                    rts                 blit save complete return


* blit_restore(BLIT *b) obj_blit.c
* blit_save(BLIT *b) obj_blit.c
*  our blit_struct is a bit different from the one in nagi
*
* PosFinalX = zeroed and never changed cause we use the next byte :-)
* PosFinalY = x_count (x_size)         when cmpx ha ha
* ScratchA2 = y_count (y_size)
* ScratchA8 = pic buffer start pic_cur
* ScratchAD = pic_cur + offset

BlitRestore         ldu       $02,s     get the pointer to the blit structure
                    ldd       $0C,u     load view_data pointer for mmu twiddle
                    lbsr      TwiddleMmu twiddle mmu

                    ldu       $02,s     get the blit_structure back in u
                    ldd       $08,u     load x/y_size
                    std       PosFinalY stow them at x/y_count
                    clr       PosFinalX clear the byte prior to x_size
                    ldb       $07,u     get the y value
                    lda       #$a0      set up PBUF_MULT
                    mul                 do the math
                    addb      $06,u     add in the x value
                    adca      #0        add in the carry bit
                    addd      #gfx_picbuff add in the base address $6040

                    ldu       $0A,u     load u with buffer pointer blit_cur
BlitRestoreLoop     std       ScratchA8 save the screen start buffer pic_cur
                    addd      PosFinalX add in the x_size
                    std       ScratchAD stow at pic_cur + offset
                    ldx       ScratchA8 load x pic_cur pointer
CopyBackLoop        ldd       ,u++      grab em from the buffer
                    std       ,x++      and send them to the screen
                    cmpx      ScratchAD moved them all ??
                    blo       CopyBackLoop nope then keep on keeping on

                    ldd       ScratchA8 load the pic_cur pointer
                    addd      #PICBUFF_WIDTH add 160
                    dec       ScratchA2 dec the y count
                    bne       BlitRestoreLoop not zero move some more
                    rts                 blit restore complete return
