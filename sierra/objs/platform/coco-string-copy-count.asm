* Existing CoCo MemCopyNull 16-bit count in its stack-local frame.
BOUNDED_COCO_COUNT  macro
                    ldd       ,s
                    subd      #$0001
                    std       ,s
                    endm
