* Existing CoCo storage geometry. Equates emit no bytes.
* These constants name a fixed ABI; changing them alone is not a port.
CocoMapBlockBytes   equ       $2000
CocoCopyWindow      equ       $4000
CocoCopyWords       equ       CocoMapBlockBytes/2
CocoFrameWidth      equ       320
CocoFrameHeight     equ       192
CocoPixelsPerByte   equ       2
CocoFrameStride     equ       CocoFrameWidth/CocoPixelsPerByte
CocoFrameBytes      equ       CocoFrameStride*CocoFrameHeight
CocoFrameBase       equ       $6000
CocoFrameEnd        equ       CocoFrameBase+CocoFrameBytes
CocoFramePairBytes  equ       2*CocoMapBlockBytes
