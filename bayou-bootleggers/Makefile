CMOC ?= cmoc
CMOC_OS9 ?= $(HOME)/Projects/cmoc_os9
NITROS9DIR ?= $(abspath ../../nitros9)
DEPS = build/deps
CFLAGS = --cpp="cpp -Wno-builtin-macro-redefined" --os9 --add-os9-stack-space=1024 -nodefaultlibs -O2 -I$(DEPS)/include -I$(DEPS)/cgfx/include
.PHONY: all test disk art package clean
all: disk
build/profile: Makefile src/bayou.c src/game.c src/render.c src/render.h src/blit.c src/unpack.c src/damage.c src/copy.c src/sprite.c src/sprites.h $(DEPS)/ready
	$(CMOC) $(CFLAGS) -DBAYOU_PROFILE -o bprof src/bayou.c src/game.c src/render.c src/copy.c src/sprite.c -L$(DEPS)/lib -lc -L$(DEPS)/cgfx -lcgfx
	mv bprof $@
$(DEPS)/ready:
	mkdir -p $(DEPS)
	cp -R "$(CMOC_OS9)/include" "$(CMOC_OS9)/lib" "$(CMOC_OS9)/cgfx" $(DEPS)/
	$(MAKE) -C $(DEPS)/lib libc.a
	$(MAKE) -C $(DEPS)/cgfx
	touch $@
art:
	python3 tools/make_art.py
	python3 tools/make_track.py
dist/bayou: Makefile src/bayou.c src/game.c src/game.h src/render.c src/render.h src/blit.c src/unpack.c src/damage.c src/copy.c src/sprite.c src/sprites.h $(DEPS)/ready
	mkdir -p dist
	$(CMOC) $(CFLAGS) -o bayou src/bayou.c src/game.c src/render.c src/copy.c src/sprite.c -L$(DEPS)/lib -lc -L$(DEPS)/cgfx -lcgfx
	mv bayou $@
dist/teeboy: Makefile src/track.c src/race.c src/race.h src/render.c src/render.h src/horses.h src/copy32.c src/horse_blit.c $(DEPS)/ready src/crowd.c src/crowd.h
	mkdir -p dist
	$(CMOC) $(CFLAGS) -DBUSH_TRACK -o teeboy src/track.c src/race.c src/crowd.c src/render.c src/copy32.c src/horse_blit.c -L$(DEPS)/lib -lc -L$(DEPS)/cgfx -lcgfx
	mv teeboy $@
build/race-bench: src/track.c src/race.c src/race.h src/render.c src/horses.h src/copy32.c src/horse_blit.c $(DEPS)/ready src/crowd.c src/crowd.h
	$(CMOC) $(CFLAGS) -DBUSH_TRACK -DRACE_BENCH -o teeboy src/track.c src/race.c src/crowd.c src/render.c src/copy32.c src/horse_blit.c -L$(DEPS)/lib -lc -L$(DEPS)/cgfx -lcgfx
	mv teeboy $@
build/test-horses: src/test_horses.c src/render.c src/horses.h src/render.h src/blit.c src/unpack.c src/copy32.c
	mkdir -p build
	cc -std=c99 -Wall -Wextra -Werror -DBUSH_TRACK -o $@ src/test_horses.c src/render.c src/blit.c src/unpack.c src/copy32.c
build/test-race: src/test_race.c src/race.c src/race.h src/crowd.c src/crowd.h
	mkdir -p build
	cc -std=c99 -Wall -Wextra -Werror -o $@ src/test_race.c src/race.c src/crowd.c
test: build/test-game build/test-render build/test-race build/test-horses
	./build/test-game
	./build/test-render
	./build/test-race
	./build/test-horses
build/test-render: src/test_render.c src/render.c src/render.h src/blit.c src/unpack.c src/damage.c src/copy.c src/sprite.c src/sprites.h
	mkdir -p build
	cc -std=c99 -Wall -Wextra -Werror -o $@ src/test_render.c src/render.c src/blit.c src/unpack.c src/damage.c src/copy.c src/sprite.c
build/test-game: src/test_game.c src/game.c src/game.h
	mkdir -p build
	cc -std=c99 -Wall -Wextra -Werror -o $@ src/test_game.c src/game.c
disk: dist/bayou dist/teeboy
	mkdir -p build/disk
	cp defsfile build/disk/defsfile
	$(RM) build/disk/bayou.dsk
	$(MAKE) -C build/disk -f $(NITROS9DIR)/recipes/coco3/coco3.mak NITROS9DIR=$(NITROS9DIR) LEVEL=2 PORTDEFSDIR= CMDS_BASE='grfdrv shell utilpak1' STARTUP=$(abspath startup) DSKIMAGE=bayou.dsk all
	os9 copy -r dist/bayou build/disk/bayou.dsk,CMDS/bayou
	os9 attr -e -pe build/disk/bayou.dsk,CMDS/bayou
	os9 copy -r dist/teeboy build/disk/bayou.dsk,CMDS/teeboy
	os9 attr -e -pe build/disk/bayou.dsk,CMDS/teeboy
	os9 makdir build/disk/bayou.dsk,BAYOU
	os9 copy -r assets/dock0.bin assets/dock1.bin assets/dock2.bin assets/title.bin assets/track.bin assets/rtitle.bin build/disk/bayou.dsk,BAYOU
	os9 copy -r assets/dock0.rle assets/dock1.rle assets/dock2.rle build/disk/bayou.dsk,BAYOU
	cp build/disk/bayou.dsk dist/bayou.dsk
package: disk
	zip -q -r dist/bayou-coco3.zip README.md Makefile startup defsfile .gitignore src tools assets screenshots benchmarks dist/bayou dist/teeboy dist/bayou.dsk -x 'tools/__pycache__/*'

clean:
	$(RM) -r build dist
