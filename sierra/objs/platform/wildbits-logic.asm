* wildbits-logic feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_FLAG_STORAGE
* ===== wildbits-flag-storage =====
* Native flag storage adapter. Index in A; U is the process-private base.
SetFlag             tfr       a,b
                    leax      vmflags,u
                    abx
                    lda       #1
                    sta       ,x
                    rts
ClearFlag           tfr       a,b
                    leax      vmflags,u
                    abx
                    clr       ,x
                    rts
ToggleFlag          tfr       a,b
                    leax      vmflags,u
                    abx
                    lda       ,x
                    eora      #1
                    sta       ,x
                    rts

TestFlag            tfr       a,b
                    leax      vmflags,u
                    abx
                    lda       ,x
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_TRACE_CODE
* ===== wildbits-game-trace-code =====
* Optional GAME_TRACE=1 build: report the exit byte and last instruction.
* Called after cleanup, with no mapping live; preserve the actual exit status.
GameTraceError      tstb
                    beq       GameTraceReturn
                    pshs      cc,d,x,y,u
                    pshs      b
                    leax      GameTracePrefix,pcr
                    ldu       <resourcebase
                    leay      picturestage,u
GameTraceCopy       lda       ,x+
                    sta       ,y+
                    bne       GameTraceCopy
                    leay      -1,y
                    puls      b
                    lbsr      GameTraceHex
                    lda       #C$SPAC
                    sta       ,y+
                    ldb       <vmopcode
                    lbsr      GameTraceHex
                    lda       #C$SPAC
                    sta       ,y+
                    ldu       <resourcebase
                    ldb       gametracestagebyte,u
                    lbsr      GameTraceHex
                    lda       #C$SPAC
                    sta       ,y+
                    ldu       <resourcebase
                    ldb       vmvariables,u
                    lbsr      GameTraceHex
                    lda       #C$SPAC
                    sta       ,y+
                    ldb       gametracekeybyte,u
                    lbsr      GameTraceHex
                    lda       #C$SPAC
                    sta       ,y+
                    ldb       gametracemenuhit,u
                    lbsr      GameTraceHex
                    lda       #C$CR
                    sta       ,y+
                    ldu       <resourcebase
                    leax      picturestage,u
                    lda       #2
                    ldy       #80
                    os9       I$WritLn
                    puls      cc,d,x,y,u,pc
GameTraceReturn     rts
GameTraceHex        pshs      b
                    lsrb
                    lsrb
                    lsrb
                    lsrb
                    lbsr      GameTraceDigit
                    puls      b
                    andb      #15
GameTraceDigit      addb      #'0
                    cmpb      #'9
                    bls       GameTraceStore
                    addb      #7
GameTraceStore      stb       ,y+
                    rts
GameTracePrefix     fcc       /wbgame error, opcode: /
                    fcb       0

GameTraceStage      pshs      cc,u
                    bcc       GameTraceStageReturn
                    ldu       <resourcebase
                    tst       gametracestagebyte,u
                    bne       GameTraceStageReturn
                    sta       gametracestagebyte,u
GameTraceStageReturn puls     cc,u,pc

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_LOGIC_CACHE
* ===== wildbits-logic-cache =====
* Bounded resident logic cache and nested calls. Cache entries (14 bytes):
* id, owned, physical-first(2), count, kind, expanded(2), stored(2), scan(2),
* reserved(2). Calls save id/index, IP, code-end and remaining instruction
* budget in a private eight-byte frame. No resource pointers survive mapping.
VmClearCache        ldu       <resourcebase
                    leax      vmcache,u
                    ldy       #448
                    clra
VmCacheZero         sta       ,x+
                    leay      -1,y
                    bne       VmCacheZero
                    clr       <vmdepth
                    clr       <vmcurrent
                    rts
VmInitializeCache   ldu       <resourcebase
                    leax      vmcache,u
                    ldb       <argnumber+1
                    stb       ,x
                    bsr      VmStoreAsset
                    rts
VmStoreAsset        ldb       <assetowned
                    stb       1,x
                    ldd       <assetfirst
                    std       2,x
                    ldb       <assetblocks
                    stb       4,x
                    ldb       <resourcekind
                    stb       5,x
                    ldd       <resourcelength
                    std       6,x
                    ldd       <resourcestored
                    std       8,x
                    ldd       #2
                    std       10,x
                    clr       <assetowned    ownership transferred, not copied
                    rts
VmSlotAddress       ldu       <resourcebase
                    leax      vmcache,u
                    lda       #14
                    mul
                    leax      d,x
                    rts
VmRestoreAsset      ldd       2,x
                    std       <assetfirst
                    ldb       4,x
                    stb       <assetblocks
                    ldb       5,x
                    stb       <resourcekind
                    ldd       6,x
                    std       <resourcelength
                    ldd       8,x
                    std       <resourcestored
                    clr       <assetowned
                    rts
* B=logic number. Ensure it is cached; return X=slot, no mapping live.
VmLoadLogic         clra
VmLoadResource      sta       <vmrequestedkind
                    stb       <vmrequested
                    lbsr      AssetUnmap
                    lbcs      VmCacheReturn
                    clr       <vmcacheindex
VmCacheFind         ldb       <vmcacheindex
                    bsr      VmSlotAddress
                    tst       1,x
                    beq       VmCacheFindNext
                    ldb       5,x
                    cmpb      <vmrequestedkind
                    bne       VmCacheFindNext
                    ldb       ,x
                    cmpb      <vmrequested
                    beq       VmCacheFound
VmCacheFindNext     inc       <vmcacheindex
                    ldb       <vmcacheindex
                    cmpb      #32
                    blo       VmCacheFind
                    clr       <vmcacheindex
VmCacheFreeSlot     ldb       <vmcacheindex
                    bsr      VmSlotAddress
                    tst       1,x
                    beq       VmCacheLoad
                    inc       <vmcacheindex
                    ldb       <vmcacheindex
                    cmpb      #32
                    blo       VmCacheFreeSlot
                    ldb       #E$MemFul
                    orcc      #1
                    rts
VmCacheLoad         stx       <vmslot
                    ldb       <vmrequested
                    stb       ,x
                    lda       <vmrequestedkind
                    sta       5,x
                    clra
                    tfr       d,y
                    ldx       <argdirectory
                    ldu       <resourcebase
                    lda       <vmrequestedkind
                    sta       <resourcekind
                    lbsr      LoadAsset
                    bcc       VmCacheLoaded
                    pshs      b
                    tst       <assetowned
                    beq       VmCacheLoadFailed
                    ldx       <vmslot
                    lbsr      VmStoreAsset    failed slab remains owned for exit
VmCacheLoadFailed   puls      b
                    orcc      #1
                    rts
VmCacheLoaded
                    ldx       <vmslot
                    lbsr      VmStoreAsset
                    pshs      x
                    leax      VmReplayLoadKinds,pcr
                    lda       <vmrequestedkind
                    lda       a,x
                    ldb       <vmrequested
                    lbsr      ReplayPush
                    puls      x
                    bcs       VmCacheReturn
VmCacheFound        clrb
VmCacheReturn       rts
* Nested call, B=logic number. The active caller owns a cache slot; save
* offsets before loading a callee, then restore its slab and code bounds.
VmCallLogic         lda       <vmdepth
                    cmpa      #16
                    lbhs      VmCacheDepthError
                    pshs      b
                    ldu       <resourcebase
                    leax      vmcallstack,u
                    ldb       #8
                    mul
                    leax      d,x
                    ldb       <vmcurrent
                    stb       ,x
                    ldd       <vmip
                    std       1,x
                    ldd       <vmend
                    std       3,x
                    ldd       <vmsteps
                    std       5,x
                    inc       <vmdepth
                    puls      b
                    lbsr      VmLoadLogic
                    bcs       VmCallRestore
                    ldb       <vmcacheindex
                    stb       <vmcurrent
                    lbsr      VmRestoreAsset
                    clr       <vmip
                    clr       <vmip+1
                    ldd       <resourcelength
                    std       <vmend
                    lbsr      VmReadWord
                    bcs       VmCallRestore
                    cmpd      #$FFFD
                    bhi       VmCallInvalid
                    addd      #2
                    cmpd      <resourcelength
                    bhi       VmCallInvalid
                    cmpd      #2
                    bls       VmCallInvalid
                    std       <vmend
                    ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    ldd       10,x
                    cmpd      <vmend
                    bhs       VmCallInvalid
                    std       <vmip
                    lbsr      ExecuteLogic
                    bra       VmCallRestore
VmCallInvalid       lbsr      VmInvalid
VmCallRestore       pshs      cc,b
                    lbsr      AssetUnmap
                    bcc       VmCallUnmapped
                    leas      2,s
                    pshs      cc,b
VmCallUnmapped      dec       <vmdepth
                    ldu       <resourcebase
                    leax      vmcallstack,u
                    lda       <vmdepth
                    ldb       #8
                    mul
                    leax      d,x
                    ldb       ,x
                    stb       <vmcurrent
                    ldd       1,x
                    std       <vmip
                    ldd       3,x
                    std       <vmend
                    ldd       5,x
                    std       <vmsteps
                    ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    puls      cc,b,pc
VmCacheDepthError   ldb       #E$MemFul
                    orcc      #1
                    rts
* Release the temporary loader slab, then every cache-owned slab. Preserve
* the first cleanup error and leave failed entries owned for a retry.
VmReleaseResources  clr       <vmcleanup
                    lbsr      AssetRelease
                    bcc       VmReleaseCache
                    rts
VmReleaseCache      clr       <vmcacheindex
VmReleaseNext       ldb       <vmcacheindex
                    lbsr      VmSlotAddress
                    tst       1,x
                    beq       VmReleaseAdvance
                    stx       <vmslot
                    lbsr      VmRestoreAsset
                    inc       <assetowned
                    lbsr      AssetRelease
                    bcs       VmReleaseFailed
                    ldx       <vmslot
                    clr       1,x
                    bra       VmReleaseAdvance
VmReleaseFailed     clr       <assetowned    cache entry retains ownership
                    tst       <vmcleanup
                    bne       VmReleaseAdvance
                    stb       <vmcleanup
VmReleaseAdvance    inc       <vmcacheindex
                    ldb       <vmcacheindex
                    cmpb      #32
                    blo       VmReleaseNext
                    ldb       <vmcleanup
                    beq       VmReleaseDone
                    orcc      #1
VmReleaseDone       rts

* A=kind/B=id. Discard a cached non-logic resource; absent resources are
* already discarded. Unmap before freeing and restore the executing logic.
VmDiscardResource   sta       <vmrequestedkind
                    stb       <vmrequested
                    lbsr      AssetUnmap
                    lbcs      VmCacheReturn
                    clr       <vmcacheindex
VmDiscardFind       ldb       <vmcacheindex
                    lbsr      VmSlotAddress
                    tst       1,x
                    beq       VmDiscardNext
                    ldb       5,x
                    cmpb      <vmrequestedkind
                    bne       VmDiscardNext
                    ldb       ,x
                    cmpb      <vmrequested
                    bne       VmDiscardNext
                    stx       <vmslot
                    lbsr      VmRestoreAsset
                    inc       <assetowned
                    lbsr      AssetRelease
                    bcs       VmDiscardFailed
                    ldx       <vmslot
                    clr       1,x
                    bra       VmDiscardRestore
VmDiscardNext       inc       <vmcacheindex
                    ldb       <vmcacheindex
                    cmpb      #32
                    blo       VmDiscardFind
VmDiscardRestore    ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    clrb
                    rts
VmDiscardFailed     clr       <assetowned    cache slot retains ownership
                    orcc      #1             CLR must not hide the release error
                    rts
VmReplayLoadKinds   fcb       0,2,1,3

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_LOGIC_DATA
* ===== wildbits-logic-data =====
* Private interpreter controls; variables/flags/argument staging are separate
* from this direct-page area. Conditions use two stack-local bytes, shared
* with CoCo traversal; there is no separate eager-evaluation state.
* Script positions are offsets, never mapped pointers.
vmip                rmb       2
vmend               rmb       2
vmsteps             rmb       2
vmopcode            rmb       1
vmargcount          rmb       1
vmargindex          rmb       1
vmtemp              rmb       1
vmleft              rmb       1
vmright             rmb       1
vmerror             rmb       1
vmcurrent           rmb       1
vmdepth             rmb       1
vmrequested         rmb       1
vmcacheindex        rmb       1
vmslot              rmb       2
vmcleanup           rmb       1
vmrequestedkind     rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_LOGIC_FETCH
* ===== wildbits-logic-fetch =====
* Start a loaded logic slab. The two-byte header is the little-endian code
* length; messages follow it and must never be executed as instructions.
StartLogic          ldu       <resourcebase
                    leax      vmvariables,u
                    ldy       #512
                    clra
VmClearState        sta       ,x+
                    leay      -1,y
                    bne       VmClearState
                    ifne      GAME_PRESENTATION
                    lbsr      GameInitialize
                    bcs      VmNativeReturn
                    endc
                    lbsr      ObjectsInitialize
                    lbsr      VmInitializeCache
                    clr       <vmip
                    clr       <vmip+1
                    ldd       <resourcelength
                    std       <vmend
                    lbsr      VmReadWord
                    bcs       VmNativeReturn
                    cmpd      #$FFFD
                    bhi       VmNativeInvalid
                    addd      #2
                    cmpd      <resourcelength
                    bhi       VmNativeInvalid
                    cmpd      #2
                    bls       VmNativeInvalid
                    std       <vmend
VmRunRoot           lbsr      ExecuteLogic
                    bcs       VmNativeReturn
                    tst       <vmroompending
                    beq       VmCompletedRootCycle
                    lbsr      ApplyRoomChange
                    bcs       VmNativeReturn
                    bra       VmRunRoot
VmCompletedRootCycle equ      *
                    ifne      GAME_PRESENTATION
                    lbsr      GameNextCycle
                    bcs       VmNativeReturn
                    ldu       <resourcebase
                    tst       gamequit,u
                    bne       VmNativeReturn
                    clr       <vmroomchanges
                    clr       <vmcurrent
                    clrb
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    ldd       10,x
                    std       <vmip
                    bra      VmRunRoot
                    endc
VmNativeReturn      pshs      b,cc
                    lbsr      AssetUnmap
                    bcs       VmNativeUnmapError
                    puls      cc,b,pc
VmNativeUnmapError  leas      2,s
                    rts
VmNativeInvalid     lbsr      VmInvalid
                    bra       VmNativeReturn
VmFetchByte         pshs      x,y,u
                    tst       <asseterror
                    bne       VmFetchFailed
                    ldd       <vmip
                    cmpd      <vmend
                    bhs       VmFetchEOF
* Sequential bytecode normally stays in the current mapped resource page.
* Reconstruct the ephemeral address; never retain it across a kernel call.
                    tst       <assetmapped
                    beq       VmFetchMap
                    anda      #$E0
                    cmpa      <assetpage
                    bne       VmFetchReloadOffset
                    ldd       <vmip
                    anda      #$1F
                    ldu       <assetmapbase
                    leau      d,u
                    bra       VmFetchRead
VmFetchReloadOffset ldd       <vmip
VmFetchMap          lbsr      AssetPointer
                    tst       <asseterror
                    bne       VmFetchFailed
VmFetchRead         ldb       ,u
                    pshs      b
                    ldd       <vmip
                    addd      #1
                    std       <vmip
                    puls      b
                    andcc     #$FE
                    puls      x,y,u,pc
VmFetchEOF          ldb       #E$EOF
                    orcc      #1
                    puls      x,y,u,pc
VmFetchFailed       ldb       <asseterror
                    orcc      #1
                    puls      x,y,u,pc

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_LOGIC_PLATFORM
* ===== wildbits-logic-platform =====
* Game commands are adapted here in small groups. Unsupported behavior
* remains an explicit error until the corresponding component is ported.
* Platform routes come from the common catalog. A temporary tail-jump
* target sits below saved D/X; both are restored before entering the handler.
* The caller return address and the other registers are untouched.
VmPlatformCommand   ldb       <vmopcode
                    cmpb      #VmPlatformCommandCount
                    lbhs      VmPlatformUnsupported
                    leas      -2,s
                    pshs      d,x
                    clra
                    lslb
                    rola
                    leax      VmPlatformCommandTable,pcr
                    ldd       d,x
                    leax      d,x
                    stx       4,s
                    puls      d,x,pc
VmPlatformCommandTable equ *
NATIVE_COMMAND_TABLE_MODE set 1
                    use shared/agi-command-table.asm
NATIVE_COMMAND_TABLE_MODE set 0
VmPlatformCommandCount equ (*-VmPlatformCommandTable)/2
VmCommandGameId     ldu       <resourcebase
                    ldb       vmarguments,u
                    lbsr      ReadLogicMessage
                    bcs       VmPlatformReturn
                    ldu       <resourcebase
                    leay      vmgameid,u
                    ldb       #7
VmGameIdCopy        lda       ,x+
                    sta       ,y+
                    beq       VmGameIdDone
                    decb
                    bne       VmGameIdCopy
                    clr       ,y
VmGameIdDone        clrb
VmPlatformReturn    rts
VmPlatformUnsupported ldb     #E$UnkSvc
                    orcc      #1
                    rts
VmPlatformTest      ldb       <vmopcode
                    ifne      GAME_PRESENTATION
                    cmpb      #15
                    lbeq      StringCompareTest
                    cmpb      #9
                    lbeq      InventoryTest
                    cmpb      #10
                    lbeq      InventoryTest
                    endc
                    cmpb      #11
                    lbeq      ObjectPositionTest
                    cmpb      #16
                    blo       VmPlatformInputTest
                    cmpb      #18
                    lbls      ObjectPositionTest
VmPlatformInputTest
                    cmpb      #12
                    blo       VmPlatformUnsupported
                    cmpb      #14
                    lbls      InputTest
                    bra      VmPlatformUnsupported
VmCommandLoadLogic  ldu       <resourcebase
                    ldb       vmarguments,u
                    lbsr      VmLoadLogic
                    bcs       VmPlatformReturn
* Loading a resource changes loader fields; restore the executing context.
                    ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    clrb
                    rts
VmCommandLoadLogicVariable bsr VmResolveLogicArgument
                    lbsr      VmLoadLogic
                    bcs       VmPlatformReturn
                    ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    clrb
                    rts
VmResolveLogicArgument ldu    <resourcebase
                    leax      vmvariables,u
                    ldb       vmarguments,u
                    clra
                    ldb       d,x
                    rts
VmCommandCallLogic  ldu       <resourcebase
                    ldb       vmarguments,u
                    lbra      VmCallLogic
VmCommandCallLogicVariable bsr VmResolveLogicArgument
                    lbra      VmCallLogic
VmCommandScanStart  ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    ldd       <vmip
                    std       10,x
                    clrb
                    rts
VmCommandScanReset  ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    ldd       #2
                    std       10,x
                    clrb
                    rts
VmCommandLoadView   ldu       <resourcebase
                    ldb       vmarguments,u
                    bra       VmLoadViewResource
VmCommandLoadViewVariable bsr VmResolveLogicArgument
VmLoadViewResource  lda       #2
                    bra       VmLoadTypedResource
VmCommandLoadSound  ldu       <resourcebase
                    ldb       vmarguments,u
                    lda       #3
VmLoadTypedResource lbsr      VmLoadResource
                    bcs       VmPlatformResourceReturn
                    ldb       <vmcurrent
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    clrb
VmPlatformResourceReturn rts
VmCommandDiscardView ldu      <resourcebase
                    ldb       vmarguments,u
                    bra       VmDiscardViewResource
VmCommandDiscardViewVariable bsr VmResolveLogicArgument
VmDiscardViewResource lda     #2
                    lbra      VmDiscardResource
VmCommandNewRoom    ldu       <resourcebase
                    ldb       vmarguments,u
                    lbra      RequestRoom
VmCommandNewRoomVariable lbsr VmResolveLogicArgument
                    lbra      RequestRoom
VmProgramControl    clr       <vmplayercontrol
                    clrb
                    rts
VmSetPlayerControl     lda       #1
                    sta       <vmplayercontrol
                    clrb
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_CONDITION_STREAM
* ===== wildbits-condition-stream =====
                    ifndef PLATFORM_WILDBITS_LOGIC_BINDINGS
                    use platform/wildbits-logic-bindings.asm
                    endc
* Bounded, process-private adapter to the common condition traversal.
CONDITION_FALSE_LABEL equ     ExecScriptJump
VmConditionInvalid  equ       VmLogicInvalid
VmConditionFailure  equ       VmLogicFailure

* A=test number. Decode operands for evaluated and skipped predicates alike.
VmConditionOperands sta       <vmopcode
                    cmpa      #1
                    lblo      VmInvalid
                    cmpa      #18
                    lbhi      VmInvalid
                    cmpa      #14
                    beq       VmConditionSaid
                    leax      VmTestCounts,pcr
                    ldb       a,x
                    stb       <vmargcount
                    lbra      VmReadArguments
VmConditionSaid     lbsr      VmFetchByte
                    lbcs      VmReturn
                    cmpb      #127
                    lbhi      VmInvalid
                    lslb
                    stb       <vmargcount
                    lbra      VmReadArguments
VmConditionTest     lbsr      VmConditionOperands
                    lbcs      VmReturn
                    lbra      VmEvaluateTest
* Validate grammar while skipping callbacks. Helper return occupies ,S;
* the shared OR/NOT locals are therefore 2,S and 3,S. A remains the code byte.
VmConditionScanControl cmpa   #$FE
                    beq       VmConditionScanInvalid
                    cmpa      #$FD
                    beq       VmConditionScanNot
                    cmpa      #$FC
                    beq       VmConditionScanOr
                    cmpa      #$FF
                    bne       VmConditionScanValid
                    ldb       2,s
                    orb       3,s
                    bne       VmConditionScanInvalid
VmConditionScanValid andcc    #$FE
                    rts
VmConditionScanNot  ldb       3,s
                    eorb      #1
                    stb       3,s
                    bra       VmConditionScanValid
VmConditionScanOr   tst       3,s
                    bne       VmConditionScanInvalid
                    ldb       2,s
                    eorb      #1
                    stb       2,s
                    bra       VmConditionScanValid
VmConditionScanInvalid lbra   VmInvalid

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_MATH_CODE
* ===== wildbits-game-math-code =====
                    ifndef PLATFORM_WILDBITS_LOGIC_BINDINGS
                    use platform/wildbits-logic-bindings.asm
                    endc
* Native argument/validation adapter; byte arithmetic belongs to the common engine.
GameMathCommand     ldu       <resourcebase
                    leay      vmarguments,u
                    ldb       <vmopcode
                    cmpb      #167
                    blo       GameMathReady
                    ldb       vmarguments+1,u
                    lda       <vmopcode
                    cmpa      #168
                    bne       GameMathDivisor
                    VARIABLE_TABLE
                    abx
                    ldb       ,x
GameMathDivisor     tstb
                    lbeq      ObjectBadIndex
GameMathReady       ldb       <vmopcode
                    subb      #165
                    lslb
                    leax      GameMathHandlers,pcr
                    ldd       b,x
                    leax      d,x
                    jsr       ,x
                    clrb
                    rts
GameMathHandlers    fdb       cmd_multn-GameMathHandlers
                    fdb       cmd_multv-GameMathHandlers
                    fdb       cmd_divn-GameMathHandlers
                    fdb       cmd_divv-GameMathHandlers
                    use       shared/math-commands.asm

GameRandomCommand   ldu       <resourcebase
                    lda       vmarguments,u
                    cmpa      vmarguments+1,u
                    lbhi      ObjectBadIndex
                    leay      vmarguments,u
                    bsr      CmdRandomImpl
                    clrb
                    rts
                    ifndef PLATFORM_WILDBITS_LOGIC_BINDINGS
                    use platform/wildbits-logic-bindings.asm
                    endc
                    use       shared/random-command.asm

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_LOGIC_CODE
* ===== wildbits-logic-code =====
                    ifndef PLATFORM_WILDBITS_LOGIC_BINDINGS
                    use platform/wildbits-logic-bindings.asm
                    endc
* Bounded AGI bytecode control/arithmetic layer, adapted from mnln's command
* semantics. No address patching: dispatch uses opcode values and PCR tables.
* ExecuteLogic uses VmFetchByte (B byte, C/error B) and platform command/test
* callbacks. All callbacks preserve U/DP; private controls survive callbacks.
* vmvariables and vmflags contain 256 bytes each; vmarguments holds 255 bytes.
* Platform commands must implement their semantics or return an error, never
* silently skip an unsupported command. This component is not a whole game.
                    ifndef PLATFORM_WILDBITS_LOGIC_BINDINGS
                    use platform/wildbits-logic-bindings.asm
                    endc
                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_CONDITION_STREAM
                    use platform/wildbits-logic.asm
ExecuteLogic        equ       ExecLogicScript
VmNext              equ       ExecScriptLoop
VmJump              equ       ExecScriptJump
VmConditionStart    equ       ExecScriptIf
                    use       shared/logic-executor.asm
VmLogicInvalid      lbsr      VmInvalid
VmLogicFailure      bra      ExecLogicScriptRet
VmReadArguments     clr       <vmargindex
VmArgumentLoop      lda       <vmargindex
                    cmpa      <vmargcount
                    bhs       VmArgumentsDone
                    lbsr      VmFetchByte
                    lbcs      VmReturn
                    ldu       <resourcebase
                    leax      vmarguments,u
                    pshs      b
                    ldb       <vmargindex
                    abx
                    puls      b
                    stb       ,x
                    inc       <vmargindex
                    bra       VmArgumentLoop
VmArgumentsDone     clrb
                    rts
* The exact variable-command bodies are also assembled by CoCo mnln.
* Operand acquisition remains in each owner; the arithmetic is shared.
VmArithmetic        ldu       <resourcebase
                    leay      vmarguments,u
                    ldb       <vmopcode
                    decb
                    lslb
                    leax      VmVariableCommands,pcr
                    ldd       b,x
                    leax      d,x
                    jsr       ,x
                    lbra      VmNext
                    use       shared/variable-commands.asm
VmVariableCommands  fdb       cmd_increment-VmVariableCommands
                    fdb       cmd_decrement-VmVariableCommands
                    fdb       cmd_assignn-VmVariableCommands
                    fdb       cmd_assignv-VmVariableCommands
                    fdb       cmd_addn-VmVariableCommands
                    fdb       cmd_addv-VmVariableCommands
                    fdb       cmd_subn-VmVariableCommands
                    fdb       cmd_subv-VmVariableCommands
                    fdb       cmd_lindirectv-VmVariableCommands
                    fdb       cmd_rindirect-VmVariableCommands
                    fdb       cmd_lindirectn-VmVariableCommands
                    fdb       CmdSetImpl-VmVariableCommands
                    fdb       CmdResetImpl-VmVariableCommands
                    fdb       CmdToggleImpl-VmVariableCommands
                    fdb       CmdSetVImpl-VmVariableCommands
                    fdb       CmdResetVImpl-VmVariableCommands
                    fdb       CmdToggleVImpl-VmVariableCommands
                    use       shared/flag-commands.asm
                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_FLAG_STORAGE
                    use platform/wildbits-logic.asm

VmReadWord          lbsr      VmFetchByte
                    lbcs      VmReturn
                    pshs      b
                    lbsr      VmFetchByte
                    bcs       VmWordError
                    tfr       b,a
                    puls      b
                    andcc     #$FE
                    rts
VmWordError         leas      1,s
                    rts
VmEvaluateTest      ldu       <resourcebase
                    ldb       <vmopcode
                    cmpb      #8
                    lbhi      VmExternalTest
                    leay      vmarguments,u
                    decb
                    lslb
                    leax      VmBuiltinTests,pcr
                    ldd       b,x
                    leax      d,x
                    jmp       ,x
CONDITION_TRUE      equ       VmTrue
CONDITION_FALSE     equ       VmFalse
                    use       shared/condition-tests.asm
VmBuiltinTests      fdb       TestEqualN-VmBuiltinTests
                    fdb       TestEqualV-VmBuiltinTests
                    fdb       TestLessN-VmBuiltinTests
                    fdb       TestLessV-VmBuiltinTests
                    fdb       TestGreaterN-VmBuiltinTests
                    fdb       TestGreaterV-VmBuiltinTests
                    fdb       TestIsSet-VmBuiltinTests
                    fdb       TestIsSetV-VmBuiltinTests
VmFalse             clrb
                    rts
VmTrue              ldb       #1
                    andcc     #$FE
                    rts
VmExternalTest      lbsr      VmPlatformTest
                    rts
VmSuccess           clrb
                    rts
VmInvalid           ldb       #E$BMode
                    stb       <vmerror
                    orcc      #1
VmReturn            rts
VmTestCounts        equ       *
                    use       shared/agi-test-table.asm
* Operand counts follow the existing CoCo command table.
VmArgumentCounts    equ       *
                    use       shared/agi-command-table.asm

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
