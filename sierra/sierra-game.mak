PORT ?= coco3
export PORT
# Shared CoCo interpreter compilation; packaging is in nitros9 recipes.
NITROS9DIR ?= $(abspath ../../../nitros9)
.DEFAULT_GOAL := all
include $(NITROS9DIR)/rules.mak
include ../sierra-engine.mak
CMDS = sierra mnln scrn shdw tocgen
all: $(CMDS)
$(CMDS): Makefile ../sierra-game.mak
clean:
	$(RM) $(CMDS) *.list *.map
.PHONY: all clean
