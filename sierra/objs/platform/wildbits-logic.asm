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
                    lbsr      VmStoreAsset
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
                    lbsr      VmSlotAddress
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
                    lbsr      VmSlotAddress
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
VmDiscardFailed     clr       <assetowned
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
                    lbcs      VmNativeReturn
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
                    lbra      VmRunRoot
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
                    lsra
                    lsra
                    lsra
                    lsra
                    lsra
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
VmPlatformCommand  ldb       <vmopcode
                    ifne      GAME_PRESENTATION
                    cmpb      #161
                    lbeq      GameMenuInput
                    cmpb      #40
                    lbeq      GameReposition
                    cmpb      #147
                    lbeq      GameReposition
                    cmpb      #148
                    lbeq      GameReposition
                    cmpb      #130
                    lbeq      GameRandomCommand
                    cmpb      #165
                    blo       VmNotGameMath
                    cmpb      #168
                    lbls      GameMathCommand
VmNotGameMath       cmpb      #124
                    lbeq      InventoryStatus
                    cmpb      #92
                    blo       VmNotInventoryCommand
                    cmpb      #97
                    lbls      InventoryCommand
VmNotInventoryCommand
                    cmpb      #83
                    lbeq      GameFollowCommand
                    cmpb      #84
                    lbeq      GameWanderCommand
                    cmpb      #99
                    lbeq      GameSoundCommand
                    cmpb      #100
                    lbeq      GameSoundCommand
                    cmpb      #90
                    lbeq      GameBlockCommand
                    cmpb      #91
                    lbeq      GameBlockCommand
                    cmpb      #81
                    lbeq      GameMoveCommand
                    cmpb      #82
                    lbeq      GameMoveCommand
                    cmpb      #105
                    lbeq      GameClearLines
                    cmpb      #103
                    lbeq      GameDisplayCommand
                    cmpb      #104
                    lbeq      GameDisplayCommand
                    cmpb      #134
                    lbeq      GameQuitCommand
                    cmpb      #136
                    lbeq      GamePauseCommand
                    cmpb      #35
                    lbeq      GameObjectVisibility
                    cmpb      #36
                    lbeq      GameObjectVisibility
                    cmpb      #24
                    lbeq      GameLoadPicture
                    cmpb      #25
                    lbeq      GameDrawPicture
                    cmpb      #26
                    lbeq      GameShowPicture
                    cmpb      #27
                    lbeq      GameDiscardPicture
                    endc
                    cmpb      #108
                    lbeq      ScreenCommand
                    cmpb      #109
                    lbeq      ScreenCommand
                    cmpb      #111
                    lbeq      ScreenCommand
                    cmpb      #112
                    lbeq      ScreenCommand
                    cmpb      #113
                    lbeq      ScreenCommand
                    cmpb      #119
                    lbeq      ScreenCommand
                    cmpb      #120
                    lbeq      ScreenCommand
                    cmpb      #121
                    lbeq      SetKeyCommand
                    ifne      GAME_PRESENTATION
                    cmpb      #115
                    lbeq      GameGetInput
                    cmpb      #118
                    lbeq      GameGetInput
                    cmpb      #116
                    lbeq      GameWordToString
                    cmpb      #101
                    lbeq      GamePrintCommand
                    cmpb      #102
                    lbeq      GamePrintCommand
                    cmpb      #117
                    lbeq      ParserCommand
                    endc
                    cmpb      #114
                    lbeq      SetStringCommand
                    cmpb      #18
                    lbeq      VmCommandNewRoom
                    cmpb      #19
                    lbeq      VmCommandNewRoomVariable
                    cmpb      #156
                    blo       VmNotMenuCommand
                    cmpb      #160
                    lbls      MenuCommand
VmNotMenuCommand    cmpb      #61
                    blo       VmNotTerrainCommand
                    cmpb      #68
                    lbls      ObjectFlagCommand
VmNotTerrainCommand cmpb      #69
                    lbeq      ObjectDistanceCommand
                    cmpb      #70
                    blo       VmNotCycleCommand
                    cmpb      #80
                    lbls      ObjectCycleCommand
VmNotCycleCommand   cmpb      #85
                    lbeq      ObjectCycleCommand
                    cmpb      #131
                    lbeq      VmProgramControl
                    cmpb      #132
                    lbeq      VmSetPlayerControl
                    cmpb      #88
                    lbeq      ObjectFlagCommand
                    cmpb      #89
                    lbeq      ObjectFlagCommand
                    cmpb      #41
                    blo       VmNotViewSelection
                    cmpb      #44
                    lbls      ViewCommand
                    cmpb      #47
                    blo       VmNotViewSelection
                    cmpb      #53
                    lbls      ViewCommand
VmNotViewSelection  cmpb      #33
                    lbeq      ObjectCommand
                    cmpb      #34
                    lbeq      ObjectCommand
                    cmpb      #37
                    blo       VmNotObjectPosition
                    cmpb      #39
                    lbls      ObjectCommand
VmNotObjectPosition cmpb      #45
                    lbeq      ObjectCommand
                    cmpb      #46
                    lbeq      ObjectCommand
                    cmpb      #54
                    blo       VmNotObjectPriority
                    cmpb      #57
                    lbls      ObjectCommand
VmNotObjectPriority cmpb      #86
                    lbeq      ObjectCommand
                    cmpb      #87
                    lbeq      ObjectCommand
                    cmpb      #142
                    lbeq      ReplayInitialize
                    cmpb      #171
                    lbeq      ReplaySaveCheckpoint
                    cmpb      #172
                    lbeq      ReplayRestore
                    cmpb      #30
                    lbeq      VmCommandLoadView
                    cmpb      #31
                    lbeq      VmCommandLoadViewVariable
                    cmpb      #32
                    lbeq      VmCommandDiscardView
                    cmpb      #153
                    lbeq      VmCommandDiscardViewVariable
                    cmpb      #98
                    lbeq      VmCommandLoadSound
                    cmpb      #20
                    lbeq      VmCommandLoadLogic
                    cmpb      #21
                    lbeq      VmCommandLoadLogicVariable
                    cmpb      #22
                    lbeq      VmCommandCallLogic
                    cmpb      #23
                    lbeq      VmCommandCallLogicVariable
                    cmpb      #145
                    lbeq      VmCommandScanStart
                    cmpb      #146
                    lbeq      VmCommandScanReset
                    cmpb      #143
                    lbne      VmPlatformUnsupported
                    ldu       <resourcebase
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
                    lbra      VmPlatformUnsupported
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
VmCommandLoadLogicVariable lbsr VmResolveLogicArgument
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
VmCommandCallLogicVariable lbsr VmResolveLogicArgument
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
VmCommandLoadViewVariable lbsr VmResolveLogicArgument
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
VmCommandDiscardViewVariable lbsr VmResolveLogicArgument
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
                    error Unknown platform feature section
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
