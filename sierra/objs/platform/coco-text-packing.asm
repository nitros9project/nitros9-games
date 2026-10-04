* CoCo packed-pixel renderer: text-packing.
* Keep optimized loops intact. See ../../PORTABILITY.md.

text_color          anda      #$0F      ; isolate foreground color nibble
                    sta       >$024C    ; store foreground color
                    lsla                ; shift foreground to high nibble (bit 3)
                    lsla                ; shift left (bit 2)
                    lsla                ; shift left (bit 1)
                    lsla                ; foreground now in high nibble of A
                    ora       >$024C    ; OR with stored foreground (packed nibbles)
                    sta       >$024C    ; store packed foreground color byte
                    andb      #$0F      ; isolate background color nibble
                    stb       >$024D    ; store background color
                    lslb                ; shift background to high nibble (bit 3)
                    lslb                ; shift left (bit 2)
                    lslb                ; shift left (bit 1)
                    lslb                ; background now in high nibble of B
                    orb       >$024D    ; OR with stored background (packed nibbles)
                    stb       >$024D    ; store packed background color byte
                    rts
