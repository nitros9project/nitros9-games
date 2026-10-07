NITROS9DIR ?= $(abspath ../../../nitros9)
LWASM ?= lwasm
AFLAGS = --6809 --format=os9 --pragma=pcaspcr,nosymbolcase,condundefzero \
	-I. -I$(NITROS9DIR)/defs

.PHONY: all probes budget probe-budget clean
# Production build; probes are optional test executables.
all: wbgame wbstate budget
probes: wbpic wbres wbdecode wbrun wbasset wbexec probe-budget
# Each owner retains its entry point as the first prerequisite ($<).
wbpic: ../tests/probes/wbpic.asm
	$(LWASM) $(AFLAGS) --list=wbpic.list --symbols -o $@ $<
wbres: ../tests/probes/wbres.asm
	$(LWASM) $(AFLAGS) --list=wbres.list --map=wbres.map --symbols -o $@ $<
wbdecode: ../tests/probes/wbdecode.asm
	$(LWASM) $(AFLAGS) --list=wbdecode.list --map=wbdecode.map --symbols -o $@ $<
wbrun: ../tests/probes/wbrun.asm
	$(LWASM) $(AFLAGS) --list=wbrun.list --map=wbrun.map --symbols -o $@ $<
wbasset: ../tests/probes/wbasset.asm
	$(LWASM) $(AFLAGS) --list=wbasset.list --map=wbasset.map --symbols -o $@ $<
wbexec: ../tests/probes/wbexec.asm
	$(LWASM) $(AFLAGS) --list=wbexec.list --map=wbexec.map --symbols -o $@ $<
wbstate: wbstate.asm
	$(LWASM) $(AFLAGS) --list=wbstate.list --map=wbstate.map --symbols -o $@ $<
wbgame: sierra.asm wbfont font-data.asm
	$(LWASM) $(AFLAGS) -DWILDBITS=1 --list=wbgame.list --map=wbgame.map --symbols -o $@ $<

# Keep every owner current when a grouped feature or shared body changes.
# This deliberately includes all common bodies for the optional probes too.
wbstate wbgame wbexec wbpic wbdecode wbrun wbasset wbres: \
	$(wildcard platform/wildbits-*.asm) $(wildcard shared/*.asm) \
	$(wildcard *.d) $(wildcard platform/*.d) \
	platform/sections.d platform/wildbits-defsfile \
	platform/wildbits-presentation.d $(NITROS9DIR)/defs/wildbits.d

wbfont: ../tests/export_font.py font-data.asm
	python3 ../tests/export_font.py $@

probe-budget: wbpic wbres wbdecode wbrun wbasset wbexec
	@python3 -c 'from pathlib import Path; n=Path("wbpic").stat().st_size; assert n <= 40192, n; print("wbpic module: %d / 40192 bytes; process data: 8192 bytes; one mapping window" % n)'
	@python3 -c 'from pathlib import Path; b=Path("wbdecode").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbdecode probe: %d / %d code bytes; private data: %d bytes; one mapping window; four owned picture blocks" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbrun").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbrun integration: %d / %d code bytes; private data: %d bytes; sequential source/frame mapping" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbasset").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbasset: %d / %d code bytes; private data: %d bytes; one mapping window" % (len(b),limit,data))'
	@python3 -c 'from pathlib import Path; b=Path("wbexec").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbexec: %d / %d code bytes; private data: %d bytes; one mapping window" % (len(b),limit,data))'
budget: wbgame wbstate
	@python3 -c 'from pathlib import Path; b=Path("wbstate").read_bytes(); entry=int.from_bytes(b[9:11],"big"); prefix=int.from_bytes(b[entry+18:entry+20],"big"); assert len(b)<=8192; assert int.from_bytes(b[11:13],"big")==0; assert entry+35<=prefix<=4096 and prefix<=len(b)-3, (entry,prefix,len(b)); print("wbstate: %d / 8192 linked bytes; writable prefix: %d / 4096 bytes; no separate private allocation" % (len(b),prefix))'
	@python3 -c 'from pathlib import Path; b=Path("wbgame").read_bytes(); data=int.from_bytes(b[11:13], "big"); limit=(7-(data+8191)//8192-1)*8192-768; assert len(b) <= limit, (len(b),limit); print("wbgame: %d / %d code bytes; private data: %d bytes; sequential resource/picture/frame mapping" % (len(b),limit,data))'
clean:
	rm -f wbgame wbgame.list wbgame.map wbfont wbstate wbstate.list wbstate.map
	rm -f wbexec wbexec.list wbexec.map
	rm -f wbasset wbasset.list wbasset.map
	rm -f wbpic wbpic.list wbpic.map wbres wbres.list wbres.map
	rm -f wbdecode wbdecode.list wbdecode.map wbrun wbrun.list wbrun.map

.PHONY: fixture check
fixture:
	python3 ../tests/make_picture_fixture.py test-picture.bin
check: all probes
	python3 ../tests/check_instances.py --transport-only
	python3 ../tests/check_native_dispatch.py
	python3 ../tests/check_native_audio.py
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
	python3 ../tests/check_resource_lifetime.py
	python3 ../tests/check_motion_setup.py
	python3 ../tests/check_cel_clipping.py
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
	python3 ../tests/check_packed_pictures.py
	python3 ../tests/check_add_to_picture.py
	python3 ../tests/check_cancel_line.py
	python3 ../tests/check_persistent_window.py
	python3 ../tests/check_picture_stream.py
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
