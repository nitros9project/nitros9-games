* Room requests adapted from mnln NewRoomSetup. Resource reset runs only
* after the call stack unwinds. Keep the root logic and private menu labels.
RequestRoom         stb       <vmnewroom
                    lda       #1
                    sta       <vmroompending
                    clrb
                    rts
ApplyRoomChange     tst       <vmdepth
                    lbne      VmInvalid
                    inc       <vmroomchanges
                    lda       <vmroomchanges
                    cmpa      #64
                    lbhs      VmInvalid
                    lbsr      AssetUnmap
                    lbcs      RoomReturn
                    lda       #1
                    sta       <vmcacheindex
RoomFreeNext        ldb       <vmcacheindex
                    lbsr      VmSlotAddress
                    tst       1,x
                    beq       RoomFreeAdvance
                    stx       <vmslot
                    lbsr      VmRestoreAsset
                    inc       <assetowned
                    lbsr      AssetRelease
                    lbcs      RoomFreeFailure
                    ldx       <vmslot
                    clr       1,x
RoomFreeAdvance     inc       <vmcacheindex
                    ldb       <vmcacheindex
                    cmpb      #32
                    blo       RoomFreeNext
                    ldu       <resourcebase
                    leax      vmobjects,u
                    ldy       #64
RoomResetObject     lda       $26,x
                    anda      #$BE
                    ora       #$10
                    sta       $26,x
                    clra
                    clrb
                    sta       $25,x
                    std       $10,x
                    std       6,x
                    std       $16,x
                    inca
                    sta       $1E,x
                    sta       $1F,x
                    sta       $20,x
                    sta       1,x
                    sta       ,x
                    leax      43,x
                    leay      -1,y
                    bne       RoomResetObject
                    leax      vmvariables,u
                    lda       ,x
                    sta       1,x
                    ldb       <vmnewroom
                    stb       ,x
                    clr       4,x
                    clr       5,x
                    lda       #36
                    sta       <vmhorizon
                    lda       vmobjects+5,u
                    sta       16,x
* Place ego on the opposite edge of the room, retaining its view width.
                    lda       2,x
                    cmpa      #1
                    beq       RoomEnterTop
                    cmpa      #2
                    beq       RoomEnterRight
                    cmpa      #3
                    beq       RoomEnterBottom
                    cmpa      #4
                    bne       RoomEntryDone
                    lda       #160
                    suba      vmobjects+$1C,u
                    sta       vmobjects+3,u
                    bra       RoomEntryDone
RoomEnterTop        lda       #167
                    sta       vmobjects+4,u
                    bra       RoomEntryDone
RoomEnterRight      clr       vmobjects+3,u
                    bra       RoomEntryDone
RoomEnterBottom     lda       #37
                    sta       vmobjects+4,u
RoomEntryDone       clr       2,x
                    lda       #1
                    sta       vmflags+5,u
                    clr       <replayused
                    clr       <replayused+1
                    clr       <replaycheckpoint
                    clr       <replaycheckpoint+1
                    ldb       <vmnewroom
                    lbsr      VmLoadLogic
                    bcs       RoomReturn
                    clr       <vmcurrent
                    clrb
                    lbsr      VmSlotAddress
                    lbsr      VmRestoreAsset
                    ldd       10,x
                    std       <vmip
                    clr       <vmroompending
                    clrb
RoomReturn          rts
RoomFreeFailure     clr       <assetowned
                    rts
