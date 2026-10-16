* Immutable AGI pen geometry shared by both platform builds.
BinaryList          fdb       $8000
                    fdb       $4000
                    fdb       $2000
                    fdb       $1000
                    fdb       $0800
                    fdb       $0400
                    fdb       $0200
                    fdb       $0100
                    fdb       $0080
                    fdb       $0040
                    fdb       $0020
                    fdb       $0010
                    fdb       $0008
                    fdb       $0004
                    fdb       $0002
                    fdb       $0001

* circle_data[] (pic_render.c)
CircleData          fdb       $8000
                    fdb       $4000
                    fdb       $e000
                    fdb       $4000
                    fdb       $7000
                    fdb       $f800
                    fdb       $f800
                    fdb       $f800
                    fdb       $7000
                    fdb       $3800
                    fdb       $7c00
                    fdb       $fe00
                    fdb       $fe00
                    fdb       $fe00
                    fdb       $7c00
                    fdb       $3800
                    fdb       $1c00
                    fdb       $7f00
                    fdb       $ff80
                    fdb       $ff80
                    fdb       $ff80
                    fdb       $ff80
                    fdb       $ff80
                    fdb       $7f00
                    fdb       $1c00
                    fdb       $0e00
                    fdb       $3f80
                    fdb       $7fc0
                    fdb       $7fc0
                    fdb       $ffe0
                    fdb       $ffe0
                    fdb       $ffe0
                    fdb       $7fc0
                    fdb       $7fc0
                    fdb       $3f80
                    fdb       $1f00
                    fdb       $0e00
                    fdb       $0f80
                    fdb       $3fe0
                    fdb       $7ff0
                    fdb       $7ff0
                    fdb       $fff8
                    fdb       $fff8
                    fdb       $fff8
                    fdb       $fff8
                    fdb       $fff8
                    fdb       $7ff0
                    fdb       $7ff0
                    fdb       $3fe0
                    fdb       $0f80
                    fdb       $07c0
                    fdb       $1ff0
                    fdb       $3ff8
                    fdb       $7ffc
                    fdb       $7ffc
                    fdb       $fffe
                    fdb       $fffe
                    fdb       $fffe
                    fdb       $fffe
                    fdb       $fffe
                    fdb       $7ffc
                    fdb       $7ffc
                    fdb       $3ff8
                    fdb       $1ff0
                    fdb       $07c0

* circle_list[] (pic_render.c)
* this data is different in the file
* { 0, 1, 4, 9, 16, 25, 37, 50 }
* These run like a set of numbers**2 {0,1,2,3,4,5,~6,~7}
* ah ha these are multiples 2*(0,1,2,3,4,5,~6,~7)**2)

CircleList          fcb       $00,$00   0
                    fcb       $00,$02   2
                    fcb       $00,$08   8
                    fcb       $00,$12   18
                    fcb       $00,$20   32
                    fcb       $00,$32   50
                    fcb       $00,$4a   74
                    fcb       $00,$64   100
