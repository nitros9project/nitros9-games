* Game commands are adapted here in small groups. Unsupported behavior
* remains an explicit error until the corresponding component is ported.
VmPlatformCommand  ldb       <vmopcode
                    cmpb      #20
                    beq       VmCommandLoadLogic
                    cmpb      #21
                    beq       VmCommandLoadLogicVariable
                    cmpb      #22
                    beq       VmCommandCallLogic
                    cmpb      #23
                    beq       VmCommandCallLogicVariable
                    cmpb      #145
                    beq       VmCommandScanStart
                    cmpb      #146
                    beq       VmCommandScanReset
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
VmPlatformTest      bra       VmPlatformUnsupported
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
