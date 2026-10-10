                    ifndef COCO_JOYSTICK_BINDINGS
COCO_JOYSTICK_BINDINGS equ 1
* Axis reads for the common direction classifier. CoCo Y increases upward.
COCO_JOYSTICK_X macro
                    ldb       1,x
                    endm
COCO_JOYSTICK_Y macro
                    ldb       2,x
                    endm
                    endc
* coco-input feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_COCO_JOYSTICK_INPUT
* ===== coco-joystick-input =====
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

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_KEYBOARD_INPUT
* ===== coco-keyboard-input =====
* CoCo platform boundary: keyboard-input.
* Included in place; see ../../PORTABILITY.md.

ReadStdinByte       leas      -$03,s    allocate three local bytes
                    sty       ,s        save Y register
                    lda       #$00      path 0 = stdin
                    ldb       #$01      GetStt code 1 = check char avail
                    os9       I$GetStt  check if char is available
                    bcs       ReadStdinByteErr branch if error (no char)
                    lda       #$00      path 0 = stdin
                    ldy       #$0001    read 1 byte
                    leax      $02,s     point X to local read buffer
                    os9       I$Read    read one byte from stdin
                    bcs       ReadStdinByteErr branch if read failed
                    lda       $02,s     load the byte we just read
                    bra       ReadStdinByteRet return with character in A
                    cmpa      #$F4      (unreachable — dead code)
                    bne       ReadStdinByteRet branch if not $F4
                    lda       <$0068    load trace-mode flag
                    bne       ReadStdinByteAlt branch if trace mode on
                    lda       >$01AF    load misc-flags byte
                    ora       #$20      set trace-active bit
                    sta       >$01AF    store updated flags
                    lbsr      TraceInit initialize trace display
                    bra       ReadStdinByteErr return error
ReadStdinByteAlt    lda       >$01AF    load misc-flags byte
                    anda      #$DF      clear trace-active bit
                    sta       >$01AF    store updated flags
                    lbsr      TraceErase erase trace display
ReadStdinByteErr    clra                return zero = no char / error
ReadStdinByteRet    ldy       ,s        restore Y register
                    leas      $03,s     release local frame
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_TERMINAL_OPTIONS
* ===== coco-terminal-options =====
* CoCo screen backend: terminal-options.
* Included in place; see ../../PORTABILITY.md for the current contract.

DisableKbdInt       leas      <-$20,s   Make temp buffer to hold PD.OPT data
                    lda       #StdIn    $00 Get 32 byte PD.OPT from Std In
                    ldb       #SS.OPT   $00
                    leax      ,s        point to our temp buffer
                    os9       I$GetStt  make the call
                    bcs       SetOptsDone error goto exit sub

* NOTE: make sure following lines assemble into 5 bit, not 8 bit
*       These appear to be loading the  echo EOF, INT and QUIT with
*       null values and saving the original ones back to vars
*       since L0115 - L0118 were initialized with $00

                    lda       >EchoSave load saved echo value (initially 0)
                    ldb       PD.EKO-PD.OPT,x Get echo option
                    sta       PD.EKO-PD.OPT,x change echo option no echo
                    stb       >EchoSave Save original echo option

                    lda       >EofSave load saved EOF char value
                    ldb       PD.EOF-PD.OPT,x Change EOF char
                    sta       PD.EOF-PD.OPT,x disable EOF character
                    stb       >EofSave save original EOF character

                    lda       >IntSave load saved interrupt char value
                    ldb       <PD.INT-PD.OPT,x Change INTerrupt char (normally CTRL-C)
                    sta       <PD.INT-PD.OPT,x disable interrupt character
                    stb       >IntSave save original interrupt character

                    lda       >QuitSave load saved quit char value
                    ldb       <PD.QUT-PD.OPT,x Change QUIT char (normally CTRL-E)
                    sta       <PD.QUT-PD.OPT,x disable quit character
                    stb       >QuitSave save original quit character

*  set current options packet
*  SetStat Function Code $00
*          Writes the options section of the path descriptor
*          from the 32 byte area pointed to by reg X`
* entry:
*       a -> path number
*       b -> function code $00 (SS.OPT)
*       x -> address holding the status packet
*
* error:
*       CC -> Carry set on error
*       b  -> error code (if any)
*

*                                x is still pointing to our temp buff
                    lda       #StdIn    $00 Set VDG screen to new options
                    ldb       #SS.OPT   $00
                    os9       I$SetStt  set them to be our new values

SetOptsDone         leas      <$20,s    Eat temp stack & return
                    rts                 return from DisableKbdInt

                    else
                    error Unknown platform feature section
                    endc
                    endc
                    endc
