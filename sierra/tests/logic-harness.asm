                    use       platform/wildbits-defsfile
resourcebase        rmb       2
                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_LOGIC_DATA
                    use platform/wildbits-logic.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_ROOM_DATA
                    use platform/wildbits-memory-resources.asm
scriptbase          rmb       2
vmvariables         rmb       256
vmflags             rmb       256
vmarguments         rmb       255
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /vmtest/
start               stu       <resourcebase
                    lbsr      ExecuteLogic
finish              nop
                    bra       finish
VmFetchByte         pshs      x
                    ldx       <vmip
                    cmpx      <vmend
                    bhs       VmFetchError
                    tfr       x,d
                    addd      <scriptbase
                    tfr       d,x
                    ldb       ,x
                    ldx       <vmip
                    leax      1,x
                    stx       <vmip
                    puls      x
                    andcc     #$FE
                    rts
VmFetchError        puls      x
                    ldb       #E$EOF
                    orcc      #1
                    rts
VmPlatformCommand  ldb       #E$UnkSvc
                    orcc      #1
                    rts
VmPlatformTest      bra       VmPlatformCommand
                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_LOGIC_CODE
                    use platform/wildbits-logic.asm
                    emod
eom                 equ       *
