* CoCo screen backend: monitor-select.
* Included in place; see ../../PORTABILITY.md for the current contract.

ConfigureMonitor
*  get current montype
*  GetStat Function Code $92
*          Allocates and maps high res screen
*          into application address space
* entry:
*       a -> path number
*       b -> function code $92 (SS.Montr)
*
* exit:
*       x -> monitor type
*
* error:
*       CC -> Carry set on error
*       b  -> error code (if any)
*
                    lda       #StdOut   $01 path number
                    ldb       #SS.Montr monitor type code (not listed for getstat $92
                    os9       I$GetStt  make the call
                    bcs       ConfigureMonitorRet
                    tfr       x,d       save in d appears he expects montype returned
                    lda       >RgbRequested
                    beq       UseOriginalMonitor
                    ldb       #RGB
UseOriginalMonitor  andb      #$01      mask out mono type only RGB or COMP
                    stb       >$0553    save that value off as display_type

                    clrb                success; global monitor mode is untouched

ConfigureMonitorRet rts
