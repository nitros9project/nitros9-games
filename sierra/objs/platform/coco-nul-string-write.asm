* Direct destination U; STA preserves the source byte's zero flag.
NUL_COCO_WRITE      macro
                    sta       ,u+
                    endm
