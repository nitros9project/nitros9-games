NITROS9DIR ?= $(abspath ../../../nitros9)
LWASM ?= lwasm
AFLAGS = --6809 --format=os9 --pragma=pcaspcr,nosymbolcase,condundefzero \
	-I. -I$(NITROS9DIR)/defs

.PHONY: all budget clean
all: wbfont wbpic wbres wbdecode wbrun wbasset wbexec wbgame budget
wbpic: wbpic.asm platform/wildbits-presentation.d platform/wildbits-presentation-data.asm platform/wildbits-presentation-buffers.asm platform/wildbits-presentation-helpers.asm platform/wildbits-presentation-palette.asm platform/wildbits-defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbpic.list --symbols -o $@ $<
wbres: wbres.asm platform/wildbits-resource-cli.asm platform/wildbits-resource-data.asm platform/wildbits-resource-code.asm platform/wildbits-defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbres.list --map=wbres.map --symbols -o $@ $<
wbdecode: wbdecode.asm platform/wildbits-decoder-data.asm platform/wildbits-decoder-code.asm platform/wildbits-decoder-lines.asm platform/wildbits-decoder-fill.asm platform/wildbits-decoder-pen.asm platform/wildbits-picture-memory.asm platform/wildbits-resource-cli.asm platform/wildbits-resource-data.asm platform/wildbits-resource-code.asm platform/wildbits-defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbdecode.list --map=wbdecode.map --symbols -o $@ $<
wbrun: wbrun.asm platform/wildbits-decoder-data.asm platform/wildbits-decoder-code.asm platform/wildbits-decoder-lines.asm platform/wildbits-decoder-fill.asm platform/wildbits-decoder-pen.asm platform/wildbits-picture-memory.asm platform/wildbits-resource-cli.asm platform/wildbits-resource-data.asm platform/wildbits-resource-code.asm platform/wildbits-presentation.d platform/wildbits-presentation-data.asm platform/wildbits-presentation-buffers.asm platform/wildbits-presentation.asm platform/wildbits-presentation-helpers.asm platform/wildbits-presentation-palette.asm platform/wildbits-defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbrun.list --map=wbrun.map --symbols -o $@ $<
wbasset: wbasset.asm platform/wildbits-asset-data.asm platform/wildbits-asset-code.asm platform/wildbits-asset-write.asm platform/wildbits-lzw-data.asm platform/wildbits-lzw-code.asm platform/wildbits-resource-cli.asm platform/wildbits-resource-data.asm platform/wildbits-resource-code.asm platform/wildbits-defsfile
	$(LWASM) $(AFLAGS) --list=wbasset.list --map=wbasset.map --symbols -o $@ $<
wbexec: wbexec.asm platform/wildbits-asset-data.asm platform/wildbits-asset-code.asm platform/wildbits-lzw-data.asm platform/wildbits-lzw-code.asm platform/wildbits-logic-data.asm platform/wildbits-logic-code.asm platform/wildbits-logic-fetch.asm platform/wildbits-logic-platform.asm platform/wildbits-logic-cache.asm platform/wildbits-message-data.asm platform/wildbits-message-code.asm platform/wildbits-replay-data.asm platform/wildbits-replay-code.asm platform/wildbits-object-code.asm platform/wildbits-menu-data.asm platform/wildbits-menu-build-code.asm platform/wildbits-room-data.asm platform/wildbits-room-code.asm platform/wildbits-view-data.asm platform/wildbits-view-code.asm platform/wildbits-screen-data.asm platform/wildbits-screen-code.asm platform/wildbits-input-data.asm platform/wildbits-input-code.asm platform/wildbits-string-code.asm platform/wildbits-resource-cli.asm platform/wildbits-resource-data.asm platform/wildbits-resource-code.asm platform/wildbits-defsfile
	$(LWASM) $(AFLAGS) --list=wbexec.list --map=wbexec.map --symbols -o $@ $<
wbgame: wbgame.asm $(wildcard platform/wildbits-*.asm) font-data.asm platform/wildbits-decoder-lines.asm platform/wildbits-decoder-fill.asm platform/wildbits-decoder-pen.asm platform/wildbits-picture-memory.asm platform/wildbits-resource-cli.asm platform/wildbits-resource-code.asm platform/wildbits-resource-data.asm platform/wildbits-presentation.d platform/wildbits-presentation-buffers.asm platform/wildbits-presentation-helpers.asm platform/wildbits-presentation-palette.asm platform/wildbits-defsfile
	$(LWASM) $(AFLAGS) --list=wbgame.list --map=wbgame.map --symbols -o $@ $<
budget: wbpic wbres wbdecode wbrun wbasset wbexec wbgame
	@python3 -c 'from pathlib import Path; n=Path("wbpic").stat().st_size; assert n <= 40192, n; print("wbpic module: %d / 40192 bytes; process data: 8192 bytes; one mapping window" % n)'
	@python3 -c 'from pathlib import Path; b=Path("wbdecode").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbdecode probe: %d / %d code bytes; private data: %d bytes; one mapping window; four owned picture blocks" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbrun").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbrun integration: %d / %d code bytes; private data: %d bytes; sequential source/frame mapping" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbasset").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbasset: %d / %d code bytes; private data: %d bytes; one mapping window" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbexec").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbexec: %d / %d code bytes; private data: %d bytes; one mapping window" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbgame").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbgame: %d / %d code bytes; private data: %d bytes; sequential resource/picture/frame mapping" % (len(b),limit,data))'
clean:
	rm -f wbgame wbgame.list wbgame.map wbfont
	rm -f wbexec wbexec.list wbexec.map
	rm -f wbasset wbasset.list wbasset.map
	rm -f wbpic wbpic.list wbpic.map wbres wbres.list wbres.map
	rm -f wbdecode wbdecode.list wbdecode.map wbrun wbrun.list wbrun.map

.PHONY: fixture check
fixture:
	python3 ../tests/make_picture_fixture.py test-picture.bin
check: all
	python3 ../tests/check_logic_executor.py
	python3 ../tests/check_condition_flow.py
	python3 ../tests/check_tokenizer.py
	python3 ../tests/check_string_compare.py
	python3 ../tests/check_coco_conditions.py
	python3 ../tests/check_object_flags.py
	python3 ../tests/check_object_coordinates.py
	python3 ../tests/check_said.py
	python3 ../tests/check_wbgame.py
	python3 ../tests/check_wbcredits.py
	python3 ../tests/check_wbsprite_damage.py
	python3 ../tests/check_wbparser.py
	python3 ../tests/check_wbplay.py
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
	python3 ../tests/export_picture.py $(GAME) $(PICTURE) reference-picture.bin \
		--assembler "$(LWASM)" --defs "$(NITROS9DIR)/defs"

wbdecode wbrun wbgame: shared/picture-pen.asm shared/picture-pen-tables.asm

wbdecode wbrun wbgame: shared/picture-line.asm platform/picture-storage.asm platform/wildbits-picture-storage.asm

wbrun wbgame: platform/presentation.asm
wbgame: shared/object-direction-tables.asm
wbdecode wbrun wbgame: shared/picture-coordinates.asm
wbexec wbgame: shared/object-distance.asm
wbexec wbgame: shared/agi-command-table.asm
wbgame: shared/object-block-test.asm
wbgame: platform/sound-code.asm
wbgame: shared/divide-byte.asm shared/object-wander.asm
wbexec wbgame: shared/object-position-test.asm

wbgame: platform/wildbits-inventory-data.asm platform/wildbits-inventory-code.asm

wbfont: ../tests/export_font.py font-data.asm
	python3 ../tests/export_font.py $@

wbgame: wbfont

wbgame: shared/object-follow.asm shared/object-move-direction.asm
wbgame: platform/wildbits-render-text.asm
wbgame: platform/wildbits-sprite-background.asm
wbgame: platform/wildbits-present-damage.asm

wbgame: platform/wildbits-logic-fetch.asm

wbdecode wbrun wbgame: shared/picture-colors.asm shared/picture-commands.asm

wbdecode wbrun wbgame: shared/picture-command-table.asm

wbexec wbgame: shared/variable-commands.asm

wbexec wbgame: shared/flag-commands.asm

wbexec wbgame: platform/wildbits-flag-storage.asm

wbexec wbgame: shared/condition-tests.asm

wbexec wbgame: shared/agi-test-table.asm

wbexec wbgame: shared/object-flag-mask.asm shared/object-flag-rules.asm

wbexec wbgame: shared/object-cycle-state.asm

wbexec wbgame: shared/object-motion-state.asm

wbexec wbgame: shared/object-rate-state.asm

wbgame: shared/said-match.asm

wbgame: shared/ascii-lower.asm

# Keep every owner current when an adapter or common algorithm changes.
wbpic wbres wbdecode wbrun wbasset wbexec wbgame: $(wildcard platform/wildbits-*.asm) platform/wildbits-defsfile platform/wildbits-presentation.d $(wildcard shared/*.asm)
wbexec wbgame: platform/object-coordinate-operands.asm
