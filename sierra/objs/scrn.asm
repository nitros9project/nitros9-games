********************************************************************
* scrn - Kings Quest III screen module
*
* Note the header shows a data size of 0 called from the sierra module
* and accesses data set up in that module.
*
* Edt/Rev  YYYY/MM/DD  Modified by
* Comment
* ------------------------------------------------------------------
*   0      2003/03/06  Paul W. Zibaila
* Disassembly of original distribution.
* Annotated by /annotate-asm (Claude Code) 2026-05-12:
*   - Renamed disassembled labels to meaningful names
*   - Added inline comments to every instruction

                    nam       scrn
                    ttl       Kings Quest III screen module

* Disassembled 00/00/00 00:15:39 by Disasm v1.6 (C) 1988 by RML

                  IFP1
                    use       defsfile
                  ENDC

tylg                set       Prgrm+Objct
atrv                set       ReEnt+rev
rev                 set       $01

                    mod       eom,name,tylg,atrv,start,size

*  equates for common data used in this module

MmuBlkNum           equ       $0012     map block value (word)
BlkMapLow           equ       $001C
BlkMapHigh          equ       $001E
u0024               equ       $0024
HiResBase           equ       $002C
u0030               equ       $0030
u0038               equ       $0038
u003E               equ       $003E
SprCurRow           equ       $0040
SprCurCol           equ       $0041
SierraPdBlk         equ       $0042     Sierra process descriptor block
Sierra2ndBlk        equ       $0043     Sierra 2nd 8K data block
PaletteFlag         equ       $0045     flag for palettes in sierra
ScrAddrHi           equ       $0046     first byte of hi res screen mem addr
ScrAddrLo           equ       $0047     second byte of hi res screen mem addr
u007E               equ       $007E
u0080               equ       $0080
u0081               equ       $0081
RowCount            equ       $00A0     busy address here
StripWidth          equ       $00A1
RowStride           equ       $00A2
ViewRightX          equ       $00A3
DrawY1              equ       $00A4
ClipLeft            equ       $00A5
ClipRight           equ       $00A6
ClipHeight          equ       $00A7
ClipBottom          equ       $00A8
ClipWidth           equ       $00A9
OverlapLeft         equ       $00AA
OverlapTop          equ       $00AB
OverlapSize         equ       $00AC
u00C0               equ       $00C0
u00C6               equ       $00C6
u00CC               equ       $00CC
u00DE               equ       $00DE
u00E0               equ       $00E0
u00F6               equ       $00F6
u00F8               equ       $00F8
u00FC               equ       $00FC
u00FE               equ       $00FE
u00FF               equ       $00FF

PicVisible          equ       $0100     pic_visible
SierraPalette       equ       $024D
DatTask1Slot1       equ       $FFA9


size                equ       .
name                equ       *
                    fcs       /scrn/
                    fcb       $00

* This module is linked to in sierra
* upon entry
*   a -> type language
*   b -> attributes / revision level
*   x -> address of the last byte of the module name + 1
*   y -> module entry point absolute address
*   u -> module header absolute address

start               equ       *
                    lbra      DrawStrip dispatch 0: blit picture strip to screen
                    lbra      SetupDrawStrip dispatch 1: forward args and call DrawStrip
                    lbra      ClearScreen dispatch 2: fill screen with value in D
                    lbra      ClearScreenBlack dispatch 3: clear screen to black
                    lbra      DrawBorder dispatch 4: draw 4-sided rectangle border
                    lbra      DrawSprites dispatch 5: render 8×8 font glyphs
                    lbra      CopyStrip dispatch 6: copy background strip
                    lbra      ClearWithPalette dispatch 7: fill screen with palette color
                    lbra      UpdateViewList dispatch 8: update all views in linked list
                    lbra      DrawView  dispatch 9: render one view/cel to screen

* probably was an info directive for an include file
CopyrightStr        fcc       'AGI (c) copyright 1988 SIERRA On-Line'
                    fcc       'CoCo3 version by Chris Iden'
                    fcb       $00
Infosz              equ       *-CopyrightStr



* map block check and sets
* MmuBlkNum is set in code in DrawStrip sub
* entry:
*      a -> value to be tested

* Platform mapping implementation; retained at its original location.
                    use       platform/screen-map.asm

* 16 marker bytes for some thing
* coco_view_pal[]     vid_render.c
* Platform renderer implementation, selected during assembly.
                    use       platform/render-spans.asm

UpdateViewList      leas      -$04,s    allocate 4 scratch bytes
                    ldx       $06,s     load pointer to view list head
                    ldu       ,x        load first node pointer
ViewListLoop        stu       ,s        save current node in scratch
                    beq       ViewListDone null pointer = end of list
                    ldu       $04,u     load next node's data pointer
                    stu       $02,s     save next pointer in scratch[2]
                    pshs      u         push view ptr as DrawView arg
                    lbsr      DrawView  render this view
                    leas      $02,s     pop DrawView arg
                    ldu       $02,s     reload next pointer
                    lda       $01,u     load view attribute byte
                    cmpa      ,u        compare with previous attribute
                    bne       ViewListNext skip coord update if changed
                    ldd       $03,u     load current X,Y coords
                    cmpd      <$1A,u    compare with previous coords
                    bne       UpdateViewCoords branch if position changed
                    lda       <$25,u    load view flags byte
                    ora       #$40      set bit 6 (stable/unchanged flag)
                    sta       <$25,u    store updated flags
                    bra       ViewListNext
UpdateViewCoords    std       <$1A,u    save new coords as previous
                    lda       <$25,u    load view flags
                    anda      #$BF      clear bit 6 (position changed)
                    sta       <$25,u    store updated flags
ViewListNext        ldu       ,s        load current node from scratch
                    ldu       ,u        follow next-node link
                    bra       ViewListLoop process next node
ViewListDone        leas      $04,s     free scratch bytes
                    rts


* Platform renderer implementation, selected during assembly.
                    use       platform/render-view.asm

BitmapFont          fcb       $00,$00,$00,$00
                    fcb       $00,$00,$00,$00
                    fcb       $7E,$81,$A5,$81
                    fcb       $BD,$99,$81,$7E
                    fcb       $7E,$FF,$DB,$FF
                    fcb       $C3,$E7,$FF,$7E
                    fcb       $6C,$FE,$FE,$FE
                    fcb       $7C,$38,$10,$00
                    fcb       $10,$38,$7C,$FE
                    fcb       $7C,$38,$10,$00
                    fcb       $38,$7C,$38,$FE
                    fcb       $FE,$7C,$38,$7C
                    fcb       $10,$10,$38,$7C
                    fcb       $FE,$7C,$38,$7C
                    fcb       $00,$00,$18,$3C
                    fcb       $3C,$18,$00,$00
                    fcb       $FF,$FF,$E7,$C3
                    fcb       $C3,$E7,$FF,$FF
                    fcb       $00,$3C,$66,$42
                    fcb       $42,$66,$3C,$00
                    fcb       $FF,$C3,$99,$BD
                    fcb       $BD,$99,$C3,$FF
                    fcb       $0F,$07,$0F,$7D
                    fcb       $CC,$CC,$CC,$78
                    fcb       $3C,$66,$66,$66
                    fcb       $3C,$18,$7E,$18
                    fcb       $3F,$33,$3F,$30
                    fcb       $30,$70,$F0,$E0
                    fcb       $7F,$63,$7F,$63
                    fcb       $63,$67,$E6,$C0
                    fcb       $99,$5A,$3C,$E7
                    fcb       $E7,$3C,$5A,$99
                    fcb       $80,$E0,$F8,$FE
                    fcb       $F8,$E0,$80,$00
                    fcb       $02,$0E,$3E,$FE
                    fcb       $3E,$0E,$02,$00
                    fcb       $18,$3C,$7E,$18
                    fcb       $18,$7E,$3C,$18
                    fcb       $66,$66,$66,$66
                    fcb       $66,$00,$66,$00
                    fcb       $7F,$DB,$DB,$7B
                    fcb       $1B,$1B,$1B,$00
                    fcb       $3E,$63,$38,$6C
                    fcb       $6C,$38,$CC,$78
                    fcb       $00,$00,$00,$00
                    fcb       $7E,$7E,$7E,$00
                    fcb       $18,$3C,$7E,$18
                    fcb       $7E,$3C,$18,$FF
                    fcb       $18,$3C,$7E,$18
                    fcb       $18,$18,$18,$00
                    fcb       $18,$18,$18,$18
                    fcb       $7E,$3C,$18,$00
                    fcb       $00,$18,$0C,$FE
                    fcb       $0C,$18,$00,$00
                    fcb       $00,$30,$60,$FE
                    fcb       $60,$30,$00,$00
                    fcb       $00,$00,$C0,$C0
                    fcb       $C0,$FE,$00,$00
                    fcb       $00,$24,$66,$FF
                    fcb       $66,$24,$00,$00
                    fcb       $00,$18,$3C,$7E
                    fcb       $FF,$FF,$00,$00
                    fcb       $00,$FF,$FF,$7E
                    fcb       $3C,$18,$00,$00
                    fcb       $00,$00,$00,$00
                    fcb       $00,$00,$00,$00
                    fcb       $30,$78,$78,$30
                    fcb       $30,$00,$30,$00
                    fcb       $6C,$6C,$6C,$00
                    fcb       $00,$00,$00,$00
                    fcb       $6C,$6C,$FE,$6C
                    fcb       $FE,$6C,$6C,$00
                    fcb       $30,$7C,$C0,$78
                    fcb       $0C,$F8,$30,$00
                    fcb       $00,$C6,$CC,$18
                    fcb       $30,$66,$C6,$00
                    fcb       $38,$6C,$38,$76
                    fcb       $DC,$CC,$76,$00
                    fcb       $60,$60,$C0,$00
                    fcb       $00,$00,$00,$00
                    fcb       $18,$30,$60,$60
                    fcb       $60,$30,$18,$00
                    fcb       $60,$30,$18,$18
                    fcb       $18,$30,$60,$00
                    fcb       $00,$66,$3C,$FF
                    fcb       $3C,$66,$00,$00
                    fcb       $00,$30,$30,$FC
                    fcb       $30,$30,$00,$00
                    fcb       $00,$00,$00,$00
                    fcb       $00,$30,$30,$60
                    fcb       $00,$00,$00,$FC
                    fcb       $00,$00,$00,$00
                    fcb       $00,$00,$00,$00
                    fcb       $00,$30,$30,$00
                    fcb       $06,$0C,$18,$30
                    fcb       $60,$C0,$80,$00
                    fcb       $7C,$C6,$CE,$DE
                    fcb       $F6,$E6,$7C,$00
                    fcb       $30,$70,$30,$30
                    fcb       $30,$30,$FC,$00
                    fcb       $78,$CC,$0C,$38
                    fcb       $60,$CC,$FC,$00
                    fcb       $78,$CC,$0C,$38
                    fcb       $0C,$CC,$78,$00
                    fcb       $1C,$3C,$6C,$CC
                    fcb       $FE,$0C,$1E,$00
                    fcb       $FC,$C0,$F8,$0C
                    fcb       $0C,$CC,$78,$00
                    fcb       $38,$60,$C0,$F8
                    fcb       $CC,$CC,$78,$00
                    fcb       $FC,$CC,$0C,$18
                    fcb       $30,$30,$30,$00
                    fcb       $78,$CC,$CC,$78
                    fcb       $CC,$CC,$78,$00
                    fcb       $78,$CC,$CC,$7C
                    fcb       $0C,$18,$70,$00
                    fcb       $00,$30,$30,$00
                    fcb       $00,$30,$30,$00
                    fcb       $00,$30,$30,$00
                    fcb       $00,$30,$30,$60
                    fcb       $18,$30,$60,$C0
                    fcb       $60,$30,$18,$00
                    fcb       $00,$00,$FC,$00
                    fcb       $00,$FC,$00,$00
                    fcb       $60,$30,$18,$0C
                    fcb       $18,$30,$60,$00
                    fcb       $78,$CC,$0C,$18
                    fcb       $30,$00,$30,$00
                    fcb       $7C,$C6,$DE,$DE
                    fcb       $DE,$C0,$78,$00
                    fcb       $30,$78,$CC,$CC
                    fcb       $FC,$CC,$CC,$00
                    fcb       $FC,$66,$66,$7C
                    fcb       $66,$66,$FC,$00
                    fcb       $3C,$66,$C0,$C0
                    fcb       $C0,$66,$3C,$00
                    fcb       $F8,$6C,$66,$66
                    fcb       $66,$6C,$F8,$00
                    fcb       $FE,$62,$68,$78
                    fcb       $68,$62,$FE,$00
                    fcb       $FE,$62,$68,$78
                    fcb       $68,$60,$F0,$00
                    fcb       $3C,$66,$C0,$C0
                    fcb       $CE,$66,$3E,$00
                    fcb       $CC,$CC,$CC,$FC
                    fcb       $CC,$CC,$CC,$00
                    fcb       $78,$30,$30,$30
                    fcb       $30,$30,$78,$00
                    fcb       $1E,$0C,$0C,$0C
                    fcb       $CC,$CC,$78,$00
                    fcb       $E6,$66,$6C,$78
                    fcb       $6C,$66,$E6,$00
                    fcb       $F0,$60,$60,$60
                    fcb       $62,$66,$FE,$00
                    fcb       $C6,$EE,$FE,$FE
                    fcb       $D6,$C6,$C6,$00
                    fcb       $C6,$E6,$F6,$DE
                    fcb       $CE,$C6,$C6,$00
                    fcb       $38,$6C,$C6,$C6
                    fcb       $C6,$6C,$38,$00
                    fcb       $FC,$66,$66,$7C
                    fcb       $60,$60,$F0,$00
                    fcb       $78,$CC,$CC,$CC
                    fcb       $DC,$78,$1C,$00
                    fcb       $FC,$66,$66,$7C
                    fcb       $6C,$66,$E6,$00
                    fcb       $78,$CC,$E0,$70
                    fcb       $1C,$CC,$78,$00
                    fcb       $FC,$B4,$30,$30
                    fcb       $30,$30,$78,$00
                    fcb       $CC,$CC,$CC,$CC
                    fcb       $CC,$CC,$FC,$00
                    fcb       $CC,$CC,$CC,$CC
                    fcb       $CC,$78,$30,$00
                    fcb       $C6,$C6,$C6,$D6
                    fcb       $FE,$EE,$C6,$00
                    fcb       $C6,$C6,$6C,$38
                    fcb       $38,$6C,$C6,$00
                    fcb       $CC,$CC,$CC,$78
                    fcb       $30,$30,$78,$00
                    fcb       $FE,$C6,$8C,$18
                    fcb       $32,$66,$FE,$00
                    fcb       $78,$60,$60,$60
                    fcb       $60,$60,$78,$00
                    fcb       $C0,$60,$30,$18
                    fcb       $0C,$06,$02,$00
                    fcb       $78,$18,$18,$18
                    fcb       $18,$18,$78,$00
                    fcb       $10,$38,$6C,$C6
                    fcb       $00,$00,$00,$00
                    fcb       $00,$00,$00,$00
                    fcb       $00,$00,$00,$FF
                    fcb       $30,$30,$18,$00
                    fcb       $00,$00,$00,$00
                    fcb       $00,$00,$78,$0C
                    fcb       $7C,$CC,$76,$00
                    fcb       $E0,$60,$60,$7C
                    fcb       $66,$66,$DC,$00
                    fcb       $00,$00,$78,$CC
                    fcb       $C0,$CC,$78,$00
                    fcb       $1C,$0C,$0C,$7C
                    fcb       $CC,$CC,$76,$00
                    fcb       $00,$00,$78,$CC
                    fcb       $FC,$C0,$78,$00
                    fcb       $38,$6C,$60,$F0
                    fcb       $60,$60,$F0,$00
                    fcb       $00,$00,$76,$CC
                    fcb       $CC,$7C,$0C,$F8
                    fcb       $E0,$60,$6C,$76
                    fcb       $66,$66,$E6,$00
                    fcb       $30,$00,$70,$30
                    fcb       $30,$30,$78,$00
                    fcb       $0C,$00,$0C,$0C
                    fcb       $0C,$CC,$CC,$78
                    fcb       $E0,$60,$66,$6C
                    fcb       $78,$6C,$E6,$00
                    fcb       $70,$30,$30,$30
                    fcb       $30,$30,$78,$00
                    fcb       $00,$00,$CC,$FE
                    fcb       $FE,$D6,$C6,$00
                    fcb       $00,$00,$F8,$CC
                    fcb       $CC,$CC,$CC,$00
                    fcb       $00,$00,$78,$CC
                    fcb       $CC,$CC,$78,$00
                    fcb       $00,$00,$DC,$66
                    fcb       $66,$7C,$60,$F0
                    fcb       $00,$00,$76,$CC
                    fcb       $CC,$7C,$0C,$1E
                    fcb       $00,$00,$DC,$76
                    fcb       $66,$60,$F0,$00
                    fcb       $00,$00,$7C,$C0
                    fcb       $78,$0C,$F8,$00
                    fcb       $10,$30,$7C,$30
                    fcb       $30,$34,$18,$00
                    fcb       $00,$00,$CC,$CC
                    fcb       $CC,$CC,$76,$00
                    fcb       $00,$00,$CC,$CC
                    fcb       $CC,$78,$30,$00
                    fcb       $00,$00,$C6,$D6
                    fcb       $FE,$FE,$6C,$00
                    fcb       $00,$00,$C6,$6C
                    fcb       $38,$6C,$C6,$00
                    fcb       $00,$00,$CC,$CC
                    fcb       $CC,$7C,$0C,$F8
                    fcb       $00,$00,$FC,$98
                    fcb       $30,$64,$FC,$00
                    fcb       $1C,$30,$30,$E0
                    fcb       $30,$30,$1C,$00
                    fcb       $18,$18,$18,$00
                    fcb       $18,$18,$18,$00
                    fcb       $E0,$30,$30,$1C
                    fcb       $30,$30,$E0,$00
                    fcb       $76,$DC,$00,$00
                    fcb       $00,$00,$00,$00
                    fcb       $00,$10,$38,$6C
                    fcb       $C6,$C6,$FE,$00

* Platform renderer implementation, selected during assembly.
                    use       platform/render-glyphs.asm

EndPad              fcb       $00,$00,$00,$00
                    fcb       $00,$00,$00,$00
EndName             fcc       /scrn/
EndNull             fcb       $00

                    emod
eom                 equ       *
                    end

