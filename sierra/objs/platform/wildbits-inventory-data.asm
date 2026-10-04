* Process-private decrypted object file and mutable item rooms.
inventoryloaded     rmb       1
inventorylength     rmb       2
inventorycount      rmb       2
inventoryrooms      rmb       256
* Names exist only during loading/status; the decoder is idle then.
inventoryfile       equ       fillstack
inventorylist       equ       fillstack+3840
inventoryvisible    rmb       2
inventoryselected   rmb       2
inventorytop        rmb       2
inventoryrow        rmb       1
inventorykey        rmb       1
inventorynames      rmb       2
inventoryprevious   rmb       2
inventorypaint      rmb       1
