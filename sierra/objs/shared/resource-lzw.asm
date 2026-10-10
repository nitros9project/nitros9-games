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

* Create the next three-byte dictionary entry and advance its index.
* D=next index on entry; owner checks dictionary capacity before expansion.
* Parameters: cursor register, next-index word, previous-code word, first-byte
* field, optional retained-index scratch (0 means use next-index directly),
* suffix-first store order (1=legacy CoCo, 0=native). Base addressing uses the
* existing dictionary provider. Compile-time choices preserve owner bytes.
RESOURCE_LZW_INSERT macro
                    ifne      \5
                    std       <\5
                    addd      <\5
                    addd      <\5
                    else
                    addd      <\2
                    addd      <\2
                    endc
                    LZW_CHAIN_BASE
                    lea\1     d,\1
                    ifne      \6
                    ldb       <\4
                    stb       $02,\1
                    endc
                    ldd       <\3
                    std       ,\1
                    ifeq      \6
                    ldb       <\4
                    stb       $02,\1
                    endc
                    ldd       <\2
                    addd      #$0001
                    std       <\2
                    endm


* Restore the AGI dictionary's initial index, width and growth threshold.
* Parameters: next-index word, threshold word, width field, word-sized width,
* width-first order. Width-first and word-sized flags preserve CoCo's original
* adjacent state-byte reset; native retains its independent previous-code flag.
RESOURCE_LZW_WIDTH_RESET macro
                    ifne      \2
                    ldd       #9
                    std       <\1
                    else
                    lda       #9
                    sta       <\1
                    endc
                    endm
RESOURCE_LZW_RESET macro
                    ifne      \5
                    RESOURCE_LZW_WIDTH_RESET \3,\4
                    endc
                    ldd       #258
                    std       <\1
                    ldd       #512
                    std       <\2
                    ifeq      \5
                    RESOURCE_LZW_WIDTH_RESET \3,\4
                    endc
                    endm
