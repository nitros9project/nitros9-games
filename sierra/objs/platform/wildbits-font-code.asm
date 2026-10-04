* Load the canonical font from the execution directory once per process.
* Keeping immutable font bytes out of the program avoids an extra code block.
GameFontLoad        leax      GameFontName,pcr
                    lda       #READ.+EXEC.
                    os9       I$Open
                    lbcs      ResourceFailed
                    sta       <resourcepath
                    inc       <resourceopen
                    ldu       <resourcebase
                    leax      gamefont,u
                    ldy       #1024
                    lbsr      ResourceReadExact
                    lbcs      ResourceFailed
* Reject trailing bytes as well as short fonts.
                    ldu       <resourcebase
                    leax      picturestage,u
                    ldy       #1
                    lda       <resourcepath
                    os9       I$Read
                    lbcc      ResourceInvalid
                    cmpb      #E$EOF
                    lbne      ResourceFailed
                    lbsr      ResourceClose
                    lbcs      ResourceFailed
                    clrb
                    rts
GameFontName        fcc       /wbfont/
                    fcb       C$CR
