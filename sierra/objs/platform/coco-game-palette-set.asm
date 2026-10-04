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
