# Build an installable Wild Bits game disk from the NitrOS-9 Jr2 L2 image.
# Example: make -C sierra -f wildbits-game.mk GAME=kingsquest1

NITROS9DIR ?= $(abspath ../../nitros9)
LWASM ?= lwasm
OS9 ?= os9
PYTHON ?= python3

GAME ?= kingsquest1
GAME_DIR ?= $(CURDIR)/$(GAME)
BASE_DISK ?= $(NITROS9DIR)/recipes/wildbits/l2/l2_wildbitsjr2.dsk
OUTPUT ?= $(CURDIR)/build/wildbits/$(GAME)-jr2.dsk
OBJS := $(CURDIR)/objs

.PHONY: all modules disk clean
all: disk

modules:
	$(MAKE) -C $(OBJS) -f wildbits.mk NITROS9DIR=$(NITROS9DIR) LWASM=$(LWASM) all

disk: modules
	$(PYTHON) package_wildbits_game.py \
		--os9 "$(OS9)" \
		--base-disk "$(BASE_DISK)" \
		--game "$(GAME_DIR)" \
		--modules "$(OBJS)" \
		--output "$(OUTPUT)"

clean:
	rm -f "$(OUTPUT)"
