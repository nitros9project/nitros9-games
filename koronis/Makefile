PORT ?= coco3
export PORT
# Compile game modules only. Disk images and MAME live in nitros9 recipes.
NITROS9DIR ?= $(abspath ../../nitros9)
.DEFAULT_GOAL := all
include $(NITROS9DIR)/rules.mak

CMDS = koronis
all: $(CMDS)
$(CMDS): Makefile

clean:
	$(RM) $(CMDS) *.list *.map

showobjs:
	@$(ECHO) $(CMDS)

.PHONY: all clean showobjs
