                    use shared/bounded-string-copy.asm
* Shared show/UI callback protocol. Keep priority wait callbacks contiguous.
                    ifndef WILDBITS_SHOW_API_LAYOUT
WILDBITS_SHOW_API_LAYOUT equ 1
ShowApiPriorityWait equ 36
ShowApiModuleHeader equ 44
ShowApiTextPresent  equ 46
ShowApiPictureUnmap equ 48
ShowApiReadMessage  equ 50
ShowApiPrintText    equ 16
ShowApiLoadResource equ 8
DIALOG_TRACE_MODE   equ 5
DIALOG_RESTART_MODE equ 6
                    endc
* Grouped diagnostic backend; owner-specific buffers stay private.
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_DIAGNOSTIC_CODE
* The restart unwind resumes through this cached entry without a directory
* argument. Its private API was captured by the original request.
AuxUiCommand        ldu       <resourcebase
                    lda       <vmopcode
                    cmpa      #VM_EVENT_MISSING_LOGIC
                    beq       AuxMissingRoomLogic
                    cmpa      #VM_EVENT_ROOM_LOAD_ERROR
                    lbeq      AuxRoomLoadIoError
                    cmpa      #182
                    lbeq      AuxTraceDispatch
                    lda       <vmroompending
                    cmpa      #3
                    lbeq      AuxRestart
                    ldb       <vmopcode
                    leax      UiCommandClasses,pcr
                    lbsr      UiCatalogNibble
                    tfr       b,a
                    cmpa      #4
                    bhs      AuxUiTraceClass
AuxUiClassLookup    pshs      a
                    lsla
                    ldd       a,y
                    leay      d,y
                    puls      a
                    cmpa      #1
                    lbeq      AuxShakeScreen
                    cmpa      #2
                    lbeq      AuxRestart
                    cmpa      #3
                    lbeq      AuxStateName
                    lbra      AuxShowObject
AuxUiTraceClass
* The first directory entry is the common game UI callback table. Only trace
* commands need this cached pointer; ordinary classes keep their old state.
                    pshs      a
                    ldd       ,y
                    leax      d,y
                    stx       coldapi,u
                    puls      a
                    ldb       <vmopcode
                    cmpb      #149
                    lbeq      AuxTraceOn
                    lbra      AuxTraceInfo
* Missing native logics use CoCo's message text and the normal modal print
* callback, keeping message formatting out of the resident code budget.
AuxMissingRoomLogic pshs      cc,d,x,y,u
                    ldu       <resourcebase
                    ldd       ,y
                    leay      d,y
                    sty       coldapi,u
                    clra
                    ldb       resourcenumber+1,u
                    pshs      b,a
                    leax      AuxMissingRoomName,pcr
                    pshs      x
                    leax      AuxMissingRoomFormat,pcr
                    leau      messagebuffer,u
                    pshs      x
                    pshs      u
                    lbsr      PrintFmtStr
                    leas      8,s
                    ldu       <resourcebase
                    ldy       coldapi,u
                    ldd       ShowApiPrintText,y
                    leay      d,y
                    leax      messagebuffer,u
                    jsr       ,y
                    puls      cc,d,x,y,u,pc
AuxMissingRoomName  fcc       /Logics/
                    fcb       0
AuxMissingRoomFormat fcc      /%s #%d not found./
                    fcb       0
* Room setup reports non-missing destination-load errors here. ENTER retries
* the logic resource; ESC ends the game through the normal VM quit state.
AuxRoomLoadIoError  pshs      cc,d,x,y,u
                    lda       <resourceerror
                    cmpa      #E$PNNF
                    lbeq      AuxRoomLoadIoMissing
                    ldu       <resourcebase
                    ldd       ,y
                    leay      d,y
                    sty       coldapi,u
AuxRoomLoadIoRetry  ldu       <resourcebase
                    lda       #DIALOG_RESTART_MODE
                    sta       dialoginputmode,u
                    ldy       coldapi,u
                    ldd       ShowApiPrintText,y
                    leay      d,y
                    leax      AuxRoomLoadIoText,pcr
                    jsr       ,y
                    ldu       <resourcebase
                    clr       dialoginputmode,u
                    lda       parsercharacter,u
                    cmpa      #13
                    bne       AuxRoomLoadIoQuit
                    ldy       coldapi,u
                    ldd       ShowApiLoadResource,y
                    leay      d,y
                    ldu       <resourcebase
                    clra
                    ldb       vmnewroom,u
                    jsr       ,y
                    bcs       AuxRoomLoadIoRetry
                    clrb
                    puls      cc,d,x,y,u
                    andcc     #$FE
                    rts
AuxRoomLoadIoQuit   ldu       <resourcebase
                    lda       #1
                    sta       gamequit,u
                    clr       <vmroompending
                    clrb
                    puls      cc,d,x,y,u
                    andcc     #$FE
                    rts
AuxRoomLoadIoText   fcc       /Room load failed./
                    fcb       10
                    fcc       /ENTER retries; ESC quits./
                    fcb       0
AuxRoomLoadIoMissing puls      cc,d,x,y,u
                    ldb       <resourceerror
                    orcc      #1
                    rts
AuxTraceDispatch    ldd       ,y
                    leax      d,y
                    stx       coldapi,u
                    lda       <vmargindex
                    sta       <vmopcode
                    ldb       restartcall+1,u
                    pshs      b
                    lda       restartcall,u
                    lbsr      AuxTraceEvent
                    leas      1,s
                    rts
* Private VM-event sentinel. Restore the real opcode before formatting so
* headers and argument masks still use the script's actual instruction.
* X=packed table, B=index. Opcode parity selects the high or low nibble.
UiCatalogNibble     lsrb
                    ldb       b,x
                    bcs       UiCatalogLow
                    lsrb
                    lsrb
                    lsrb
                    lsrb
UiCatalogLow        andb      #15
                    rts
* Derive grouping from the common command catalog, not a second opcode list.
UiClass_GameRestartCommand equ 2
UiClass_GameStateCommand equ 3
UiClass_GameTraceOnCommand equ 4
UiClass_GameTraceInfoCommand equ 5
UiEmitTraceMasks    set 0
AGI_COMMAND         macro
                    ifne UiEmitTraceMasks
                    AGI_EMIT_NIBBLE ((\2)>>4)
                    else
                    ifdef UiClass_\3
                    AGI_EMIT_NIBBLE UiClass_\3
                    else
                    AGI_EMIT_NIBBLE 0
                    endc
                    endc
                    endm
AGI_NIBBLE_PAIR     set 0
UiCommandClasses    equ *
                    use shared/agi-command-table.asm
* Native trace configuration, event formatting and key-stepped display.
* Allocation follows the owner's terminal readiness validation.
AuxTraceInfo        ldu       <resourcebase
                    lda       #1
                    sta       traceconfigured,u
                    leay      vmarguments,u
                    AGI_TRACE_CONFIG AuxTraceInfoRows
AuxTraceOn          ldu       <resourcebase
                    AGI_TRACE_ACTIVATE AuxTraceOnReturn,AuxTraceOnCheck
                    bsr       AuxTraceInitialize
                    bcc       AuxTraceOnReturn
                    pshs      cc,b
                    lbsr      AuxTraceRelease
                    clr       <tracemode
                    puls      cc,b,pc
AuxTraceOnReturn    clrb
                    rts
AuxTraceInitialize  ldu       <resourcebase
                    tst       traceconfigured,u
                    bne       AuxTraceHaveConfig
                    clr       traceconfiglogic,u
                    lda       #1
                    sta       traceconfigline,u
                    sta       traceconfigured,u
                    lda       #15
                    sta       traceconfigrows,u
AuxTraceHaveConfig  bsr       AuxTraceAllocate
                    bcs       AuxTraceInitReturn
                    bsr       AuxTraceMap
                    bcs       AuxTraceInitReturn
                    leax      2000,x
                    ldy       #1000
                    lda       #32
AuxTraceBlankHistory sta      ,x+
                    leay      -1,y
                    bne       AuxTraceBlankHistory
* Preserve wrapped byte arithmetic, then bound the native 40x25 text plane.
                    lda       <vmpicturetop
                    inca
                    adda      traceconfigline,u
                    cmpa      #23
                    bls       AuxTraceTopReady
                    lda       #23
AuxTraceTopReady    sta       tracetop,u
                    ldb       #25
                    subb      tracetop,u
                    cmpb      traceconfigrows,u
                    bls       AuxTraceRowsReady
                    ldb       traceconfigrows,u
AuxTraceRowsReady   stb       tracelines,u
                    lda       tracecol,u
                    anda      #$80
                    ora       #2
                    sta       tracecol,u
                    bra      AuxTraceUnmap
AuxTraceInitReturn  rts

* A single owned page holds text backup, history and UI context.
* Resource/picture mappings must be gone before borrowing the map window.
AuxTraceAllocate    ldu       <resourcebase
                    tst       traceowned,u
                    bne       AuxTracePageSuccess
                    ldx       #1
                    clra
                    ldb       #$D4
                    os9       I$SetStt
                    bcs       AuxTracePageReturn
                    ldu       <resourcebase
                    stx       tracefirst,u
                    inc       traceowned,u
AuxTracePageSuccess clrb
AuxTracePageReturn  rts
AuxTraceMap         ldu       <resourcebase
                    tst       tracemapped,u
                    bne       AuxTraceMapReady
                    tst       traceowned,u
                    beq       AuxTracePageInvalid
                    UI_CALL_REGS   18
                    bcs       AuxTracePageReturn
                    UI_CALL_REGS   48
                    bcs       AuxTracePageReturn
                    ldu       <resourcebase
                    ldx       tracefirst,u
                    ldb       #1
                    os9       F$MapBlk
                    bcs       AuxTracePageReturn
                    tfr       u,x
                    ldu       <resourcebase
                    stx       tracemapbase,u
                    inc       tracemapped,u
AuxTraceMapReady    ldx       tracemapbase,u
                    clrb
                    rts
AuxTracePageInvalid ldb       #E$BMode
                    orcc      #1
                    rts
AuxTraceUnmap       ldu       <resourcebase
                    tst       tracemapped,u
                    beq       AuxTracePageSuccess
                    ldu       tracemapbase,u
                    ldb       #1
                    os9       F$ClrBlk
                    bcs       AuxTracePageReturn
                    ldu       <resourcebase
                    clr       tracemapped,u
                    clrb
                    rts
AuxTraceRelease     bsr       AuxTraceRestore
                    bcs       AuxTracePageReturn
                    ldu       <resourcebase
                    tst       traceowned,u
                    beq       AuxTraceReleased
                    ldx       tracefirst,u
                    ldu       #1
                    clra
                    ldb       #$D5
                    os9       I$SetStt
                    bcs       AuxTracePageReturn
                    ldu       <resourcebase
                    clr       traceowned,u
AuxTraceReleased    clr       <tracemode
                    clrb
                    rts

* 0..1999 text/attributes; 2000..2999 history; 3000 cold controls;
* 3100 onward contiguous cursor/inventory/parser/dialog context.
* Keep resourcecommands intact: a held dialog owns its existing backup.
AuxTraceSave        ldu       <resourcebase
                    tst       tracesaved,u
                    bne      AuxTracePageInvalid
                    lbsr      AuxTraceMap
                    bcs       AuxTraceBackupReturn
                    tfr       x,y
                    leax      textcharacters,u
                    ldd       #1000
                    jsr       [copywordentry,u]
                    ldy       tracemapbase,u
                    leay      3000,y
                    leax      textstoremodule,u
                    ldb       #statesimplename-textstoremodule
AuxTraceSaveCells   lda       ,x+
                    sta       ,y+
                    decb
                    bne       AuxTraceSaveCells
                    leax      textpointer,u
                    ldy       tracemapbase,u
                    leay      3100,y
                    ldd       #(terminalchanged-textpointer)/2
                    jsr       [copywordentry,u]
                    inc       tracesaved,u
                    clrb
AuxTraceBackupReturn rts
AuxTraceRestore     ldu       <resourcebase
                    tst       tracesaved,u
                    lbeq      AuxTraceUnmap
                    lbsr      AuxTraceMap
                    bcs       AuxTraceBackupReturn
                    leay      textcharacters,u
                    ldd       #1000
                    jsr       [copywordentry,u]
                    ldx       tracemapbase,u
                    leax      3000,x
                    leay      textstoremodule,u
                    ldb       #statesimplename-textstoremodule
AuxTraceRestoreCells lda      ,x+
                    sta       ,y+
                    decb
                    bne       AuxTraceRestoreCells
                    ldx       tracemapbase,u
                    leax      3100,x
                    leay      textpointer,u
                    ldd       #(terminalchanged-textpointer)/2
                    jsr       [copywordentry,u]
                    clr       tracesaved,u
                    lbra      AuxTraceUnmap
                    ifne (terminalchanged-textpointer)&1
                    error Trace text/parser context must be word aligned
                    endc
                    ifgt 3100+terminalchanged-textpointer-8192
                    error Trace context backup exceeds its owned page
                    endc
                    ifgt 3000+statesimplename-textstoremodule-3100
                    error Trace cold backup overlaps context backup
                    endc

* Pure history operations: no OS calls while the history page is mapped.
AuxTraceNewline     pshs      d,x,y
                    ldx       tracemapbase,u
                    leay      2000,x
                    leax      2040,x
                    ldb       tracelines,u
                    decb
                    lda       #20
                    mul
                    jsr       [copywordentry,u]
                    lda       #32
                    ldb       #40
AuxTraceBlankRow    sta       ,y+
                    decb
                    bne       AuxTraceBlankRow
                    lda       #2
                    sta       tracecol,u
                    puls      d,x,y,pc
AuxTraceChar        pshs      d,x,y
                    cmpa      #10
                    beq       AuxTraceCharNewline
                    ldb       tracecol,u
                    cmpb      #38
                    blo       AuxTraceCharPosition
                    bsr       AuxTraceNewline
AuxTraceCharPosition ldb      tracelines,u
                    decb
                    lda       #40
                    mul
                    addb      tracecol,u
                    adca      #0
                    ldx       tracemapbase,u
                    leax      2000,x
                    leax      d,x
                    lda       ,s
                    sta       ,x
                    inc       tracecol,u
                    puls      d,x,y,pc
AuxTraceCharNewline bsr       AuxTraceNewline
                    puls      d,x,y,pc
AuxTraceString      lda       ,x+
                    beq       AuxTraceStringDone
                    bsr       AuxTraceChar
                    bra       AuxTraceString
AuxTraceStringDone  clrb
                    rts
AuxTraceOverlay     ldu       <resourcebase
                    ldb       tracetop,u
                    lda       #40
                    mul
                    leay      textcharacters,u
                    leay      d,y
                    leay      2,y
                    ldx       tracemapbase,u
                    leax      2002,x
                    lda       tracelines,u
                    pshs      a
AuxTraceOverlayRow  ldb       #36
AuxTraceOverlayCell lda       ,x+
                    sta       ,y
                    lda       #$0F
                    sta       1000,y
                    leay      1,y
                    decb
                    bne       AuxTraceOverlayCell
                    leax      4,x
                    leay      4,y
                    dec       ,s
                    bne       AuxTraceOverlayRow
                    leas      1,s
                    lbra      AuxTraceUnmap

* Reuse signed common formatting, beyond the prefetched argument bytes.
AuxTraceNumber      pshs      d
                    leax      AuxTraceNumberFormat,pcr
                    pshs      x
                    leax      messagebuffer+480,u
                    pshs      x
                    lbsr      PrintFmtStr
                    leas      6,s
                    tfr       u,x
                    ldu       <resourcebase
                    bra      AuxTraceString
AuxTraceNumberFormat fcc      /%d/
                    fcb       0

* Use the catalog's variable masks; FE is encoded with the unused F nibble.
* Verification rejects every other unrepresentable mask and the F0 mask.
UiEmitTraceMasks    set 1
AGI_NIBBLE_PAIR     set 0
AuxTraceCommandMasks equ *
                    use shared/agi-command-table.asm
AGI_TEST macro
                    AGI_EMIT_NIBBLE ((\2)>>4)
                    endm
AGI_NIBBLE_PAIR     set 0
AuxTracePredicateMasks equ *
                    use shared/agi-test-table.asm
                    AGI_EMIT_NIBBLE 0
AuxTraceVariableMask lbsr     UiCatalogNibble
                    lslb
                    lslb
                    lslb
                    lslb
                    cmpb      #$F0
                    bne       AuxTraceMaskReturn
                    ldb       #$FE
AuxTraceMaskReturn  rts

* Re-read all consumed operands: vmarguments retains only the first 42 bytes.
AuxTracePrefetch    ldu       <resourcebase
                    tst       tracemapped,u
                    lbne      AuxTracePageInvalid
                    ldb       <vmargcount
                    stb       showcached,u
                    beq       AuxTracePrefetchDone
                    clra
                    std       showposition,u
                    ldd       <vmip
                    subd      showposition,u
                    std       showposition,u
                    UI_CALL_REGS   18
                    bcs       AuxTracePrefetchReturn
                    ldb       <vmcurrent
                    UI_CALL_REGS   20
                    UI_CALL_REGS   10
                    leay      messagebuffer,u
AuxTracePrefetchByte ldd      showposition,u
                    UI_CALL   14
                    bcs       AuxTracePrefetchReturn
                    stb       ,y+
                    ldd       showposition,u
                    addd      #1
                    std       showposition,u
                    dec       showcached,u
                    bne       AuxTracePrefetchByte
                    UI_CALL_REGS   18
AuxTracePrefetchReturn rts
AuxTracePrefetchDone clrb
                    rts

* A=raw/resolved selector, B=variable mask. SAID operands are signed LE words.
AuxTraceArguments   pshs      a
                    stb       showview,u
                    clr       showposition,u
                    clr       showposition+1,u
                    ldb       <vmargcount
                    stb       showcached,u
                    lda       #1
                    ldb       restartcall,u
                    cmpb      #2
                    bne       AuxTraceWidthReady
                    ldb       <vmopcode
                    cmpb      #14
                    bne       AuxTraceWidthReady
                    inca
AuxTraceWidthReady  sta       tracewidth,u
                    lda       #'(
                    lbsr      AuxTraceChar
                    tst       showcached,u
                    beq       AuxTraceArgumentsDone
AuxTraceArgument    ldx       <resourcebase
                    leax      messagebuffer,x
                    ldd       showposition,u
                    leax      d,x
                    ldb       tracewidth,u
                    cmpb      #2
                    beq       AuxTraceWordArgument
                    clra
                    ldb       ,x
                    tst       ,s
                    beq       AuxTraceArgumentReady
                    tst       showview,u
                    bpl       AuxTraceArgumentReady
                    leax      vmvariables,u
                    ldb       d,x
                    bra       AuxTraceArgumentReady
AuxTraceWordArgument ldd      ,x
                    exg       a,b
AuxTraceArgumentReady lbsr    AuxTraceNumber
                    ldd       showposition,u
                    addb      tracewidth,u
                    adca      #0
                    std       showposition,u
                    ldb       showcached,u
                    subb      tracewidth,u
                    stb       showcached,u
                    beq       AuxTraceArgumentsDone
                    lsl       showview,u
                    lda       #',
                    lbsr      AuxTraceChar
                    bra       AuxTraceArgument
AuxTraceArgumentsDone lda     #')
                    lbsr      AuxTraceChar
                    leas      1,s
                    clrb
                    rts

* Header consumes the pending logic-zero separator in the column's high bit.
* Between trace events the old column is dead; the next header starts a row.
AuxTraceHeader      tst       tracecol,u
                    bpl       AuxTraceHeaderRow
                    lbsr      AuxTraceNewline
                    ldb       #26
                    lda       #'=
AuxTraceSeparator   lbsr      AuxTraceChar
                    decb
                    bne       AuxTraceSeparator
AuxTraceHeaderRow   lbsr      AuxTraceNewline
                    ldb       <vmcurrent
                    cmpb      #32
                    lbhs      AuxTracePageInvalid
                    lda       #VM_CACHE_ENTRY_BYTES
                    mul
                    leax      vmcache,u
                    ldb       d,x
                    clra
                    lbsr      AuxTraceNumber
                    lda       #':
                    lbsr      AuxTraceChar
                    lda       #32
                    lbsr      AuxTraceChar
                    ldb       traceconfiglogic,u
                    beq       AuxTraceHeaderNumeric
                    leax      vmcache,u
                    ldy       #32
AuxTraceFindName    tst       1,x
                    beq       AuxTraceFindNext
                    tst       5,x
                    bne       AuxTraceFindNext
                    cmpb      ,x
                    beq       AuxTraceNameFound
AuxTraceFindNext    leax      VM_CACHE_ENTRY_BYTES,x
                    leay      -1,y
                    bne       AuxTraceFindName
AuxTraceHeaderNumeric clra
                    ldb       <vmopcode
                    lbra      AuxTraceNumber
AuxTraceNameFound   tst       <vmopcode
                    bne       AuxTraceReadName
                    leax      AuxTraceReturnName,pcr
                    lbra      AuxTraceString
AuxTraceReturnName  fcc       /return/
                    fcb       0
AuxTraceReadName    pshs      x
                    ldd       <vmend
                    pshs      d
                    lbsr      AuxTraceUnmap
                    bcs      AuxTraceNameUnmapFailed
                    ldx       2,s
                    UI_CALL_REGS   10
                    ldd       #0
                    UI_CALL   12
                    bcs       AuxTraceRestoreRoot
                    addd      #2
                    bcs       AuxTraceNameInvalid
                    cmpd      <resourcelength
                    bhs       AuxTraceNameInvalid
                    std       <vmend
                    ldb       <vmopcode
                    lda       restartcall,u
                    cmpa      #2
                    bne       AuxTraceReadMessage
                    addb      #220
AuxTraceReadMessage UI_CALL   50
                    bra       AuxTraceRestoreRoot
AuxTraceNameInvalid ldb       #E$BMode
                    orcc      #1
AuxTraceRestoreRoot pshs      cc,b
                    UI_CALL_REGS   18
                    bcc       AuxTraceRootUnmapped
* Preserve the first failure; use the unmap failure if decoding succeeded.
                    lda       ,s
                    bita      #1
                    bne       AuxTraceRootUnmapped
                    stb       1,s
                    ora       #1
                    sta       ,s
AuxTraceRootUnmapped ldd      2,s
                    std       <vmend
                    ldb       <vmcurrent
                    UI_CALL_REGS   20
                    UI_CALL_REGS   10
                    puls      cc,b
                    leas      4,s
                    bcs       AuxTraceHeaderReturn
                    lbsr      AuxTraceMap
                    bcs       AuxTraceHeaderReturn
                    leax      messagebuffer,u
                    lbra      AuxTraceString
AuxTraceNameUnmapFailed leas  4,s
AuxTraceHeaderReturn rts

* Kind 1=command, 2=predicate; predicate's saved truth byte is at 2,S.
* Kind 3 is teardown and retries one transient release failure.
AuxTraceEvent       cmpa      #3
                    bne       AuxTraceStep
                    lbsr      AuxTraceRelease
                    bcs       AuxTraceReleaseRetry
                    rts
AuxTraceReleaseRetry lbra     AuxTraceRelease
AuxTraceStep        ldb       2,s
                    pshs      d
                    lbsr      AuxTraceSave
                    lbcs      AuxTraceSaveFailed
                    puls      d
                    std       restartcall,u
                    lbsr      AuxTraceHeader
                    lbcs      AuxTraceFinish
                    lbsr      AuxTraceUnmap
                    lbcs      AuxTraceFinish
                    lbsr      AuxTracePrefetch
                    lbcs      AuxTraceFinish
                    lbsr      AuxTraceMap
                    bcs      AuxTraceFinish
                    ldb       <vmopcode
                    leax      AuxTraceCommandMasks,pcr
                    lda       restartcall,u
                    deca
                    beq       AuxTraceSelectMask
                    leax      AuxTracePredicateMasks,pcr
AuxTraceSelectMask  lbsr      AuxTraceVariableMask
                    lda       tracecol,u
                    pshs      d          original column and variable mask
                    clra
                    lbsr      AuxTraceArguments
                    ldb       1,s
                    beq       AuxTraceArgumentsReady
                    lbsr      AuxTraceNewline
* CoCo PopRowCol aligns the resolved list under the raw argument list.
                    lda       ,s
                    sta       tracecol,u
                    ldb       1,s
                    lda       #1
                    lbsr      AuxTraceArguments
AuxTraceArgumentsReady leas   2,s
                    lda       restartcall,u
                    deca
                    beq       AuxTracePresent
                    lda       #35
                    sta       tracecol,u
                    lda       #32
                    lbsr      AuxTraceChar
                    lda       #':
                    lbsr      AuxTraceChar
                    lda       #'T
                    ldb       restartcall+1,u
                    bne       AuxTraceTruthReady
                    lda       #'F
AuxTraceTruthReady  lbsr      AuxTraceChar
AuxTracePresent     bsr       AuxTraceShow
                    bcs       AuxTraceFinish
                    lda       #DIALOG_TRACE_MODE
                    sta       dialoginputmode,u
                    ldy       coldapi,u
                    leay      ShowApiPriorityWait,y
                    lbsr      AuxPrintWait
                    bcs       AuxTraceFinish
                    AGI_TRACE_KEY_ADVANCE AuxTraceKeyAdvanced
AuxTraceKeyAdvanced clrb
AuxTraceFinish      pshs      cc,b
                    lbsr      AuxTraceRestore
                    bcs       AuxTraceCleanupFailed
                    UI_CALL_REGS 30
                    bcs       AuxTraceCleanupFailed
                    UI_CALL_REGS 32
                    bcs       AuxTraceCleanupFailed
AuxTraceFinishStatus puls     cc,b,pc
AuxTraceCleanupFailed lda     ,s
                    bita      #1
                    bne       AuxTraceFinishStatus
                    stb       1,s
                    ora       #1
                    sta       ,s
                    bra       AuxTraceFinishStatus
AuxTraceSaveFailed  leas      2,s
AuxTraceEventReturn rts
AuxTraceShow        lbsr      AuxTraceOverlay
                    bcs       AuxTraceEventReturn
                    UI_CALL_REGS 46
                    rts

* File-name staging is cold; persistent name configuration is caller-private.
AuxStateName        ldu       <resourcebase
                    sty       coldapi,u
                    tst       statesimplename,u
                    bne       AuxStateAutoName
                    lda       #1
                    sta       dialoginputmode,u
                    ldd       #$0A02
                    std       inventoryrow,u
                    lda       #39
                    sta       inventorypaint,u
                    UI_CALL   2
                    leax      StatePrompt,pcr
                    UI_CALL   0
                    bcs       AuxStateNameReturn
                    ldu       <resourcebase
                    clr       dialoginputmode,u
                    clrb
AuxStateNameReturn  rts
AuxStateAutoName    leax      statesimplename,u
                    leay      parserline,u
                    clrb
AuxStateNameCopy    lda       b,x
                    sta       b,y
                    beq       AuxStateNameDone
                    incb
                    cmpb      #31
                    blo       AuxStateNameCopy
                    clr       b,y
AuxStateNameDone    stb       parserlength,u
                    clrb
                    rts
StatePrompt         fcc       /File:/
                    fcb       0
SIMPLE_SAVE_FETCH macro
                    ldu       <resourcebase
                    lda       vmarguments,u
                    cmpa      #12
                    lbhs      AuxSimpleSaveInvalid
                    endm
SIMPLE_SAVE_STRING_TABLE macro
                    leax      vmstrings,u
                    endm
SIMPLE_SAVE_NAME_ADDRESS macro
                    leau      statesimplename,u
                    endm
SIMPLE_SAVE_COPY macro
                    BOUNDED_STRING_COPY u,AuxSimpleCopy,AuxSimpleDone,BOUNDED_BYTE_COUNT
                    ldu       <resourcebase
                    clrb
                    endm
AuxSimpleSaveName   AGI_SIMPLE_SAVE_NAME
AuxSimpleSaveInvalid ldb      #E$BMode
                    orcc      #1
                    rts
* Diagnostics use private text storage, not CoCo's 404-byte stack frame.
OBJECT_STATUS_FRAME equ 4
OBJECT_STATUS_OBJECT equ 2
OBJECT_STATUS_CYCLE equ 0
OBJECT_STATUS_SELECT macro
                    ldu       <resourcebase
                    clra
                    ldb       vmarguments,u
                    leax      vmvariables,u
                    ldb       d,x
                    cmpb      #64
                    lbhs      AuxStatusBadObject
                    lda       #43
                    mul
                    leau      vmobjects,u
                    leau      d,u
                    tfr       u,d
                    pshs      d
                    lbsr      AuxDiagnosticPrepare
                    lbcs      AuxStatusSetupError
                    puls      d
                    tfr       d,u
                    endm
OBJECT_STATUS_MOTION_BUFFER macro
                    ldx       <resourcebase
                    leax      messagebuffer+320,x
                    endm
OBJECT_STATUS_MOTION_FORMAT macro
                    lbsr      PrintFmtStr
                    tfr       u,x
                    endm
OBJECT_STATUS_OUTPUT_BUFFER macro
                    ldx       <resourcebase
                    leax      messagebuffer,x
                    endm
OBJECT_STATUS_DISPLAY macro
                    tfr       u,x
                    ldu       <resourcebase
                    UI_CALL 16
                    endm
                    OBJECT_EMIT_STATUS_STRINGS
                    OBJECT_EMIT_STATUS
* Release cached root mapping before allocating/drawing through another window.
AuxDiagnosticPrepare UI_CALL_REGS 18
                    bcs       AuxDiagnosticPrepareReturn
                    tst       <pictureowned
                    bne       AuxDiagnosticPrepareReturn
                    UI_CALL_REGS 26
AuxDiagnosticPrepareReturn rts
AuxStatusSetupError leas      2+OBJECT_STATUS_FRAME,s
                    ldu       <resourcebase
                    orcc      #1
                    rts
AuxStatusBadObject  leas      OBJECT_STATUS_FRAME,s
                    ldu       <resourcebase
                    ldb       #E$IllArg
                    orcc      #1
                    rts
* Segmented native memory has no CoCo flat-heap "free" byte category.
* Report actual owned pages and module/private extents without double counting.
AuxMemoryInfo       ldu       <resourcebase
                    bsr       AuxDiagnosticPrepare
                    lbcs      AuxMemoryReturn
                    leas      -4,s
                    ldd       #0
                    std       ,s          total owned cache pages
                    std       2,s         largest loaded logic resource
                    leax      vmcache,u
                    ldy       #32
AuxMemoryCache      tst       1,x
                    beq       AuxMemoryNext
                    clra
                    ldb       4,x
                    addd      ,s
                    std       ,s
                    tst       5,x
                    bne       AuxMemoryNext
                    ldd       6,x
                    cmpd      2,s
                    bls       AuxMemoryNext
                    std       2,s
AuxMemoryNext       leax      VM_CACHE_ENTRY_BYTES,x
                    leay      -1,y
                    bne       AuxMemoryCache
                    ldd       2,s
                    pshs      d           maximum logic resource bytes
                    clra
                    clrb
                    tst       <bitmapowned
                    beq       AuxMemoryBitmap
                    ldb       #10
AuxMemoryBitmap     pshs      d
                    clrb
                    tst       gamebackgroundowned,u
                    beq       AuxMemoryBackground
                    ldb       #4
AuxMemoryBackground pshs      d
                    clrb
                    tst       <pictureowned
                    beq       AuxMemoryPicture
                    ldb       #4
AuxMemoryPicture    pshs      d
                    ldd       8,s         cache pages (four pushed words)
                    pshs      d
                    ldd       >UiName-13+M$Size,pcr
                    pshs      d           immutable UI module bytes
                    ldd       #size
                    pshs      d           declared process-private bytes
                    ldy       coldapi,u
                    ldd       ShowApiModuleHeader,y * relative resident module header
                    leax      d,y
                    ldd       M$Size,x
                    pshs      d
                    clra
                    ldb       vmvariables,u
                    pshs      d           current room
                    leax      AuxMemoryFormat,pcr
                    pshs      x
                    leax      messagebuffer,u
                    pshs      x
                    lbsr      PrintFmtStr
                    leas      22,s        output, format and nine word args
                    tfr       u,x
                    ldu       <resourcebase
                    UI_CALL 16
                    leas      4,s
AuxMemoryReturn     rts
AuxMemoryFormat     fcc       /room: %u/
                    fcb       10
                    fcc       /code bytes: %u/
                    fcb       10
                    fcc       /private bytes: %u/
                    fcb       10
                    fcc       /UI bytes: %u/
                    fcb       10
                    fcc       /owned 8K pages:/
                    fcb       10
                    fcc       /cache: %u  picture: %u/
                    fcb       10
                    fcc       /background: %u  bitmap: %u/
                    fcb       10
                    fcc       /max logic bytes: %u/
                    fcb       0
PrintFmtStr         ldu       <resourcebase
                    ldd       2,s
                    std       textpointer,u
                    ldx       4,s
                    leau      6,s
                    bsr       PrintFmtLoop
                    ldu       2,s
                    rts
                    FORMAT_EMIT_WORD_ARGUMENTS
PrintFmtOutputChar  pshs      u,x
                    ldu       <resourcebase
                    ldx       textpointer,u
                    sta       ,x+
                    stx       textpointer,u
                    puls      u,x,pc
WORD_HEX_OUTPUT_END macro
                    ldx       <resourcebase
                    leax      messagebuffer+511,x
                    endm
WORD_DECIMAL_OUTPUT_END macro
                    WORD_HEX_OUTPUT_END
                    endm
WORD_DECIMAL_OUTPUT_DIVIDE macro
                    lbsr      UIntDivide
                    endm
WORD_CONVERSION_DEFINITIONS_ONLY equ 1
                    use shared/unsigned-decimal.asm
                    UNSIGNED_DECIMAL_EMIT WordUIntToDecStr,WordUIntToDecLoop,WORD_DECIMAL_OUTPUT_END,WORD_DECIMAL_OUTPUT_DIVIDE
                    WORD_EMIT_HEX_DIVIDE
                    else
* Immutable text/UI backend executes while sierraui remains linked.
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_TEXT_STORE_CODE
AuxTextStore        tst       dialogactive,u
                    bne       GameTextStoreActive
* text.screen displays use the same bounded white panel and word wrapping as
* modal print text. Initialize once; later display calls share this panel.
AuxTextScreenStart  tst       <vmgraphics
                    lbne      GameTextRead
                    lbsr      AuxTextModePanel
GameTextStoreActive tst       dialogactive,u
                    lbeq      GameTextRead
                    tst       <vmgraphics
                    bne       GameTextPanelBoundsReady
                    lda       #2
                    sta       dialogleft,u
                    lda       #36
                    sta       dialogright,u
                    lda       textrow,u
                    cmpa      #2
                    bhs       GameTextPanelRowLimit
                    lda       #2
                    sta       textrow,u
                    bra       GameTextPanelColumn
GameTextPanelRowLimit cmpa #23
                    blo       GameTextPanelColumn
                    lda       #22
                    sta       textrow,u
GameTextPanelRowReady
GameTextPanelColumn
                    lda       textcolumn,u
                    cmpa      #2
                    bhs       GameTextPanelColumnLimit
                    lda       #2
                    sta       textcolumn,u
                    bra       GameTextPanelBoundsReady
GameTextPanelColumnLimit cmpa #38
                    blo       GameTextPanelBoundsReady
                    lda       #2
                    sta       textcolumn,u
                    inc       textrow,u
GameTextPanelBoundsReady
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
                    lda       textcolumn,u
                    tst       dialogactive,u
                    beq       AuxTextColumnReady
                    pshs      a
                    lda       <vmstatusenabled
                    lsra
                    lsra
                    lsra
                    adda      ,s+
AuxTextColumnReady cmpa      #40
                    blo       AuxTextColumnClip
                    lda       #39
AuxTextColumnClip   pshs      a
                    lda       textrow,u
                    ldb       #40
                    mul
                    addb      ,s
                    leas      1,s
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
AuxTextPresent      tst       dialogactive,u
                    beq       AuxTextPresentCall
                    tst       <vmgraphics
                    bne       AuxTextPresentCall
                    lbsr      AuxTextPanelFrame
AuxTextPresentCall  jmp       ,y

* Build a 38-column white panel with a solid black one-cell frame in the
* private text plane. Preserve the two status-offset columns and input row.
AuxTextModePanel    pshs      d,x,y,u
                    ldu       <resourcebase
                    clr       <vmtextforeground
                    lda       #15
                    sta       <vmtextbackground
                    lda       #1
                    sta       dialogactive,u
                    sta       dialogwordstart,u
                    lda       #2
                    sta       dialogleft,u
                    lda       #36
                    sta       dialogright,u
                    lda       #2
                    sta       textrow,u
                    sta       textcolumn,u
                    leax      textcharacters+41,u ; row 1, column 1
                    leay      textcolors+41,u
                    bsr       AuxTextPanelBlackRow
                    leax      2,x                 ; row 2, column 1
                    leay      2,y
                    lda       #21                 ; text rows 2 through 22
                    pshs      a
AuxTextPanelRow     lda       #32
                    sta       ,x+
                    clr       ,y+
                    ldb       #36
AuxTextPanelWhite   lda       #32
                    sta       ,x+
                    lda       #15
                    sta       ,y
                    leay      1,y
                    decb
                    bne       AuxTextPanelWhite
                    lda       #32
                    sta       ,x+
                    clr       ,y+
                    leay      1,y
                    leax      2,x                ; skip col 39 and next row col 0
                    leay      2,y
                    dec       ,s
                    bne       AuxTextPanelRow
                    leas      1,s
                    bsr       AuxTextPanelBlackRow ; row 23, column 1
                    puls      d,x,y,u,pc
AuxTextPanelBlackRow lda #32
                    ldb       #38
AuxTextPanelBlackCell
                    sta       ,x+
                    clr       ,y+
                    decb
                    bne       AuxTextPanelBlackCell
                    rts
AuxTextPanelFrame   pshs      d,x,y,u
                    ldu       <resourcebase
                    leax      textcharacters+41,u ; top edge, row 1
                    leay      textcolors+41,u
                    bsr       AuxTextPanelBlackRow
                    leax      textcharacters+921,u ; bottom edge, row 23
                    leay      textcolors+921,u
                    bsr       AuxTextPanelBlackRow
                    leax      textcharacters+81,u ; side edges, row 2
                    leay      textcolors+81,u
                    lda       #21
                    pshs      a
AuxTextPanelSide     lda       #32
                    sta       ,x
                    clr       ,y
                    leax      37,x
                    leay      37,y
                    sta       ,x
                    clr       ,y
                    leax      3,x
                    leay      3,y
                    dec       ,s
                    bne       AuxTextPanelSide
                    leas      1,s
                    puls      d,x,y,u,pc
                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_DIALOG_WAIT_CODE
* Read-only modal loop. Timer and callback state belong to this process.
AuxPrintWait        pshs      y
                    lda       gameclockreset,u
                    sta       dialogepoch,u
                    tst       dialoginputmode,u
                    bne       AuxWaitUntimed
                    lda       <vmopcode
                    cmpa      #135
                    beq       AuxWaitTimer
                    cmpa      #133
                    beq       AuxWaitTimer
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
                    lbcs      AuxWaitRestore
                    sta       dialogseen,u
                    lda       #2
                    sta       dialogtimed,u
                    bra       AuxWaitLoop
AuxWaitUntimed      clr       dialogtimed,u
* Trace mode accepts the queued key, including during diagnostic commands.
                    lda       dialoginputmode,u
                    cmpa      #DIALOG_TRACE_MODE
                    beq       AuxWaitLoop
                    lda       <vmopcode
                    cmpa      #133
                    beq       AuxDiagnosticFresh
                    cmpa      #135
                    bne       AuxWaitLoop
AuxDiagnosticFresh  lbsr      AuxDiagnosticDrain
                    lbcs      AuxWaitRestore
AuxWaitLoop         ldy       ,s
                    ldd       ,y
                    leax      d,y
                    jsr       ,x
                    lbcs      AuxWaitRestore
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
                    lbcs      AuxWaitRestore
                    ldb       gameclockreset,u
                    cmpb      dialogepoch,u
                    beq       AuxWaitDelta
                    stb       dialogepoch,u
                    sta       dialogseen,u
                    bra      AuxWaitLoop
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
                    lbcs      AuxWaitRestore
                    ldu       <resourcebase
                    lda       dialoginputmode,u
                    cmpa      #3         have.key: key variable only, no parser
                    bne       AuxWaitInputMode
                    lda       parsercharacter,u
                    lbeq      AuxWaitLoop ; no real key, like CoCo TestHaveKey
                    sta       vmvariables+19,u
                    bra       AuxWaitKeyDone
AuxWaitInputMode
                    cmpa      #DIALOG_RESTART_MODE
                    beq       AuxRestartKey
                    cmpa      #DIALOG_TRACE_MODE * trace: any key advances, no editor
                    beq       AuxWaitKeyDone
                    tst       dialoginputmode,u
                    bne       AuxWaitEditor
                    lda       <vmopcode
                    cmpa      #133
                    beq       AuxDiagnosticKey
                    cmpa      #135
                    bne       AuxWaitKeyDone
AuxDiagnosticKey    lda       parsercharacter,u
                    cmpa      #13
                    beq       AuxWaitKeyDone
                    cmpa      #5
                    beq       AuxWaitKeyDone
                    cmpa      #27
                    beq       AuxWaitKeyDone
                    lbra      AuxWaitLoop
AuxRestartKey       lda       parsercharacter,u
                    cmpa      #13
                    beq       AuxWaitKeyDone
                    cmpa      #5
                    beq       AuxWaitKeyDone
                    cmpa      #27
                    beq       AuxWaitKeyDone
                    lbra      AuxWaitLoop
AuxWaitEditor       tst       dialoginputmode,u
                    beq       AuxWaitKeyDone
                    ldy       ,s
                    ldd       2,y
                    leax      d,y
                    jsr       ,x
                    lbcs      AuxWaitRestore
                    tsta
                    lbeq      AuxWaitLoop
AuxWaitKeyDone      clrb
                    lbra     AuxWaitRestore
* CoCo BooleanPoll clears queued events after an untimed box is visible.
AuxDiagnosticDrain  clra
                    ldb       #SS.Ready
                    os9       I$GetStt
                    bcc       AuxDiagnosticRead
                    cmpb      #E$NotRdy
                    bne       AuxDiagnosticError
                    clrb
                    rts
AuxDiagnosticRead   ldu       <resourcebase
                    leax      parsercharacter,u
                    ldy       #1
                    clra
                    os9       I$Read
                    bcs       AuxDiagnosticReturn
                    ldu       <resourcebase
                    bra       AuxDiagnosticDrain
AuxDiagnosticError  orcc      #1
AuxDiagnosticReturn rts
AuxWaitSample       ldy       2,s
                    ldd       6,y
                    leax      d,y
                    jmp       ,x
                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_TEXT_RECT_CODE
AuxClearTextRect    pshs      y
                    ldu       <resourcebase
                    leax      vmarguments,u
                    lda       <vmopcode
                    cmpa      #106      text.screen owns the full 40x25 plane
                    bne       AuxRectArguments
                    clr       ,x
AuxRectArguments    lda       4,x
                    cmpa      #$82      private print-panel request
                    bne       AuxRectPanelReady
                    lda       #2
                    sta       dialogwordstart,u
                    clr       4,x       first pass paints the black frame
AuxRectPanelReady  lda       ,x
                    tst       dialogactive,u
                    beq       AuxRectRowsReady
                    lda       <vmstatusenabled
                    lsra
                    lsra
                    lsra
                    adda      1,x
                    sta       1,x
                    lda       <vmstatusenabled
                    lsra
                    lsra
                    lsra
                    adda      3,x
                    cmpa      #40
                    bls       AuxRectRightReady
                    lda       #40
AuxRectRightReady  sta       3,x
AuxRectRowsReady   lda       ,x
                    cmpa      #24
                    lbhs      AuxRectNoOp
                    ldb       2,x
                    cmpa      2,x
                    lbhi      AuxRectInvalid
                    cmpb      #24
                    blo       AuxRectRowClipped
                    lda       #23      CoCo text rectangle clips at row 23
                    sta       2,x
AuxRectRowClipped  lda       1,x
                    ldb       3,x
                    cmpb      #41      column 40 spills into next text row
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
* CoCo's text_color writes white foreground and the requested background
* nibble (FF00, FF11, ... FFFF); retain that color in the cell overlay.
* clear.lines passes a tagged boolean because its CoCo helper uses only
* foreground white (FF) or black (00), not the rectangle color convention.
                    lda       4,x
                    bita      #$80
                    beq       GameRectColorNibble
                    bita      #1
                    bne       GameRectBooleanWhite
                    clra
                    bra       GameRectRow
GameRectBooleanWhite lda #$FF
                    bra       GameRectRow
GameRectColorNibble lda      #$F0
                    ora       4,x
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
                    ldu       <resourcebase
                    lda       dialogwordstart,u
                    cmpa      #2
                    beq       AuxRectPanelInterior
                    cmpa      #3
                    bne       AuxRectDone
                    lda       #1       restore initial print word-wrap state
                    sta       dialogwordstart,u
                    bra       AuxRectDone
AuxRectPanelInterior lda #3
                    sta       dialogwordstart,u
                    leax      vmarguments,u
                    inc       ,x
                    inc       1,x
                    dec       2,x
                    dec       3,x
                    lda       #15      white interior, black outer cell remains
                    sta       4,x
                    lbra      AuxRectRowsReady
AuxRectDone        equ       *
                    puls      y
                    jmp       ,y

AuxRectNoOp        puls      y
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
* B/X/Y/U-only callbacks do not need an original A argument.
UI_CALL_REGS       macro
                    lda       #\1
                    lbsr      AuxUIRegsCall
                    endm
AuxShowObject       ldu       <resourcebase
                    sty       coldapi,u
                    lda       <vmopcode
                    cmpa      #170
                    lbeq      AuxSimpleSaveName
                    cmpa      #161
                    lbeq      AuxMenuRequest
                    cmpa      #177
                    lbeq      AuxMenuVisibility
                    cmpa      #135
                    lbeq      AuxMemoryInfo
                    cmpa      #133
                    lbeq      CmdObjStatusV
                    cmpa      #29
                    lbeq      AuxPriorityView
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
AuxShowPrepare      UI_CALL_REGS 24
                    lbcs      AuxShowReturn
                    tst       <pictureowned
                    bne       AuxShowHavePicture
                    UI_CALL_REGS 26
                    lbcs      AuxShowReturn
AuxShowHavePicture  tst       gamebackgroundowned,u
                    bne       AuxShowHaveBackground
                    UI_CALL_REGS 2
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
                    UI_CALL_REGS 10
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
                    bcs      AuxShowReturn
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
                    bra      AuxShowInvalid
AuxShowEmpty        clr       ,x
AuxShowCopied       UI_CALL_REGS 18
                    bcs      AuxShowReturn
                    ldb       <vmcurrent
                    UI_CALL_REGS 20
                    UI_CALL_REGS 10
* Inventory previews require dismissal, independent of print flags/timers.
                    leax      messagebuffer,u
                    inc       showactive,u
                    lbsr      AuxBlockingPrint
                    pshs      cc,b
                    clr       showactive,u
                    puls      cc,b
                    bcs      AuxShowReturn
* The fast sprite eraser scans game records, not this temporary preview.
* Restore the pristine background fully, then recompose ordinary objects.
                    lda       #1
                    sta       gamecopydirection,u
                    UI_CALL 28
                    bcs      AuxShowReturn
                    UI_CALL_REGS 30
                    bcs      AuxShowReturn
                    UI_CALL_REGS 32
                    bcs      AuxShowReturn
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
* Priority diagnostic uses its own modal callbacks and never enters save UI.
AuxPriorityView     UI_CALL_REGS   34
                    bcs       AuxShowReturn
                    tst       <pictureowned
                    bne       AuxPriorityHavePicture
                    UI_CALL_REGS   26
                    bcs       AuxShowReturn
AuxPriorityHavePicture inc    <gamepriorityview
                    lda       #4
                    sta       dialoginputmode,u
                    UI_CALL_REGS   32
                    bcs       AuxPriorityRestore
                    ldy       coldapi,u
                    leay      ShowApiPriorityWait,y
                    lbsr      AuxPrintWait
AuxPriorityRestore  pshs      cc,b
                    ldu       <resourcebase
                    clr       <gamepriorityview
                    clr       dialoginputmode,u
                    UI_CALL_REGS   32
                    bcs       AuxPriorityRestoreError
                    puls      cc,b,pc
AuxPriorityRestoreError leas   2,s
                    rts
* Interpreter information shares the existing text callback and cold entry.
AuxJoystickInfo     leax      JoystickInfo,pcr
                    bra      AuxBlockingPrint
JoystickInfo        fcc       /Joystick service unavailable./
                    fcb       13
                    fcc       /Use the keyboard to play./
                    fcb       0
AuxInterpreterInfo  leax      InterpreterInfo,pcr
                    bra      AuxBlockingPrint
InterpreterInfo     fcc       /Adventure Game Interpreter/
                    fcb       13
                    fcc       /      Version 2.072/
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
AuxUIRegsCall      pshs      d
                    bsr       AuxUICall
                    leas      2,s
                    rts
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
                    beq      AuxRestartApply
                    sty       restartapi,u
                    tst       vmflags+16,u
                    bne       AuxRestartAccepted
                    lda       vmflags+15,u
                    pshs      a
                    lda       dialoginputmode,u
                    pshs      a
                    lda       #DIALOG_RESTART_MODE
                    sta       dialoginputmode,u
                    clr       vmflags+15,u
                    leax      AuxRestartPrompt,pcr
                    clra
                    lbsr      AuxRestartCall
                    puls      a
                    sta       dialoginputmode,u
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
AuxRestartPrompt    fcc       /ENTER restarts; ESC cancels./
                    fcb       0
AuxRestartApply     lda       #2       stop owned sound
                    bsr      AuxRestartCall
                    bcs       AuxRestartReturn
                    lda       #4       unregister/close this raster subscription
                    bsr      AuxRestartCall
                    bcs       AuxRestartReturn
                    lda       #6       release temporary and all cached resources
                    bsr      AuxRestartCall
                    bcs       AuxRestartReturn
                    lda       #8       release the saved background
                    bsr      AuxRestartCall
                    bcs       AuxRestartReturn
                    lda       #10      release the combined picture slab
                    bsr      AuxRestartCall
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
                    bsr      AuxRestartCall
                    lda       #16
                    bsr      AuxRestartCall
                    lda       #18
                    bsr      AuxRestartCall
* The original CLI root number/directory never change during resource loads.
                    clr       <resourcekind
                    ldx       <argdirectory
                    ldy       <argnumber
                    lda       #12
                    bra      AuxRestartCall
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
GamePrintSave equ *
                    lbsr      GameCopyWords
                    lda       <vmtextforeground
                    ldb       <vmtextbackground
                    pshs      d
                    clr       <vmtextforeground ; black ink on a white panel
                    lda       #15
                    sta       <vmtextbackground
                    lbsr      GameTextInitialize ; leave cells outside popup transparent
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
                    lbhs      GamePrintAtBad
                    cmpb      #40
                    lbhs      GamePrintAtBad
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
                    lda       #4       print.at keeps its requested position
                    sta       dialogactive,u
                    bra       GamePrintPositionReady
GamePrintDefaultPosition
                    ldd       #$0500    centered full-width, 15-row panel
                    std       vmarguments,u
                    ldd       #$1325    bottom/right: rows 5..19, columns 0..37
                    std       vmarguments+2,u
                    lda       #$82      black frame with white interior
                    sta       vmarguments+4,u
                    lbsr      GameClearTextRect
                    lbcs      GamePrintRestore
                    ldu       <resourcebase
                    lda       #7
                    sta       textrow,u
                    lda       #2
                    sta       textcolumn,u
                    sta       dialogleft,u
                    lda       #36
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
GamePrintCopyBack equ *
                    lbsr      GameCopyWords
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
ShakeCallbacks      fdb       GameFramePointer-ShakeCallbacks,unmap-ShakeCallbacks
                    fdb       GameModalForeground-ShakeCallbacks,GameClockSample-ShakeCallbacks
                    fdb       AssetUnmap-ShakeCallbacks,PictureUnmap-ShakeCallbacks
* Rare UI commands share a cache/loader; priority screen calls retain their
* distinct Y=0..3 entry contract and are deliberately not part of this bridge.
GameRestartCommand  equ       *
GameShowPriorityCommand equ   *
GameVersionCommand  equ       *
GameShowObjectCommand equ     *
GameTraceOnCommand  equ       *
GameTraceInfoCommand equ      *
GameUiCommand       ldu       <resourcebase
                    leax      uicommandentry,u
                    ldb       #24
                    leay      UiCommandCallbacks,pcr
                    lbra      GameColdInvoke
UiCommandCallbacks  fdb       ShowCallbacks-UiCommandCallbacks
                    fdb       ShakeCallbacks-UiCommandCallbacks
                    fdb       RestartCallbacks-UiCommandCallbacks
                    fdb       StateNameCallbacks-UiCommandCallbacks
StateNameCallbacks  fdb       GamePrintText-StateNameCallbacks,ParserClearLine-StateNameCallbacks
ShowCallbacks       fdb       ViewSelect-ShowCallbacks,GameSaveBackground-ShowCallbacks
                    fdb       SpriteRenderObject-ShowCallbacks,PresentPicture-ShowCallbacks
                    fdb       VmLoadResource-ShowCallbacks,VmRestoreAsset-ShowCallbacks
                    fdb       AssetReadWord-ShowCallbacks,AssetReadByte-ShowCallbacks
                    fdb       GamePrintText-ShowCallbacks,AssetUnmap-ShowCallbacks
                    fdb       VmSlotAddress-ShowCallbacks,VmDiscardResource-ShowCallbacks
                    fdb       GameCloseWindow-ShowCallbacks,GameCreateScreen-ShowCallbacks
                    fdb       GameCopyBackground-ShowCallbacks,GameComposeScene-ShowCallbacks
                    fdb       RefreshPicture-ShowCallbacks
                    fdb       GamePriorityPrepare-ShowCallbacks
PriorityWaitCallbacks fdb     GameModalForeground-PriorityWaitCallbacks
                    fdb       GamePriorityKey-PriorityWaitCallbacks
                    fdb       GameStateReturn-PriorityWaitCallbacks
                    fdb       GameClockSample-PriorityWaitCallbacks
ShowModuleHeader    fdb       name-13-ShowCallbacks * ABI-10: read-only header metadata
                    fdb       GameTextPresent-ShowCallbacks,PictureUnmap-ShowCallbacks
                    fdb       ReadLogicMessage-ShowCallbacks
                    ifne PriorityWaitCallbacks-ShowCallbacks-ShowApiPriorityWait
                    error Show API priority-wait directory moved
                    endc
                    ifne ShowModuleHeader-ShowCallbacks-ShowApiModuleHeader
                    error Show API resident-header metadata moved
                    endc
* Discard queued input before displaying the diagnostic, like events_clear.
* Private VT input queues are small; stop after 256 reads rather than spinning
* indefinitely if an input source continuously replenishes the queue.
GamePriorityPrepare lbsr      AssetUnmap
                    bcs       GamePriorityDrainError
                    lbsr      PictureUnmap
                    bcs       GamePriorityDrainError
                    clra
                    pshs      d
GamePriorityDrain   clra
                    ldb       #SS.Ready
                    os9       I$GetStt
                    bcs       GamePriorityDrainDone
                    leax      1,s
                    ldy       #1
                    clra
                    os9       I$Read
                    bcs       GamePriorityDrainDone
                    dec       ,s
                    bne       GamePriorityDrain
                    ldb       #E$BMode
                    orcc      #1
GamePriorityDrainDone leas    2,s
                    cmpb      #E$NotRdy
                    bne       GamePriorityDrainError
                    clrb
                    rts
GamePriorityDrainError orcc   #1
                    rts
GamePriorityKey     lda       parsercharacter,u
                    cmpa      #13
                    beq       GamePriorityAccepted
                    cmpa      #5         Wild Bits physical Escape
                    beq       GamePriorityAccepted
                    cmpa      #27
                    beq       GamePriorityAccepted
                    clra
                    rts
GamePriorityAccepted lda      #1
                    clrb
                    rts
RestartCallbacks          fdb       GamePrintText-RestartCallbacks,GameSoundStop-RestartCallbacks
                    fdb       GameClockClose-RestartCallbacks,VmReleaseResources-RestartCallbacks
                    fdb       GameReleaseBackground-RestartCallbacks,PictureRelease-RestartCallbacks
                    fdb       LoadAsset-RestartCallbacks,GameTextInitialize-RestartCallbacks
                    fdb       MenuInitialize-RestartCallbacks,ScreenInitialize-RestartCallbacks
GameStateCommand    lbsr      GameSoundStop
                    bcs      GameStateReturn
                    lbsr      GameUiCommand
                    bcs      GameStateReturn
                    ldu       <resourcebase
                    tst       parserlength,u
                    beq      GameStateSuccess
                    lbsr      PictureUnmap
                    bcs      GameStateReturn
                    ldu       <resourcebase
                    pshs      u
                    bsr       StateLoadModule
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
StateFailure        fcc       /Error/
                    fcb       0
* Shared, bounded cold-image loader. Success leaves U=module, X=metadata
* after the eight-byte private ABI. Y is the checked copy length for state;
* UI metadata reserves that word as zero and never uses a copied prefix.
* No image is copied here.
StateLoadModule     clra
                    leax      StateModule,pcr
                    bra       ColdLoadModule
UiLoadModule        lda       #1
                    leax      UiModule,pcr
ColdLoadModule      pshs      a,x,u
                    lbsr      AssetUnmap
                    bcs       StateModuleFailure
                    ldx       1,s
                    lda       #Sbrtn+Objct
                    os9       F$Load
                    bcs       StateModuleFailure
                    ldd       M$Size,u
                    cmpd      #8192
                    bhi       StateLoadBad
                    ldd       M$Exec,u
                    cmpd      #13
                    blo       StateLoadBad
                    addd      #39       branch, private ABI, thirteen metadata words and CRC must fit
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
* Only the state role copies code. Its prefix must cover the whole image,
* excluding CRC, and fit the existing private workspace. UI never copies code.
                    tst       ,s
                    bne       ColdDirectoryReady
                    ldd       M$Size,u
                    subd      #3
                    cmpd      8,x
                    bne       StateLoadBad
                    cmpd      #4096
                    bhi       StateLoadBad
ColdDirectoryReady  ldy       8,x
                    leas      5,s
                    clrb
                    rts
StateLoadBad        os9       F$UnLink
                    ldb       #E$BMode
                    orcc      #1
StateModuleFailure  puls      a,x,u,pc
UiModule            fcc       /sierraui/
                    fcb       C$CR
StateModule         fcc       /sierrastate/
                    fcb       C$CR
StateSignature      STATE_ABI
* Position-independent callbacks: offsets are relative to this table's base.
StateAPI            fdb       AssetUnmap-StateAPI,PictureUnmap-StateAPI
                    fdb       VmReleaseCache-StateAPI,GameReleaseBackground-StateAPI
                    fdb       PictureRelease-StateAPI,VmLoadResource-StateAPI
                    fdb       VmSlotAddress-StateAPI,VmRestoreAsset-StateAPI
                    fdb       PictureAllocate-StateAPI,PicturePointer-StateAPI
                    fdb       GameSaveBackground-StateAPI,GameComposeScene-StateAPI
                    fdb       RefreshPicture-StateAPI,GameWarmPriority-StateAPI

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
                    bsr       ParserByte
                    bcs       DictionaryReadReturn
                    tfr       b,a
                    andcc     #$FE
DictionaryReadReturn puls    x,y,u,pc
DictionaryReadCached leay    assetinput,u
                    lda       d,y
                    andcc     #$FE
                    puls      x,y,u,pc
DictionaryPrefix    pshs      a
                    bsr       DictionaryReadAt
                    bcs       DictionaryPrefixError
                    tfr       a,b
                    puls      a
                    leax      1,x
                    andcc     #$FE
                    rts
DictionaryPrefixError puls   a,pc
DictionaryReadID    pshs      x
                    leax      1,x
                    bsr       DictionaryReadAt
                    bcs       DictionaryIDReturn
                    pshs      a
                    leax      1,x
                    bsr       DictionaryReadAt
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
                    ldd       #1000
GameWindowRestore   lbsr      GameCopyWords
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
                    lbsr      UiLoadModule
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
                    tst       traceowned,u
                    beq       GameTextUnlinkModule
                    ldu       <resourcebase
                    lda       #1
                    sta       <tracemode
                    lda       #3
                    clrb
                    lbsr      GameTraceEvent
                    bcs       GameTextUnlinkDone
GameTextUnlinkModule equ    *
                    ldu       <resourcebase
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
                    std       menuentry,u
                    std       formatentry,u
GameTextUnlinkDone  rts
GameTextPresent     lbsr      AssetUnmap
                    bcs       GameTextReturn
                    ldu       <resourcebase
* text.screen displays retain the scene but must paint every occupied cell,
* including the blank cells that make the white background opaque.
                    tst       <bitmapowned
                    bne       GameDrawText
                    tst       <pictureowned
                    bne       GameTextShowPicture
                    bsr      GameCreateScreen
                    bcs       GameTextReturn
GameTextShowPicture lbsr      PresentPicture
                    bcs       GameTextReturn
                    lbra      GameDrawText
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

* text.screen remains on the game picture; the first display builds a bounded
* black-frame/white panel and wraps its text there.
GameTextScreen      lbsr      GameCloseWindow
                    lbcs      GameTextReturn
                    clr       <vmgraphics
                    clrb
                    rts

GameGraphicsMode    lbsr      GameCloseWindow
                    lbcs      GameTextReturn
                    lda       #1
                    sta       <vmgraphics
                    lbsr      GameTextInitialize
                    clr       dialogactive,u
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
                    beq       GameClearLinesBlack
                    ldb       #$81
                    bra       GameClearLinesColor
GameClearLinesBlack ldb       #$80
GameClearLinesColor stb       vmarguments+4,u
                    ldb       vmarguments+1,u
                    stb       vmarguments+2,u
                    clr       vmarguments+1,u
                    ldb       #39
                    stb       vmarguments+3,u
                    bra      GameClearTextRect

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
InventorySaveText equ *
                    lbsr      GameCopyWords
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
InventoryRestoreText equ *
                    lbsr      GameCopyWords
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
MenuInitialize      clr       <menupending
                    clr       <menucount
                    clr       <menuitems
                    clr       <menucurrent
                    clr       <menuready
                    clr       <menutextused
                    clr       <menutextused+1
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
MenuSetTitle        tst       <menuready
                    bne       MenuBuildReturn
                    ldb       <menucount
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
MenuBuildReturn     equ       *
                    clrb
                    rts
MenuSetItem         tst       <menuready
                    bne       MenuBuildReturn
                    tst       <menucount
                    lbeq      MenuInvalid
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
                    clrb
                    rts
MenuSubmit          tst       <menucount
                    beq       MenuInvalid
                    lda       #1
                    sta       <menuready
                    clrb
                    rts
MenuCommand         ldb       <vmopcode
                    cmpb      #156
                    beq       MenuSetTitle
                    cmpb      #157
                    beq       MenuSetItem
                    cmpb      #158
                    beq       MenuSubmit
                    cmpb      #159
                    beq       MenuEnable
                    cmpb      #160
                    beq       MenuDisable
                    ldb       #E$UnkSvc
                    orcc      #1
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
* Retain the raw literal like CoCo MenuExtraFlag; only zero hides it.
AuxMenuVisibility   ldu       <resourcebase
                    ldb       vmarguments,u
                    stb       menuvisibility,u
                    lda       #1
                    sta       menuvisibilityset,u
                    clrb
                    rts
MENU_REQUEST_ALLOWED macro
                    ldu       <resourcebase
                    tst       vmflags+14,u
                    endm
MENU_REQUEST_STORE macro
                    sta       <menupending
                    endm
MENU_REQUEST_RETURN macro
                    andcc     #$FE
                    endm
AuxMenuRequest      AGI_MENU_REQUEST AuxMenuRequestReturn
AuxMenuInput        ldu       <resourcebase
                    sty       coldapi,u
                    tst       menuvisibilityset,u
                    beq       AuxMenuVisible
                    tst       menuvisibility,u
                    lbeq      AuxMenuSuccess
AuxMenuVisible      tst       <menuready
                    lbeq      AuxMenuInvalid
                    tst       <menuitems
                    lbeq      AuxMenuSuccess
                    UI_CALL   0
                    lbcs      AuxMenuReturn
                    UI_CALL_REGS   2
                    lbcs      AuxMenuReturn
                    ldu       <resourcebase
* An open dialog owns resourcecommands as its saved text-plane backup.
* Do not borrow that workspace for a nested menu snapshot.
                    tst       dialogactive,u
                    lbne      AuxMenuSuccess
                    leax      textcharacters,u
                    leay      resourcecommands,u
                    ldd       #1000
GameMenuSave equ *
                    jsr       [copywordentry,u]
                    clr       inventoryselected,u
                    clr       inventoryselected+1,u
GameMenuDraw        ldu       <resourcebase
* Restore the saved overlay planes before repainting.
                    leax      resourcecommands,u
                    leay      textcharacters,u
                    ldd       #1000      copy 1000 words = 2000 bytes
                    jsr       [copywordentry,u]
                    ldu       <resourcebase
* Keep the familiar menu heading and all titles/items in script order.
                    lda       #1
                    sta       inventoryrow,u
                    lda       #$0F
                    sta       inventorykey,u
                    lbsr      GameMenuFillRow
                    leax      GameMenuTitle,pcr
                    leay      textcharacters+42,u
                    ldb       #34
                    lbsr      GameMenuLabel
* Page the global item list around the selected action.
                    lda       inventoryselected+1,u
                    cmpa      #21
                    blo       GameMenuPageStart
                    suba      #20
                    bra       GameMenuPage
GameMenuPageStart   clra
GameMenuPage        sta       inventorytop+1,u
                    sta       inventoryprevious+1,u
                    clr       inventoryprevious,u
                    lda       #3
                    sta       inventoryrow,u
GameMenuItem        lda       inventoryprevious+1,u
                    cmpa      <menuitems
                    lbhs      GameMenuHelpLine
                    cmpa      inventoryselected+1,u
                    bne       GameMenuNormal
                    ldb       #6
                    mul
                    leax      menuentries,u
                    leax      d,x
                    tst       4,x
                    beq       GameMenuDisabled
                    lda       #$F0
                    bra       GameMenuRowColor
GameMenuNormal      lda       inventoryprevious+1,u
                    ldb       #6
                    mul
                    leax      menuentries,u
                    leax      d,x
                    tst       4,x
                    beq       GameMenuDisabled
                    lda       #$0F
                    bra       GameMenuRowColor
GameMenuDisabled    lda       #$7F
GameMenuRowColor    sta       inventorykey,u
                    lbsr      GameMenuFillRow
* Draw the parent title, separator and option label on one bounded row.
                    ldu       <resourcebase
                    lda       inventoryprevious+1,u
                    ldb       #6
                    mul
                    leax      menuentries,u
                    leax      d,x
                    lda       3,x
                    ldb       #4
                    mul
                    leax      menutitles,u
                    leax      d,x
                    ldd       ,x
                    leax      menutext,u
                    leax      d,x
                    lda       inventoryrow,u
                    ldb       #40
                    mul
                    addd      #2
                    leay      textcharacters,u
                    leay      d,y
                    ldb       #15
                    lbsr      GameMenuLabel
                    leax      GameMenuColon,pcr
                    ldb       #2
                    lbsr      GameMenuLabel
                    ldu       <resourcebase
                    lda       inventoryprevious+1,u
                    ldb       #6
                    mul
                    leax      menuentries,u
                    leax      d,x
                    ldd       ,x
                    leax      menutext,u
                    leax      d,x
                    ldb       #19
                    lbsr      GameMenuLabel
                    inc       inventoryprevious+1,u
                    inc       inventoryrow,u
                    lda       inventoryrow,u
                    cmpa      #24
                    lblo      GameMenuItem
GameMenuHelpLine    lda       #24
                    sta       inventoryrow,u
                    lda       #$0F
                    sta       inventorykey,u
                    lbsr      GameMenuFillRow
* The help line uses 38 cells, extending one cell beyond the normal panel.
                    lda       #' '
                    sta       textcharacters+961,u
                    sta       textcharacters+998,u
                    lda       #$0F
                    sta       textcolors+961,u
                    sta       textcolors+998,u
                    leax      GameMenuHelp,pcr
                    leay      textcharacters+961,u
                    ldb       #38
                    lbsr      GameMenuLabel
                    lbra      GameMenuPresent
* Fill only the menu line and leave both side gutters untouched.
GameMenuFillRow     pshs      d,x,y
                    ldu       <resourcebase
                    lda       inventoryrow,u
                    ldb       #40
                    mul
                    addd      #2
                    leay      textcharacters,u
                    leay      d,y
                    ldb       #36
                    lda       #' '
GameMenuFillChars   sta       ,y+
                    decb
                    bne       GameMenuFillChars
                    ldu       <resourcebase
                    lda       inventoryrow,u
                    ldb       #40
                    mul
                    addd      #2
                    leax      textcolors,u
                    leax      d,x
                    lda       inventorykey,u
                    ldb       #36
GameMenuFillColors  sta       ,x+
                    decb
                    bne       GameMenuFillColors
                    puls      d,x,y
                    rts
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
                    lbeq      GameMenuCancel
                    cmpa      #27
                    lbeq      GameMenuCancel
                    cmpa      #13
                    lbeq      GameMenuSelect
                    cmpa      #12
                    lbeq      GameMenuUp
                    cmpa      #8
                    lbeq      GameMenuLeft
                    cmpa      #10
                    beq       GameMenuDown
                    cmpa      #9
                    beq       GameMenuRight
                    lbra      GameMenuWait
* CoCo Down returns to the head item of the currently selected title.
GameMenuDown        ldx       <resourcebase
                    ldb       inventoryselected+1,u
                    lda       #6
                    mul
                    leax      d,x
                    leax      menuentries,x
                    lda       3,x
                    ldb       #4
                    mul
                    ldx       <resourcebase
                    leax      menutitles,x
                    leax      d,x
                    lda       2,x
                    sta       inventoryselected+1,u
                    lbra      GameMenuChanged
* CoCo's right-arrow event advances to the next nonempty menu title and
* highlights that title's final item.  K2 reports right-arrow as TAB ($09).
GameMenuRight       ldx       <resourcebase
                    ldb       inventoryselected+1,u
                    lda       #6
                    mul
                    leax      d,x
                    leax      menuentries,x
                    lda       3,x
                    inca
                    cmpa      <menucount
                    blo       GameMenuRightGroup
                    clra
GameMenuRightGroup  sta       <menucurrent
                    clr       inventorykey,u
GameMenuRightScan   ldx       <resourcebase
                    leax      menutitles,x
                    lda       <menucurrent
                    ldb       #4
                    mul
                    leax      d,x
                    tst       3,x
                    bne       GameMenuRightFound
                    inc       <menucurrent
                    lda       <menucurrent
                    cmpa      <menucount
                    blo       GameMenuRightNext
                    clr       <menucurrent
GameMenuRightNext   inc       inventorykey,u
                    lda       inventorykey,u
                    cmpa      <menucount
                    blo       GameMenuRightScan
                    lbra      GameMenuWait
GameMenuRightFound  lda       2,x
                    adda      3,x
                    deca
                    sta       inventoryselected+1,u
                    bra       GameMenuChanged
* CoCo's left-arrow event highlights the second item of the current title;
* a one-item title wraps to its only item. K2 reports left as backspace ($08).
GameMenuLeft        ldx       <resourcebase
                    ldb       inventoryselected+1,u
                    lda       #6
                    mul
                    leax      d,x
                    leax      menuentries,x
                    lda       3,x
                    sta       inventorykey,u
                    ldx       <resourcebase
                    leax      menutitles,x
                    lda       inventorykey,u
                    ldb       #4
                    mul
                    leax      d,x
                    lda       2,x
                    ldb       3,x
                    cmpb      #2
                    blo       GameMenuLeftFound
                    inca
GameMenuLeftFound   sta       inventoryselected+1,u
                    bra       GameMenuChanged
GameMenuUp          ldx       <resourcebase
                    ldb       inventoryselected+1,u
                    lda       #6
                    mul
                    leax      d,x
                    leax      menuentries,x
                    lda       3,x
                    sta       inventorykey,u
                    ldx       <resourcebase
                    leax      menutitles,x
                    lda       inventorykey,u
                    ldb       #4
                    mul
                    leax      d,x
                    lda       2,x
                    cmpa      inventoryselected+1,u
                    bne       GameMenuDecrement
                    lda       3,x
                    adda      2,x
                    deca
                    sta       inventoryselected+1,u
                    bra       GameMenuChanged
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
                    UI_CALL_REGS   10
                    ora       ,x
                    sta       ,x
GameMenuCancel      clrb
GameMenuRestore     pshs      cc,b
                    ldu       <resourcebase
                    leax      resourcecommands,u
                    leay      textcharacters,u
                    ldd       #1000
GameMenuCopyBack equ *
                    jsr       [copywordentry,u]
                    puls      cc,b
                    bcs      AuxMenuReturn
                    UI_CALL   12
                    bcs      AuxMenuReturn
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
GameMenuHelp        fcc       /Arrows select; ENTER opens; ESC cancel/
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
menupending         rmb       1
                    ifne GAME_PRESENTATION
tracemode           rmb       1
                    endc
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
                    clra
                    sta       textrenderdirty,x
                    ldd       #1000
                    std       textrenderend,x
                    clr       textrow,x
                    clr       textcolumn,x
TextFastPrepare     lbsr      AssetUnmap
                    bcs       GameTextReturn
                    lbsr      PictureUnmap
                    bcs       GameTextReturn
                    ldx       <resourcebase
TextFastNextRow     lbsr      foreground
                    bcs       GameTextReturn
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
                    bsr       GameFramePointer
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
FormatPart          tst       ,x
                    lbeq      FormatSuccess
                    lda       formatdepth,u
                    cmpa      #4
                    lbhs      FormatInvalid
                    clrb
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
                    beq       FormatDone
* CoCo ignores an unknown two-byte escape without consuming following digits.
                    cmpa      #'w
                    beq       FormatNumberStart
                    cmpa      #'s
                    beq       FormatNumberStart
                    cmpa      #'m
                    beq       FormatNumberStart
                    cmpa      #'g
                    beq       FormatNumberStart
                    cmpa      #'v
                    beq       FormatNumberStart
                    cmpa      #'o
                    bne       FormatNext
FormatNumberStart   sta       parsercharacter,u
FormatNumber        lbsr      ParseDecStr
                    stb       parserwordlength,u
FormatDispatch      lda       parsercharacter,u
                    FORMAT_EMIT_DIRECTIVES
FormatUnsupported   ldb       #E$UnkSvc
                    bra       FormatSetError
FormatDone          dec       formatdepth,u
FormatSuccess       clrb
FormatReturn        rts
FormatPartInvalid   ldb       #E$BMode
FormatSetError      orcc      #1
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
* CLR of the terminator already cleared carry.
                    puls      d,y,pc
FormatFull          puls      d,y
                    bra       FormatInvalid
FormatWord          tstb
                    lbeq      FormatNext
                    cmpb      #20
                    lbhi      FormatNext
                    lda       parsercount,u
                    tst       vmvariables+9,u
                    beq       FormatWordBound
                    inca
FormatWordBound     pshs      a
                    cmpb      ,s+
                    lbhi      FormatNext
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
* Global/object readers share the checked recursive expansion return.
* Platform acquisition lives in the immutable cold helper.
FormatExternal      pshs      x
                    leax      formatentry,u
                    ldb       #22
                    leay      FormatExternalCallbacks,pcr
                    lbsr      GameColdInvoke
                    bra       FormatMessageReturn
FormatExternalCallbacks fdb AssetUnmap-FormatExternalCallbacks,ResourceClose-FormatExternalCallbacks,FormatPart-FormatExternalCallbacks
                    fdb FormatReadMessage-FormatExternalCallbacks,AssetReadWord-FormatExternalCallbacks,StateAPI-FormatExternalCallbacks,ResourceReadExact-FormatExternalCallbacks
* Formatter-only optional messages. Other message commands retain strict errors.
* CoCo skips indices above the declared count. Zero is a bounded empty expansion,
* avoiding its reference header-as-pointer access; corrupt tables still fail.
FormatReadMessage   tstb
                    beq       FormatReadEmpty
                    lda       #255
                    sta       <messagecount
                    lbsr      ReadLogicMessage
                    bcc       FormatReadReturn
                    cmpb      #E$BMode
                    bne       FormatReadReturn
                    ldb       <messagenumber
                    cmpb      <messagecount
                    bhi       FormatReadEmpty
                    ldb       #E$BMode
                    orcc      #1
FormatReadReturn    rts
FormatReadEmpty     ldu       <resourcebase
                    leax      messagebuffer,u
                    clr       ,x
                    clrb
                    rts
FormatMessage       pshs      x
                    bsr       FormatReadMessage
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
                    bsr      ParseDecStr
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
                    ifeq GAME_PRESENTATION
StringsInitialize   ldu       <resourcebase
                    leax      vmstrings,u
                    ldy       #480
                    clra
StringsClear        sta       ,x+
                    leay      -1,y
                    bne       StringsClear
                    rts
                    endc
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
* Y names relative callbacks: unmap, close, recurse, message, word, StateAPI.
* Object reads do not allocate or mutate item rooms. State is private to S.
AuxFormatExpansion  lda       parsercharacter,u
                    cmpa      #'g
                    lbeq      AuxFormatGlobal
                    pshs      y
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
                    bne      AuxObjectInvalid
                    ldb       ,x
                    lda       1,x
                    cmpd      #768
                    bhi      AuxObjectInvalid
                    std       ,s
AuxObjectTableCheck  subd      #3
                    blo      AuxObjectInvalid
                    bne       AuxObjectTableCheck
                    ldd       4,s
                    cmpd      ,s
                    bhs      AuxObjectInvalid
                    addd      #3
                    ldy       #3
                    bsr       AuxObjectReadAt
                    bcs      AuxObjectFailed
                    cmpy      #3
                    bne      AuxObjectInvalid
                    ldb       ,x
                    lda       1,x
                    addd      #3
                    bcs      AuxObjectInvalid
                    cmpd      #2048
                    bhs      AuxObjectInvalid
                    std       2,s
                    subd      #3
                    cmpd      ,s
                    blo      AuxObjectInvalid
                    ldd       #2048
                    subd      2,s
                    cmpd      #512
                    bls       AuxObjectReadLength
                    ldd       #512
AuxObjectReadLength tfr       d,y
                    ldd       2,s
                    bsr      AuxObjectReadAt
                    bcs       AuxObjectFailed
                    pshs      x
AuxObjectBound      lda       ,x+
                    beq       AuxObjectReady
                    leay      -1,y
                    bne       AuxObjectBound
                    leas      2,s
                    bra       AuxObjectInvalid
AuxObjectReady      bsr      AuxObjectClose
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
                    bsr      AuxObjectClose
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
* Reuse the resident bounded reader, including partial-read/EOF accounting.
                    ldy       12,s
                    ldd       12,y
                    leay      d,y
                    pshs      y
                    ldy       4,s
                    jsr       [,s]
                    leas      2,s
                    bcc       AuxObjectReadComplete
                    cmpb      #E$EOF
                    bne      AuxObjectReadError
AuxObjectReadComplete ldd     2,s
                    subd      <resourceremaining
                    beq      AuxObjectReadInvalid
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
* Nested global messages temporarily select logic zero and restore the caller.
AuxFormatGlobal     ldb       <vmcurrent
                    pshs      b
                    ldd       <vmend
                    pshs      d
                    pshs      y
                    ldd       ,y
                    leay      d,y
                    jsr       ,y
                    lbcs      AuxGlobalReturn
                    ldu       <resourcebase
                    ldy       ,s
                    ldd       10,y
                    leay      d,y
                    ldd       10,y
                    leay      d,y
                    clra
                    clrb
                    jsr       ,y       ; ensure logic zero is cache-owned
                    bcs      AuxGlobalRestore
                    ldb       <vmcacheindex
                    stb       <vmcurrent
                    ldy       ,s
                    ldd       10,y
                    leay      d,y
                    ldd       14,y
                    leay      d,y
                    jsr       ,y
                    ldy       ,s
                    ldd       8,y
                    leay      d,y
                    ldd       #0
                    jsr       ,y
                    bcs       AuxGlobalRestore
                    addd      #2
                    bcs       AuxGlobalInvalid
                    cmpd      #2
                    bls       AuxGlobalInvalid
                    cmpd      <resourcelength
                    bhs       AuxGlobalInvalid
                    std       <vmend
                    ldy       ,s
                    ldd       6,y
                    leay      d,y
                    ldb       parserwordlength,u
                    jsr       ,y
                    bcs       AuxGlobalRestore
                    ldy       ,s
                    ldd       4,y
                    leay      d,y
                    jsr       ,y
AuxGlobalRestore    pshs      b,cc
                    ldy       2,s
                    ldd       ,y
                    leay      d,y
                    jsr       ,y
                    bcc       AuxGlobalUnmapped
                    leas      2,s
                    pshs      b,cc
AuxGlobalUnmapped   ldy       2,s
                    ldd       10,y
                    leay      d,y
                    ldd       12,y
                    leay      d,y
                    ldb       6,s
                    stb       <vmcurrent
                    jsr       ,y
                    ldy       2,s
                    ldd       10,y
                    leay      d,y
                    ldd       14,y
                    leay      d,y
                    jsr       ,y
                    ldd       4,s
                    std       <vmend
                    puls      cc,b
AuxGlobalReturn     puls      y
                    leas      3,s
                    rts
AuxGlobalInvalid    ldb       #E$BMode
                    orcc      #1
                    bra       AuxGlobalRestore
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
                    endc
