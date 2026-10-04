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
