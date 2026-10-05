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
                    use       platform/wildbits-decoder-data.asm
                    use       platform/wildbits-presentation-data.asm
presentoffset       rmb       2
                    use       platform/wildbits-resource-data.asm
fillstack           rmb       4096
picturestage        rmb       512
                    use       platform/wildbits-presentation-buffers.asm
                    rmb       1024
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbrun/
                    fcb       1
                    use       platform/wildbits-resource-cli.asm
                    use       platform/wildbits-resource-code.asm
                    use       platform/wildbits-decoder-code.asm
                    use       platform/wildbits-decoder-lines.asm
                    use       platform/wildbits-picture-memory.asm
                    use       platform/wildbits-decoder-fill.asm
                    use       platform/wildbits-decoder-pen.asm
                    use       platform/presentation.asm
                    use       platform/wildbits-presentation-helpers.asm
                    use       platform/wildbits-presentation-palette.asm
help                fcc       /Usage: wbrun game-directory picture-number; any key exits/
                    fcb       C$CR
                    emod
eom                 equ       *
                    end
