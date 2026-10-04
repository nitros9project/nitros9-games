NITROS9DIR ?= $(abspath ../../../nitros9)
LWASM ?= lwasm
AFLAGS = --6809 --format=os9 --pragma=pcaspcr,nosymbolcase,condundefzero \
	-I. -I$(NITROS9DIR)/defs

.PHONY: all budget clean
all: wbpic wbres budget
wbpic: wbpic.asm defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbpic.list --symbols -o $@ $<
wbres: wbres.asm resource-data.asm resource-code.asm defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbres.list --map=wbres.map --symbols -o $@ $<
budget: wbpic
	@python3 -c 'from pathlib import Path; n=Path("wbpic").stat().st_size; assert n <= 40192, n; print("wbpic module: %d / 40192 bytes; process data: 8192 bytes; one mapping window" % n)'
clean:
	rm -f wbpic wbpic.list wbpic.map wbres wbres.list wbres.map

.PHONY: fixture check
fixture:
	python3 make_picture_fixture.py test-picture.bin
check: all
	python3 ../tests/test_picture_resource.py
	python3 ../tests/check_wbres.py
	python3 ../tests/check_wbpic.py

GAME ?= ../kingsquest1
PICTURE ?= 1
.PHONY: reference
reference:
	python3 export_picture.py $(GAME) $(PICTURE) reference-picture.bin \
		--assembler "$(LWASM)" --defs "$(NITROS9DIR)/defs"
