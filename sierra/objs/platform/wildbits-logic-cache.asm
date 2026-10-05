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
