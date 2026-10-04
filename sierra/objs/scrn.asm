                    use       buffer-layout.d

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

                    use       font-data.asm

* Platform renderer implementation, selected during assembly.
                    use       platform/render-glyphs.asm

EndPad              fcb       $00,$00,$00,$00
                    fcb       $00,$00,$00,$00
EndName             fcc       /scrn/
EndNull             fcb       $00

                    emod
eom                 equ       *
                    end

