* Persistent text cells survive picture refreshes; zero means no overlay.
textcharacters      rmb      1000
* High nibble is logical foreground, low nibble logical background (0..15).
textcolors          rmb      1000
textpointer         rmb      2
textindex           rmb      2
textend             rmb      2
textfontpointer     rmb      2
textrow             rmb      1
textcolumn          rmb      1
textglyphrow        rmb      1
textglyphpixel      rmb      1
textbits            rmb      1
textcolor           rmb      1
textforeground      rmb      1
textbackground      rmb      1

* Inclusive occupied span for the scanline text renderer.
textfirstcolumn     rmb      1
textlastcolumn      rmb      1
