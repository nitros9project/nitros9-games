* Logical AGI dimensions, independent of the presentation pixel format.
AgiPictureWidth     equ       160
AgiPictureHeight    equ       168
AgiPicturePixels    equ       AgiPictureWidth*AgiPictureHeight

* Platform storage geometry is selected at assembly time.
                    ifne      WILDBITS
                    error     Wild Bits buffer layout is not implemented
                    else
                    use       platform/coco-buffer-layout.d
                    endc
