* AGI resource LZW primitives. Included once; emits no code until expanded.
SHARED_RESOURCE_LZW_DEFINED equ 1

* Extract a code from a three-byte little-endian window. B=bit alignment
* (0..7). Parameters: high byte, low word, width byte, mask table, shift
* label, mask label. D returns the code; X/B are scratch. Byte acquisition
* and source bounds remain with the owner. The production width is 9..11.
RESOURCE_LZW_EXTRACT macro
                    beq       \6
\5                  lsr       <\1
                    ror       <\2
                    ror       <\2+1
                    decb
                    bne       \5
\6                  ldb       <\3
                    subb      #9
                    lslb
                    leax      >\4,pcr
                    abx
                    ldd       <\2
                    anda      ,x
                    andb      $01,x
                    endm

* Retain the legacy 12-bit mask entry, although AGI stops growing at 11 bits.
RESOURCE_LZW_MASKS macro
                    fcb       1,$ff,3,$ff,7,$ff,$0f,$ff
                    endm

* Follow dictionary prefixes and push suffix bytes until reaching a literal.
* D is the initial code. Providers retain bounds, entry addressing and the
* stack policy; register parameter selects the owner's dictionary cursor.
* Parameters: loop label, literal continuation, dictionary register.
RESOURCE_LZW_WALK macro
\1                  cmpd      #$0100
                    bcs       \2
                    LZW_CHAIN_VALIDATE
                    LZW_CHAIN_PREPARE
                    LZW_CHAIN_SCALE
                    LZW_CHAIN_BASE
                    lea\3     d,\3
                    ldb       $02,\3
                    LZW_CHAIN_PUSH
                    ldd       ,\3
                    LZW_CHAIN_RETAIN
                    bra       \1
                    endm
