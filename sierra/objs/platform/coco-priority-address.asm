* CoCo platform boundary: priority-address.
* Included in place; see ../../PORTABILITY.md.

CalcPriAddr         suba      <$005F    subtract priority base row offset
                    ldb       #$20      bytes per priority strip = 32
                    mul                 A×32 = byte offset into strip
                    exg       b,a       swap bytes (shift left 8)
                    subd      #$2000    subtract $2000 for final addr
                    leau      d,u       advance U by computed offset
                    rts
*
*======================================================================
* PRIORITY COORDINATE CALCULATION
*   Converts a screen Y coordinate to a priority value and maps a view's
*   logic page into the address space.
*======================================================================
*
CalcPriCoord        tfr       u,d       transfer priority address to D
                    anda      #$1F      isolate column within strip
                    adda      #$20      add $20 base column
                    exg       d,u       swap D and U
                    lsra                shift right (divide by 2)
                    lsra                shift right
                    lsra                shift right
                    lsra                shift right
                    lsra                shift right (divide by 32)
                    adda      <$005F    add priority base row to result
                    tfr       a,b       copy row to B
                    incb                increment for 1-based row
                    rts
