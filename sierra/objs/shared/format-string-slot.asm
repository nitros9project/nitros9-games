* Resolve a 40-byte AGI string slot, then expand its contents. The caller
* supplies B=index (or an adapter which parses it), validation and storage.
* CoCo recursively formats a resolved slot; native emits its literal bytes.
FormatStringSlot    FORMAT_STRING_PREPARE
                    lda       #40
                    mul
                    FORMAT_STRING_ADDRESS
                    FORMAT_STRING_EXPAND
