* Native resource-to-display integration, not yet the game interpreter.
                    nam       wbrun
WILDBITS            equ       1
                    use       defsfile
DECODE_PICTURE      equ       1
PICTURE_BOUNDED_READ equ       1
PRESENT_PICTURE     equ       1
                    use       presentation.d
cmd_start           equ       $F0
x_max               equ       159
y_max               equ       167
PICBUFF_WIDTH       equ       160
argdirectory        rmb       2
argnumber           rmb       2
argdigit            rmb       1
                    use       decoder-data.asm
                    use       presentation-data.asm
presentoffset       rmb       2
                    use       resource-data.asm
fillstack           rmb       4096
picturestage        rmb       512
                    use       presentation-buffers.asm
                    rmb       1024
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbrun/
                    fcb       1
                    use       resource-cli.asm
                    use       resource-code.asm
                    use       decoder-code.asm
                    use       decoder-lines.asm
                    use       platform/wildbits-picture-memory.asm
                    use       decoder-fill.asm
                    use       decoder-pen.asm
                    use       platform/presentation.asm
                    use       platform/wildbits-presentation-helpers.asm
                    use       platform/wildbits-presentation-palette.asm
help                fcc       /Usage: wbrun game-directory picture-number; any key exits/
                    fcb       C$CR
                    emod
eom                 equ       *
                    end
