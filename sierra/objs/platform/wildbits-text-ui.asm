* Immutable text-store backend executes while wbstate remains linked.
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_TEXT_STORE_CODE
AuxTextStore        tst       dialogactive,u
                    beq       GameTextRead
                    tst       dialogwordstart,u
                    beq       GameTextRead
                    lda       textcolumn,u
                    cmpa      dialogleft,u
                    bls       GameTextRead
                    ldx       textpointer,u
                    clrb
GameTextWordLength  lda       b,x
                    beq       GameTextWordEnd
                    cmpa      #32
                    beq       GameTextWordEnd
                    cmpa      #10
                    beq       GameTextWordEnd
                    cmpa      #13
                    beq       GameTextWordEnd
                    incb
                    cmpb      #40
                    blo       GameTextWordLength
GameTextWordEnd     addb      textcolumn,u
                    cmpb      dialogright,u
                    bls       GameTextRead
                    lda       dialogleft,u
                    sta       textcolumn,u
                    inc       textrow,u
                    lda       textrow,u
                    cmpa      #25
                    lbhs      AuxTextPresent
GameTextRead        ldx       textpointer,u
                    lda       ,x+
                    stx       textpointer,u
                    tsta
                    lbeq     AuxTextPresent
                    cmpa      #10
                    beq       GameTextNewline
                    cmpa      #13
                    beq       GameTextNewline
                    tst       dialogactive,u
                    beq       GameTextCharacter
                    clr       dialogwordstart,u
                    cmpa      #32
                    bne       GameTextCharacter
                    inc       dialogwordstart,u
                    ldb       textcolumn,u
                    cmpb      dialogleft,u
                    lbeq     AuxTextStore
GameTextCharacter   pshs      a
                    lda       textrow,u
                    ldb       #40
                    mul
                    addb      textcolumn,u
                    adca      #0
                    leax      textcharacters,u
                    leax      d,x
                    puls      a
                    sta       ,x
* Color cells follow characters at the same fixed offset. Reuse the cell
* address rather than multiplying its row a second time.
                    lda       <vmtextforeground
                    lsla
                    lsla
                    lsla
                    lsla
                    ora       <vmtextbackground
                    sta       1000,x
                    inc       textcolumn,u
                    lda       textcolumn,u
                    cmpa      dialogright,u
                    lblo      AuxTextStore
GameTextNewline     clr       textcolumn,u
                    tst       dialogactive,u
                    beq       GameTextAdvanceRow
                    lda       dialogleft,u
                    sta       textcolumn,u
                    lda       #1
                    sta       dialogwordstart,u
GameTextAdvanceRow  inc       textrow,u
                    lda       textrow,u
                    cmpa      #25
                    lblo      AuxTextStore
AuxTextPresent      jmp       ,y
                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_DIALOG_WAIT_CODE
* Read-only modal loop. Timer and callback state belong to this process.
AuxPrintWait        pshs      y
                    lda       gameclockreset,u
                    sta       dialogepoch,u
                    tst       dialoginputmode,u
                    bne       AuxWaitUntimed
                    lda       <vmopcode
                    cmpa      #101
                    beq       AuxWaitTimer
                    cmpa      #102
                    beq       AuxWaitTimer
                    cmpa      #151
                    blo       AuxWaitUntimed
                    cmpa      #152
                    bhi       AuxWaitUntimed
AuxWaitTimer        ldb       vmvariables+21,u
                    lda       #30
                    mul
                    std       dialogticks,u
                    beq       AuxWaitUntimed
                    lda       #1
                    sta       dialogtimed,u
                    lda       gameclockpath,u
                    cmpa      #$FF
                    beq       AuxWaitLoop
                    lbsr      AuxWaitSample
                    bcs       AuxWaitRestore
                    sta       dialogseen,u
                    lda       #2
                    sta       dialogtimed,u
                    bra       AuxWaitLoop
AuxWaitUntimed      clr       dialogtimed,u
AuxWaitLoop         ldy       ,s
                    ldd       ,y
                    leax      d,y
                    jsr       ,x
                    bcs       AuxWaitRestore
                    lda       #0
                    ldb       #SS.Ready
                    os9       I$GetStt
                    bcc       AuxWaitKey
                    cmpb      #E$NotRdy
                    bne       AuxWaitRestore
                    ldx       #2
                    os9       F$Sleep
                    ldu       <resourcebase
                    lda       dialogtimed,u
                    beq       AuxWaitLoop
                    cmpa      #2
                    bne       AuxWaitOneTick
                    lbsr      AuxWaitSample
                    bcs       AuxWaitRestore
                    ldb       gameclockreset,u
                    cmpb      dialogepoch,u
                    beq       AuxWaitDelta
                    stb       dialogepoch,u
                    sta       dialogseen,u
                    lbra      AuxWaitLoop
AuxWaitDelta        suba      dialogseen,u
                    ldb       gameclockticks,u
                    stb       dialogseen,u
                    tfr       a,b
                    clra
                    bra       AuxWaitSubtract
AuxWaitOneTick      ldd       #1
AuxWaitSubtract     pshs      d
                    ldd       dialogticks,u
                    subd      ,s++
                    bls       AuxWaitExpired
                    std       dialogticks,u
                    bra       AuxWaitLoop
AuxWaitExpired      clrb
AuxWaitRestore      pshs      cc,b
                    ldu       <resourcebase
                    tst       dialogtimed,u
                    beq       AuxWaitRestoreFlags
                    clr       vmvariables+21,u
AuxWaitRestoreFlags ldy       2,s
                    ldd       4,y
                    leax      d,y
                    puls      cc,b
                    leas      2,s
                    jmp       ,x
AuxWaitKey          lda       #0
                    ldu       <resourcebase
                    leax      parsercharacter,u
                    ldy       #1
                    os9       I$Read
                    bcs       AuxWaitRestore
                    ldu       <resourcebase
                    lda       dialoginputmode,u
                    cmpa      #3         have.key: key variable only, no parser
                    bne       AuxWaitInputMode
                    lda       parsercharacter,u
                    lbeq      AuxWaitLoop ; no real key, like CoCo TestHaveKey
                    sta       vmvariables+19,u
                    bra       AuxWaitKeyDone
AuxWaitInputMode
                    tst       dialoginputmode,u
                    beq       AuxWaitKeyDone
                    ldy       ,s
                    ldd       2,y
                    leax      d,y
                    jsr       ,x
                    bcs       AuxWaitRestore
                    tsta
                    lbeq      AuxWaitLoop
AuxWaitKeyDone      clrb
                    lbra      AuxWaitRestore
AuxWaitSample       ldy       2,s
                    ldd       6,y
                    leax      d,y
                    jmp       ,x
                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_TEXT_RECT_CODE
AuxClearTextRect    pshs      y
                    ldu       <resourcebase
                    leax      vmarguments,u
                    lda       ,x
                    ldb       2,x
                    cmpb      #25
                    lbhs      AuxRectInvalid
                    cmpa      2,x
                    lbhi      AuxRectInvalid
                    lda       1,x
                    ldb       3,x
                    cmpb      #40
                    lbhs      AuxRectInvalid
                    cmpa      3,x
                    lbhi      AuxRectInvalid
                    subb      1,x
                    incb
                    pshs      b
                    lda       2,x
                    suba      ,x
                    inca
                    pshs      a
                    lda       ,x
                    ldb       #40
                    mul
                    addb      1,x
                    adca      #0
                    leay      textcharacters,u
                    leay      d,y
                    clra
                    tst       <vmgraphics
                    beq       GameRectRow
                    tst       4,x
                    beq       GameRectRow
                    lda       #$FF
GameRectRow         ldb       1,s
GameRectCell        pshs      b
                    ldb       #32
                    stb       ,y
                    sta       1000,y
                    leay      1,y
                    puls      b
                    decb
                    bne       GameRectCell
                    ldb       #40
                    subb      1,s
                    leay      b,y
                    dec       ,s
                    bne       GameRectRow
                    leas      2,s
                    puls      y
                    jmp       ,y

AuxRectInvalid      puls      y
                    ldb       #E$IllArg
                    orcc      #1
                    rts
                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_SHOW_OBJECT_CODE
* Non-game object preview uses an idle private renderer-list record.
UI_CALL           macro
                    pshs      d
                    lda       #\1
                    lbsr      AuxUICall
                    leas      2,s
                    endm
AuxShowObject       ldu       <resourcebase
                    sty       coldapi,u
                    lda       <vmopcode
                    cmpa      #141
                    lbeq      AuxInterpreterInfo
                    cmpa      #139
                    lbeq      AuxJoystickInfo
                    ldb       vmarguments,u
                    lda       <vmopcode
                    cmpa      #162
                    bne       AuxShowNumber
                    leax      vmvariables,u
                    clra
                    ldb       d,x
AuxShowNumber       stb       showview,u
                    clr       showcached,u
                    leax      vmcache,u
                    ldy       #32
AuxShowFind          tst       1,x
                    beq       AuxShowFindNext
                    lda       5,x
                    cmpa      #2
                    bne       AuxShowFindNext
                    cmpb      ,x
                    bne       AuxShowFindNext
                    inc       showcached,u
                    bra       AuxShowPrepare
AuxShowFindNext      leax      VM_CACHE_ENTRY_BYTES,x
                    leay      -1,y
                    bne       AuxShowFind
AuxShowPrepare      UI_CALL 24
                    lbcs      AuxShowReturn
                    tst       <pictureowned
                    bne       AuxShowHavePicture
                    UI_CALL 26
                    lbcs      AuxShowReturn
AuxShowHavePicture  tst       gamebackgroundowned,u
                    bne       AuxShowHaveBackground
                    UI_CALL 2
                    lbcs      AuxShowReturn
AuxShowHaveBackground equ     *
                    leax      spritelist+128,u
                    stx       <viewobject
                    ldb       #43
AuxShowZero         clr       ,x+
                    decb
                    bne       AuxShowZero
                    ldx       <viewobject
                    lda       #255
                    sta       2,x       preview must not publish ego visibility
                    lda       showview,u
                    sta       5,x
                    lda       #167
                    sta       4,x
                    lda       #$18       fixed priority; ignore horizon
                    sta       $26,x
                    lda       #15
                    sta       $24,x
                    UI_CALL 0
                    lbcs      AuxShowReturn
                    ldx       <viewobject
                    lda       #160
                    suba      $1C,x
                    lsra
                    sta       3,x
                    tfr       x,u
                    UI_CALL 4
                    lbcs      AuxShowReturn
                    clr       gamebackgroundclean,u
                    UI_CALL 6
                    lbcs      AuxShowReturn
* Copy the bounded plain view description before restoring the root slab.
                    lda       #2
                    ldb       showview,u
                    UI_CALL 8
                    lbcs      AuxShowReturn
                    UI_CALL 10
                    ldd       #3
                    UI_CALL 12
                    lbcs      AuxShowReturn
                    std       showposition,u
                    leax      messagebuffer,u
                    stx       textpointer,u
                    cmpd      #0
                    beq       AuxShowEmpty
                    cmpd      #5
                    lblo      AuxShowInvalid
                    ldy       #512
AuxShowCopy         ldd       showposition,u
                    cmpd      <resourcelength
                    lbhs      AuxShowInvalid
                    UI_CALL 14
                    lbcs      AuxShowReturn
                    ldx       textpointer,u
                    stb       ,x+
                    stx       textpointer,u
                    tstb
                    beq       AuxShowCopied
                    ldd       showposition,u
                    addd      #1
                    std       showposition,u
                    leay      -1,y
                    bne       AuxShowCopy
                    lbra      AuxShowInvalid
AuxShowEmpty        clr       ,x
AuxShowCopied       UI_CALL 18
                    lbcs      AuxShowReturn
                    ldb       <vmcurrent
                    UI_CALL 20
                    UI_CALL 10
* Inventory previews require dismissal, independent of print flags/timers.
                    leax      messagebuffer,u
                    inc       showactive,u
                    lbsr      AuxBlockingPrint
                    pshs      cc,b
                    clr       showactive,u
                    puls      cc,b
                    lbcs      AuxShowReturn
* The fast sprite eraser scans game records, not this temporary preview.
* Restore the pristine background fully, then recompose ordinary objects.
                    lda       #1
                    sta       gamecopydirection,u
                    UI_CALL 28
                    lbcs      AuxShowReturn
                    UI_CALL 30
                    lbcs      AuxShowReturn
                    UI_CALL 32
                    lbcs      AuxShowReturn
                    tst       showcached,u
                    bne       AuxShowDone
                    lda       #2
                    ldb       showview,u
                    UI_CALL 22
AuxShowReturn       rts
AuxShowDone         clrb
                    rts
AuxShowInvalid      ldb       #E$BMode
                    orcc      #1
                    rts
* Interpreter information shares the existing text callback and cold entry.
AuxJoystickInfo     leax      JoystickInfo,pcr
                    bra       AuxBlockingPrint
JoystickInfo        fcc       /Joystick service unavailable./
                    fcb       13
                    fcc       /Use the keyboard to play./
                    fcb       0
AuxInterpreterInfo  leax      InterpreterInfo,pcr
                    bra       AuxBlockingPrint
InterpreterInfo     fcc       /Adventure Game Interpreter/
                    fcb       13
                    fcc       /Wild Bits NitrOS-9 engine/
                    fcb       0
AuxBlockingPrint
                    lda       vmflags+15,u
                    ldb       vmvariables+21,u
                    pshs      d
                    clr       vmflags+15,u
                    clr       vmvariables+21,u
                    UI_CALL 16
                    puls      a
                    sta       vmflags+15,u
                    puls      a
                    sta       vmvariables+21,u
                    rts
* Preserve caller arguments, including a scratch object's U. The indirect
* destination is a stack word, never a patched instruction or shared variable.
AuxUICall         pshs      x,y,u
                    ldu       <resourcebase
                    ldy       coldapi,u
                    ldd       a,y
                    leax      d,y
                    pshs      x
                    ldd       10,s
                    ldx       2,s
                    ldy       4,s
                    ldu       6,s
                    jsr       [,s]
                    leas      8,s
                    ldu       <resourcebase
                    rts
                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_RESTART_CODE
* Read-only restart backend. Request and apply run on opposite sides of unwind.
AuxRestart          ldu       <resourcebase
                    lda       <vmroompending
                    cmpa      #3
                    lbeq      AuxRestartApply
                    sty       restartapi,u
                    tst       vmflags+16,u
                    bne       AuxRestartAccepted
                    lda       vmflags+15,u
                    pshs      a
                    clr       vmflags+15,u
                    leax      AuxRestartPrompt,pcr
                    clra
                    lbsr      AuxRestartCall
                    puls      a
                    sta       vmflags+15,u
                    bcs       AuxRestartReturn
                    lda       parsercharacter,u
                    cmpa      #C$CR
                    bne       AuxRestartSuccess
AuxRestartAccepted  lda       #3
                    sta       <vmroompending
AuxRestartSuccess   clrb
AuxRestartReturn    rts
AuxRestartPrompt    fcc       /Restart game? ENTER confirms./
                    fcb       0
AuxRestartApply     lda       #2       stop owned sound
                    lbsr      AuxRestartCall
                    bcs       AuxRestartReturn
                    lda       #4       unregister/close this raster subscription
                    lbsr      AuxRestartCall
                    bcs       AuxRestartReturn
                    lda       #6       release temporary and all cached resources
                    lbsr      AuxRestartCall
                    bcs       AuxRestartReturn
                    lda       #8       release the saved background
                    lbsr      AuxRestartCall
                    bcs       AuxRestartReturn
                    lda       #10      release the combined picture slab
                    lbsr      AuxRestartCall
                    bcs       AuxRestartReturn
* Strings, labels, key bindings, controllers, object records and cache cells.
                    leax      vmvariables,u
                    ldy       #textstoremodule-vmvariables
                    clra
AuxRestartClear     sta       ,x+
                    leay      -1,y
                    bne       AuxRestartClear
                    clr       parserlastline,u
                    clr       <vmkeycount
                    clr       <vmhavekey
                    clr       <vmdepth
                    clr       <vmcurrent
                    clr       <vmroomchanges
                    clr       <replaylimit
                    clr       <replayused
                    clr       <replayused+1
                    clr       <replaycheckpoint
                    clr       <replaycheckpoint+1
                    lda       #36
                    sta       <vmhorizon
                    clr       gameclockmuted,u
                    clr       presentationconfigured,u
                    lda       #14
                    lbsr      AuxRestartCall
                    lda       #16
                    lbsr      AuxRestartCall
                    lda       #18
                    lbsr      AuxRestartCall
* The original CLI root number/directory never change during resource loads.
                    clr       <resourcekind
                    ldx       <argdirectory
                    ldy       <argnumber
                    lda       #12
                    lbra      AuxRestartCall
AuxRestartCall      pshs      x,y
                    ldy       restartapi,u
                    ldd       a,y
                    leax      d,y
                    stx       restartcall,u
                    puls      x,y
                    jsr       [restartcall,u]
                    ldu       <resourcebase
                    rts
                    else
* wildbits-text-ui feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_DIALOG_CODE
* ===== wildbits-dialog-code =====
* print/print.v: modal text with private screen backup and no mapped wait.
* The picture/LZW command workspace is idle until the window is dismissed.
* Pause shares the modal restoration path. Rebaseline the game clock on
* resume so the time spent waiting does not advance AGI seconds/minutes.
* Modal waits own copied text and hold no picture/resource mapping.
* Keep sound queued here; rendering foreground checks retain their context.
GameModalForeground lbsr      foreground
                    bcs       GameModalReturn
                    lbra      GameSoundTick
GameModalReturn     rts

GamePauseCommand    ldu       <resourcebase
                    clr       dialoginputmode,u
                    leax      GamePausePrompt,pcr
                    bsr      GamePrintText
                    bcs       GamePauseReturn
                    ldu       <resourcebase
                    lda       #1
                    sta       gameclockreset,u
                    clrb
GamePauseReturn     rts
GamePausePrompt     fcc       /Game paused. Press a key to resume./
                    fcb       0

GamePrintCommand    ldu       <resourcebase
                    clr       dialoginputmode,u
                    ldb       vmarguments,u
                    lda       <vmopcode
                    cmpa      #102
                    beq       GamePrintVariable
                    cmpa      #152
                    bne       GamePrintMessage
GamePrintVariable   equ       *
                    leax      vmvariables,u
                    clra
                    ldb       d,x
GamePrintMessage    lbsr      ReadLogicMessage
                    lbcs      GameTextReturn
GamePrintText       ldu       <resourcebase
                    stx       textpointer,u
                    lbsr      GameCloseWindow
                    lbcs      GameTextReturn
                    ldu       <resourcebase
                    leax      textcharacters,u
                    leay      resourcecommands,u
                    ldd       #1000
                    pshs      d
GamePrintSave       ldd       ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       GamePrintSave
                    leas      2,s
                    lda       <vmtextforeground
                    ldb       <vmtextbackground
                    pshs      d
                    clr       <vmtextforeground
                    lda       #15
                    sta       <vmtextbackground
                    leax      textcharacters,u
                    ldy       #1000
GamePrintClear      lda       #32
                    tst       showactive,u
                    beq       GamePrintClearCell
                    clra       preview leaves cells outside its message transparent
GamePrintClearCell  sta       ,x
                    lda       #$0F
                    sta       1000,x
                    leax      1,x
                    leay      -1,y
                    bne       GamePrintClear
                    lda       #1
                    sta       dialogactive,u
                    sta       dialogwordstart,u
* print.at takes literal row/column/width; only print.at.v's message is a var.
                    lda       <vmopcode
                    cmpa      #151
                    blo       GamePrintDefaultPosition
                    cmpa      #152
                    bhi       GamePrintDefaultPosition
                    ldd       vmarguments+1,u
                    cmpa      #25
                    bhs       GamePrintAtBad
                    cmpb      #40
                    bhs       GamePrintAtBad
                    sta       textrow,u
                    stb       textcolumn,u
                    stb       dialogleft,u
                    lda       vmarguments+3,u
                    bne       GamePrintWidth
                    lda       #30
GamePrintWidth      adda      dialogleft,u
                    bcs       GamePrintClipWidth
                    cmpa      #40
                    bls       GamePrintWidthReady
GamePrintClipWidth  lda       #40
GamePrintWidthReady sta       dialogright,u
                    bra       GamePrintPositionReady
GamePrintDefaultPosition ldd  #$0802
                    sta       textrow,u
                    stb       textcolumn,u
                    stb       dialogleft,u
                    lda       #40
                    sta       dialogright,u
GamePrintPositionReady ldx    textpointer,u
                    lbsr      GameTextValidate
                    bcs       GamePrintRestore
                    ldu       <resourcebase
                    tst       dialoginputmode,u
                    bne       GamePrintWait
                    tst       vmflags+15,u
                    beq       GamePrintWait
                    lbsr      GameHoldDialog
                    bcs       GamePrintRestore
                    ldu       <resourcebase
                    clr       vmflags+15,u
                    lda       #2
                    sta       dialogactive,u
                    puls      d
                    sta       <vmtextforeground
                    stb       <vmtextbackground
                    clrb
                    rts
GamePrintAtBad      ldb       #E$BMode
                    orcc      #1
                    bra       GamePrintRestore
* CoCo TestHaveKey waits for fresh input when v19 has been cleared. Reuse
* the cold modal loop, retaining the visible text and private parser state.
GameHaveKeyWait     lbsr      AssetUnmap
                    bcs       GameHaveKeyError
                    lbsr      PictureUnmap
                    bcs       GameHaveKeyError
                    ldu       <resourcebase
                    lda       #3
                    sta       dialoginputmode,u
                    bra       GamePrintWait
GameHaveKeyError    rts
GamePrintWait       leax      textwaitentry,u
                    ldb       #6
                    leay      GameDialogCallbacks,pcr
                    lbra      GameColdInvoke
GameDialogCallbacks fdb       GameModalForeground-GameDialogCallbacks
                    fdb       GameLineKey-GameDialogCallbacks
                    fdb       GamePrintRestore-GameDialogCallbacks
                    fdb       GameClockSample-GameDialogCallbacks
GameHaveKeyRestore  clr       dialoginputmode,u
                    lda       #1
                    sta       gameclockreset,u
                    puls      cc,b
                    bcs       GameHaveKeyError
                    ldb       #1
                    andcc     #$FE
                    rts
GamePrintRestore    pshs      cc,b
                    ldu       <resourcebase
                    lda       dialoginputmode,u
                    cmpa      #3
                    beq       GameHaveKeyRestore
                    clr       dialogactive,u
                    leax      resourcecommands,u
                    leay      textcharacters,u
                    ldd       #1000
                    pshs      d
GamePrintCopyBack   ldd       ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       GamePrintCopyBack
                    leas      2,s
                    puls      cc,b
                    puls      a
                    sta       <vmtextforeground
                    puls      a
                    sta       <vmtextbackground
                    lbcs      GameTextReturn
                    lbsr      GameComposeScene
                    lbcs      GameTextReturn
                    lbra      RefreshPicture


* State entry is a phase-local alias: no formatter runs between validated
* staging and root-stack unwind. Both persistent text planes end before it.
stateentry          equ       textpointer
GameShakeCommand    ldu       <resourcebase
                    leax      shakeentry,u
                    ldb       #18
                    leay      ShakeCallbacks,pcr
                    lbra      GameColdInvoke
ShakeCallbacks      fdb       GameFramePointer-ShakeCallbacks,unmap-ShakeCallbacks
                    fdb       GameModalForeground-ShakeCallbacks,GameClockSample-ShakeCallbacks
GameVersionCommand  equ       *
GameShowObjectCommand ldu     <resourcebase
                    leax      showentry,u
                    ldb       #16
                    leay      ShowCallbacks,pcr
                    lbra      GameColdInvoke
ShowCallbacks       fdb       ViewSelect-ShowCallbacks,GameSaveBackground-ShowCallbacks
                    fdb       SpriteRenderObject-ShowCallbacks,PresentPicture-ShowCallbacks
                    fdb       VmLoadResource-ShowCallbacks,VmRestoreAsset-ShowCallbacks
                    fdb       AssetReadWord-ShowCallbacks,AssetReadByte-ShowCallbacks
                    fdb       GamePrintText-ShowCallbacks,AssetUnmap-ShowCallbacks
                    fdb       VmSlotAddress-ShowCallbacks,VmDiscardResource-ShowCallbacks
                    fdb       GameCloseWindow-ShowCallbacks,GameCreateScreen-ShowCallbacks
                    fdb       GameCopyBackground-ShowCallbacks,GameComposeScene-ShowCallbacks
                    fdb       RefreshPicture-ShowCallbacks
GameRestartCommand  ldu       <resourcebase
                    leax      restartentry,u
                    ldb       #12
                    leay      RestartCallbacks,pcr
                    lbra      GameColdInvoke
RestartCallbacks          fdb       GamePrintText-RestartCallbacks,GameSoundStop-RestartCallbacks
                    fdb       GameClockClose-RestartCallbacks,VmReleaseResources-RestartCallbacks
                    fdb       GameReleaseBackground-RestartCallbacks,PictureRelease-RestartCallbacks
                    fdb       LoadAsset-RestartCallbacks,GameTextInitialize-RestartCallbacks
                    fdb       MenuInitialize-RestartCallbacks,ScreenInitialize-RestartCallbacks
GameStateCommand    lbsr      GameSoundStop
                    lbcs      GameStateReturn
                    ldu       <resourcebase
                    lda       #1
                    sta       dialoginputmode,u
                    ldd       #$0A02
                    std       inventoryrow,u
                    lda       #39
                    sta       inventorypaint,u
                    lbsr      ParserClearLine
                    leax      StatePrompt,pcr
                    lbsr      GamePrintText
                    lbcs      GameStateReturn
                    ldu       <resourcebase
                    clr       dialoginputmode,u
                    tst       parserlength,u
                    beq      GameStateSuccess
                    lbsr      PictureUnmap
                    lbcs      GameStateReturn
                    ldu       <resourcebase
                    pshs      u
                    lbsr      StateLoadModule
                    bcs       StateLoadReturn
                    ldx       ,s
                    ldd       M$Exec,u
                    addd      #fillstack
                    addd      <resourcebase
                    std       stateentry,x
                    pshs      u
                    tfr       u,x
                    ldu       2,s
                    leau      fillstack,u
StateCopy           lda       ,x+
                    sta       ,u+
                    leay      -1,y
                    bne       StateCopy
                    puls      u
                    os9       F$UnLink
StateLoadReturn     puls      u
                    bcs       GameStateFailure
                    lda       <vmopcode
                    suba      #125
                    bra       GameStateInvoke
GameStateApply      lda       #2
GameStateInvoke     pshs      a
                    ldu       <resourcebase
                    leax      parserline,u
                    leay      StateAPI,pcr
                    jsr       [stateentry,u]
                    puls      a
                    bcs       GameStateCallFailed
                    cmpa      #1
                    bne       GameStateSuccess
                    lda       #2
                    sta       <vmroompending
GameStateSuccess    ldu       <resourcebase
                    lda       #1
                    sta       gameclockreset,u
                    lbra      ParserClearLine
GameStateReturn     rts
GameStateCallFailed deca
                    deca                preserve the helper failure carry
                    beq       GameStateReturn
GameStateFailure    ldu       <resourcebase
                    clr       dialoginputmode,u
                    leax      StateFailure,pcr
                    lbsr      GamePrintText
                    bcc       GameStateSuccess
                    rts
StatePrompt         fcc       /File:/
                    fcb       0
StateFailure        fcc       /File error./
                    fcb       0
* Shared, bounded cold-image loader. Success leaves U=module, X=metadata
* after the eight-byte private ABI, Y=bounded writable-prefix length.
* No image is copied here.
StateLoadModule     pshs      u
                    lbsr      AssetUnmap
                    bcs       StateModuleFailure
                    leax      StateModule,pcr
                    lda       #Sbrtn+Objct
                    os9       F$Load
                    bcs       StateModuleFailure
                    ldd       M$Size,u
                    cmpd      #8192
                    bhi       StateLoadBad
                    ldd       M$Exec,u
                    cmpd      #13
                    blo       StateLoadBad
                    addd      #37       branch, private ABI, twelve metadata words and CRC must fit
                    bcs       StateLoadBad
                    cmpd      M$Size,u
                    bhi       StateLoadBad
                    leay      2,y
                    leax      StateSignature,pcr
                    ldb       #8
StateCheckABI       lda       ,x+
                    cmpa      ,y+
                    bne       StateLoadBad
                    decb
                    bne       StateCheckABI
                    tfr       y,x       validated metadata follows the ABI
* Only the writable state prefix is copied; linked cold code stays shared.
                    ldd       M$Exec,u
                    addd      #37
                    cmpd      8,x
                    bhi       StateLoadBad
                    ldy       8,x
                    cmpy      #4096
                    bhi       StateLoadBad
                    cmpy      M$Size,u
                    bhi       StateLoadBad
                    leas      2,s
                    clrb
                    rts
StateLoadBad        os9       F$UnLink
                    ldb       #E$BMode
                    orcc      #1
StateModuleFailure  puls      u,pc
StateModule         fcc       /wbstate/
                    fcb       C$CR
StateSignature      STATE_ABI
* Position-independent callbacks: offsets are relative to this table's base.
StateAPI            fdb       AssetUnmap-StateAPI,PictureUnmap-StateAPI
                    fdb       VmReleaseCache-StateAPI,GameReleaseBackground-StateAPI
                    fdb       PictureRelease-StateAPI,VmLoadResource-StateAPI
                    fdb       VmSlotAddress-StateAPI,VmRestoreAsset-StateAPI
                    fdb       PictureAllocate-StateAPI,PicturePointer-StateAPI
                    fdb       GameSaveBackground-StateAPI,GameComposeScene-StateAPI
                    fdb       RefreshPicture-StateAPI

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_DICTIONARY_CODE
* ===== wildbits-dictionary-code =====
* Random-access encoded byte provider over the existing 512-byte file buffer.
* X=file offset, U=input cursor; A=byte/C clear or B=OS error/C set.
* X/Y/U are preserved, B is scratch. No mapped slab crosses file I/O.
DictionaryReadAt    pshs      x,y,u
                    ldu       <resourcebase
                    tfr       x,d
                    subd      dictionarycachebase,u
                    cmpd      parserreadlength,u
                    blo       DictionaryReadCached
                    ldx       ,s
                    stx       dictionarycachebase,u
                    ldd       #0
                    std       parserreadindex,u
                    std       parserreadlength,u
                    tfr       x,u
                    ldx       #0
                    lda       <resourcepath
                    os9       I$Seek
                    bcs       DictionaryReadReturn
                    lbsr      ParserByte
                    bcs       DictionaryReadReturn
                    tfr       b,a
                    andcc     #$FE
DictionaryReadReturn puls    x,y,u,pc
DictionaryReadCached leay    assetinput,u
                    lda       d,y
                    andcc     #$FE
                    puls      x,y,u,pc
DictionaryPrefix    pshs      a
                    lbsr      DictionaryReadAt
                    bcs       DictionaryPrefixError
                    tfr       a,b
                    puls      a
                    leax      1,x
                    andcc     #$FE
                    rts
DictionaryPrefixError puls   a,pc
DictionaryReadID    pshs      x
                    leax      1,x
                    lbsr      DictionaryReadAt
                    bcs       DictionaryIDReturn
                    pshs      a
                    leax      1,x
                    lbsr      DictionaryReadAt
                    bcs       DictionaryIDError
                    tfr       a,b
                    puls      a
                    andcc     #$FE
DictionaryIDReturn  puls     x,pc
DictionaryIDError   leas     1,s
                    puls      x,pc
* Validation already established EOF only at an entry boundary or trailing zero.
* Restore the common frame before propagating a real seek/read error.
DictionaryReadFailure cmpb   #E$EOF
                    lbeq      LookupWordNotFound
                    leas      6,s
                    orcc      #1
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_TEXT_CODE
* ===== wildbits-game-text-code =====
* A persistent window saves the character/color plane in unused bytes of
* its owned framebuffer: block nine, offset 3072 (past the 76800 pixels).
* No additional allocation or private state; ordinary frame clears retain it.
GameHoldDialog      lda       #9
                    sta       <blockindex
                    lbsr      mapblock
                    bcs       GameWindowReturn
                    leay      3072,u
                    ldx       <resourcebase
                    leax      resourcecommands,x
                    ldu       #1000
GameWindowSave      ldd       ,x++
                    std       ,y++
                    leau      -1,u
                    cmpu      #0
                    bne       GameWindowSave
                    lbra      unmap
GameCloseWindow     ldu       <resourcebase
                    lda       dialogactive,u
                    cmpa      #2
                    bne       GameWindowClosed
GameWindowCloseReady equ      *
                    lbsr      AssetUnmap
                    bcs       GameWindowReturn
                    lbsr      PictureUnmap
                    bcs       GameWindowReturn
                    lda       #9
                    sta       <blockindex
                    lbsr      mapblock
                    bcs       GameWindowReturn
                    leax      3072,u
                    ldy       <resourcebase
                    leay      textcharacters,y
                    ldu       #1000
GameWindowRestore   ldd       ,x++
                    std       ,y++
                    leau      -1,u
                    cmpu      #0
                    bne       GameWindowRestore
                    lbsr      unmap
                    bcs       GameWindowReturn
                    ldu       <resourcebase
                    clr       dialogactive,u
                    lbsr      GameComposeScene
                    bcs       GameWindowReturn
                    lbra      RefreshPicture
GameWindowClosed    clrb
GameWindowReturn    rts

GameTextInitialize  ldu       <resourcebase
                    leax      textcharacters,u
                    ldy       #1000
GameTextClear       clr       ,x+
                    leay      -1,y
                    bne       GameTextClear
                    rts

* draw.pic replaces all pixels within the configured 21-row picture area.
* Drop the corresponding saved text too, or the next frame resurrects old
* credits/messages over the new picture. Keep status/input rows outside it.
GameTextClearPicture ldu      <resourcebase
                    lda       <vmpicturetop
                    ldb       #40
                    mul
                    leax      textcharacters,u
                    leax      d,x
                    ldy       #840
                    bra       GameTextClear

* display/display.v. Messages are copied into private persistent cells;
* a framebuffer refresh can redraw them without reopening the logic slab.
GameDisplayCommand  ldu       <resourcebase
                    leax      vmarguments,u
                    lda       <vmopcode
                    cmpa      #104
                    bne       GameDisplayArguments
                    leay      vmvariables,u
                    ldb       ,x
                    clra
                    ldb       d,y
                    stb       ,x
                    ldb       1,x
                    ldb       d,y
                    stb       1,x
                    ldb       2,x
                    ldb       d,y
                    stb       2,x
GameDisplayArguments lda      ,x
                    cmpa      #25
                    lbhs      GameTextInvalid
                    sta       textrow,u
                    lda       1,x
                    cmpa      #40
                    lbhs      GameTextInvalid
                    sta       textcolumn,u
                    ldd       #$0228
                    std       dialogleft,u
                    ldb       2,x
                    lbsr      ReadLogicMessage
                    lbcs      GameTextReturn
                    ldu       <resourcebase
                    stx       textpointer,u
* Expand copied messages without retaining resource-window pointers.
GameTextValidate    lbsr      GameFormatMessage
                    lbcs      GameTextReturn
                    stx       textpointer,u
* The immutable helper retains a code window; all cells remain process-private.
GameTextStore       leax      textstoreentry,u
                    ldb       #4
                    leay      GameTextPresent,pcr
* B selects the immutable entry; X names its private cache, Y its callback.
GameColdInvoke      tst       ,x
                    beq       GameColdLoad
                    ldx       ,x
                    jmp       ,x
GameColdLoad         pshs      b,x,y
                    ldu       textstoremodule,u
                    bne       GameColdLinked
                    ldu       <resourcebase
                    lbsr      StateLoadModule
                    bcs       GameColdFailure
                    ldy       <resourcebase
                    stu       textstoremodule,y
                    bra       GameColdMetadata
GameColdLinked      ldd       M$Exec,u
                    addd      #10
                    leax      d,u
GameColdMetadata    ldb       ,s
                    ldd       b,x
                    cmpd      #13
                    blo       GameColdBad
                    ldy       M$Size,u
                    leay      -3,y
                    pshs      y
                    cmpd      ,s
                    leas      2,s
                    bhs       GameColdBad
                    leax      d,u
                    ldy       1,s
                    stx       ,y
                    ldu       <resourcebase
                    leas      3,s
                    puls      y
                    jmp       ,x
GameColdBad         ldb       #E$BMode
GameColdFailure     ldu       <resourcebase
                    lda       ,s
                    leas      5,s
                    cmpa      #6
                    orcc      #1
                    bne       GameColdReturn
                    lbra      GamePrintRestore
GameColdReturn      rts
GameTextUnlink      ldu       <resourcebase
                    ldx       textstoremodule,u
                    beq       GameTextUnlinkDone
                    tfr       x,u
                    os9       F$UnLink
                    ldu       <resourcebase
                    bcs       GameTextUnlinkDone
                    clra
                    clrb
                    std       textstoremodule,u
                    std       textstoreentry,u
                    std       textwaitentry,u
                    std       textrectentry,u
                    std       restartentry,u
                    std       screenentry,u
                    std       showentry,u
                    std       shakeentry,u
                    std       menuentry,u
                    std       formatentry,u
GameTextUnlinkDone  rts
GameTextPresent     lbsr      AssetUnmap
                    bcs       GameTextReturn
* Preview dialogs replace opaque text-mode cells with transparent cells.
* Repaint their underlying picture; a text-only pass cannot undo old pixels.
                    ldu       <resourcebase
                    tst       showactive,u
                    lbne      RefreshPicture
                    tst       <bitmapowned
                    bne       GameDrawText
                    tst       <pictureowned
                    bne       GameTextShowPicture
                    bsr      GameCreateScreen
                    bcs       GameTextReturn
GameTextShowPicture lbra      PresentPicture
GameTextInvalid     ldb       #E$IllArg
                    orcc      #1
GameTextReturn      rts

GameCreateScreen    lbsr      PictureAllocate
                    bcs       GameTextReturn
                    ldy       #0
GameBlankPage       tfr       y,d
                    lbsr      PicturePointer
                    tst       <decodeerror
                    bne       GameTextDecodeError
                    ldx       #8192
                    lda       #$40       opaque black with default priority
GameBlankByte       sta       ,u+
                    leax      -1,x
                    bne       GameBlankByte
                    leay      8192,y
                    cmpy      #32768
                    blo       GameBlankPage
                    lbsr      PictureUnmap
                    bcs       GameTextReturn
                    clrb
                    rts
GameTextDecodeError ldb       <decodeerror
                    orcc      #1
                    rts

                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_RENDER_TEXT
                    use platform/wildbits-text-ui.asm
* A bounded contiguous cell range; caller sets index/end/row/column.
GameDrawTextRange   ldx       <resourcebase
                    clr       textrenderdirty,x
                    ldd       textend,x
                    std       textrenderend,x
                    lbra      TextFastPrepare

* D=framebuffer offset; return ephemeral U, preserve D/X/Y.
GameFramePointer    pshs      d,x,y
                    lsra
                    lsra
                    lsra
                    lsra
                    lsra
                    tst       <mapped
                    beq       GameFrameMap
                    cmpa      <blockindex
                    beq       GameFrameAddress
                    pshs      a
                    lbsr      unmap
                    puls      a
                    bcs       GameFrameReturn
GameFrameMap        sta       <blockindex
                    lbsr      mapblock
                    bcs       GameFrameReturn
GameFrameAddress    ldd       ,s
                    anda      #$1F
                    ldu       <mapbase
                    leau      d,u
                    andcc     #$FE
GameFrameReturn     puls      d,x,y,pc

* Text mode uses opaque cells on the owned bitmap; retain the game picture.
GameTextScreen      lbsr      GameCloseWindow
                    lbcs      GameTextReturn
                    clr       <vmgraphics
                    ldu       <resourcebase
                    leax      textcharacters,u
                    ldy       #1000
GameTextScreenCell  lda       #32
                    sta       ,x
                    lda       <vmtextbackground
                    sta       1000,x
                    leax      1,x
                    leay      -1,y
                    bne       GameTextScreenCell
                    lbra      GameTextPresent

GameGraphicsMode    lbsr      GameCloseWindow
                    lbcs      GameTextReturn
                    lda       #1
                    sta       <vmgraphics
                    lbsr      GameTextInitialize
                    tst       <pictureowned
                    bne       GameGraphicsReady
                    lbsr      GameCreateScreen
                    lbcs      GameTextReturn
GameGraphicsReady   lbsr      GameComposeScene
                    lbcs      GameTextReturn
                    lda       <presentationconfigured
                    ora       #$C0
                    sta       <presentationconfigured
                    lbra      PresentPicture

* clear.text.rect(top,left,bottom,right,color): inclusive cell bounds.
GameClearTextRect   ldu       <resourcebase
                    leax      textrectentry,u
                    ldb       #10
                    leay      GameTextPresent,pcr
                    lbra      GameColdInvoke

* clear.lines is a full-width rectangle. Arguments are command-local scratch.
GameClearLines      ldu       <resourcebase
                    ldb       vmarguments+2,u
                    stb       vmarguments+4,u
                    ldb       vmarguments+1,u
                    stb       vmarguments+2,u
                    clr       vmarguments+1,u
                    ldb       #39
                    stb       vmarguments+3,u
                    lbra      GameClearTextRect

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_TEXT_DATA
* ===== wildbits-game-text-data =====
* Persistent text cells survive picture refreshes; zero means no overlay.
textcharacters      rmb      1000
* High nibble is logical foreground, low nibble logical background (0..15).
textcolors          rmb      1000
textpointer         rmb      2
textindex           rmb      2
textend             rmb      2
textrenderend       rmb      2
textrenderdirty     rmb      1
textfontpointer     rmb      2
textrow             rmb      1
textcolumn          rmb      1
textglyphrow        rmb      1
textbits            rmb      1
textforeground      rmb      1
textbackground      rmb      1

* Inclusive occupied span for the scanline text renderer.
textfirstcolumn     rmb      1
textlastcolumn      rmb      1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_INVENTORY_CODE
* ===== wildbits-inventory-code =====
* Lazy bounded object-file load. No resource slab remains mapped across I/O.
* Names stay immutable after validation; only inventoryrooms changes.
InventoryLoad       ldu       <resourcebase
                    tst       inventoryloaded,u
                    lbne      InventorySuccess
InventoryLoadNames  lbsr      AssetUnmap
                    lbcs      InventoryReturn
                    lbsr      PictureUnmap
                    lbcs      InventoryReturn
                    ldu       <resourcebase
                    ldy       resourcenameend,u
                    leax      InventoryFilename,pcr
                    lbsr      ResourceSuffix
                    lbsr      OpenPicturePath
                    lbcs      ResourceFailed
                    ldu       <resourcebase
                    clr       inventorylength,u
                    clr       inventorylength+1,u
InventoryRead       ldd       inventorylength,u
                    leax      inventoryfile,u
                    leax      d,x
                    pshs      d
                    ldd       #2048
                    subd      ,s++
                    tfr       d,y
                    beq       InventoryProbe
                    lda       <resourcepath
                    os9       I$Read
                    bcs       InventoryReadEnd
                    cmpy      #0
                    lbeq      ResourceInvalid
                    tfr       y,d
                    ldu       <resourcebase
                    addd      inventorylength,u
                    cmpd      #2048
                    lbhi      ResourceInvalid
                    std       inventorylength,u
                    bra       InventoryRead
InventoryProbe      leax      picturestage,u
                    ldy       #1
                    lda       <resourcepath
                    os9       I$Read
                    lbcc      ResourceInvalid
InventoryReadEnd    cmpb      #E$EOF
                    lbne      ResourceFailed
                    lbsr      ResourceClose
                    lbcs      ResourceFailed
                    ldu       <resourcebase
                    ldd       inventorylength,u
                    cmpd      #3
                    lblo      InventoryInvalid
                    leax      inventoryfile,u
                    leau      d,x
                    lbsr      XorDecrypt
                    ldy       #0        ; retain the old countdown-loop result
                    ldu       <resourcebase
                    leax      inventoryfile,u
                    ldb       ,x
                    lda       1,x
                    cmpd      #768
                    lbhi      InventoryInvalid
                    pshs      d
                    addd      #3
                    std       inventorynames,u
                    cmpd      inventorylength,u
                    puls      d
                    lbhs      InventoryInvalid
                    tfr       d,y
                    clr       inventorycount,u
                    clr       inventorycount+1,u
InventoryCountLoop  cmpy      #0
                    beq       InventoryValidate
                    cmpy      #3
                    blo       InventoryInvalid
                    leay      -3,y
                    ldd       inventorycount,u
                    addd      #1
                    std       inventorycount,u
                    bra       InventoryCountLoop
InventoryValidate   leax      3,x
                    leay      inventoryrooms,u
                    ldd       inventorycount,u
                    pshs      d
InventoryEntry      ldd       ,s
                    beq       InventoryValidated
                    ldb       ,x
                    lda       1,x
                    addd      #3
                    cmpd      inventorynames,u
                    blo       InventoryEntryInvalid
                    cmpd      inventorylength,u
                    bhs       InventoryEntryInvalid
                    pshs      x,y
                    leay      inventoryfile,u
                    leay      d,y
InventoryName       cmpd      inventorylength,u
                    bhs       InventoryNameInvalid
                    tst       ,y+
                    beq       InventoryNameDone
                    addd      #1
                    bra       InventoryName
InventoryNameInvalid puls     x,y
InventoryEntryInvalid leas    2,s
                    bra       InventoryInvalid
InventoryNameDone   puls      x,y
                    tst       inventoryloaded,u
                    bne       InventoryKeepRoom
                    lda       2,x
                    sta       ,y
InventoryKeepRoom   leay      1,y
                    leax      3,x
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bra       InventoryEntry
InventoryValidated  leas      2,s
                    lda       #1
                    sta       inventoryloaded,u
InventorySuccess    clrb
InventoryReturn     rts
InventoryInvalid    ldb       #E$BMode
                    orcc      #1
                    rts
InventoryFilename   fcc       /object/
                    fcb       C$CR
                    use shared/xor-decrypt.asm

* Command rules shared with CoCo; item/name loading and storage stay native.
                    ifndef PLATFORM_WILDBITS_TEXT_UI_BINDINGS
                    use platform/wildbits-text-ui-bindings.asm
                    endc
                    use       shared/inventory-commands.asm
InventoryCommand    lbsr      InventoryLoad
                    bcs      InventoryReturn
                    ldu       <resourcebase
                    leay      vmarguments,u
                    ldb       <vmopcode
                    subb      #92
                    cmpb      #5
                    bhi      InventoryInvalid
                    lslb
                    leax      InventoryCommands,pcr
                    ldd       b,x
                    leax      d,x
                    jmp       ,x
InventoryCommands   fdb       InventoryGet-InventoryCommands
                    fdb       InventoryGetVariable-InventoryCommands
                    fdb       InventoryDrop-InventoryCommands
                    fdb       InventoryPut-InventoryCommands
                    fdb       InventoryPutVariable-InventoryCommands
                    fdb       InventoryGetRoom-InventoryCommands
InventoryGet        INVENTORY_SET_LOCATION 0,$FF
                    clrb
                    rts
InventoryGetVariable INVENTORY_SET_LOCATION 1,$FF
                    clrb
                    rts
InventoryDrop       INVENTORY_SET_LOCATION 0,$00
                    clrb
                    rts
InventoryPut        INVENTORY_PUT_LOCATION 0
                    clrb
                    rts
InventoryPutVariable INVENTORY_PUT_LOCATION 1
                    clrb
                    rts
InventoryGetRoom    INVENTORY_GET_LOCATION
                    clrb
                    rts
InventoryVariableItemAddress ldb ,y+
                    leax      vmvariables,u
                    clra
                    ldb       d,x
                    bra       InventoryResolveItem
InventoryItemAddress ldb      ,y+
InventoryResolveItem clra
                    cmpd      inventorycount,u
                    lbhs      InventoryInvalid
                    leax      inventoryrooms,u
                    leax      d,x
                    andcc     #$FE
                    rts

* Modal status screen. Picture-command staging is dead after decoding and
* supplies the 2000-byte text backup; no resource loads occur while modal.
InventoryStatus     lbsr      InventoryLoadNames
                    lbcs      InventoryReturn
                    ldu       <resourcebase
                    leax      textcharacters,u
                    leay      resourcecommands,u
                    ldd       #1000
                    pshs      d
InventorySaveText   ldd       ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       InventorySaveText
                    leas      2,s
                    clr       inventoryvisible,u
                    clr       inventoryvisible+1,u
                    clr       inventoryselected,u
                    clr       inventoryselected+1,u
                    clr       inventorytop,u
                    clr       inventorytop+1,u
                    leax      inventoryrooms,u
                    leay      inventorylist,u
                    ldd       #0
InventoryBuildList  cmpd      inventorycount,u
                    bhs       InventoryRedraw
                    pshs      d
                    lda       ,x+
                    cmpa      #255
                    bne       InventoryListNext
                    ldb       1,s
                    stb       ,y+
                    ldd       inventoryvisible,u
                    addd      #1
                    std       inventoryvisible,u
InventoryListNext   puls      d
                    addd      #1
                    bra       InventoryBuildList
InventoryRedraw     leax      textcharacters,u
                    ldy       #1000
InventoryWhite      lda       #32
                    sta       ,x
                    lda       #$0F
                    sta       1000,x
                    leax      1,x
                    leay      -1,y
                    bne       InventoryWhite
                    leax      InventoryTitle,pcr
                    leay      textcharacters+42,u
                    lbsr      InventoryString
                    leax      InventoryReturnText,pcr
                    tst       vmflags+13,u
                    beq       InventoryFooter
                    leax      InventorySelectText,pcr
InventoryFooter     leay      textcharacters+961,u
                    lbsr      InventoryString
                    ldd       inventoryvisible,u
                    bne       InventoryItems
                    leax      InventoryNothing,pcr
                    leay      textcharacters+122,u
                    lbsr      InventoryString
                    bra      InventoryPresent
InventoryItems      lda       #3
                    sta       inventoryrow,u
                    ldd       inventorytop,u
                    pshs      d
InventoryDrawItem   ldd       ,s
                    cmpd      inventoryvisible,u
                    bhs       InventoryItemsDone
                    leax      inventorylist,u
                    ldb       d,x
                    lda       #3
                    mul
                    leax      inventoryfile+3,u
                    leax      d,x
                    ldb       ,x
                    lda       1,x
                    leax      inventoryfile+3,u
                    leax      d,x
                    lda       inventoryrow,u
                    ldb       #40
                    mul
                    addd      #2
                    leay      textcharacters,u
                    leay      d,y
                    lbsr      InventoryString
                    tst       vmflags+13,u
                    beq       InventoryNextRow
                    ldd       ,s
                    cmpd      inventoryselected,u
                    bne       InventoryNextRow
                    lda       inventoryrow,u
                    ldb       #40
                    mul
                    leay      textcolors,u
                    leay      d,y
                    ldb       #40
InventoryHighlight  lda       #$F0
                    sta       ,y
                    leay      1,y
                    decb
                    bne       InventoryHighlight
InventoryNextRow    ldd       ,s
                    addd      #1
                    std       ,s
                    inc       inventoryrow,u
                    lda       inventoryrow,u
                    cmpa      #24
                    blo       InventoryDrawItem
InventoryItemsDone  leas      2,s
InventoryPresent    lbsr      GameTextPresent
                    lbcs      InventoryRestoreError
InventoryWait       lbsr      GameModalForeground
                    lbcs      InventoryRestoreError
                    ldu       <resourcebase
                    clra
                    ldb       #SS.Ready
                    os9       I$GetStt
                    bcc       InventoryReadKey
                    cmpb      #E$NotRdy
                    lbne      InventoryRestoreError
                    ldx       #2
                    os9       F$Sleep
                    bra      InventoryWait
InventoryReadKey    ldu       <resourcebase
                    leax      inventorykey,u
                    ldy       #1
                    clra
                    os9       I$Read
                    lbcs      InventoryRestoreError
                    ldu       <resourcebase
                    cmpy      #1
                    bne      InventoryWait
                    tst       vmflags+13,u
                    lbeq      InventoryDismiss
                    ldd       inventoryselected,u
                    std       inventoryprevious,u
                    lda       inventorykey,u
                    cmpa      #5
                    lbeq      InventoryCancel
                    cmpa      #27
                    lbeq      InventoryCancel
                    cmpa      #3
                    lbeq      InventoryCancel
                    cmpa      #13
                    beq      InventoryChoose
                    ldd       inventoryvisible,u
                    beq      InventoryWait
                    lda       inventorykey,u
                    cmpa      #12
                    beq       InventoryUp
                    cmpa      #10
                    bne      InventoryWait
                    ldd       inventoryselected,u
                    addd      #1
                    cmpd      inventoryvisible,u
                    lbhs      InventoryWait
                    std       inventoryselected,u
                    subd      inventorytop,u
                    cmpd      #21
                    blo       InventoryDrawAgain
                    ldd       inventorytop,u
                    addd      #1
                    std       inventorytop,u
                    bra       InventoryPageChange
InventoryUp         ldd       inventoryselected,u
                    lbeq      InventoryWait
                    subd      #1
                    std       inventoryselected,u
                    cmpd      inventorytop,u
                    bhs       InventoryDrawAgain
                    std       inventorytop,u
InventoryPageChange lbra      InventoryRedraw
InventoryDrawAgain  lda       #$0F
                    sta       inventorypaint,u
                    ldd       inventoryprevious,u
                    bsr      InventoryPaintRow
                    bcs      InventoryRestoreError
                    ldu       <resourcebase
                    lda       #$F0
                    sta       inventorypaint,u
                    ldd       inventoryselected,u
                    bsr      InventoryPaintRow
                    bcs      InventoryRestoreError
                    lbra      InventoryWait
InventoryChoose     ldd       inventoryvisible,u
                    beq      InventoryCancel
                    ldd       inventoryselected,u
                    leax      inventorylist,u
                    lda       d,x
                    bra       InventorySelection
InventoryCancel     lda       #255
InventorySelection  sta       vmvariables+25,u
InventoryDismiss    clrb
InventoryRestoreError pshs    cc,b
                    ldu       <resourcebase
                    leax      resourcecommands,u
                    leay      textcharacters,u
                    ldd       #1000
                    pshs      d
InventoryRestoreText ldd      ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       InventoryRestoreText
                    leas      2,s
                    puls      cc,b
                    lbcs      InventoryReturn
                    lbsr      GameComposeScene
                    lbcs      InventoryReturn
                    lbra      RefreshPicture

* Change and draw only one highlight row when the visible page is unchanged.
InventoryPaintRow   ldx       <resourcebase
                    subd      inventorytop,x
                    addd      #3
                    stb       textrow,x
                    clr       textcolumn,x
                    lda       #40
                    mul
                    std       textindex,x
                    leay      textcolors,x
                    leay      d,y
                    addd      #40
                    std       textend,x
                    ldb       #40
InventoryPaintCell  lda       inventorypaint,x
                    sta       ,y
                    leay      1,y
                    decb
                    bne       InventoryPaintCell
                    lbra      GameDrawTextRange

* Render at most 38 columns. File names were bounded and NUL-validated.
InventoryString     ldb       #38
InventoryStringByte lda      ,x+
                    beq       InventoryStringDone
                    sta       ,y+
                    decb
                    bne       InventoryStringByte
InventoryStringDone rts
InventoryTitle      fcc       /You are carrying:/
                    fcb       0
InventoryNothing    fcc       /nothing/
                    fcb       0
InventoryReturnText fcc       /Press a key to return to the game/
                    fcb       0
InventorySelectText fcc       /ENTER selects; ESC cancels/
                    fcb       0

* has(item) and obj.in.room(item, room-variable) share the mutable room table.
InventoryTest       lbsr      InventoryLoad
                    lbcs      InventoryReturn
                    ldu       <resourcebase
                    leay      vmarguments,u
                    ldb       <vmopcode
                    cmpb      #9
                    beq       InventoryHas
                    cmpb      #10
                    lbne      InventoryInvalid
                    INVENTORY_ROOM_TEST
InventoryHas        INVENTORY_HAS_TEST
InventoryFalse      clrb
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_INVENTORY_DATA
* ===== wildbits-inventory-data =====
* Process-private decrypted object file and mutable item rooms.
inventoryloaded     rmb       1
inventorylength     rmb       2
inventorycount      rmb       2
inventoryrooms      rmb       256
* Names exist only during loading/status; the decoder is idle then.
inventoryfile       equ       fillstack
inventorylist       equ       fillstack+3840
inventoryvisible    rmb       2
inventoryselected   rmb       2
inventorytop        rmb       2
inventoryrow        rmb       1
inventorykey        rmb       1
inventorynames      rmb       2
inventoryprevious   rmb       2
inventorypaint      rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_MENU_BUILD_CODE
* ===== wildbits-menu-build-code =====
* AGI menu construction. Owner buffers: eight 4-byte titles, thirty-two
* 6-byte items, and 768 bytes of NUL-terminated labels. Drawing/navigation
* remain a separate component; no resource pointer is stored in these records.
MenuInitialize      clr       <menucount
                    clr       <menuitems
                    clr       <menucurrent
                    clr       <menuready
                    clr       <menutextused
                    clr       <menutextused+1
                    rts
MenuCommand         ldb       <vmopcode
                    cmpb      #156
                    beq       MenuSetTitle
                    cmpb      #157
                    beq       MenuSetItem
                    cmpb      #158
                    lbeq      MenuSubmit
                    cmpb      #159
                    lbeq      MenuEnable
                    cmpb      #160
                    lbeq      MenuDisable
                    ldb       #E$UnkSvc
                    orcc      #1
                    rts
MenuCopyLabel       ldu       <resourcebase
                    ldb       vmarguments,u
                    lbsr      ReadLogicMessage
                    bcs       MenuReturn
                    tfr       y,d
                    addd      #1
                    addd      <menutextused
                    bcs       MenuFull
                    cmpd      #768
                    bhi       MenuFull
                    pshs      d
                    ldd       <menutextused
                    std       <menulabel
                    ldu       <resourcebase
                    leay      menutext,u
                    leay      d,y
MenuCopyByte        lda       ,x+
                    sta       ,y+
                    bne       MenuCopyByte
                    puls      d
                    std       <menutextused
                    clrb
MenuReturn          rts
MenuFull            ldb       #E$MemFul
                    orcc      #1
                    rts
MenuSetTitle        ldb       <menucount
                    cmpb      #8
                    bhs       MenuFull
                    bsr      MenuCopyLabel
                    bcs       MenuReturn
                    ldu       <resourcebase
                    leax      menutitles,u
                    ldb       <menucount
                    stb       <menucurrent
                    lda       #4
                    mul
                    leax      d,x
                    ldd       <menulabel
                    std       ,x
                    ldb       <menuitems
                    stb       2,x
                    clr       3,x
                    inc       <menucount
                    clr       <menuready
                    clrb
                    rts
MenuSetItem         tst       <menucount
                    beq      MenuInvalid
                    ldb       <menuitems
                    cmpb      #32
                    bhs       MenuFull
                    bsr      MenuCopyLabel
                    bcs       MenuReturn
                    ldu       <resourcebase
                    leax      menuentries,u
                    ldb       <menuitems
                    lda       #6
                    mul
                    leax      d,x
                    ldd       <menulabel
                    std       ,x
                    ldb       vmarguments+1,u
                    stb       2,x
                    ldb       <menucurrent
                    stb       3,x
                    lda       #1
                    sta       4,x
                    leax      menutitles,u
                    lda       #4
                    mul
                    leax      d,x
                    inc       3,x
                    inc       <menuitems
                    clr       <menuready
                    clrb
                    rts
MenuSubmit          tst       <menucount
                    beq       MenuInvalid
                    lda       #1
                    sta       <menuready
                    clrb
                    rts
MenuEnable          lda       #1
                    bra       MenuSetEnabled
MenuDisable         clra
MenuSetEnabled      sta       <menuoperation
                    ldu       <resourcebase
                    leax      menuentries,u
                    ldy       #0
                    ldb       vmarguments,u
MenuEnableNext      tfr       y,d
                    cmpb      <menuitems
                    bhs       MenuEnabledDone
                    ldb       vmarguments,u
                    cmpb      2,x
                    bne       MenuEnableAdvance
                    lda       <menuoperation
                    sta       4,x
MenuEnableAdvance   leax      6,x
                    leay      1,y
                    bra       MenuEnableNext
MenuEnabledDone     clrb
                    rts
MenuInvalid         ldb       #E$BMode
                    orcc      #1
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_MENU_CODE
* Only the requested menu display is cold; the game loop remains resident.
GameMenuInput       ldu       <resourcebase
                    ifne      GAME_TRACE
                    inc       gametracemenuhit,u
                    endc
                    leax      menuentry,u
                    ldb       #20
                    leay      MenuCallbacks,pcr
                    lbra      GameColdInvoke
MenuCallbacks       fdb       AssetUnmap-MenuCallbacks,PictureUnmap-MenuCallbacks
                    fdb       InventoryString-MenuCallbacks,GameTextPresent-MenuCallbacks
                    fdb       GameModalForeground-MenuCallbacks,InputControllerAddress-MenuCallbacks
                    fdb       GameComposeScene-MenuCallbacks,RefreshPicture-MenuCallbacks

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_MENU_COLD_CODE
* ===== wildbits-menu-code =====
* Process-private modal menu. Existing labels/controllers retain their ABI.
* Display a paged list of titled items; disabled entries cannot be selected.
AuxMenuInput        ldu       <resourcebase
                    sty       coldapi,u
                    tst       <menuready
                    lbeq      AuxMenuInvalid
                    tst       <menuitems
                    lbeq      AuxMenuSuccess
                    UI_CALL   0
                    lbcs      AuxMenuReturn
                    UI_CALL   2
                    lbcs      AuxMenuReturn
                    ldu       <resourcebase
                    leax      textcharacters,u
                    leay      resourcecommands,u
                    ldd       #1000
                    pshs      d
GameMenuSave        ldd       ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       GameMenuSave
                    leas      2,s
                    clr       inventoryselected,u
                    clr       inventoryselected+1,u
GameMenuDraw        ldu       <resourcebase
                    leax      textcharacters,u
                    ldy       #1000
GameMenuWhite       lda       #32
                    sta       ,x
                    lda       #$0F
                    sta       1000,x
                    leax      1,x
                    leay      -1,y
                    bne       GameMenuWhite
                    leax      GameMenuTitle,pcr
                    leay      textcharacters+42,u
                    UI_CALL   4
                    leax      GameMenuHelp,pcr
                    leay      textcharacters+961,u
                    UI_CALL   4
                    clra
                    ldb       inventoryselected+1,u
                    cmpb      #21
                    blo       GameMenuPage
                    lda       #21
GameMenuPage        sta       inventorytop+1,u
                    clr       inventorytop,u
                    sta       inventoryprevious+1,u
                    clr       inventoryprevious,u
                    lda       #3
                    sta       inventoryrow,u
GameMenuItem        ldb       inventoryprevious+1,u
                    cmpb      <menuitems
                    lbhs      GameMenuPresent
                    lda       #6
                    mul
                    leax      menuentries,u
                    leax      d,x
                    pshs      x
                    lda       inventoryrow,u
                    ldb       #40
                    mul
                    leay      textcharacters,u
                    leay      d,y
                    pshs      y
                    ldb       #40
                    lda       inventoryprevious+1,u
                    cmpa      inventoryselected+1,u
                    bne       GameMenuNormal
                    lda       #$F0
                    bra       GameMenuRowColor
GameMenuNormal      lda       #$0F
                    tst       4,x
                    bne       GameMenuRowColor
                    lda       #$7F
GameMenuRowColor    sta       1000,y
                    leay      1,y
                    decb
                    bne       GameMenuRowColor
                    puls      y
                    leay      2,y
                    ldb       3,x
                    lda       #4
                    mul
                    leax      menutitles,u
                    ldd       d,x
                    leax      menutext,u
                    leax      d,x
                    ldb       #38
                    lbsr      GameMenuLabel
                    leax      GameMenuColon,pcr
                    lbsr      GameMenuLabel
                    puls      x
                    pshs      x
                    lda       inventoryrow,u
                    ldb       #40
                    mul
                    addd      #40
                    leax      textcharacters,u
                    leax      d,x
                    pshs      y
                    tfr       x,d
                    subd      ,s++
                    stb       inventorykey,u
                    puls      x
                    ldd       ,x
                    leax      menutext,u
                    leax      d,x
                    ldb       inventorykey,u
                    lbsr      GameMenuLabel
                    inc       inventoryprevious+1,u
                    inc       inventoryrow,u
                    lda       inventoryrow,u
                    cmpa      #24
                    lblo      GameMenuItem
GameMenuPresent     UI_CALL   6
                    lbcs      GameMenuRestore
GameMenuWait        UI_CALL   8
                    lbcs      GameMenuRestore
                    clra
                    ldb       #SS.Ready
                    os9       I$GetStt
                    bcc       GameMenuReadKey
                    cmpb      #E$NotRdy
                    lbne      GameMenuRestore
                    ldx       #2
                    os9       F$Sleep
                    bra       GameMenuWait
GameMenuReadKey     ldu       <resourcebase
                    leax      parsercharacter,u
                    ldy       #1
                    clra
                    os9       I$Read
                    lbcs      GameMenuRestore
                    ldu       <resourcebase
                    lda       parsercharacter,u
                    cmpa      #5
                    beq       GameMenuCancel
                    cmpa      #27
                    beq       GameMenuCancel
                    cmpa      #13
                    beq       GameMenuSelect
                    cmpa      #12
                    beq       GameMenuUp
                    cmpa      #8
                    beq       GameMenuUp
                    cmpa      #10
                    beq       GameMenuDown
                    cmpa      #9
                    bne       GameMenuWait
GameMenuDown        inc       inventoryselected+1,u
                    lda       inventoryselected+1,u
                    cmpa      <menuitems
                    blo       GameMenuChanged
                    clr       inventoryselected+1,u
                    bra       GameMenuChanged
GameMenuUp          tst       inventoryselected+1,u
                    bne       GameMenuDecrement
                    lda       <menuitems
                    sta       inventoryselected+1,u
GameMenuDecrement   dec       inventoryselected+1,u
GameMenuChanged     lbra      GameMenuDraw
GameMenuSelect      ldb       inventoryselected+1,u
                    lda       #6
                    mul
                    leax      menuentries,u
                    leax      d,x
                    tst       4,x
                    lbeq      GameMenuWait
                    ldb       2,x
                    UI_CALL   10
                    ora       ,x
                    sta       ,x
GameMenuCancel      clrb
GameMenuRestore     pshs      cc,b
                    ldu       <resourcebase
                    leax      resourcecommands,u
                    leay      textcharacters,u
                    ldd       #1000
                    pshs      d
GameMenuCopyBack    ldd       ,x++
                    std       ,y++
                    ldd       ,s
                    subd      #1
                    std       ,s
                    bne       GameMenuCopyBack
                    leas      2,s
                    puls      cc,b
                    lbcs      AuxMenuReturn
                    UI_CALL   12
                    lbcs      AuxMenuReturn
                    UI_CALL   14
                    rts
GameMenuLabel       tstb
                    beq       GameMenuLabelDone
                    lda       ,x+
                    beq       GameMenuLabelDone
                    sta       ,y+
                    decb
                    bra       GameMenuLabel
GameMenuLabelDone   rts
GameMenuTitle       fcc       /Game menu/
                    fcb       0
GameMenuColon       fcc       /: /
                    fcb       0
GameMenuHelp        fcc       /Arrows select; ENTER opens; ESC cancels/
                    fcb       0

AuxMenuSuccess      clrb
AuxMenuReturn       rts
AuxMenuInvalid      ldb       #E$BMode
                    orcc      #1
                    rts
                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_MENU_DATA
* ===== wildbits-menu-data =====
* Private menu construction controls. Labels are copied out of logic slabs.
menucount           rmb       1
menuitems           rmb       1
menucurrent         rmb       1
menuready           rmb       1
menutextused        rmb       2
menulabel           rmb       2
menuoperation       rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_MESSAGE_CODE
* ===== wildbits-message-code =====
* ReadLogicMessage: B=1-based message number. X=private messagebuffer,
* Y=length excluding NUL on success; C/error B otherwise. U/DP retained.
* Message offsets are little endian relative to the length word following
* the count. Plain AGI logic strings use Avis Durgan; LZW strings are plain.
* Every table/string access is checked against the owned expanded slab.
ReadLogicMessage    stb       <messagenumber
                    ldd       <vmend
                    lbsr      AssetReadByte
                    lbcs      MessageReturn
                    stb       <messagecount
                    tst       <messagenumber
                    lbeq      MessageInvalid
                    ldb       <messagenumber
                    cmpb      <messagecount
                    lbhi      MessageInvalid
                    ldd       <vmend
                    addd      #1
                    std       <messagebase
                    lbsr      AssetReadWord
                    lbcs      MessageReturn
                    cmpd      #2
                    lblo      MessageInvalid
                    addd      <messagebase
                    lbcs      MessageInvalid
                    cmpd      <resourcelength
                    lbhi      MessageInvalid
                    std       <messageend
                    clra
                    ldb       <messagecount
                    lslb
                    rola
                    addd      #2
                    addd      <messagebase
                    lbcs      MessageInvalid
                    std       <messagestart
                    cmpd      <messageend
                    lbhi      MessageInvalid
                    clra
                    ldb       <messagenumber
                    lslb
                    rola
                    addd      <messagebase
                    lbsr      AssetReadWord
                    lbcs      MessageReturn
                    cmpd      #0
                    lbeq      MessageInvalid
                    addd      <messagebase
                    lbcs      MessageInvalid
                    cmpd      <messagestart
                    blo      MessageInvalid
                    cmpd      <messageend
                    bhs      MessageInvalid
                    std       <messageposition
                    subd      <messagestart
MessageKeyModulo    cmpd      #11
                    blo       MessageKeyReady
                    subd      #11
                    bra       MessageKeyModulo
MessageKeyReady     stb       <messagekey
                    clr       <messagelength
                    clr       <messagelength+1
MessageCopyNext     ldd       <messageposition
                    cmpd      <messageend
                    bhs      MessageInvalid
                    lbsr      AssetReadByte
                    bcs      MessageReturn
                    pshs      b
                    ldd       <messageposition
                    addd      #1
                    std       <messageposition
                    ldd       <resourcestored
                    cmpd      <resourcelength
                    puls      b
                    bne       MessagePlainByte
                    leax      MessageXorKey,pcr
                    lda       <messagekey
                    eorb      a,x
                    inc       <messagekey
                    lda       <messagekey
                    cmpa      #11
                    blo       MessagePlainByte
                    clr       <messagekey
MessagePlainByte    pshs      b
                    ldu       <resourcebase
                    leax      messagebuffer,u
                    ldd       <messagelength
                    leax      d,x
                    puls      b
                    stb       ,x
                    tstb
                    beq       MessageDone
                    ldd       <messagelength
                    addd      #1
                    std       <messagelength
                    cmpd      #512
                    blo       MessageCopyNext
                    ldb       #E$MemFul
                    orcc      #1
                    bra       MessageReturn
MessageDone         ldu       <resourcebase
                    leax      messagebuffer,u
                    ldy       <messagelength
                    clrb
MessageReturn       rts
MessageInvalid      ldb       #E$BMode
                    orcc      #1
                    rts

MessageXorKey       equ       XorKeyStr
                    use shared/agi-xor-key.asm

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_MESSAGE_DATA
* ===== wildbits-message-data =====
* Private mapped-logic message reader controls.
messagebase         rmb       2
messageend          rmb       2
messagestart        rmb       2
messageposition     rmb       2
messagelength       rmb       2
messagenumber       rmb       1
messagecount        rmb       1
messagekey          rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_PARSER_DATA
* ===== wildbits-parser-data =====
* Persistent submitted words must survive resource loads in the logic cycle.
parserline          rmb       40
parserword          rmb       40
parserids           rmb       40
parsercount         rmb       1
parserlength        rmb       1
parserposition      rmb       1
parserwordlength    rmb       1
parserbestlength    rmb       1
parserbestid        rmb       2
parserreadindex     rmb       2
parserreadlength    rmb       2
parserid            rmb       2
parsercharacter     rmb       1
parserseen          rmb       1
parserstart         rmb       2
parserlastline      rmb       40
parseroffsets       rmb       20
parserlengths       rmb       20
formatdepth         rmb       1
dialogactive        rmb       1
dialogwordstart     rmb       1
dialoginputmode     rmb       1
terminalchanged     rmb       1
terminalecho        rmb       1
terminaleof         rmb       1
terminalquit        rmb       1
* The old decoded-ID scratch is now the selected encoded entry offset.
dictionaryentry     equ       parserid
* Stream cache base adds two bytes, still within three private pages.
dictionarycachebase rmb       2
* Temporary offsets occupy idle formatter output only during ParserParse.
dictionarygroups    equ       fillstack+2048

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_RENDER_TEXT
* ===== wildbits-render-text =====
* Render occupied text rows horizontally, avoiding a MapBlk round trip for
* each character when its eight scanlines straddle a framebuffer page.
* rowoutput is private, and index zero means leave that framebuffer pixel.
GameDrawTextDirty   lda       #1
                    ldb       <presentationconfigured
                    bpl       TextFastMode
GameDrawText        clra
TextFastMode        ldx       <resourcebase
                    sta       textrenderdirty,x
TextFastInitialize  ldd       #1000
                    std       textrenderend,x
                    clr       textrow,x
                    clr       textcolumn,x
TextFastPrepare     lbsr      AssetUnmap
                    lbcs      GameTextReturn
                    lbsr      PictureUnmap
                    lbcs      GameTextReturn
                    ldx       <resourcebase
TextFastNextRow     lbsr      foreground
                    lbcs      GameTextReturn
                    ldx       <resourcebase
                    lda       textrow,x
                    ldb       #40
                    mul
                    cmpd      textrenderend,x
                    lbhs      TextFastDone
                    std       textindex,x
                    tst       textrenderdirty,x
                    beq       TextFastReadRow
                    lda       textrow,x
                    suba      <vmpicturetop
                    bcs       TextFastDirtySkip
                    cmpa      #21
                    bhs       TextFastDirtySkip
                    lbsr      GameDamageTest
                    bne       TextFastDirtyPaint
TextFastDirtySkip   lbra      TextFastAdvanceRow
TextFastDirtyPaint  ldx       <resourcebase
TextFastReadRow     ldd       textrenderend,x
                    subd      textindex,x
                    cmpd      #40
                    bls       TextFastRowLimit
                    ldd       #40
TextFastRowLimit    decb
                    stb       textlastcolumn,x
                    incb
                    subb      textcolumn,x
                    pshs      b
                    ldd       textindex,x
                    leau      textcharacters,x
                    leau      d,u
                    ldb       textcolumn,x
                    leau      b,u
                    puls      b
TextFastFind        lda       ,u+
                    bne       TextFastOccupied
                    decb
                    bne       TextFastFind
                    lbra      TextFastAdvanceRow
TextFastOccupied    negb
                    incb
                    addb      textlastcolumn,x
                    stb       textfirstcolumn,x
* Locate the final occupied cell. Render the bounded span, preserving holes.
                    lda       textrow,x
                    ldb       #40
                    mul
                    leau      textcharacters,x
                    leau      d,u
                    ldb       textlastcolumn,x
                    leau      b,u
                    leau      1,u
TextFastFindLast    lda       ,-u
                    bne       TextFastLastFound
                    decb
                    bra       TextFastFindLast
TextFastLastFound   stb       textlastcolumn,x
                    clr       textglyphrow,x
TextFastGlyphRow    lda       textrow,x
                    ldb       #40
                    mul
                    addb      textfirstcolumn,x
                    adca      #0
                    std       textindex,x
                    lda       textfirstcolumn,x
                    sta       textcolumn,x
                    leay      rowoutput,x
TextFastCell        ldd       textindex,x
                    leau      textcharacters,x
                    lda       d,u
                    beq       TextFastEmpty
                    anda      #$7F
                    ldb       #8
                    mul
                    addb      textglyphrow,x
                    adca      #0
                    leau      gamefont,x
                    lda       d,u
                    sta       textbits,x
                    ldd       textindex,x
                    leau      textcolors,x
                    lda       d,u
                    tfr       a,b
                    anda      #$0F
                    inca
                    sta       textbackground,x
                    tfr       b,a
                    lsra
                    lsra
                    lsra
                    lsra
                    inca
                    sta       textforeground,x
                    ldb       #8
TextFastBits        lda       textbackground,x
                    lsl       textbits,x
                    bcc       TextFastPixel
                    lda       textforeground,x
TextFastPixel       sta       ,y+
                    decb
                    bne       TextFastBits
                    bra       TextFastNextCell
TextFastEmpty       clra
                    ldb       #8
TextFastBlank       sta       ,y+
                    decb
                    bne       TextFastBlank
TextFastNextCell    ldd       textindex,x
                    addd      #1
                    std       textindex,x
                    inc       textcolumn,x
                    lda       textcolumn,x
                    cmpa      textlastcolumn,x
                    bls      TextFastCell
                    leay      rowoutput,x
                    sty       textfontpointer,x
                    lda       textrow,x
                    ldb       #8
                    mul
                    addb      textglyphrow,x
                    adca      #0
                    lda       #160
                    mul
                    lslb
                    rola
                    pshs      d
                    lda       textfirstcolumn,x
                    ldb       #8
                    mul
                    addd      ,s++
                    std       textindex,x
                    lda       textlastcolumn,x
                    suba      textfirstcolumn,x
                    inca
                    ldb       #8
                    mul
                    std       textend,x
TextFastWriteSpan   ldd       textindex,x
                    lbsr      GameFramePointer
                    lbcs      GameTextReturn
                    anda      #$1F
                    pshs      d
                    ldd       #8192
                    subd      ,s++
                    cmpd      textend,x
                    bls       TextFastSpanSize
                    ldd       textend,x
TextFastSpanSize    ldy       textfontpointer,x
                    pshs      d,x
                    tfr       d,x
TextFastCopy        lda       ,y+
                    beq       TextFastSkip
                    sta       ,u
TextFastSkip        leau      1,u
                    leax      -1,x
                    bne       TextFastCopy
                    puls      d,x
                    sty       textfontpointer,x
                    pshs      d
                    addd      textindex,x
                    std       textindex,x
                    ldd       textend,x
                    subd      ,s++
                    std       textend,x
                    bne       TextFastWriteSpan
                    inc       textglyphrow,x
                    lda       textglyphrow,x
                    cmpa      #8
                    lblo      TextFastGlyphRow
TextFastAdvanceRow  ldx       <resourcebase
                    inc       textrow,x
                    clr       textcolumn,x
                    lbra      TextFastNextRow
TextFastDone        equ       *
                    tst       <mapped
                    lbeq      GameCycleSuccess
                    lbra      unmap

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_REPLAY_CODE
* ===== wildbits-replay-code =====
* Size/reset/checkpoint commands adapted from mnln's script-buffer routines.
* A record is D = operation/resource. C/error B on overflow; U retained.
ReplayInitialize    ldu       <resourcebase
                    ldb       vmarguments,u
                    stb       <replaylimit
                    clr       <replayused
                    clr       <replayused+1
                    clr       <replaycheckpoint
                    clr       <replaycheckpoint+1
                    clrb
                    rts
ReplayPush          pshs      d,x
                    tst       <replaylimit
                    beq       ReplayDisabled
                    clra
                    ldb       <replaylimit
                    lslb
                    rola
                    cmpd      <replayused
                    bls       ReplayOverflow
                    ldu       <resourcebase
                    leax      replaybuffer,u
                    ldd       <replayused
                    leax      d,x
                    ldd       ,s
                    std       ,x
                    ldd       <replayused
                    addd      #2
                    std       <replayused
                    puls      d,x
                    andcc     #$FE
                    rts
ReplayDisabled      puls      d,x
                    andcc     #$FE
                    rts
ReplayOverflow      puls      d,x
                    ldb       #E$MemFul
                    orcc      #1
                    rts
ReplaySaveCheckpoint    ldd       <replayused
                    std       <replaycheckpoint
                    clrb
                    rts
ReplayRestore       ldd       <replaycheckpoint
                    cmpd      <replayused
                    bhi       ReplayInvalid
                    std       <replayused
                    clrb
                    rts
ReplayInvalid       ldb       #E$BMode
                    orcc      #1
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_REPLAY_DATA
* ===== wildbits-replay-data =====
* Replay records store resource operations for eventual save/restore.
* Private control state; the owner supplies a 510-byte record buffer.
replaylimit         rmb       1
replayused          rmb       2
replaycheckpoint    rmb       2

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_FORMAT_CODE
* ===== wildbits-format-code =====
                    ifndef PLATFORM_WILDBITS_TEXT_UI_BINDINGS
                    use platform/wildbits-text-ui-bindings.asm
                    endc
* Bounded formatter. Four 512-byte source frames and a 2048-byte output
* share the idle fill stack; recursion never retains a mapped message pointer.
                    use shared/nul-string-copy.asm
                    ifne WILDBITS
                    ifndef PLATFORM_WILDBITS_TEXT_UI_BINDINGS
                    use platform/wildbits-text-ui-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_TEXT_UI_BINDINGS
                    use platform/coco-text-ui-bindings.asm
                    endc
                    endc
                    use shared/formatter.asm
GameFormatMessage   ldu       <resourcebase
                    clr       formatdepth,u
                    clr       parserreadlength,u
                    clr       parserreadlength+1,u
                    leay      fillstack+2048,u
                    sty       parserreadindex,u
                    clr       ,y
                    bsr      FormatPart
                    lbcs      FormatReturn
                    leax      fillstack+2048,u
                    clrb
                    rts
FormatPart          lda       formatdepth,u
                    cmpa      #4
                    lbhs      FormatInvalid
                    ldb       #0
                    lsla
                    leay      fillstack,u
                    leay      d,y
                    pshs      y
                    NUL_STRING_COPY x,FormatCopy,1,NUL_FRAME_WRITE,NUL_COPY_NOOP,NUL_COPY_NOOP
                    puls      x
                    inc       formatdepth,u
FormatNext          equ *
                    FORMAT_EMIT_SCAN
FormatDirective     lda       ,x+
                    cmpa      #'%
                    bne       FormatNumberStart
                    bsr      FormatPut
                    bcs      FormatPartError
                    bra       FormatNext
FormatNumberStart   sta       parsercharacter,u
                    clr       parserwordlength,u
                    clr       parserbestlength,u
FormatNumber        lbsr      ParseDecStr
                    bcs      FormatPartError
FormatDispatch      tst       parserbestlength,u
                    beq      FormatPartInvalid
                    lda       parsercharacter,u
                    ldb       parserwordlength,u
                    FORMAT_EMIT_DIRECTIVES
FormatUnsupported   ldb       #E$UnkSvc
                    orcc      #1
                    bra       FormatPartError
FormatDone          dec       formatdepth,u
                    clrb
FormatReturn        rts
FormatPartInvalid   ldb       #E$BMode
                    orcc      #1
FormatPartError     dec       formatdepth,u
                    rts
FormatInvalid       ldb       #E$BMode
                    orcc      #1
                    rts
FormatPut           pshs      d,y
                    ldd       parserreadlength,u
                    cmpd      #2047
                    bhs       FormatFull
                    addd      #1
                    std       parserreadlength,u
                    ldy       parserreadindex,u
                    lda       ,s
                    sta       ,y+
                    clr       ,y
                    sty       parserreadindex,u
                    andcc     #$FE
                    puls      d,y,pc
FormatFull          puls      d,y
                    ldb       #E$BMode
                    orcc      #1
                    rts
FormatWord          tstb
                    beq      FormatPartInvalid
                    cmpb      #20
                    bhi      FormatPartInvalid
                    lda       parsercount,u
                    tst       vmvariables+9,u
                    beq       FormatWordBound
                    inca
FormatWordBound     pshs      a
                    cmpb      ,s+
                    bhi      FormatPartInvalid
                    decb
                    leay      parseroffsets,u
                    leay      b,y
                    lda       ,y
                    ldb       20,y
                    leay      parserlastline,u
                    leay      a,y
FormatWordCopy      tstb
                    lbeq      FormatNext
                    lda       ,y+
                    bsr      FormatPut
                    bcs      FormatPartError
                    decb
                    bra       FormatWordCopy
FormatString        equ *
                    FORMAT_EMIT_STRING_SLOT
                    NUL_STRING_COPY y,FormatStringCopy,0,FORMAT_STRING_WRITE,FORMAT_STRING_DONE,FORMAT_STRING_ERROR
* Object names use the same checked recursive expansion as messages.
* The cold adapter reads a bounded inventory name and resolves v[index].
FormatObject        pshs      x
                    leax      formatentry,u
                    ldb       #22
                    leay      FormatObjectCallbacks,pcr
                    lbsr      GameColdInvoke
                    bra       FormatMessageReturn
FormatObjectCallbacks fdb AssetUnmap-FormatObjectCallbacks,ResourceClose-FormatObjectCallbacks,FormatPart-FormatObjectCallbacks
FormatMessage       pshs      x
                    lbsr      ReadLogicMessage
                    bcs       FormatMessageReturn
FormatMessageReturn equ FormatExpansionReturn
                    FORMAT_EMIT_EXPANSION
* Optional decimal width belongs to this numeric expansion only. No recursive
* expansion occurs between parsing the width and consuming its zero padding.
FormatVariable      pshs      b
                    clrb
                    lda       ,x
                    cmpa      #'|
                    bne       FormatWidthReady
                    leax      1,x
                    clr       parserwordlength,u
                    clr       parserbestlength,u
                    lbsr      ParseDecStr
                    bcc       FormatWidthReady
                    leas      1,s
                    lbra      FormatPartError
FormatWidthReady    stb       parserbestlength,u
                    puls      b
                    leay      vmvariables,u
                    clra
                    ldb       d,y
* Keep the source cursor/context and four numeric bytes on the caller stack.
* No copied message, source frame, or persistent argument buffer is reused.
                    pshs      u,x
                    leas      -4,s
                    leax      3,s
                    bsr      UIntToDecStr
                    tfr       x,y
* The converter ends at stack byte 3; subtract the first digit address.
                    leax      3,s
                    tfr       x,d
                    pshs      y
                    subd      ,s++
                    ldu       6,s
                    pshs      b
                    ldb       parserbestlength,u
                    subb      ,s+
                    bls       FormatWidthDone
                    lda       #'0
FormatWidthPad      lbsr      FormatPut
                    bcs       FormatVariableError
                    decb
                    bne       FormatWidthPad
FormatWidthDone     ldx       4,s
                    NUL_STRING_COPY y,FormatVariableCopy,0,FORMAT_STRING_WRITE,FORMAT_NUMBER_DONE,FORMAT_NUMBER_ERROR
FormatVariableDone  leas      8,s
                    lbra      FormatNext
FormatVariableError leas      8,s
                    lbra      FormatPartError

* Assembly-time decimal output storage/division interface.
                    ifne      WILDBITS
                    ifndef PLATFORM_WILDBITS_TEXT_UI_BINDINGS
                    use platform/wildbits-text-ui-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_TEXT_UI_BINDINGS
                    use platform/coco-text-ui-bindings.asm
                    endc
                    endc
                    use       shared/unsigned-decimal.asm
* Bind the common quotient/remainder ABI to the existing 8-bit divider.
* D <= 255, U=10; return U=quotient and D=remainder, preserving X/Y.
FormatByteDivide10  lda       #10
                    lbsr      Div8
                    pshs      a
                    clra
                    tfr       d,u
                    puls      b
                    rts

* Assembly-time formatter index policy; no runtime dispatch.
                    ifne      WILDBITS
                    ifndef PLATFORM_WILDBITS_TEXT_UI_BINDINGS
                    use platform/wildbits-text-ui-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_TEXT_UI_BINDINGS
                    use platform/coco-text-ui-bindings.asm
                    endc
                    endc
                    use       shared/decimal-index.asm
DecimalIndexOverflow ldb     #E$BMode
                    orcc      #1
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_PARSER_CODE
* ===== wildbits-parser-code =====
                    ifndef PLATFORM_WILDBITS_TEXT_UI_BINDINGS
                    use platform/wildbits-text-ui-bindings.asm
                    endc
* Streaming original words.tok; no slab is held across file or terminal I/O.
* Private line/IDs survive assetinput being reused by subsequent logic loads.
ParserInitialize    ldu       <resourcebase
                    clr       parserlength,u
                    clr       parserline,u
                    clr       parsercount,u
                    clr       dialogactive,u
                    clr       dialogwordstart,u
                    clr       dialoginputmode,u
                    rts
ParserCommand       ldu       <resourcebase
                    lda       vmarguments,u
                    cmpa      #12
                    lbhs      ParserInvalid
                    ldb       #40
                    mul
                    leax      vmstrings,u
                    leax      d,x
                    leay      parserline,u
                    clr       parserlength,u
ParserCopy          lda       ,x+
                    beq       ParserCopyDone
                    bsr      ParserLower
                    sta       ,y+
                    inc       parserlength,u
                    ldb       parserlength,u
                    cmpb      #39
                    blo       ParserCopy
ParserCopyDone      clr       ,y
                    bra      ParserParse
ParserLower         equ       LowercaseByte
ParserLowerDone     equ       LowercaseReturn
                    use       shared/ascii-lower.asm
ParserParse         lbsr      ParserNormalize
                    lbsr      AssetUnmap
                    lbcs      ParserReturn
                    lbsr      PictureUnmap
                    lbcs      ParserReturn
                    ldu       <resourcebase
                    leax      parserline,u
                    leay      parserlastline,u
                    ldb       #40
ParserSaveLine      lda       ,x+
                    sta       ,y+
                    decb
                    bne       ParserSaveLine
                    clr       parsercount,u
                    clr       parserposition,u
                    clr       parserseen,u
                    clr       vmflags+2,u
                    clr       vmflags+4,u
                    clr       vmvariables+9,u
                    ldy       resourcenameend,u
                    leax      ParserFilename,pcr
                    lbsr      ResourceSuffix
                    lbsr      OpenPicturePath
                    lbcs      ResourceFailed
* Validate complete 26-letter index, then scan entries from offset 52.
                    ldu       <resourcebase
                    leax      assetinput,u
                    ldy       #52
                    lbsr      ResourceReadExact
                    lbcs      ResourceFailed
                    ldu       <resourcebase
                    leax      assetinput,u
                    ldy       #26
                    ldd       #$FFFF
                    std       parserstart,u
ParserIndex         ldd       ,x++
                    beq       ParserIndexNext
                    cmpd      #52
                    lblo      ParserMalformed
                    cmpd      parserstart,u
                    bhs       ParserIndexNext
                    std       parserstart,u
ParserIndexNext     leay      -1,y
                    bne       ParserIndex
                    ldd       parserstart,u
                    cmpd      #$FFFF
                    bne       ParserNextInput
                    ldd       #52
                    std       parserstart,u
ParserNextInput     ldu       <resourcebase
                    leax      parserline,u
                    ldb       parserposition,u
                    lda       b,x
                    lbeq      ParserComplete
                    cmpa      #32
                    bne       ParserSearch
                    inc       parserposition,u
                    bra       ParserNextInput
ParserSearch        tst       parserseen,u
                    bne      ParserSelectGroup
                    leax      dictionarygroups,u
                    ldy       #256
                    ldd       #$FFFF
DictionaryClearGroups std    ,x++
                    leay      -1,y
                    bne       DictionaryClearGroups
                    clr       parserwordlength,u
                    clr       parserreadindex,u
                    clr       parserreadindex+1,u
                    clr       parserreadlength,u
                    clr       parserreadlength+1,u
                    ldd       parserstart,u
                    std       dictionarycachebase,u
                    lda       <resourcepath
                    ldx       #0
                    ldu       parserstart,u
                    os9       I$Seek
                    lbcs      ResourceFailed
                    ldu       <resourcebase
                    lbra      DictionaryValidateEntry
ParserSelectGroup   leax      parserline,u
                    ldb       parserposition,u
                    lda       b,x
                    ldb       #2
                    mul
                    leax      dictionarygroups,u
                    leax      d,x
                    ldd       ,x
                    std       dictionaryentry,u
ParserLookup        leax      parserline,u
                    ldb       parserposition,u
                    leau      b,x
                    pshs      u
                    lbsr      LookupWord
                    bcc       ParserLookupResult
                    leas      2,s
                    lbra      ResourceFailed
ParserLookupResult  pshs      d
                    tfr       u,d
                    subd      2,s
                    cmpb      #0
                    beq       ParserLookupLength
                    lda       -1,u
                    cmpa      #32
                    bne       ParserLookupLength
                    decb
ParserLookupLength  ldu       <resourcebase
                    stb       parserbestlength,u
                    puls      d
                    std       parserbestid,u
                    leas      2,s
                    bra      ParserSearchDone
ParserSearchDone    lda       parserbestlength,u
                    beq       ParserUnknown
                    adda      parserposition,u
                    sta       parserposition,u
                    ldd       parserbestid,u
                    lbeq      ParserNextInput
                    ldb       parsercount,u
                    cmpb      #20
                    bhs       ParserMalformed
                    leay      parseroffsets,u
                    lda       parserposition,u
                    suba      parserbestlength,u
                    sta       b,y
                    lda       parserbestlength,u
                    leay      b,y
                    sta       20,y
                    lslb
                    leax      parserids,u
                    leax      b,x
                    ldd       parserbestid,u
                    std       ,x
                    inc       parsercount,u
                    lbra      ParserNextInput
ParserUnknown       ldb       parsercount,u
                    cmpb      #20
                    bhs      ParserMalformed
                    leay      parseroffsets,u
                    leay      b,y
                    lda       parserposition,u
                    sta       ,y
                    leax      parserlastline,u
                    leax      a,x
                    clrb
ParserUnknownLength lda      ,x+
                    beq       ParserUnknownEnd
                    cmpa      #32
                    beq       ParserUnknownEnd
                    incb
                    bra       ParserUnknownLength
ParserUnknownEnd    stb       20,y
                    lda       parsercount,u
                    inca
                    sta       vmvariables+9,u
ParserComplete      lda       parserlength,u
                    beq       ParserClose
                    lda       #1
                    sta       vmflags+2,u
ParserClose         lbra      ResourceClose
ParserTruncated     cmpb      #E$EOF
                    lbne      ResourceFailed
ParserMalformed     ldb       #E$BMode
                    lbra      ResourceFailed
ParserInvalid       ldb       #E$IllArg
                    orcc      #1
ParserReturn        rts
ParserFilename      fcc       /words.tok/
                    fcb       C$CR
DictionaryValidateEntry ldd dictionarycachebase,u
                    addd      parserreadindex,u
                    std       parserbestid,u
                    lbsr      ParserByte
                    bcc       ParserPrefix
                    cmpb      #E$EOF
                    lbne      ResourceFailed
                    bra      DictionaryValidateDone
ParserPrefix        cmpb      parserwordlength,u
                    bhi      ParserMalformed
                    stb       parserwordlength,u
ParserSuffix        lbsr      ParserByte
                    bcc       ParserSuffixByte
                    cmpb      #E$EOF
                    lbne      ResourceFailed
                    tst       parserwordlength,u
                    beq      DictionaryValidateDone
                    bra      ParserMalformed
ParserSuffixByte
                    stb       parsercharacter,u
                    andb      #$7F
                    eorb      #$7F
                    cmpb      #32
                    blo      ParserMalformed
                    lda       parserwordlength,u
                    cmpa      #39
                    bhs      ParserMalformed
                    leax      parserword,u
                    stb       a,x
                    inc       parserwordlength,u
                    tst       parsercharacter,u
                    bpl       ParserSuffix
                    lbsr      ParserByte
                    bcs      ParserTruncated
                    lbsr      ParserByte
                    bcs      ParserTruncated
                    lda       parserword,u
                    ldb       #2
                    mul
                    leax      dictionarygroups,u
                    leax      d,x
                    ldd       ,x
                    cmpd      #$FFFF
                    bne      DictionaryValidateEntry
                    ldd       parserbestid,u
                    std       ,x
                    lbra      DictionaryValidateEntry
DictionaryValidateDone ldd  #0
                    std       parserreadlength,u
                    inc       parserseen,u
                    lbra      ParserSelectGroup

                    ifne WILDBITS
                    ifndef PLATFORM_WILDBITS_TEXT_UI_BINDINGS
                    use platform/wildbits-text-ui-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_TEXT_UI_BINDINGS
                    use platform/coco-text-ui-bindings.asm
                    endc
                    endc
                    use shared/dictionary-lookup.asm
                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_DICTIONARY_CODE
                    use platform/wildbits-text-ui.asm

* Buffered partial reads, with EOF accepted only between complete entries.
ParserByte          ldu       <resourcebase
                    ldd       parserreadindex,u
                    cmpd      parserreadlength,u
                    blo       ParserBuffered
                    ldd       dictionarycachebase,u
                    addd      parserreadlength,u
                    std       dictionarycachebase,u
                    lda       <resourcepath
                    leax      assetinput,u
                    ldy       #512
                    os9       I$Read
                    lbcs      ParserReturn
                    ldu       <resourcebase
                    cmpy      #0
                    beq       ParserReadInvalid
                    cmpy      #512
                    bhi       ParserReadInvalid
                    sty       parserreadlength,u
                    ldd       #0
                    std       parserreadindex,u
ParserBuffered      leax      assetinput,u
                    leax      d,x
                    ldb       ,x
                    pshs      b
                    ldd       parserreadindex,u
                    addd      #1
                    std       parserreadindex,u
                    puls      b
                    andcc     #$FE
                    rts
ParserReadInvalid   ldb       #E$BMode
                    orcc      #1
                    rts
* said words are little endian in bytecode; dictionary IDs are big endian.
ParserSaid          ldu       <resourcebase
                    tst       vmflags+2,u
                    beq       ParserFalse
                    tst       vmflags+4,u
                    bne       ParserFalse
                    leax      parserids,u
                    leay      vmarguments,u
                    lda       parsercount,u
                    sta       <vmright
                    lda       <vmargcount
                    lsra
                    sta       <vmleft
SaidExpected        equ       vmleft
SaidParsed          equ       vmright
                    use       shared/said-match.asm
SaidCheckDone       ldd       <SaidExpected
                    bne       SaidNoMatch
SaidSetMatch        lda       #1
                    sta       vmflags+4,u
                    ldb       #1
                    andcc     #$FE
                    rts
SaidNoMatch         lsla
                    leay      a,y
ParserFalse         clrb
                    rts
* Unbound printable keys feed the input line; controllers retain precedence.
ParserKey           ldu       <resourcebase
                    tst       <vminputenabled
                    lbeq      GameCycleSuccess
                    lda       <vmkeybyte
                    cmpa      #13
                    beq       ParserSubmit
                    cmpa      #8
                    beq       ParserBackspace
                    cmpa      #32
                    lblo      GameCycleSuccess
                    cmpa      #126
                    lbhi      GameCycleSuccess
                    ldb       parserlength,u
                    cmpb      #38
                    lbhs      GameCycleSuccess
                    cmpb      vmvariables+24,u
                    lbhs      GameCycleSuccess
                    lbsr      ParserLower
                    leax      parserline,u
                    sta       b,x
                    incb
                    clr       b,x
                    stb       parserlength,u
                    lbra      GameCycleSuccess
ParserBackspace     ldb       parserlength,u
                    lbeq      GameCycleSuccess
                    decb
                    stb       parserlength,u
                    leax      parserline,u
                    clr       b,x
                    lbra      GameCycleSuccess
ParserSubmit        lbsr      ParserParse
                    lbcs      ParserReturn
                    ldu       <resourcebase
                    clr       parserlength,u
                    clr       parserline,u
                    clrb
                    rts
* Rebuild the input row before ordinary presentation, never in modal screens.
ParserDrawInput     clr       <vmopcode    internal screen refresh, not an AGI opcode
                    lbsr      ScreenCommand
                    lbcs      GameCycleReturn
                    ldu       <resourcebase
                    tst       <vminputenabled
                    lbeq      GameCycleSuccess
                    tst       vmstrings,u
                    bne       ParserInputVisible
                    tst       parserlength,u
                    lbeq      GameCycleSuccess
ParserInputVisible  lda       <vminputrow
                    ldb       #40
                    mul
                    leax      textcharacters,u
                    leax      d,x
                    pshs      x
                    leay      rowoutput,u
                    ldb       #40
ParserInputSnapshot lda       ,x
                    sta       ,y+
                    lda       1000,x
                    sta       ,y+
                    leax      1,x
                    decb
                    bne       ParserInputSnapshot
                    ldx       ,s
                    ldb       #40
ParserBlankInput    lda       #32
                    sta       ,x
                    lda       <vmtextforeground
                    lsla
                    lsla
                    lsla
                    lsla
                    ora       <vmtextbackground
                    sta       1000,x
                    leax      1,x
                    decb
                    bne       ParserBlankInput
                    ldx       ,s
                    leay      vmstrings,u     string zero is the AGI prompt
                    ldb       #40
ParserPrompt        lda       ,y+
                    beq       ParserInputText
                    sta       ,x+
                    decb
                    bne       ParserPrompt
                    bra       ParserInputCompare
ParserInputText     leay      parserline,u
ParserInputCopy     lda       ,y+
                    beq       ParserCursor
                    sta       ,x+
                    decb
                    bne       ParserInputCopy
                    bra       ParserInputCompare
ParserCursor        lda       <vmcursor
                    sta       ,x
ParserInputCompare  puls      x
                    leay      rowoutput,u
                    ldb       #40
ParserInputCheck    lda       ,x
                    cmpa      ,y+
                    bne       ParserInputChanged
                    lda       1000,x
                    cmpa      ,y+
                    bne       ParserInputChanged
                    leax      1,x
                    decb
                    bne       ParserInputCheck
                    lbra      GameCycleSuccess
ParserInputChanged  lda       <presentationconfigured
                    ora       #$80
                    sta       <presentationconfigured
                    lbra      GameCycleSuccess

* In-place adapter to the same sentence tokenizer assembled by CoCo.
ParserNormalize     ldu       <resourcebase
                    leau      parserline,u
                    bsr      TokenizeString
                    ldu       <resourcebase
                    rts
                    use       shared/tokenize-string.asm
                    use       shared/find-byte.asm
                    use       shared/parser-punctuation.asm

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_STRING_CODE
* ===== wildbits-string-code =====
                    ifndef PLATFORM_WILDBITS_TEXT_UI_BINDINGS
                    use platform/wildbits-text-ui-bindings.asm
                    endc
                    use       shared/bounded-string-copy.asm
* Private 12-slot, 40-byte string table matching the existing CoCo layout.
StringsInitialize   ldu       <resourcebase
                    leax      vmstrings,u
                    ldy       #480
                    clra
StringsClear        sta       ,x+
                    leay      -1,y
                    bne       StringsClear
                    rts
SetStringCommand    ldu       <resourcebase
                    lda       vmarguments,u
                    cmpa      #12
                    bhs       StringInvalid
                    ldb       vmarguments+1,u
                    lbsr      ReadLogicMessage
                    bcs       StringReturn
                    ldu       <resourcebase
                    leay      vmstrings,u
                    lda       vmarguments,u
                    ldb       #40
                    mul
                    leay      d,y
                    ldb       #39
                    BOUNDED_STRING_COPY y,StringCopy,StringDone,BOUNDED_BYTE_COUNT
                    clrb
StringReturn        rts
StringInvalid       ldb       #E$IllArg
                    orcc      #1
                    rts

                    ifne      GAME_PRESENTATION
* Condition 15 uses the CoCo normalization/comparison body on private slots.
StringCompareTest   ldu       <resourcebase
                    ldd       vmarguments,u
                    cmpa      #12
                    bhs      StringInvalid
                    cmpb      #12
                    bhs      StringInvalid
                    bsr      MatchWord
                    ldu       <resourcebase
                    tfr       a,b
                    andcc     #$FE
                    rts
NORMAL_STRING_FOLD  equ       ParserLower
                    use       shared/compare-strings.asm
                    use       shared/string-punctuation.asm
                    endc

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_FORMAT_COLD_CODE
* Object names are read into the 512-byte I/O buffer, never inventoryfile:
* inventoryfile aliases the live recursive formatter frames in fillstack.
* Y names relative callbacks (unmap, close, recursive format). No allocation
* or inventory-room mutation is needed; all state lives on the private stack.
AuxFormatObject     pshs      y
                    leas      -6,s     ; table bytes, name offset, item offset
                    clra
                    ldb       parserwordlength,u
                    leax      vmvariables,u
                    ldb       d,x
                    lda       #3
                    mul
                    std       4,s
                    ldd       ,y
                    leax      d,y
                    jsr       ,x       ; release ephemeral asset mapping
                    lbcs      AuxObjectReturn
                    ldu       <resourcebase
                    ldy       resourcenameend,u
                    leax      AuxObjectFilename,pcr
AuxObjectPath       lda       ,x+
                    sta       ,y+
                    cmpa      #C$CR
                    bne       AuxObjectPath
                    leax      resourcefilename,u
                    lda       #READ.
                    os9       I$Open
                    lbcs      AuxObjectReturn
                    sta       <resourcepath
                    inc       <resourceopen
                    ldd       #0
                    ldy       #3
                    lbsr      AuxObjectReadAt
                    lbcs      AuxObjectFailed
                    cmpy      #3
                    lbne      AuxObjectInvalid
                    ldb       ,x
                    lda       1,x
                    cmpd      #768
                    lbhi      AuxObjectInvalid
                    std       ,s
AuxObjectTableCheck  subd      #3
                    lblo      AuxObjectInvalid
                    bne       AuxObjectTableCheck
                    ldd       4,s
                    cmpd      ,s
                    lbhs      AuxObjectInvalid
                    addd      #3
                    ldy       #3
                    lbsr      AuxObjectReadAt
                    lbcs      AuxObjectFailed
                    cmpy      #3
                    lbne      AuxObjectInvalid
                    ldb       ,x
                    lda       1,x
                    addd      #3
                    lbcs      AuxObjectInvalid
                    cmpd      #2048
                    lbhs      AuxObjectInvalid
                    std       2,s
                    subd      #3
                    cmpd      ,s
                    lblo      AuxObjectInvalid
                    ldd       #2048
                    subd      2,s
                    cmpd      #512
                    bls       AuxObjectReadLength
                    ldd       #512
AuxObjectReadLength tfr       d,y
                    ldd       2,s
                    lbsr      AuxObjectReadAt
                    bcs       AuxObjectFailed
                    pshs      x
AuxObjectBound      lda       ,x+
                    beq       AuxObjectReady
                    leay      -1,y
                    bne       AuxObjectBound
                    leas      2,s
                    bra       AuxObjectInvalid
AuxObjectReady      lbsr      AuxObjectClose
                    puls      x
                    bcs       AuxObjectReturn
                    ldy       6,s
                    ldd       4,y
                    leay      d,y
                    jsr       ,y       ; shared recursive formatter body
AuxObjectReturn     leas      6,s
                    puls      y,pc
AuxObjectInvalid    ldb       #E$BMode
                    orcc      #1
AuxObjectFailed     pshs      b,cc
                    lbsr      AuxObjectClose
                    puls      cc,b
                    bra       AuxObjectReturn
* Return address, saved X or error, six locals, then the callback pointer.
AuxObjectClose      ldy       10,s
                    ldd       2,y
                    leay      d,y
                    jmp       ,y
* D=file offset, Y=maximum read; return X=decoded bytes, Y=actual length.
* Decryption starts at the absolute file offset, not the current read window.
AuxObjectReadAt     pshs      d,y
                    tfr       d,u
                    ldx       #0
                    lda       <resourcepath
                    os9       I$Seek
                    bcs       AuxObjectReadError
                    ldu       <resourcebase
                    leax      assetinput,u
                    ldy       2,s
                    stx       <resourcepointer
                    sty       <resourceremaining
AuxObjectReadMore   lda       <resourcepath
                    ldx       <resourcepointer
                    ldy       <resourceremaining
                    os9       I$Read
                    bcs       AuxObjectReadEnd
                    cmpy      #0
                    lbeq      AuxObjectReadInvalid
                    tfr       y,d
                    leax      d,x
                    stx       <resourcepointer
                    ldy       <resourceremaining
                    pshs      d
                    tfr       y,d
                    subd      ,s++
                    std       <resourceremaining
                    bne       AuxObjectReadMore
                    bra       AuxObjectReadComplete
AuxObjectReadEnd    cmpb      #E$EOF
                    lbne      AuxObjectReadError
AuxObjectReadComplete ldd     2,s
                    subd      <resourceremaining
                    lbeq      AuxObjectReadInvalid
                    tfr       d,y
                    ldu       <resourcebase
                    leax      assetinput,u
                    pshs      y
                    ldd       2,s
AuxObjectKeyModulo  cmpd      #11
                    blo       AuxObjectKeyReady
                    subd      #11
                    bra       AuxObjectKeyModulo
AuxObjectKeyReady   leau      AuxObjectKey,pcr
AuxObjectDecrypt    lda       ,x
                    eora      b,u
                    sta       ,x+
                    incb
                    cmpb      #11
                    blo       AuxObjectNextByte
                    clrb
AuxObjectNextByte   leay      -1,y
                    bne       AuxObjectDecrypt
                    puls      y
                    ldu       <resourcebase
                    leax      assetinput,u
                    clrb
                    bra       AuxObjectReadReturn
AuxObjectReadInvalid ldb      #E$BMode
                    orcc      #1
AuxObjectReadError  ldu       <resourcebase
AuxObjectReadReturn leas      4,s
                    rts
AuxObjectFilename   fcc       /object/
                    fcb       C$CR
AuxObjectKey        fcc       /Avis Durgan/

                    else
                    error Unknown platform feature section
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
