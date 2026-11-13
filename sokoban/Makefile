# Host cross-build; no implicit native compiler rules.
.SUFFIXES:
C3ROOT ?= $(abspath ../../nitros9-languages/c3)
NITROS9DIR ?= $(abspath ../../nitros9)
PREP = $(C3ROOT)/build/unix/prep/c3prep
COMP = $(C3ROOT)/build/unix/comp/c3comp
OPTX = $(C3ROOT)/build/unix/optx/c3optx
PROG = sokoban
OBJECTS = sok play showscrn score readscrn save curses compat
RFILES = $(addprefix build/,$(addsuffix .r,$(OBJECTS)))
C3LIB = $(C3ROOT)/lwbackend

.PHONY: all clean disk run
all: build/$(PROG)
build:
	mkdir -p $@
build/%.r: %.c $(wildcard *.h) | build
	$(PREP) -DOS9 -v=$(C3ROOT)/defs -v=. $< > build/$*.i
	$(COMP) build/$*.i > build/$*.s
	$(OPTX) < build/$*.s > build/$*.opt.s
	awk -f $(C3LIB)/c3lw.awk build/$*.opt.s > build/$*.lw.s
	lwasm --format=obj -o $@ build/$*.lw.s
build/$(PROG): $(RFILES) $(C3LIB)/crt0.o $(C3LIB)/fpdummy.o $(C3LIB)/libc3.a $(C3LIB)/libc3lw.a
	cd build && lwlink --format=os9 -s $(C3LIB)/os9c3.ld -o $(PROG) $(C3LIB)/crt0.o $(C3LIB)/fpdummy.o $(notdir $(RFILES)) -L$(C3LIB) -lc3 -lc3lw
clean:
	rm -rf build cfg
	rm -f *.list *.map

EMUDIR = build/emulator
DISK = $(EMUDIR)/$(PROG).dsk
MAME ?= mame
MAME_ROM_PATH ?= $(HOME)/.local/share/mame/roms
MAME_FLAGS ?= -window -skip_gameinfo -ramsize 512k
disk: $(DISK)
$(DISK): build/$(PROG) run.startup Makefile $(wildcard screens/screen.*) data/sok.score
	mkdir -p $(EMUDIR)
	cp $(NITROS9DIR)/recipes/coco3/floppy/defsfile $(EMUDIR)/defsfile
	$(MAKE) -C $(EMUDIR) -f $(NITROS9DIR)/recipes/coco3/coco3.mak \
	    NITROS9DIR=$(NITROS9DIR) LEVEL=2 CPU=6809 TERM_COLS=80 \
	    CMDS="shell grfdrv utilpak1 load link echo merge" PORTDEFSDIR= \
	    STARTUP=$(CURDIR)/run.startup DSKIMAGE=$(PROG).dsk all
	os9 copy -r build/$(PROG) $(DISK),CMDS/$(PROG)
	os9 attr -e -pe $(DISK),CMDS/$(PROG)
	os9 makdir $(DISK),SCREENS
	os9 copy -l -r screens/screen.* $(DISK),SCREENS
	os9 copy -r data/sok.score $(DISK),sok.score
run: $(DISK)
	$(MAME) coco3 -rompath "$(MAME_ROM_PATH)" -cfg_directory "$(abspath build/mame-cfg)" -nvram_directory "$(abspath build/mame-nvram)" $(MAME_FLAGS) \
	    -ext fdc -ext:fdc:wd17xx:0 525qd -flop1 "$(abspath $(DISK))" \
	    -autoboot_delay 2 -autoboot_command "DOS\n"
