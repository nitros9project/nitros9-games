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
