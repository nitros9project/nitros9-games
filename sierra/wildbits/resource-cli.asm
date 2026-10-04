* Shared probe argument/output body. Owning module supplies state and help.
start               stu       <resourcebase
                    clr       <resourceopen
                    ifne      DECODE_PICTURE
                    clr       <pictureowned
                    clr       <picturemapped
                    clr       <decodeerror
                    pshs      x
                    leax      DecodeIntercept,pcr
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
                    lbsr      LoadPicture
                    bcs       Exit
                    ifne      DECODE_PICTURE
                    lbsr      DecodeLines
                    bcs       Exit
                    lbsr      PictureWrite
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
                    ifne      DECODE_PICTURE
                    stb       <pictureexiterror
                    lbsr      PictureRelease
                    bcc       PictureExitResult
                    tst       <pictureexiterror
                    bne       PictureExitRetry
                    stb       <pictureexiterror
PictureExitRetry    lbsr      PictureRelease
PictureExitResult   ldb       <pictureexiterror
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
