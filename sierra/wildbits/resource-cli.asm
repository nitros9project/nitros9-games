* Shared probe argument/output body. Owning module supplies state and help.
start               stu       <resourcebase
                    clr       <resourceopen
                    ifne      AGI_ASSET
                    clr       <assetowned
                    clr       <assetmapped
                    clr       <asseterror
                    clr       <resourcekind
                    ifne      AGI_VM
                    pshs      x
                    lbsr      VmClearCache
                    puls      x
                    endc
                    pshs      x
                    leax      AssetIntercept,pcr
                    os9       F$Icpt
                    puls      x
                    lbcs      Exit
                    endc
                    ifne      DECODE_PICTURE
                    clr       <pictureowned
                    clr       <picturemapped
                    clr       <decodeerror
                    pshs      x
                    ifne      PRESENT_PICTURE
                    lbsr      PresentationInitialize
                    leax      intercept,pcr
                    else
                    leax      DecodeIntercept,pcr
                    endc
                    os9       F$Icpt
                    lbcs      Exit
                    puls      x
                    endc
                    lbsr      SkipSpaces
                    stx       <argdirectory
FindNumber          lda       ,x+
                    cmpa      #C$CR
                    lbeq      ArgumentsBad
                    cmpa      #C$SPAC
                    bne       FindNumber
                    lbsr      SkipSpaces
                    clr       <argnumber
                    clr       <argnumber+1
                    lda       ,x
                    cmpa      #'0
                    lblo      ArgumentsBad
                    cmpa      #'9
                    lbhi      ArgumentsBad
NumberDigit         lda       ,x+
                    cmpa      #'0
                    blo       NumberEnd
                    cmpa      #'9
                    bhi       NumberEnd
                    suba      #'0
                    sta       <argdigit
                    ldd       <argnumber
                    lda       #10
                    mul
                    addb      <argdigit
                    adca      #0
                    cmpd      #255
                    lbhi      ArgumentsBad
                    std       <argnumber
                    bra       NumberDigit
NumberEnd           cmpa      #C$CR
                    beq       LoadResource
                    cmpa      #C$SPAC
                    lbne      ArgumentsBad
                    lbsr      SkipSpaces
                    lda       ,x
                    cmpa      #C$CR
                    lbne      ArgumentsBad
LoadResource        ldx       <argdirectory
                    ldy       <argnumber
                    ldu       <resourcebase
                    ifne      AGI_ASSET
                    lbsr      LoadAsset
                    bcs       Exit
                    ifne      AGI_VM
                    lbsr      StartLogic
                    bcs       Exit
                    ldu       <resourcebase
                    leax      vmvariables,u
                    ldy       #512
                    stx       <resourcepointer
                    sty       <resourceremaining
                    lbra      WriteMore
                    else
                    lbsr      AssetWrite
                    endc
                    bra       Exit
                    else
                    lbsr      LoadPicture
                    bcs       Exit
                    endc
                    ifne      DECODE_PICTURE
                    lbsr      DecodeLines
                    bcs       Exit
                    ifne      PRESENT_PICTURE
                    lbsr      PresentPicture
                    else
                    lbsr      PictureWrite
                    endc
                    bra       Exit
                    endc
                    stx       <resourcepointer
                    sty       <resourceremaining
WriteMore           lda       #1
                    ldx       <resourcepointer
                    ldy       <resourceremaining
                    os9       I$Write
                    bcs       Exit
                    cmpy      #0
                    beq       WriteBad
                    cmpy      <resourceremaining
                    bhi       WriteBad
                    tfr       y,d
                    addd      <resourcepointer
                    std       <resourcepointer
                    ldd       <resourceremaining
                    pshs      y
                    subd      ,s++
                    std       <resourceremaining
                    bne       WriteMore
                    clrb
Exit                equ       *
                    ifne      AGI_ASSET
                    stb       <assetexiterror
                    ifne      AGI_VM
                    lbsr      VmReleaseResources
                    else
                    lbsr      AssetRelease
                    endc
                    bcc       AssetExitDone
                    tst       <assetexiterror
                    bne       AssetExitRetry
                    stb       <assetexiterror
AssetExitRetry      lbsr      AssetRelease
AssetExitDone       ldb       <assetexiterror
                    endc
                    ifne      DECODE_PICTURE
                    stb       <pictureexiterror
                    lbsr      PictureRelease
                    bcc       PictureExitResult
                    tst       <pictureexiterror
                    bne       PictureExitRetry
                    stb       <pictureexiterror
PictureExitRetry    lbsr      PictureRelease
PictureExitResult   equ       *
                    ifne      PRESENT_PICTURE
                    lbsr      PresentationRelease
                    bcc       PresentationExitResult
                    tst       <pictureexiterror
                    bne       PresentationExitResult
                    stb       <pictureexiterror
PresentationExitResult equ    *
                    endc
                    ldb       <pictureexiterror
                    endc
                    os9       F$Exit
WriteBad            ldb       #E$BMode
                    bra       Exit
ArgumentsBad        leax      help,pcr
                    ldy       #80
                    lda       #2
                    os9       I$WritLn
                    ldb       #E$IllArg
                    bra       Exit
SkipSpaces          lda       ,x+
                    cmpa      #C$SPAC
                    beq       SkipSpaces
                    leax      -1,x
                    rts
