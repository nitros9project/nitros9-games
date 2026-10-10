* wildbits-input feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_INPUT_CODE
* ===== wildbits-input-code =====
InputInitialize     clr       <vmkeycount
                    clr       <vmhavekey
                    ldu       <resourcebase
                    leax      vmcontrollers,u
                    ldy       #32
                    clra
InputClearController sta      ,x+
                    leay      -1,y
                    bne       InputClearController
                    rts
SetKeyCommand       ldu       <resourcebase
                    leax      vmkeys,u
                    ldy       #0
InputFindKey        tfr       y,d
                    cmpb      <vmkeycount
                    bhs       InputAddKey
                    ldd       vmarguments,u
                    cmpd      ,x
                    beq       InputStoreKey
                    leax      3,x
                    leay      1,y
                    bra       InputFindKey
InputAddKey         ldb       <vmkeycount
                    cmpb      #50
                    bhs       InputKeyFull
                    inc       <vmkeycount
InputStoreKey       ldd       vmarguments,u
                    std       ,x
                    ldb       vmarguments+2,u
                    stb       2,x
                    clrb
                    rts
InputKeyFull        ldb       #E$MemFul
                    orcc      #1
                    rts
InputTest           ldb       <vmopcode
                    cmpb      #12
                    beq       InputControllerTest
                    cmpb      #13
                    beq       InputHaveKeyTest
                    cmpb      #14
                    beq       InputSaidTest
                    ldb       #E$UnkSvc
                    orcc      #1
                    rts
InputControllerTest ldu       <resourcebase
                    ldb       vmarguments,u
                    bsr      InputControllerAddress
                    bita      ,x
                    beq       InputTestFalse
InputTestTrue       ldb       #1
                    andcc     #$FE
                    rts
* B=controller (all 256 supported); X=private byte, A=one-bit mask.
InputControllerAddress pshs   b
                    andb      #7
                    leax      InputControllerMasks,pcr
                    lda       b,x
                    puls      b
                    lsrb
                    lsrb
                    lsrb
                    pshs      a
                    clra
                    leax      vmcontrollers,u
                    leax      d,x
                    puls      a,pc
InputControllerMasks fcb      1,2,4,8,16,32,64,128
InputHaveKeyTest
                    ifne      GAME_PRESENTATION
* Scripts clear v19 to request a fresh key, including inside a logic loop.
* The submitting key's cycle flag must not satisfy that request.
                    ldu       <resourcebase
                    ldb       vmvariables+19,u
                    bne       InputTestTrue
                    lbra      GameHaveKeyWait
                    else
                    ldb       <vmhavekey
                    andcc     #$FE
                    rts
                    endc
InputSaidTest       ldu       <resourcebase
                    tst       vmflags+2,u
                    beq       InputTestFalse
                    ifne      GAME_PRESENTATION
                    lbra      ParserSaid
                    endc
* The bytecode-only probe does not own a vocabulary parser.
                    ldb       #E$UnkSvc
                    orcc      #1
                    rts
InputTestFalse      clrb
                    rts

                    ifne      GAME_PRESENTATION
* Digital stick 0 through the terminal driver. Never read hardware directly.
GameJoystickCommand lbsr      AssetUnmap
                    lbcs      GameJoystickReturn
                    ldu       <resourcebase
                    lda       joystickenabled,u
                    eora      #1
                    sta       joystickenabled,u
                    beq       GameJoystickStop
                    clra
                    ldb       #SS.Joy
                    ldx       #0
                    os9       I$GetStt
                    ldu       <resourcebase
                    bcs       GameJoystickUnavailable
                    anda      #3
                    sta       joystickbuttons,u
                    clr       joystickpressed,u
                    clr       joysticklast,u
                    clrb
                    rts
GameJoystickUnavailable clr   joystickenabled,u
                    clr       joysticklast,u
                    lbra      GameVersionCommand
GameJoystickStop    lda       joysticklast,u
                    cmpa      vmvariables+6,u
                    bne       GameJoystickForget
                    clr       vmvariables+6,u
GameJoystickForget  clr       joysticklast,u
                    clr       joystickbuttons,u
                    clr       joystickpressed,u
GameJoystickDone    clrb
GameJoystickReturn  rts

* Poll once per completed cycle, after foreground gating and before motion.
* Release only a direction this stick still owns; retain keyboard/script changes.
GamePollJoystick    ldu       <resourcebase
                    tst       joystickenabled,u
                    lbeq      GameJoystickDone
                    clra
                    ldb       #SS.Joy
                    ldx       #0
                    os9       I$GetStt
                    ldu       <resourcebase
                    lbcs      GameJoystickDisable
                    anda      #3
                    tfr       a,b
                    lda       joystickpressed,u
                    cmpa      #$FF
                    beq       GameJoystickPrime
                    tfr       b,a
                    eora      joystickbuttons,u
                    pshs      b
                    anda      ,s+
                    sta       joystickpressed,u
                    stb       joystickbuttons,u
                    bra       GameJoystickMotion
GameJoystickPrime   stb       joystickbuttons,u
                    clr       joystickpressed,u
GameJoystickMotion  tst       <vmplayercontrol
                    beq       GameJoystickNoMotion
                    use shared/object-move-direction.asm
WILDBITS_JOYSTICK_X macro
                    tfr       x,d
                    endm
WILDBITS_JOYSTICK_Y macro
                    tfr       y,d
                    endm
                    JOYSTICK_DIRECTION 128,128,WILDBITS_JOYSTICK_X,WILDBITS_JOYSTICK_Y,GameJoystickDirections
GameJoystickLeft equ JoystickLeft
GameJoystickRight equ JoystickRight
GameJoystickColumn equ JoystickColumn
GameJoystickUp equ JoystickUp
GameJoystickDown equ JoystickDown
GameJoystickRow equ JoystickRow
                    beq       GameJoystickRelease
                    sta       joysticklast,u
                    sta       vmvariables+6,u
                    bra       GameJoystickButton
GameJoystickRelease lda       joysticklast,u
                    cmpa      vmvariables+6,u
                    bne       GameJoystickNoMotion
                    clr       vmvariables+6,u
GameJoystickNoMotion clr      joysticklast,u
GameJoystickButton  lda       joystickpressed,u
                    lbeq      GameJoystickDone
                    ldb       #13
                    bita      #1
                    bne       GameJoystickKey
                    ldb       #27
GameJoystickKey     stb       <vmkeybyte
                    stb       vmvariables+19,u
                    lda       #1
                    sta       <vmhavekey
                    clr       gamekeyscan,u
                    leax      vmkeys,u
                    ldy       #0
                    lbra      GameKeyBinding
GameJoystickDisable clr       joystickenabled,u
                    lbra      GameJoystickStop
GameJoystickDirections JOYSTICK_DIRECTION_TABLE 0
                    endc

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_INPUT_DATA
* ===== wildbits-input-data =====
* Private keyboard/controller controls. Device I/O belongs to the game loop.
vmkeycount          rmb       1
vmhavekey           rmb       1
vmkeybyte           rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_LINE_INPUT_CODE
* ===== wildbits-line-input-code =====
* get.string/get.num use a modal bounded editor; pending game input is saved.
* Cancel pending parser input; the ordinary cycle redraws its prompt row.
ParserClearLine     ldu       <resourcebase
                    clr       parserlength,u
                    clr       parserline,u
                    clrb
                    rts
GameCancelLine      lbsr      ParserClearLine
                    tst       <vminputenabled
                    lbne      ParserInputVisible
                    clrb
                    rts
* Echo the previous command suffix, preserving an already typed prefix.
* Match CoCo input_echo, bounded by the native editor's 38-byte capacity.
GameEchoLine        ldu       <resourcebase
                    tst       <vminputenabled
                    beq       GameEchoDone
                    leax      parserlastline,u
                    clrb
GameEchoLength      cmpb      #38
                    bhs       GameEchoHaveLength
                    tst       b,x
                    beq       GameEchoHaveLength
                    incb
                    bra       GameEchoLength
GameEchoHaveLength  cmpb      parserlength,u
                    bls       GameEchoDone
                    pshs      b
                    ldb       parserlength,u
                    leay      parserline,u
GameEchoCopy        lda       b,x
                    sta       b,y
                    incb
                    cmpb      ,s
                    blo       GameEchoCopy
                    leas      1,s
                    clr       b,y
                    stb       parserlength,u
                    lbra      ParserInputVisible
GameEchoDone        clrb
                    rts
GameGetInput        ldu       <resourcebase
                    lda       #1
                    sta       dialoginputmode,u
                    lda       <vmopcode
                    cmpa      #118
                    beq       GameGetNumber
                    lda       vmarguments,u
                    cmpa      #12
                    lbhs      GameGetInvalid
                    lda       vmarguments+2,u
                    cmpa      #25
                    lbhs      GameGetInvalid
                    sta       inventoryrow,u
                    lda       vmarguments+3,u
                    cmpa      #40
                    lbhs      GameGetInvalid
                    sta       inventorykey,u
                    lda       vmarguments+4,u
                    cmpa      #39
                    lbhi      GameGetInvalid
                    sta       inventorypaint,u
                    ldb       vmarguments+1,u
                    bra       GameGetSave
GameGetNumber       lda       #2
                    sta       dialoginputmode,u
                    sta       inventorykey,u
                    lda       #10
                    sta       inventoryrow,u
                    lda       #3
                    sta       inventorypaint,u
                    ldb       vmarguments,u
GameGetSave         pshs      b
                    leax      parserline,u
                    leay      resourcecommands+2000,u
                    ldb       #40
GameGetSaveByte     lda       ,x+
                    sta       ,y+
                    decb
                    bne       GameGetSaveByte
                    lda       parserlength,u
                    sta       ,y
                    lbsr      ParserClearLine
                    puls      b
                    lbsr      GamePrintMessage
                    pshs      cc,b
                    bcs       GameGetRestore
                    ldu       <resourcebase
                    lda       dialoginputmode,u
                    cmpa      #2
                    beq       GameGetCommitNumber
                    lda       vmarguments,u
                    ldb       #40
                    mul
                    leay      vmstrings,u
                    leay      d,y
                    leax      parserline,u
GameGetCommitString lda      ,x+
                    sta       ,y+
                    bne       GameGetCommitString
                    bra       GameGetRestore
GameGetCommitNumber leax      parserline,u
                    bsr      AtoI
                    tfr       a,b
GameGetNumberStore  leay      vmvariables,u
                    lda       vmarguments+1,u
                    pshs      b
                    tfr       a,b
                    clra
                    leay      d,y
                    puls      b
                    stb       ,y
GameGetRestore      ldu       <resourcebase
                    leax      resourcecommands+2000,u
                    leay      parserline,u
                    ldb       #40
GameGetRestoreByte  lda       ,x+
                    sta       ,y+
                    decb
                    bne       GameGetRestoreByte
                    lda       ,x
                    sta       parserlength,u
                    clr       dialoginputmode,u
                    puls      cc,b,pc
GameGetInvalid      clr       dialoginputmode,u
                    lbra      ObjectBadIndex
                    use       shared/decimal-byte.asm
* A=1 finished, A=0 continue; C/error B. No vocabulary submission here.
GameLineKey         ldu       <resourcebase
                    lda       parsercharacter,u
                    cmpa      #13
                    lbeq      GameLineDone
                    cmpa      #5
                    beq       GameLineCancel
                    cmpa      #27
                    bne       GameLineBackspaceTest
GameLineCancel      clr       parserline,u
                    clr       parserlength,u
                    lbra      GameLineDone
GameLineBackspaceTest cmpa    #8
                    bne       GameLinePrintable
                    ldb       parserlength,u
                    beq       GameLineDraw
                    decb
                    stb       parserlength,u
                    leax      parserline,u
                    clr       b,x
                    bra       GameLineDraw
GameLinePrintable   cmpa      #32
                    blo       GameLineDraw
                    cmpa      #126
                    bhi       GameLineDraw
                    ldb       dialoginputmode,u
                    cmpb      #2
                    bne       GameLineStore
                    cmpa      #'0
                    blo       GameLineDraw
                    cmpa      #'9
                    bhi       GameLineDraw
GameLineStore       ldb       parserlength,u
                    cmpb      inventorypaint,u
                    bhs       GameLineDraw
                    cmpb      #39
                    bhs       GameLineDraw
                    leax      parserline,u
                    sta       b,x
                    incb
                    stb       parserlength,u
                    clr       b,x
GameLineDraw        ldx       <resourcebase
                    lda       inventoryrow,x
                    sta       textrow,x
                    ldb       #40
                    mul
                    addb      inventorykey,x
                    adca      #0
                    std       textindex,x
                    leay      textcharacters,x
                    leay      d,y
                    lda       inventorykey,x
                    sta       textcolumn,x
                    ldb       #40
                    subb      inventorykey,x
GameLineBlank       lda       #32
                    sta       ,y
                    lda       #$0F
                    sta       1000,y
                    leay      1,y
                    decb
                    bne       GameLineBlank
                    ldd       textindex,x
                    leay      textcharacters,x
                    leay      d,y
                    leau      parserline,x
                    ldb       #40
                    subb      inventorykey,x
GameLineCopy        lda       ,u+
                    beq       GameLineCursor
                    sta       ,y+
                    decb
                    bne       GameLineCopy
                    bra       GameLineShow
GameLineCursor      lda       #'_
                    sta       ,y
GameLineShow        lda       inventoryrow,x
                    ldb       #40
                    mul
                    addd      #40
                    std       textend,x
                    lbsr      GameDrawTextRange
                    bcs       GameLineReturn
                    clra
GameLineReturn      rts
GameLineDone        lda       #1
                    clrb
                    rts

GameWordToString    ldu       <resourcebase
                    ldb       vmarguments,u
                    beq       GameWordInvalid
                    cmpb      #20
                    bhi       GameWordInvalid
                    lda       parsercount,u
                    tst       vmvariables+9,u
                    beq       GameWordBound
                    inca
GameWordBound       pshs      a
                    cmpb      ,s+
                    bhi       GameWordInvalid
                    lda       vmarguments+1,u
                    cmpa      #12
                    bhs       GameWordInvalid
                    pshs      b
                    ldb       #40
                    mul
                    leay      vmstrings,u
                    leay      d,y
                    puls      b
                    decb
                    leax      parseroffsets,u
                    leax      b,x
                    lda       ,x
                    ldb       20,x
                    leax      parserlastline,u
                    leax      a,x
GameWordCopy        tstb
                    beq       GameWordEnd
                    lda       ,x+
                    sta       ,y+
                    decb
                    bra       GameWordCopy
GameWordEnd         clr       ,y
                    clrb
                    rts
GameWordInvalid     lbra      ObjectBadIndex

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_TERMINAL_OPTIONS
* ===== wildbits-terminal-options =====
* Restore only the options this process changes. Keep CTRL-C as an interrupt.
GameTerminalEnter   leas      -32,s
                    leax      ,s
                    clra
                    ldb       #SS.Opt
                    os9       I$GetStt
                    bcs       GameTerminalReturn
                    tst       ,x
                    bne       GameTerminalInvalid
                    ldu       <resourcebase
                    lda       PD.EKO-PD.OPT,x
                    sta       terminalecho,u
                    lda       PD.EOF-PD.OPT,x
                    sta       terminaleof,u
                    lda       PD.QUT-PD.OPT,x
                    sta       terminalquit,u
                    clr       PD.EKO-PD.OPT,x
                    clr       PD.EOF-PD.OPT,x
                    clr       PD.QUT-PD.OPT,x
                    lda       #1
                    sta       terminalchanged,u
                    clra
                    ldb       #SS.Opt
                    os9       I$SetStt
GameTerminalReturn  leas      32,s
                    rts
GameTerminalInvalid ldb       #E$BMode
                    orcc      #1
                    bra       GameTerminalReturn
GameTerminalRestore ldu       <resourcebase
                    tst       terminalchanged,u
                    beq       GameTerminalSuccess
                    leas      -32,s
                    leax      ,s
                    clra
                    ldb       #SS.Opt
                    os9       I$GetStt
                    bcs       GameTerminalReturn
                    ldu       <resourcebase
                    lda       terminalecho,u
                    sta       PD.EKO-PD.OPT,x
                    lda       terminaleof,u
                    sta       PD.EOF-PD.OPT,x
                    lda       terminalquit,u
                    sta       PD.QUT-PD.OPT,x
                    clra
                    ldb       #SS.Opt
                    os9       I$SetStt
                    bcs       GameTerminalReturn
                    ldu       <resourcebase
                    clr       terminalchanged,u
                    bra       GameTerminalReturn
GameTerminalSuccess clrb
                    rts

                    else
                    error Unknown platform feature section
                    endc
                    endc
                    endc
                    endc
