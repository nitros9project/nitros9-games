* Native resource-to-display integration, not yet the game interpreter.
                    nam       wbrun
WILDBITS            equ       1
                    use       platform/wildbits-defsfile
DECODE_PICTURE      equ       1
PICTURE_BOUNDED_READ equ       1
PRESENT_PICTURE     equ       1
                    use       platform/wildbits-presentation.d
cmd_start           equ       $F0
x_max               equ       159
y_max               equ       167
PICBUFF_WIDTH       equ       160
argdirectory        rmb       2
argnumber           rmb       2
argdigit            rmb       1
                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_DECODER_DATA
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_PRESENTATION_DATA
                    use platform/wildbits-graphics.asm
presentoffset       rmb       2
PLATFORM_SECTION    set PLATFORM_WILDBITS_RESOURCE_DATA
                    use platform/wildbits-memory-resources.asm
fillstack           rmb       4096
picturestage        rmb       512
PLATFORM_SECTION    set PLATFORM_WILDBITS_PRESENTATION_BUFFERS
                    use platform/wildbits-graphics.asm
                    rmb       1024
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbrun/
                    fcb       1
PLATFORM_SECTION    set PLATFORM_WILDBITS_RESOURCE_CLI
                    use platform/wildbits-memory-resources.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_RESOURCE_CODE
                    use platform/wildbits-memory-resources.asm
                    use       platform/wildbits-decoder-code.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_DECODER_LINES
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_PICTURE_MEMORY
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_DECODER_FILL
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_DECODER_PEN
                    use platform/wildbits-graphics.asm
* Assembly-time platform selection.
* CoCo entry: gfx_picbuff_update, legacy module ABI.
* Wild Bits entries: PresentPicture/PresentationRelease, native private ABI.
* Callers must supply the selected state contract; these are not ABI aliases.
                    ifne      WILDBITS
PLATFORM_SECTION    set PLATFORM_WILDBITS_PRESENTATION
                    use platform/wildbits-graphics.asm
                    else
PLATFORM_SECTION    set PLATFORM_COCO_PRESENTATION
                    use platform/coco-graphics.asm
                    endc
PLATFORM_SECTION    set PLATFORM_WILDBITS_PRESENTATION_HELPERS
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_PRESENTATION_PALETTE
                    use platform/wildbits-graphics.asm
help                fcc       /Usage: wbrun game-directory picture-number; any key exits/
                    fcb       C$CR
                    emod
eom                 equ       *
                    end
