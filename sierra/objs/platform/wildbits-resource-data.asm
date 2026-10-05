* Private picture-resource state. Include once in the owning module's RMB area.
                    ifne      AGI_ASSET
resourcekind        rmb       1
resourcestored      rmb       2
                    endc
resourcebase        rmb       2
resourcepath        rmb       1
resourceopen        rmb       1
resourceerror       rmb       1
resourcevolume      rmb       1
resourcenumber      rmb       2
resourceoffset      rmb       4
resourcelength      rmb       2
resourcepointer     rmb       2
resourceremaining   rmb       2
resourcenameend     rmb       2
                    ifeq      AGI_ASSET
resourceentry       rmb       3
resourceheader      rmb       7
                    endc
                    ifgt      .-$100
                    error     Picture resource control fields must fit the private direct page
                    endc
resourcefilename    rmb       160
                    ifne      AGI_ASSET
resourceentry       rmb       3
resourceheader      rmb       7
                    endc
resourcecommands    rmb       8192
