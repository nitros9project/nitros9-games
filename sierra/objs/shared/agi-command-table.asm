* One AGI command catalog for CoCo dispatch and native operand decoding.
* AGI_COMMAND expands to a platform handler/descriptor or operand-count byte.
                    AGI_COMMAND NoopCmdsRet,$0000 *do nothing
                    AGI_COMMAND cmd_increment,$180 *increment
                    AGI_COMMAND cmd_decrement,$180 *decrement
                    AGI_COMMAND cmd_assignn,$280 *assign nn
                    AGI_COMMAND cmd_assignv,$2c0 *assign nv
                    AGI_COMMAND cmd_addn,$280 *add n
                    AGI_COMMAND cmd_addv,$2c0 *add v
                    AGI_COMMAND cmd_subn,$280 *sub n
                    AGI_COMMAND cmd_subv,$2c0 *sub v
                    AGI_COMMAND cmd_lindirectv,$2c0 *l indirect v
                    AGI_COMMAND cmd_rindirect,$2c0 *r indirect
                    AGI_COMMAND cmd_lindirectn,$280 *l indirect n
                    AGI_COMMAND CmdSetImpl,$100 *set
                    AGI_COMMAND CmdResetImpl,$100 *reset
                    AGI_COMMAND CmdToggleImpl,$100 *toggle
                    AGI_COMMAND CmdSetVImpl,$180 *set v
                    AGI_COMMAND CmdResetVImpl,$180 *reset v
                    AGI_COMMAND CmdToggleVImpl,$180 *toggle v
                    AGI_COMMAND cmd_new_room,$100 *new room
                    AGI_COMMAND cmd_new_room_v,$180 *new room v
                    AGI_COMMAND cmd_load_logics,$100 *load logics
                    AGI_COMMAND cmd_load_logics_v,$180 *load logics v
                    AGI_COMMAND cmd_call,$100 *call
                    AGI_COMMAND cmd_call_v,$180 *call v
                    AGI_COMMAND cmd_load_pic,$180 *load pic
                    AGI_COMMAND cmd_draw_pic,$180 *draw pic
                    AGI_COMMAND cmd_show_pic,$0000 *show pic
                    AGI_COMMAND cmd_discard_pic,$180 *discard overlay
                    AGI_COMMAND cmd_overlay_pic,$180 *animate obj
                    AGI_COMMAND CmdSaveGame,$0000 *show pri
                    AGI_COMMAND cmd_load_view,$100 *load view
                    AGI_COMMAND cmd_load_view_v,$180 *load view v
                    AGI_COMMAND cmd_discard_view,$100 *discard view
                    AGI_COMMAND CmdAnimateObj,$100 *animate obj
                    AGI_COMMAND CmdUnanimateAll,$0000 *unanumate all
                    AGI_COMMAND CmdDrawImpl,$100 *draw
                    AGI_COMMAND CmdEraseImpl,$100 *erase
                    AGI_COMMAND cmd_position,$300 *position
                    AGI_COMMAND cmd_position_v,$360 *position v
                    AGI_COMMAND cmd_get_position,$360 *get position
                    AGI_COMMAND cmd_reposition,$360 *reposition
                    AGI_COMMAND cmd_set_view,$200 *set view
                    AGI_COMMAND cmd_set_view_v,$240 *set view v
                    AGI_COMMAND cmd_set_loop,$200 *set loop
                    AGI_COMMAND cmd_set_loop_v,$240 *set loop v
                    AGI_COMMAND CmdFixLoop,$100 *fix loop
                    AGI_COMMAND CmdReleaseLoop,$100 *release loop
                    AGI_COMMAND cmd_set_cel,$200 *set cel
                    AGI_COMMAND cmd_set_cel_v,$240 *set cel v
                    AGI_COMMAND cmd_last_cel,$240 *last cel
                    AGI_COMMAND cmd_current_cel,$240 *current cel
                    AGI_COMMAND cmd_current_loop,$240 *current loop
                    AGI_COMMAND cmd_current_view,$240 *current view
                    AGI_COMMAND cmd_number_of_loops,$240 *number of loops
                    AGI_COMMAND cmd_set_priority,$200 *set priority
                    AGI_COMMAND cmd_set_priority_v,$240 *set priority v
                    AGI_COMMAND cmd_release_priority,$100 *release priority
                    AGI_COMMAND cmd_get_priority,$240 *get priority
                    AGI_COMMAND CmdStopUpdate,$100 *stop update
                    AGI_COMMAND CmdStartUpdate,$100 *start update
                    AGI_COMMAND CmdForceUpdate,$100 *force update
                    AGI_COMMAND cmd_ignore_horizon,$100 *ignore horizon
                    AGI_COMMAND cmd_observe_horizon,$100 *observe horizon
                    AGI_COMMAND cmd_set_horizon,$100 *set horizon
                    AGI_COMMAND cmd_obj_on_water,$100 *obj on water
                    AGI_COMMAND cmd_obj_on_land,$100 *obj on land
                    AGI_COMMAND cmd_obj_on_anything,$100 *obj on anything
                    AGI_COMMAND CmdIgnoreObjects,$100 *ignore objects
                    AGI_COMMAND CmdObserveObjects,$100 *observe objects
                    AGI_COMMAND CmdDistance,$320 *distance
                    AGI_COMMAND CmdStopCycling,$100 *stop cycling
                    AGI_COMMAND CmdStartCycling,$100 *start cycling
                    AGI_COMMAND CmdNormalCycle,$100 *normal cycle
                    AGI_COMMAND CmdEndOfLoop,$200 *end of loop
                    AGI_COMMAND CmdReverseCycle,$100 *reverse cycle
                    AGI_COMMAND CmdReverseLoop,$200 *reverse loop
                    AGI_COMMAND CmdSetCycleTime,$240 *cycle time
                    AGI_COMMAND cmd_stop_motion,$100 *stop motion
                    AGI_COMMAND cmd_start_motion,$100 *start motion
                    AGI_COMMAND cmd_step_size_v,$240 *step size
                    AGI_COMMAND cmd_step_time,$240 *step time
                    AGI_COMMAND cmd_move_obj,$500 *move obj
                    AGI_COMMAND cmd_move_obj_v,$570 *move obj v
                    AGI_COMMAND cmd_follow_ego,$300 *follow ego
                    AGI_COMMAND cmd_wander,$100 *wander
                    AGI_COMMAND cmd_normal_motion,$100 *normal motion
                    AGI_COMMAND cmd_set_dir,$240 *set dir
                    AGI_COMMAND cmd_get_dir,$240 *get dir
                    AGI_COMMAND CmdIgnoreBlocks,$100 *ignore blocks
                    AGI_COMMAND CmdObserveBlocks,$100 *observe blocks
                    AGI_COMMAND CmdSetBlock,$400 *block
                    AGI_COMMAND CmdClearBlock,$0000 *unblock
                    AGI_COMMAND cmd_get,$100 *get
                    AGI_COMMAND cmd_get_v,$180 *get v
                    AGI_COMMAND cmd_drop,$100 *drop
                    AGI_COMMAND cmd_put,$200 *put
                    AGI_COMMAND cmd_put_v,$240 *put v
                    AGI_COMMAND cmd_get_room_v,$2c0 *get room v
                    AGI_COMMAND cmd_load_sound,$100 *load sound
                    AGI_COMMAND cmd_sound,$200 *sound
                    AGI_COMMAND NoopCmdsRet,$0000 *stop sound
                    AGI_COMMAND cmd_print,$100 *print
                    AGI_COMMAND cmd_print_v,$180 *print v
                    AGI_COMMAND cmd_display,$300 *display
                    AGI_COMMAND cmd_display_v,$3e0 *display v
                    AGI_COMMAND cmd_clear_lines,$300 *clear lines
                    AGI_COMMAND cmd_text_screen,$0000 *text screen
                    AGI_COMMAND cmd_graphics,$0000 *graphics
                    AGI_COMMAND cmd_set_cursor_char,$100 *set cursor char
                    AGI_COMMAND cmd_set_text_attribute,$200 *set text attribute
                    AGI_COMMAND cmd_shake_screen,$100 *shake screen
                    AGI_COMMAND cmd_config_screen,$300 *config screen
                    AGI_COMMAND cmd_status_line_on,$0000 *status line on
                    AGI_COMMAND cmd_status_line_off,$0000 *status line off
                    AGI_COMMAND cmd_set_string,$200 *set string
                    AGI_COMMAND cmd_get_string,$500 *get string
                    AGI_COMMAND cmd_word_to_string,$200 *word to string
                    AGI_COMMAND cmd_parse,$100 *parse
                    AGI_COMMAND CmdObjStatus,$240 *get num
                    AGI_COMMAND cmd_prevent_input,$0000 *prevent input
                    AGI_COMMAND cmd_accept_input,$0000 *accept inpur
                    AGI_COMMAND CmdSetKey,$300 *set key
                    AGI_COMMAND cmd_add_to_pic,$700 *add to pic
                    AGI_COMMAND cmd_add_to_pic_v,$7fe *add to pic v
                    AGI_COMMAND cmd_status,$0000 *status
                    AGI_COMMAND cmd_save_game,$0000 *save game
                    AGI_COMMAND cmd_restore_game,$0000 *restore game
                    AGI_COMMAND NoopCmdsRet,$0000 *init disk
                    AGI_COMMAND cmd_restart_game,$0000 *restart game
                    AGI_COMMAND cmd_show_obj,$100 *sow obj
                    AGI_COMMAND CmdRandomImpl,$320 *random
                    AGI_COMMAND cmd_program_control,$0000 *program control
                    AGI_COMMAND cmd_player_control,$0000 *player control
                    AGI_COMMAND CmdObjStatusV,$180 *obj status v
                    AGI_COMMAND CmdQuitImpl,$100 *quit
                    AGI_COMMAND CmdShowMemInfo,$0000 *show mem
                    AGI_COMMAND CmdPauseImpl,$0000 *pause
                    AGI_COMMAND cmd_echo_line,$0000 *echo line
                    AGI_COMMAND cmd_cancel_line,$0000 *cancel line
                    AGI_COMMAND cmd_init_joy,$0000 *init joy
                    AGI_COMMAND cmd_toggle_monitor,$0000 *toggle monitor
                    AGI_COMMAND CmdShowAgiInfo,$0000 *version
                    AGI_COMMAND cmd_script_size,$100 *script size
                    AGI_COMMAND cmd_set_game_id,$100 *set game id
                    AGI_COMMAND cmd_shake_screen,$100 *log
                    AGI_COMMAND cmd_set_scan_start,$0000 *set scan start
                    AGI_COMMAND cmd_reset_scan_start,$0000 *reset scan start
                    AGI_COMMAND cmd_reposition_to,$300 *reposition to
                    AGI_COMMAND cmd_reposition_to_v,$360 *reposition to v
                    AGI_COMMAND cmd_trace_on,$0000 *trace on
                    AGI_COMMAND cmd_trace_info,$300 *trace info
                    AGI_COMMAND cmd_print_at,$400 *print at
                    AGI_COMMAND cmd_print_at_v,$480 *print at v
                    AGI_COMMAND cmd_discard_view_v,$180 *discard view v
                    AGI_COMMAND cmd_clear_text_rect,$500 *clear text rect
                    AGI_COMMAND cmd_set_upper_left,$200 *set upper left
                    AGI_COMMAND cmd_set_menu,$100 *set menu
                    AGI_COMMAND cmd_set_menu_item,$200 *set menu item
                    AGI_COMMAND cmd_submit_menu,$0000 *submit menu
                    AGI_COMMAND cmd_enable_item,$100 *enable item
                    AGI_COMMAND cmd_disable_item,$100 *disable item
                    AGI_COMMAND cmd_menu_input,$0000 *menu input
                    AGI_COMMAND cmd_show_obj_v,$100 *show obj v
                    AGI_COMMAND NoopCmdsRet,$0000 *open dialogue
                    AGI_COMMAND NoopCmdsRet,$0000 *close dialogue
                    AGI_COMMAND cmd_multn,$280 *mult n
                    AGI_COMMAND cmd_multv,$2c0 *mult v
                    AGI_COMMAND cmd_divn,$280 *div n
                    AGI_COMMAND cmd_divv,$2c0 *div v
                    AGI_COMMAND cmd_close_window,$0000 *close window
                    AGI_COMMAND cmd_set_simple,$100 *set simple
                    AGI_COMMAND cmd_push_script,$0000 *push script
                    AGI_COMMAND cmd_pop_script,$0000 *pop script
                    AGI_COMMAND NoopCmdsRet,$0000 *hold key
                    AGI_COMMAND SetPriBaseStub,$100 *set pri base, via patch stub
                    AGI_COMMAND cmd_shake_screen,$180 *discard sound
                    AGI_COMMAND NoopCmdsRet,$0000 *do nothing
                    AGI_COMMAND cmd_show_menu,$100
                    AGI_COMMAND NoopCmdsRet,$0000 *do nothing
                    AGI_COMMAND cmd_hide_mouse,$400 *hide mouse
                    AGI_COMMAND cmd_set_upper_left,$2c0 *allow menu
                    AGI_COMMAND NoopCmdsRet,$0000 *do nothing
