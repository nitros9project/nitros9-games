* Priority/direction assignment on a resolved 43-byte object record.
* Priority preloading is an ABI trait, preserving flags/read/write ordering.
* Parameters: record register and literal/variable source trait for priority;
* record register and loaded-value register for direction.
OBJECT_SET_PRIORITY macro
                    ifne      PRIORITY_PRELOADED
                    PRIORITY_VALIDATE
                    stb       <$24,\1
                    endc
                    lda       <$26,\1
                    ora       #4
                    sta       <$26,\1
                    ifeq      PRIORITY_PRELOADED
                    PRIORITY_READ \2
                    sta       <$24,\1
                    endc
                    endm
OBJECT_SET_DIRECTION macro
                    DIRECTION_READ
                    DIRECTION_VALIDATE
                    st\2      <$21,\1
                    DIRECTION_EGO_TEST \3
                    DIRECTION_EGO_STORE
                    endm
