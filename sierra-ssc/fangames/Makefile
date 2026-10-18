include $(NITROS9DIR)/rules.mak

dirs	= enclosure kingsquest6 operationrecon sorcerer \
	spacequest0 spacequesttlc starcommander v voodoogirl

# Make all components
all:
	@$(ECHO) "**************************************************"
	@$(ECHO) "*                                                *"
	@$(ECHO) "*                  AGI Fan Games                 *"
	@$(ECHO) "*                                                *"
	@$(ECHO) "**************************************************"
	$(foreach dir,$(dirs),$(MAKE) -C $(dir) &&) :

# Clean all components
clean:
	$(foreach dir,$(dirs),$(MAKE) -C $(dir) clean &&) :

.PHONY: all clean
