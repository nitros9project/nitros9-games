ifndef NITROS9DIR
NITROS9DIR := $(abspath ../nitros9)
endif

NITROS9_GAMES_DIR := $(CURDIR)

export NITROS9DIR
export NITROS9_GAMES_DIR

include $(NITROS9DIR)/rules.mak

dirs = arcadepak flightsim2 koronis kyumgai mmission pacos9 rescueof rogue \
	sierra subsim

all:
	$(foreach dir,$(dirs),$(MAKE) -C $(dir) &&) :

clean:
	$(foreach dir,$(dirs),$(MAKE) -C $(dir) clean &&) :

.PHONY: all clean
