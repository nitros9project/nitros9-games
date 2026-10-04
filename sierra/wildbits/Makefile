NITROS9DIR ?= $(abspath ../../../nitros9)
LWASM ?= lwasm
AFLAGS = --6809 --format=os9 --pragma=pcaspcr,nosymbolcase,condundefzero \
	-I. -I$(NITROS9DIR)/defs

.PHONY: all budget clean
all: wbpic wbres wbdecode wbrun wbasset wbexec wbgame budget
wbpic: wbpic.asm presentation.d presentation-data.asm presentation-buffers.asm presentation-helpers.asm presentation-palette.asm defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbpic.list --symbols -o $@ $<
wbres: wbres.asm resource-cli.asm resource-data.asm resource-code.asm defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbres.list --map=wbres.map --symbols -o $@ $<
wbdecode: wbdecode.asm decoder-data.asm decoder-code.asm decoder-lines.asm decoder-fill.asm decoder-pen.asm picture-memory.asm resource-cli.asm resource-data.asm resource-code.asm defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbdecode.list --map=wbdecode.map --symbols -o $@ $<
wbrun: wbrun.asm decoder-data.asm decoder-code.asm decoder-lines.asm decoder-fill.asm decoder-pen.asm picture-memory.asm resource-cli.asm resource-data.asm resource-code.asm presentation.d presentation-data.asm presentation-buffers.asm presentation-code.asm presentation-helpers.asm presentation-palette.asm defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbrun.list --map=wbrun.map --symbols -o $@ $<
wbasset: wbasset.asm asset-data.asm asset-code.asm asset-write.asm lzw-data.asm lzw-code.asm resource-cli.asm resource-data.asm resource-code.asm defsfile
	$(LWASM) $(AFLAGS) --list=wbasset.list --map=wbasset.map --symbols -o $@ $<
wbexec: wbexec.asm asset-data.asm asset-code.asm lzw-data.asm lzw-code.asm logic-data.asm logic-code.asm logic-fetch.asm logic-platform.asm logic-cache.asm message-data.asm message-code.asm replay-data.asm replay-code.asm object-code.asm menu-data.asm menu-code.asm room-data.asm room-code.asm view-data.asm view-code.asm screen-data.asm screen-code.asm input-data.asm input-code.asm string-code.asm resource-cli.asm resource-data.asm resource-code.asm defsfile
	$(LWASM) $(AFLAGS) --list=wbexec.list --map=wbexec.map --symbols -o $@ $<
wbgame: wbgame.asm ../objs/font-data.asm $(wildcard *-code.asm *-data.asm) decoder-lines.asm decoder-fill.asm decoder-pen.asm picture-memory.asm resource-cli.asm resource-code.asm resource-data.asm presentation.d presentation-buffers.asm presentation-helpers.asm presentation-palette.asm defsfile
	$(LWASM) $(AFLAGS) --list=wbgame.list --map=wbgame.map --symbols -o $@ $<
budget: wbpic wbres wbdecode wbrun wbasset wbexec wbgame
	@python3 -c 'from pathlib import Path; n=Path("wbpic").stat().st_size; assert n <= 40192, n; print("wbpic module: %d / 40192 bytes; process data: 8192 bytes; one mapping window" % n)'
	@python3 -c 'from pathlib import Path; b=Path("wbdecode").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(8-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbdecode probe: %d / %d code bytes; private data: %d bytes; one mapping window; four owned picture blocks" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbrun").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(8-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbrun integration: %d / %d code bytes; private data: %d bytes; sequential source/frame mapping" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbasset").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(8-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbasset: %d / %d code bytes; private data: %d bytes; one mapping window" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbexec").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(8-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbexec: %d / %d code bytes; private data: %d bytes; one mapping window" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbgame").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(8-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbgame: %d / %d code bytes; private data: %d bytes; sequential resource/picture/frame mapping" % (len(b),limit,data))'
clean:
	rm -f wbgame wbgame.list wbgame.map
	rm -f wbexec wbexec.list wbexec.map
	rm -f wbasset wbasset.list wbasset.map
	rm -f wbpic wbpic.list wbpic.map wbres wbres.list wbres.map
	rm -f wbdecode wbdecode.list wbdecode.map wbrun wbrun.list wbrun.map

.PHONY: fixture check
fixture:
	python3 make_picture_fixture.py test-picture.bin
check: all
	python3 ../tests/check_wbgame.py
	python3 ../tests/check_wbexec.py
	python3 ../tests/check_logic.py
	python3 ../tests/check_wbasset.py
	python3 ../tests/check_lzw.py
	python3 ../tests/test_picture_resource.py
	python3 ../tests/check_wbres.py
	python3 ../tests/check_wbdecode.py
	python3 ../tests/check_wbpic.py

GAME ?= ../kingsquest1
PICTURE ?= 1
.PHONY: reference
reference:
	python3 export_picture.py $(GAME) $(PICTURE) reference-picture.bin \
		--assembler "$(LWASM)" --defs "$(NITROS9DIR)/defs"
