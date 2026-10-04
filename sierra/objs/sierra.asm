********************************************************************
* sierra - Sierra AGI game setup module
*
* Edt/Rev  YYYY/MM/DD  Modified by
* Comment
* ------------------------------------------------------------------
*   0      2003/01/31  Paul W. Zibaila
* Disassembly of original distribution and merged in comments from
* disasm dated 1992.
*
*   1      2003/03/10  Boisy G. Pitre
* Monitor type bug now fixed.
*
*   2      2012/01/05  Robert Gault
* Converted raw reads of $FFA0-$FFAF to a routine that gets images
* from the system. Now works with 2 or 8Meg systems. Unfortunately
* it was necessary to make buffers within the code rather than data
* area because it was safer given data was shared with other modules.
*
* Simplified some other routines.
*
* Annotated by /annotate-asm (Claude Code) 2026-05-12:
*   - Renamed disassembled labels to meaningful names
*   - Added inline comments to every instruction
* Annotated by /annotate-asm (Claude Code) 2026-05-14:
*   - Renamed data-area variables (mtf173→MultitaskFlagCopy, scr174→HiResScrnNum, etc.)
*   - Fixed module description (removed KQ3-specific title — module is game-generic)
*   - Added ====== section headers throughout code body

* I/O path definitions
StdIn               equ       0
StdOut              equ       1
StdErr              equ       2

                    nam       sierra
                    ttl       Sierra AGI game setup module

                  IFP1
                    use       defsfile
                  ENDC

tylg                set       Prgrm+Objct
atrv                set       ReEnt+rev
rev                 set       $01
edition             set       2

                    mod       eom,name,tylg,atrv,start,size

                    org       0
DataAreaSize        rmb       2         stack ptr − $04FF = data area size
MmuBlk2Orig         rmb       1         original MMU block # mapped at $4000–$5FFF
MmuBlk3Orig         rmb       1         original MMU block # mapped at $6000–$7FFF
ScrStartAddr        rmb       2         hi-res screen start address (physical)
ScrEndAddr          rmb       2         hi-res screen end address
MmuSaveTmp          rmb       1         MMU block # scratch slot
MmuBlkSierra        rmb       1         MMU block # Sierra module occupies
MmuTask1Blk0        rmb       1         task-1 DAT slot 0 ($0000–$1FFF)
MmuTask1Blk1        rmb       1         task-1 DAT slot 1 ($2000–$3FFF)
MmuTask1Blk2        rmb       1         task-1 DAT slot 2 ($4000–$5FFF)
MmuTask1Blk3        rmb       1         task-1 DAT slot 3 ($6000–$7FFF)
MmuTask1Blk4        rmb       1         task-1 DAT slot 4 ($8000–$9FFF)
MmuTask1Blk5        rmb       1         task-1 DAT slot 5 ($A000–$BFFF)
MmuTask1Blk6        rmb       1         task-1 DAT slot 6 ($E000–$FFFF)
MmuInitFlag         rmb       3         MMU init flag (1 byte + 2 pad)
ScrStart2           rmb       2         second hi-res screen start reference
ScrEnd2             rmb       2         second hi-res screen end reference
ScrEndPad           rmb       4         pad after second screen addresses
BlkMapLow           rmb       2         low task-1 MMU block pair for mapping
BlkMapHigh          rmb       4         high task-1 MMU block pairs for mapping
BlockRef            rmb       2         block reference pair (2-byte value)
MnlnRemap           rmb       2         mnln remap value holder
ScrnRemap           rmb       2         scrn remap value holder
ShdwRemap           rmb       2         shdw remap value holder
CallerSp            rmb       2         saves stack pointer of caller to MmuSwitch
HiResBase           rmb       2         hi-res screen base address
EntryTable          rmb       16        MnLn entry vector table pointer + pad
TickCountHi         rmb       1         game tick counter high byte
TickCountLo         rmb       2         game tick counter low byte + pad
Reserved41          rmb       1         pad byte at $41
SierraPdBlk         rmb       1         MMU block # of Sierra's process descriptor
Sierra2ndBlk        rmb       2         ptr to Sierra's 2nd block in DAT image
PaletteFlag         rmb       1         flag after color table sets
ScrAddrHi           rmb       2         hi-res screen address high word
TickAccum           rmb       2         tick accumulator (20 ticks = 1 second)
IrqCountdown        rmb       5         VIRQ countdown byte + 4 pad
GameState4F         rmb       4         game state 4-byte field at $004F
InitParam53         rmb       2         game init word at $53 (init $06CE)
InitParam55         rmb       10        game init words at $55–$5E (init $06CE)
PathTable           rmb       163       module name/path table
GamePausedFlag      rmb       112       game paused flag + game data [$102–$171]
MultitaskFlagCopy   rmb       1         multitasking flag copied from startup parms
HiResScrnNum        rmb       1         allocated hi-res screen number
GameStateBuf        rmb       212       game state buffer [$175–$248]
GameTimerB3         rmb       1         32-bit game timer byte 3 (MSB)
GameTimerB2         rmb       1         32-bit game timer byte 2
GameTimerB1         rmb       1         32-bit game timer byte 1
GameTimerB0         rmb       497       32-bit game timer byte 0 (LSB) + pad
TimeOfDay           rmb       245       time-of-day: seconds, minutes, hours, days
VolHandleTable      rmb       16        vol_handle_table (pointer to file structures)
VolTablePad         rmb       15        pad after vol handle table
GivenPicPtr         rmb       2         given_pic_data (pointer)
DisplayType         rmb       1         display_type
GameDataBuf         rmb       154       general game data buffer
                    rmb       169       padding before SigIntercept/MmuSwitch slots
int5EE              rmb       107       slot for SigIntercept routine copy [$696–$700]
sub659              rmb       117       slot for MmuSwitch routine copy [$701–$775]
* Per-process setup state. Never put writable state in a linked module.
MultitaskFlag       rmb       1
RgbRequested        rmb       1
ProcMapReady        rmb       1
OwnProcessId        rmb       1         process ID used to locate our descriptor
OptionsChanged      rmb       1
SierraMmuBlk2       rmb       2
SierraMmuBlk3       rmb       2
EchoSave            rmb       1
EofSave             rmb       1
IntSave             rmb       1
QuitSave            rmb       1
                    rmb       1         reserved for ABI stability
ViDevAddr           rmb       2
ViPathNum           rmb       1
PrivateNext         rmb       1         next unused private engine block
PrivateLimit        rmb       1         exclusive end of /VI allocation
mmubuf              rmb       16
                    rmb       1         keep heap word pointers even
InstanceHeapBase    equ       .
gprbuf              equ       .         512-byte startup scratch; released before engine entry
u0xxx               rmb       $1FFF-.  keep the original 8K data allocation
size                equ       .
                    use       instance.d
                  IFNE        InstanceHeapBase-SierraHeapBase
                    error     private state / heap ABI mismatch
                  ENDC

* ====== Module Header ======
name                fcs       /sierra/
                    fcb       edition

* ====== Dispatch Table: Entry and Exit Vectors ======
start               equ       *
EntryDispatch       lbra      InitEntry branch to entry process params
ExitDispatch        lbra      ExitDispEntry agi_exit() branch to clean up routines




* ====== Static String Constants ======
* Text strings think this was probably an Info thing
CopyrightStr        fcc       'AGI (c) copyright 1988 SIERRA On-Line'
                    fcc       'CoCo3 version by Chris Iden'
                    fcb       $00
Infosz              equ       *-CopyrightStr


* Useage text string
UsageStr            fcc       'Usage: Sierra -Rgb -Multitasking'
                    fcb       C$CR
Usgsz               equ       *-UsageStr


* ====== InitEntry: Startup — Parse Command Line Arguments ======
InitEntry           tfr       s,d       save stack ptr / start of param ptr into d
*
                    subd      #$04FF    start of stack/end of data mem ptr
                    std       <DataAreaSize store this value in user var
                    pshs      x         preserve the command-line pointer
                    lbsr      InitDataArea initialize private state before parsing options
                    puls      x
                    bsr       ArgParseLoop branch to input processer routine

PostArgInit         lbsr      SetupModule initialize this instance
                    bcc       MainInit
                    pshs      b         preserve the startup error
                    lbsr      ShutdownFull release only this instance
                    puls      b
                    bra       ExitNow

MainInit            ldd       <DataAreaSize load the data pointer
                    beq       ExitNow   if it is zero we have a problem
*         ldd   >$FFA9     ??? MMU task 1 block 1 ???
                    lbsr      mmuini2   get MMU values $FFA8-$FFAF
                    ldd       >mmubuf+9 load task-1 MMU block entry (9th byte)
                    std       <MmuTask1Blk0 save the task 1 block one value
* No further descriptor snapshots occur after startup. Restore the heap's
* initial zero-fill before allowing the engine to allocate this scratch area.
                    ldx       #gprbuf
                    ldy       #P$Size/2
                    clra
                    clrb
ClearSetupScratch   std       ,x++
                    leay      -1,y
                    bne       ClearSetupScratch
                    lda       #$00      clear a to zero
                    sta       <MmuInitFlag save that value
                    ldx       <MnlnRemap set up to jump to mnln and go for it
                    jsr       sub659    code at MmuSwitch plays with mmu blocks
                    rts                 return after game exits via MmuSwitch

* Process any command line args
* See F$Fork description 8-15 for entry conditions

ArgParseLoop        lda       ,x+       get next char after name string
                    cmpa      #C$CR     is it a CR?
                    beq       ArgsDone  yes exit from routine
                    cmpa      #$2D      is it a dash '-
                    bne       ArgParseLoop not a dash go look again

                    lda       ,x+       was as dash get the next char
                    ora       #$20      apply mask to lower case
                    cmpa      #$72      is it a 'r ?
                    beq       HandleOptRgb yep go set up for RGB monitor
                    cmpa      #$6D      is it an 'm ?
                    beq       HandleOptMulti if so go store a flag and continue

*  We've found something other than Mm or Rr after a dash
*  write usage message and Exit program

                    lda       #StdOut   load path std out
                    leax      >UsageStr,pcr load address of message
                    ldy       #Usgsz    $0021  load the size of the message
                    os9       I$WritLn  write it
                    clrb                clear the error code (unneeded branch to ExitOk)
                    bra       ExitNow   and branch to exit!

* found a "-r"
HandleOptRgb        lda       #1
                    sta       >RgbRequested apply after screen ownership is acquired
                    bra       ArgParseLoop

* found an "-m"
HandleOptMulti      lda       #$01      we have found a -m and load a flag
                    sta       >MultitaskFlag save this instance's option
                    bra       ArgParseLoop check for next param

ArgsDone            rts                 return


* ====== ExitDispEntry: Clean Up and Exit ======
*  This is just a relay call to L0336
agi_exit
ExitDispEntry       lbsr      ShutdownFull call full shutdown sequence

ExitOk              clrb                clear error code (success)
ExitNow             os9       F$Exit    time to check out


* ====== Static Data: Color Tables, MMU Slots, and Module Name Strings ======
* same sequence of bytes at L454C in mnln

* Platform screen implementation, selected during assembly.
                    use       platform/screen-colors.asm

* Name strings of other modules to load.

ShdwModName         fcc       'Shdw'
                    fcb       C$CR

ScrnModName         fcc       'Scrn'
                    fcb       C$CR

MnlnModName         fcc       'MnLn'
                    fcb       C$CR




* ====== SetupModule / ShutdownFull: Setup and Shutdown Orchestration ======
* L011A called by PostArgInit
SetupModule         lbsr      CheckInstanceServices
                    bcs       SetupModuleRet
                    lbsr      mmuini1   get MMU values $FFA0-$FFA7
                    lbsr      SetupProcMap Change our process image to dupe block 0 to 1-2
CopySubroutines     lbsr      CopySubsToData copies two subs to data area so others can use them

                    lbsr      SetupVirq load intercept routine and open /VI and allocate Ram
                    bcs       SetupModuleRet

                    lbsr      LoadModules NMLoads the three other modules and sets up vals
                    bcs       SetupModuleRet

                    lbsr      SetupScreen go set up screens
SetupModuleRet      rts                 startup error is handled by InitEntry

* Require matching input/output terminals and the ownership-aware screen
* service. Reject old bootfiles before changing any device or MMU state.
CheckInstanceServices lda     #StdIn
                    ldb       #SS.DevNm
                    ldx       #gprbuf
                    os9       I$GetStt
                    bcs       InstanceServiceRet
                    lda       #StdOut
                    ldb       #SS.DevNm
                    ldx       #gprbuf+32
                    os9       I$GetStt
                    bcs       InstanceServiceRet
                    ldx       #gprbuf
                    ldy       #gprbuf+32
                    ldb       #32
InstanceNameLoop    lda       ,x+
                    cmpa      ,y+
                    bne       InstanceServiceBad
                    tsta
                    beq       InstanceNamesMatch
                    bmi       InstanceNamesMatch
                    decb
                    bne       InstanceNameLoop
InstanceServiceBad  comb
                    ldb       #E$IllArg
                    rts
InstanceNamesMatch  lda       #StdOut
                    ldb       #SS.AScrn
                    os9       I$GetStt  query the ownership-aware application-screen ABI
                    bcs       InstanceServiceRet
                    cmpx      #2
                    bcc       InstanceServiceOK
                    comb
                    ldb       #E$UnkSvc
InstanceServiceRet  rts
InstanceServiceOK   clrb
                    rts

* clean up and shut down
agi_shutdown
ShutdownFull        lbsr      RestoreScreen go deallocate hi res screens
CleanupMods
CleanupVirq         lbsr      CloseVirqPath Close VIRQ device
                    lbsr      RestoreMmu restore the MMU blocks
                    rts                 return to caller

* ====== InitDataArea: Clear and Initialize Sierra Data Area ======
* at this point DataAreaSize contains the value of s on entry minus $04FF
* which should be the size of our initialized data
* so we don't over write it but clear the rest of the data area

InitDataArea        ldx       #$0002    Init data area from 2-end with 0's
                    ldd       #$0000    zero value to fill data area
ClearLoop           std       ,x++      write zero word and advance pointer
                    cmpx      <DataAreaSize should have the value $04FF
                    bcs       ClearLoop appears this zeros out memory somewhere

* initialize some variables

                    ldd       #InstanceHeapBase start the heap after private setup state
                    std       <InitParam53 initialize game parameter at $53
                    std       <InitParam55 initialize game parameter at $55

                    lda       #$5C      load constant for game state init
                    sta       >$0101    store game state byte at $0101

                    lda       #$17      load constant for game state init
                    sta       >$01D7    store game state byte at $01D7

                    lda       #$0F      load constant for game state init
                    sta       >$023E    store game state byte at $023E

                    ldd       #$0000    zero value for game state word
                    std       <GameState4F clear game state field at $004F

* initialize more variables

                    lda       #$32      load game state constant
                    sta       >$0245    store game state byte at $0245

                    ldd       #$6000    This is the start of high res screen memory
                    std       <ScrAddrHi store hi-res screen start address

                    lda       #$15      load game state constant
                    sta       >$0247    store game state byte at $0247

                    lda       #$FF      Init 15 bytes at VolHandleTable to $FF
                    sta       $05EE
                    ldb       #$10
                    ldx       #$0531

* Fill routine-one byte pattern
* Entry: A=Byte to fill with
*        B=# bytes to fill
*        X=Start address of fill

FillBytes           sta       ,x+       store fill byte and advance pointer
                    decb                decrement byte count
                    bne       FillBytes loop until count reaches zero
                    rts                 return from FillBytes/InitDataArea

* Platform screen implementation, selected during assembly.
                    use       platform/monitor-select.asm

* ====== DisableKbdInt: Save and Suppress Keyboard Signals ======
*  Raw disassembly of followin code
*L01AF    orcc  #$50
*         ldx   #$0002
*         stx   <u0022
*         lda   >$FFAF
*         sta   <u0008
*         clr   >$FFA9
*         ldd   >$2050
*         anda  #$1F
*         addd  #$2043
*         std   <u0043
*         ldb   >$2050
*         andb  #$E0
*         lsrb
*         lsrb
*         lsrb
*         lsrb
*         lsrb
*         ldx   #$FFA0
*         lda   b,x
*         sta   <u0042
*         sta   >$FFA9
*         ldx   <u0043
*         ldd   -$01,x
*         std   >L0102,pcr
*         ldd   $01,x
*         std   >L0104,pcr
*         ldd   -$03,x
*         std   -$01,x
*         std   $01,x
*         tfr   b,a
*         std   >$FFA9
*         std   <u0002
*         andcc #$AF
*         rts

**********************************************************
* COMMENTS FROM CODE RECIEVED
* Change our process map:
*         Blocks 1-2 become duplicates of block 0 (data area...
*         changes actual MMU regs themselves &
*         changes them in our process descriptor
*
* NOTE: SHOULD CHANGE SO IT MAPS IN BLOCK 0 IN AN UNUSED BLOCK 1ST
*       TO GET PROCESS DESCRIPTOR DAT IMAGE FOR SIERRA.
*       THEN, CAN BUMP BLOCKS AROUND WITH THE ACTUAL BLOCK #
*       IN FULL 2 MB RANGE, INSTEAD OF JUST GIME 512K RANGE.

* Platform loader/memory implementation, selected during assembly.
                    use       platform/process-map.asm

* ====== CopySubsToData: Copy Runtime Subroutines to Data Area ======
* NOTE: 6809/6309 MOD: STUPID. DO LEAX, AND THEN PSHS X

* load first routine
*L01FA    leas  -2,s         Make 2 word buffer on stack
*         leax  >L054F,pc    Point to end of routine
*         stx   ,s           Save ptr
* Platform loader/memory implementation, selected during assembly.
                    use       platform/runtime-copy.asm

* ====== LoadModules: NMLoad and Link All Three AGI Modules ======
* Called from dispatch table at L0120
* The last op in the subroutine before this one
* was a puls a,b after a puhs x and a setsatt call for process+path to VIRQ

* Platform loader/memory implementation, selected during assembly.
                    use       platform/engine-load.asm

*****************************************************
*
*  Set up screens
*  SetStat Function Code $8B
*          Allocates and maps high res screen
*          into application address space
* entry:
*       a -> path number
*       b -> function code $8B (SS.AScrn)
*       x -> screen type
*            0 = 640 x 192 x 2 colors (16K)
*            1 = 320 x 192 x 4 colors (16K)
*            2 = 160 x 192 x 16 colors (16K)
*            3 = 640 x 192 x 4 colors (32K)
*            4 = 320 x 192 x 16 colors (32K)
*
* exit:
*       x -> application address space of screen
*       y -> screen number (1-3)
*
* error:
*       CC -> Carry set on error
*       b  -> error code (if any)
*
*  Call use VDGINT allocates high res graphics for use with screens
*  updated by the process, does not clear the screens only allocates
*  See OS-9 Technical Reference 8-142 for more details
*

* Platform screen implementation, selected during assembly.
                    use       platform/screen-setup.asm

*  Raw disassembly of following section
*L02E9    leas  <-$20,s
*         lda   #$00
*         ldb   #$00
*         leax  ,s
*         os9   I$GetStt
*         bcs   L0332
*         lda   >L0115,pcr
*         ldb   $04,x
*         sta   $04,x
*         stb   >L0115,pcr
*         lda   >L0116,pcr
*         ldb   $0C,x
*         sta   $0C,x
*         stb   >L0116,pcr
*         lda   >L0117,pcr
*         ldb   <$10,x
*         sta   <$10,x
*         stb   >L0117,pcr
*         lda   >L0118,pcr
*         ldb   <$11,x
*         sta   <$11,x
*         stb   >L0118,pcr
*         lda   #$00
*         ldb   #$00
*         os9   I$SetStt
*L0332    leas  <$20,s
*         rts

* Kills the echo, eof, int and quit signals
*  get current options packet
*  GetStat Function Code $00
*          Reads the options section of the path descriptor and
*          copies it into the 32 byte area pointed to by reg X`
* entry:
*       a -> path number
*       b -> function code $00 (SS.OPT)
*       x -> address to recieve status packet
*
* error:
*       CC -> Carry set on error
*       b  -> error code (if any)
*

* Platform screen implementation, selected during assembly.
                    use       platform/terminal-options.asm

* ====== RestoreScreen: Return to Text Screen, Free Hi-Res Screen ======
*  raw disassembly
*L0336    leas  -$02,s
*         tst   >$0174
*         beq   L036D
*         lbsr  L02E9
*         bcs   L036D
**         lda   #$1B
*         sta   ,s
*         lda   #$30
*         sta   $01,s
*         ldy   #$0002
*         lda   #$01
*         leax  ,s
*         os9   I$Write
*         bcs   L036D
*         ldb   #$8C
*         ldy   #$0000
*         os9   I$SetStt
*         clra
*         ldb   >$0174
*         tfr   d,y
*         lda   #$01
*         ldb   #$8D
*         os9   I$SetStt
*L036D    leas  $02,s
*         rts


*  Return the screen to default text sreen and its values
*  deallocate and free memory of high res screen created

* Platform screen implementation, selected during assembly.
                    use       platform/screen-restore.asm

* Templates are unlinked immediately after copying; no global unload at exit.
*L0388    orcc  #$50
*         lda   <u0042
*         sta   >$FFA9
*         ldx   <u0043
*         ldd   >L0104,pcr
*         std   $01,x
*         stb   >$FFAA
*         ldd   >L0102,pcr
*         std   -$01,x
*         stb   >$FFA9
*         andcc #$AF
*         clra
*         ldb   >L0119,pcr
*         andb  #$03
*         tfr   d,x
*         lda   #$01
*         ldb   #$92
*         os9   I$SetStt
*         rts
**
*L03B6    tfr   x,d
*         exg   a,b
*         lsrb
*         lsrb
*         lsrb
*         lsrb
*         lsrb
*         pshs  b
*         ldu   #$FFA8
*         lda   b,u
*         incb
*         andb  #$07
*         ldb   b,u
*         tfr   d,u
*         puls  a
*         rts


* ====== RestoreMmu: Restore MMU to Pre-Game State ======
* Restore original MMU block numbers
* Platform loader/memory implementation, selected during assembly.
                    use       platform/map-restore.asm

* ====== TwiddleAddr: Map Logical Address to Physical Block Pair ======
* twiddles address
* called with value to be twiddled in X
* returns block # in a
*         ?????   in u
* Platform loader/memory implementation, selected during assembly.
                    use       platform/address-blocks.asm

*************************************************************
*  Called from  within sub at L0229
*  entry:
*	x -> is loaded with the address of the name string to load
*       u -> contains some arbitrary value
*

* Link an immutable template, copy its complete occupied 8K pages to
* this process's /VI allocation, then balance exactly our own link.
* U on return remains the logical template header address; LoadModules
* uses its offset when constructing the relocated entry-vector address.
* Platform loader/memory implementation, selected during assembly.
                    use       platform/private-load.asm

ViDevPath           fcc       '/VI'
ViDevPathEnd        fcb       C$CR

**************************************************************
*
*   subroutine entry is L0419
*   sets up Sig Intercept
*   verifies /VI device is loaded links to it
*   and allocates ram for it
*   called from dispatch table around L0120


* Set signal intercept trap
*  entry:
*        x -> address of intercept routine
*        u -> starting adress of routines memory area
*  exit:
*       Signals sent to the process cause the intercept to be
*       called instead of the process being killed

* Platform loader/memory implementation, selected during assembly.
                    use       platform/private-allocate.asm

* ====== SigIntercept / SigHandlerCore: VIRQ Timer and Game Clock ======
* Signal Intercept processing gets copied to int5EE mem slot
SigIntercept        cmpb      #$80      b gets the signal code if not $80 ignore
                    bne       SigInterceptRet $80 is user defined
                    tfr       u,d       copy U (data area ptr) into D
                    tfr       a,dp      set direct page register to data area base
                    dec       <IrqCountdown decrement IRQ countdown counter
                    bne       SigInterceptRet not yet time — return
                    bsr       SigHandlerCore call timer and game-clock handler
                    lda       #$03      reload countdown to 3 intervals
                    sta       <IrqCountdown reset IRQ countdown
SigInterceptRet     rti                 return from interrupt

SigHandlerCore      inc       >GameTimerB0,u increment low byte of 32-bit game timer
                    bne       TimerUpdate no carry — skip upper bytes
                    inc       >GameTimerB1,u propagate carry to byte 1
                    bne       TimerUpdate no carry — skip upper bytes
                    inc       >GameTimerB2,u propagate carry to byte 2
                    bne       TimerUpdate no carry — skip upper bytes
                    inc       >GameTimerB3,u propagate carry to high byte
TimerUpdate         tst       >GamePausedFlag,u check if game is paused
                    bne       TimerRet  paused — skip tick accumulation
                    inc       <TickCountLo increment low tick counter
                    bne       TickUpdate no overflow — process tick accumulator
                    inc       <TickCountHi increment high tick counter on overflow
TickUpdate          ldd       <TickAccum load tick accumulator
                    addd      #$0001    add one tick
                    std       <TickAccum save updated accumulator
                    cmpd      #$0014    check if 20 ticks elapsed (one second)
                    bcs       TimerRet  not yet — return
                    subd      #$0014    subtract 20 (one second)
                    std       <TickAccum save remainder
                    ldd       #$003C    60 = max value for seconds and minutes
                    leax      >TimeOfDay,u point to time-of-day seconds field
                    inc       ,x        increment seconds
                    cmpb      ,x        compare seconds with 60
                    bhi       TimerRet  less than 60 — done
                    sta       ,x+       reset seconds to 0, advance to minutes
                    inc       ,x        increment minutes
                    cmpb      ,x        compare minutes with 60
                    bhi       TimerRet  less than 60 — done
                    sta       ,x+       reset minutes to 0, advance to hours
                    inc       ,x        increment hours
                    ldb       #$18      24 = max hours per day
                    cmpb      ,x        compare hours with 24
                    bhi       TimerRet  less than 24 — done
                    sta       ,x+       reset hours to 0, advance to days
                    inc       ,x        increment day counter
TimerRet            rts                 return from timer handler

* ====== CloseVirqPath: Release VIRQ Device ======
* deallocates the VIRQ device
* Platform loader/memory implementation, selected during assembly.
                    use       platform/private-release.asm

* ====== MmuSwitch: Switch Between Module MMU Address Spaces ======
*  Twiddles with MMU blocks for us
*  This sub gets copied into $0659 and executed there from this and
*  the other modules this one loads (sub659)
*
*  s and x loaded by calling routine

* Platform mapping implementation; retained at its original location.
                    use       platform/engine-switch.asm

MmuSwitchEnd        fcb       $00,$00,$00,$00,$00,$00,$00,$00 ........
SierraNameStr       fcb       $73,$69,$65,$72,$72,$61,$00 sierra.

* ====== mmuini1 / mmuini2: Snapshot Task MMU Block Tables ======
* New routines so we don't have raw reads of the MMU bytes. RG
* Get $FFA0-$FFA7
* PID 1 belongs to SysGo, not the kernel. Snapshot the real D.SysDAT
* through system block 0, borrowing the $2000 slot with interrupts masked.
* First capture our own image so the borrowed slot can be restored.
* Platform mapping implementation; retained at its original location.
                    use       platform/map-snapshot.asm

                    emod
eom                 equ       *
                    end
