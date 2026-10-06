NITROS9DIR ?= $(abspath ../../../nitros9)
LWASM ?= lwasm
AFLAGS = --6809 --format=os9 --pragma=pcaspcr,nosymbolcase,condundefzero \
	-I. -I$(NITROS9DIR)/defs

.PHONY: all probes budget probe-budget clean
# Production build; probes are optional test executables.
all: wbgame budget
probes: wbpic wbres wbdecode wbrun wbasset wbexec probe-budget
wbpic: ../tests/probes/wbpic.asm platform/wildbits-presentation.d platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbpic.list --symbols -o $@ $<
wbres: ../tests/probes/wbres.asm platform/wildbits-memory-resources.asm platform/wildbits-memory-resources.asm platform/wildbits-memory-resources.asm platform/wildbits-defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbres.list --map=wbres.map --symbols -o $@ $<
wbdecode: ../tests/probes/wbdecode.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-memory-resources.asm platform/wildbits-memory-resources.asm platform/wildbits-memory-resources.asm platform/wildbits-defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbdecode.list --map=wbdecode.map --symbols -o $@ $<
wbrun: ../tests/probes/wbrun.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-memory-resources.asm platform/wildbits-memory-resources.asm platform/wildbits-memory-resources.asm platform/wildbits-presentation.d platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-defsfile $(NITROS9DIR)/defs/wildbits.d
	$(LWASM) $(AFLAGS) --list=wbrun.list --map=wbrun.map --symbols -o $@ $<
wbasset: ../tests/probes/wbasset.asm \
	platform/wildbits-memory-resources.asm \
	platform/wildbits-defsfile
	$(LWASM) $(AFLAGS) --list=wbasset.list --map=wbasset.map --symbols -o $@ $<
wbexec: ../tests/probes/wbexec.asm \
	platform/wildbits-memory-resources.asm \
	platform/wildbits-logic.asm \
	platform/wildbits-text-ui.asm \
	platform/wildbits-objects.asm \
	platform/wildbits-graphics.asm \
	platform/wildbits-input.asm \
	platform/wildbits-defsfile
	$(LWASM) $(AFLAGS) --list=wbexec.list --map=wbexec.map --symbols -o $@ $<
wbgame: sierra.asm $(wildcard platform/wildbits-*.asm) font-data.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-memory-resources.asm platform/wildbits-memory-resources.asm platform/wildbits-memory-resources.asm platform/wildbits-presentation.d platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-graphics.asm platform/wildbits-defsfile
	$(LWASM) $(AFLAGS) -DWILDBITS=1 --list=wbgame.list --map=wbgame.map --symbols -o $@ $<
probe-budget: wbpic wbres wbdecode wbrun wbasset wbexec
	@python3 -c 'from pathlib import Path; n=Path("wbpic").stat().st_size; assert n <= 40192, n; print("wbpic module: %d / 40192 bytes; process data: 8192 bytes; one mapping window" % n)'
	@python3 -c 'from pathlib import Path; b=Path("wbdecode").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbdecode probe: %d / %d code bytes; private data: %d bytes; one mapping window; four owned picture blocks" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbrun").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbrun integration: %d / %d code bytes; private data: %d bytes; sequential source/frame mapping" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbasset").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbasset: %d / %d code bytes; private data: %d bytes; one mapping window" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbexec").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbexec: %d / %d code bytes; private data: %d bytes; one mapping window" % (len(b),limit,data))'
budget: wbgame
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
check: all probes
	python3 ../tests/check_logic_executor.py
	python3 ../tests/check_random_command.py
	python3 ../tests/check_math_commands.py
	python3 ../tests/check_view_queries.py
	python3 ../tests/check_game_clock.py
	python3 ../tests/check_decimal_index.py
	python3 ../tests/check_decimal_output.py
	python3 ../tests/check_condition_flow.py
	python3 ../tests/check_tokenizer.py
	python3 ../tests/check_string_compare.py
	python3 ../tests/check_coco_conditions.py
	python3 ../tests/check_object_flags.py
	python3 ../tests/check_object_block_state.py
	python3 ../tests/check_object_scalar_commands.py
	python3 ../tests/check_object_placement_step.py
	python3 ../tests/check_object_bounds.py
	python3 ../tests/check_object_collision_filter.py
	python3 ../tests/check_motion_setup.py
	python3 ../tests/check_cel_advance.py
	python3 ../tests/check_inventory_commands.py
	python3 ../tests/check_xor_decrypt.py
	python3 ../tests/check_text_helpers.py
	python3 ../tests/check_string_slots.py
	python3 ../tests/check_object_coordinates.py
	python3 ../tests/check_move_direction.py
	python3 ../tests/check_object_terrain.py
	python3 ../tests/check_said.py
	python3 ../tests/check_wbgame.py
	python3 ../tests/check_wbcredits.py
	python3 ../tests/check_wbsprite_damage.py
	python3 ../tests/check_wbparser.py
	python3 ../tests/check_dictionary_lookup.py
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

wbdecode wbrun wbgame: shared/picture-line.asm platform/sections.d platform/wildbits-graphics.asm

wbrun wbgame: platform/sections.d
wbgame: shared/object-animation.asm
wbdecode wbrun wbgame: shared/picture-coordinates.asm
wbexec wbgame: shared/object-distance.asm
wbexec wbgame: shared/agi-command-table.asm
wbgame: shared/object-block-test.asm
wbgame: platform/sections.d
wbgame: shared/divide-byte.asm shared/object-wander.asm
wbexec wbgame: shared/object-position-test.asm

wbgame: platform/wildbits-text-ui.asm

wbfont: ../tests/export_font.py font-data.asm
	python3 ../tests/export_font.py $@

wbgame: wbfont

wbgame: shared/object-follow.asm shared/object-move-direction.asm
wbgame: platform/wildbits-graphics.asm

wbgame: platform/wildbits-logic.asm

wbdecode wbrun wbgame: shared/picture-colors.asm shared/picture-commands.asm

wbdecode wbrun wbgame: shared/picture-command-table.asm

wbexec wbgame: shared/variable-commands.asm

wbexec wbgame: shared/flag-commands.asm

wbexec wbgame: platform/wildbits-logic.asm

wbexec wbgame: shared/condition-tests.asm

wbexec wbgame: shared/agi-test-table.asm

wbexec wbgame: shared/object-commands.asm shared/object-flag-rules.asm




wbgame: shared/said-match.asm

wbgame: shared/ascii-lower.asm

# Keep every owner current when an adapter or common algorithm changes.
wbpic wbres wbdecode wbrun wbasset wbexec wbgame: $(wildcard platform/wildbits-*.asm) platform/wildbits-defsfile platform/wildbits-presentation.d $(wildcard shared/*.asm)
wbexec wbgame: platform/sections.d





















wbgame wbexec wbpic wbdecode wbrun wbasset wbres: platform/sections.d
