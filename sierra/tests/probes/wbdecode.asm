* Native mapped AGI picture decoder probe, not the game interpreter.
                    nam       wbdecode
WILDBITS            equ       1
                    use       platform/wildbits-defsfile
DECODE_PICTURE      equ       1
PICTURE_BOUNDED_READ equ       1
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
PLATFORM_SECTION    set PLATFORM_WILDBITS_RESOURCE_DATA
                    use platform/wildbits-memory-resources.asm
fillstack           rmb       4096
picturestage        rmb       512
                    rmb       1024
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbdecode/
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
help                fcc       /Usage: wbdecode game-directory picture-number >combined-file/
                    fcb       C$CR
                    emod
eom                 equ       *
                    end
