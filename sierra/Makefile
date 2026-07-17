include $(NITROS9DIR)/rules.mak

dirs	= blackcauldron christmas86 goldrush \
	kingsquest1 kingsquest2 kingsquest3 kingsquest4 \
	leisuresuitlarry manhunter1 manhunter2 \
	policequest1 spacequest0 spacequest1 spacequest2

# Make all components
all:
	@$(ECHO) "**************************************************"
	@$(ECHO) "*                                                *"
	@$(ECHO) "*             Sierra Adventure Games             *"
	@$(ECHO) "*                                                *"
	@$(ECHO) "**************************************************"
	$(foreach dir,$(dirs),$(MAKE) -C $(dir) &&) :

# Clean all components
clean:
	$(foreach dir,$(dirs),$(MAKE) -C $(dir) clean &&) :

.PHONY: all clean
