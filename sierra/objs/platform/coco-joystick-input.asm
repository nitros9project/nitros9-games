* CoCo platform boundary: joystick-input.
* Included in place; see ../../PORTABILITY.md.

ReadJoystick        pshs      y         save Y register across system call
                    lda       #$00      path number 0
                    ldb       #$13      GetStt code $13 = read joystick
                    ldx       <$0096    load joystick path descriptor
                    os9       I$GetStt  read joystick position
                    tfr       x,d       transfer result X to D
                    leax      >JoystickData,pcr point to joystick-data buffer
                    sty       $01,x     store Y-axis value
                    std       ,x        store X and button bytes
                    puls      y         restore Y register
                    rts
ReadJoyButton       pshs      y         save Y register across system call
                    lda       #$00      path number 0
                    ldb       #$13      GetStt code $13 = read joystick
                    ldx       <$0096    load joystick path descriptor
                    os9       I$GetStt  read joystick button state
                    sta       >$0541    store button-pressed flag
                    puls      y         restore Y register
                    rts
