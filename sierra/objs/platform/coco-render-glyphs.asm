* CoCo packed-pixel renderer: render-glyphs.
* Keep optimized loops intact. See ../../PORTABILITY.md.

DrawSprites         leas      -$02,s    allocate 2 scratch bytes
                    pshs      y         save Y register
                    ldx       $06,s     load pointer to glyph data
                    ldu       #SierraPalette point U to Sierra palette table
                    lda       <SprCurRow load current sprite row
                    lsla                row × 2
                    lsla                row × 4
                    lsla                row × 8
                    ldb       #$A0      B = 160
                    mul                 D = row × 8 × 160 = pixel row offset
                    tfr       d,y       Y = row pixel offset
                    clra                clear A for column calculation
                    ldb       <SprCurCol load current sprite column
                    lslb                col × 2
                    lslb                col × 4 (bytes per glyph col)
                    addd      #$6000    add screen base $6000
                    leay      d,y       Y = screen address for this glyph
DrawSpriteLoop      tst       ,x        test next glyph byte
                    lbeq      DrawSpritesDone zero byte = end of glyph data
                    ldb       ,x+       load glyph index, advance X
                    stx       $06,s     save updated X pointer in scratch
                    leax      >BitmapFont,pcr point X to bitmap font table
                    lslb                index × 2
                    abx                 advance X by index×2
                    abx                 advance X by index×2 again
                    abx                 advance X by index×2 again
                    abx                 X now points to glyph (index × 8)
                    lda       #$08      A = 8 rows per glyph
                    sta       $02,s     save row counter in scratch
DrawSpriteRow       ldb       ,x+       load 8-bit row bitmap, advance X
                    lda       #$04      A = 4 pixel pairs per row
                    sta       $03,s     save pixel pair counter
DrawSpritePixel     sex                 sign-extend B into A (B MSB → A)
                    lda       a,u       look up high nibble color in palette
                    anda      #$F0      keep high nibble only
                    sta       ,y        write high-color pixel to screen
                    lslb                shift next pixel bit into sign
                    sex                 sign-extend B for low nibble
                    lda       a,u       look up low nibble color in palette
                    anda      #$0F      keep low nibble only
                    ora       ,y        merge with high nibble on screen
                    ora       <PaletteFlag flag for palettes set in sierra
                    sta       ,y+       write merged pixel byte, advance Y
                    lslb                shift next pixel bits
                    dec       $03,s     one fewer pixel pair this row
                    bne       DrawSpritePixel loop for all 4 pairs
                    lda       <PaletteFlag flag for palettes set in sierra
                    beq       FlipPaletteFlag skip invert if flag already zero
                    coma                invert A ($FF → $00)
                    sta       <PaletteFlag flag for palettes set in sierra
FlipPaletteFlag     leay      >$009C,y  advance Y to next glyph row ($9C = 156)
                    dec       $02,s     one fewer glyph row remaining
                    bne       DrawSpriteRow loop for all 8 glyph rows
                    ldx       $06,s     restore X pointer to glyph list
                    inc       <SprCurCol advance to next sprite column slot
                    leay      >-$04FC,y rewind Y back to top of this glyph col
                    bra       DrawSpriteLoop process next glyph
DrawSpritesDone     puls      y         restore Y register
                    leas      $02,s     free scratch bytes
                    rts
