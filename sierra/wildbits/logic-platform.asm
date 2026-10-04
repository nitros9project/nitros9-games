* Game commands are adapted here in small groups. Unsupported behavior
* remains an explicit error until the corresponding component is ported.
VmPlatformCommand  ldb       <vmopcode
                    ifne      GAME_PRESENTATION
                    cmpb      #124
                    lbeq      InventoryStatus
                    cmpb      #92
                    blo       VmNotInventoryCommand
                    cmpb      #97
                    lbls      InventoryCommand
VmNotInventoryCommand
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
