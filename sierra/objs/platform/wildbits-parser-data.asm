* Persistent submitted words must survive resource loads in the logic cycle.
parserline          rmb       40
parserword          rmb       40
parserids           rmb       40
parsercount         rmb       1
parserlength        rmb       1
parserposition      rmb       1
parserwordlength    rmb       1
parserbestlength    rmb       1
parserbestid        rmb       2
parserreadindex     rmb       2
parserreadlength    rmb       2
parserid            rmb       2
parsercharacter     rmb       1
parserseen          rmb       1
parserstart         rmb       2
parserlastline      rmb       40
parseroffsets       rmb       20
parserlengths       rmb       20
formatdepth         rmb       1
dialogactive        rmb       1
dialogwordstart     rmb       1
dialoginputmode     rmb       1
terminalchanged     rmb       1
terminalecho        rmb       1
terminaleof         rmb       1
terminalquit        rmb       1
* The old decoded-ID scratch is now the selected encoded entry offset.
dictionaryentry     equ       parserid
* Stream cache base adds two bytes, still within three private pages.
dictionarycachebase rmb       2
* Temporary offsets occupy idle formatter output only during ParserParse.
dictionarygroups    equ       fillstack+2048
