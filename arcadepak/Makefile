PORT ?= coco3
export PORT
NITROS9DIR ?= $(abspath ../../nitros9)
export NITROS9DIR
.DEFAULT_GOAL := all
SUBDIRS = smash thexder shanghai
all clean:
	@set -e; for dir in $(SUBDIRS); do $(MAKE) -C $$dir $@; done
.PHONY: all clean
