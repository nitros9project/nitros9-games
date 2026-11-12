include $(NITROS9DIR)/rules.mak

dirs	= demopack1 demopack2 demopack3 demopack4 \
	demopack5 kq4demo

# Make all components
all:
	@$(ECHO) "**************************************************"
	@$(ECHO) "*                                                *"
	@$(ECHO) "*                  Sierra Demos                  *"
	@$(ECHO) "*                                                *"
	@$(ECHO) "**************************************************"
	$(foreach dir,$(dirs),$(MAKE) -C $(dir) &&) :

# Clean all components
clean:
	$(foreach dir,$(dirs),$(MAKE) -C $(dir) clean &&) :

.PHONY: all clean
