* Shared F0-F3 color/mask commands; bounded reads selected at assembly time.
EnablePicDraw       ldd       <DrawColor pulls in color and sbuff_drawmask
                    anda      #$f0      and color with $F0
                    ifne      PICTURE_BOUNDED_READ
                    pshs      d
                    lbsr      ReadColor
                    sta       <decodevalue
                    puls      d
                    ora       <decodevalue
                    else
                    ora       ,x+
                    endc       or that result with the pic_byte and bump to next
                    orb       #$0f      or the sbuff_drawmask with $0F
                    std       <DrawColor store the updated values
                    ifne      PICTURE_BOUNDED_READ
                    lbsr      ReadNext       return value ignored so this just bumps to next pic_byte
                    else
                    lda       ,x+
                    endc
                    rts                 return to pic_cmd_loop


* Command $F1 Disable picture draw
*  disable_pic_draw()
*
*  DrawColor = color
*  DrawMask = sbuff_drawmask
*  x contains pointer to given_pic_data known as the pic_byte
*  after ldd
*  a contains color
*  b contains draw mask
*  returns the next pic_byte in a

DisablePicDraw      ldd       <DrawColor pulls in color and sbuff_drawmask
                    ora       #$0f      ors color with $0F (white ??)
                    andb      #$f0      ands draw mask with $F0
                    std       <DrawColor store the updated values
                    ifne      PICTURE_BOUNDED_READ
                    lbsr      ReadNext       return value ignored so this just bumps to next pic_byte
                    else
                    lda       ,x+
                    endc
                    rts                 return to pic_cmd_loop

* Command $F2 Changes priority color and enables priority draw
*  enable_pri_draw() pic_render.c
*
*  DrawColor = color
*  DrawMask = sbuff_drawmask
*  x contains pointer to given_pic_data known as the pic_byte
*  after ldd
*  a contains color
*  b contains draw mask
*  returns the next pic_byte in a

EnablePriDraw       ldd       <DrawColor pulls in color and sbuff_drawmask
                    anda      #$0f      ands color with $0F
                    sta       <DrawColor save color
                    ifne      PICTURE_BOUNDED_READ
                    lbsr      ReadColor
                    else
                    lda       ,x+
                    endc
                    asla                times 2 with sign extend
                    asla                again times 2
                    asla                and again times 2
                    asla                end result is multiply pic_byte by 16 ($10)
                    ora       <DrawColor or that value with the modified color
                    orb       #$f0      or the sbuff_drawmask with $F0
                    std       <DrawColor store the updated values
                    ifne      PICTURE_BOUNDED_READ
                    lbsr      ReadNext       return value ignored so this just bumps to next pic_byte
                    else
                    lda       ,x+
                    endc
                    rts                 return to pic_cmd_loop

* Command $F3 Disable priority draw
*  diasable_pri_draw() pic_render.c
*
*  DrawColor = color
*  DrawMask = sbuff_drawmask
*  x contains pointer to given_pic_data known as the pic_byte
*  after ldd
*  a contains color
*  b contains draw mask
*  returns the next pic_byte in a


DisablePriDraw      ldd       <DrawColor pulls in color and sbuff_drawmask
                    ora       #$f0      or the color with $F0
                    andb      #$0f      and the sbuff_drawmask with $0F
                    std       <DrawColor store the updated values
                    ifne      PICTURE_BOUNDED_READ
                    lbsr      ReadNext       return value ignored so this just bumps to next pic_byte
                    else
                    lda       ,x+
                    endc
                    rts                 return to pic_cmd_loop

