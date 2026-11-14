PORT ?= coco3
export PORT
# Compile game modules only. Disk images and MAME live in nitros9 recipes.
NITROS9DIR ?= $(abspath ../../nitros9)
.DEFAULT_GOAL := all
include $(NITROS9DIR)/rules.mak

CMDS = presub sub sub1 sub2 sub3 sub4 sub5 sub6
all: $(CMDS)
$(CMDS): Makefile

clean:
	$(RM) $(CMDS) *.list *.map

showobjs:
	@$(ECHO) $(CMDS)

.PHONY: all clean showobjs
