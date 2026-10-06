* One AGI command catalog for CoCo dispatch and native decoding/dispatch.
* Fields: CoCo handler, operand descriptor, native platform handler, game-only.
* Owners expand their fields at assembly time; unsupported native commands
* retain an explicit error target. No mutable dispatch addresses are emitted.
                    AGI_COMMAND NoopCmdsRet,$0000,VmPlatformUnsupported,0 *do nothing
                    AGI_COMMAND cmd_increment,$180,VmPlatformUnsupported,0 *increment
                    AGI_COMMAND cmd_decrement,$180,VmPlatformUnsupported,0 *decrement
                    AGI_COMMAND cmd_assignn,$280,VmPlatformUnsupported,0 *assign nn
                    AGI_COMMAND cmd_assignv,$2c0,VmPlatformUnsupported,0 *assign nv
                    AGI_COMMAND cmd_addn,$280,VmPlatformUnsupported,0 *add n
                    AGI_COMMAND cmd_addv,$2c0,VmPlatformUnsupported,0 *add v
                    AGI_COMMAND cmd_subn,$280,VmPlatformUnsupported,0 *sub n
                    AGI_COMMAND cmd_subv,$2c0,VmPlatformUnsupported,0 *sub v
                    AGI_COMMAND cmd_lindirectv,$2c0,VmPlatformUnsupported,0 *l indirect v
                    AGI_COMMAND cmd_rindirect,$2c0,VmPlatformUnsupported,0 *r indirect
                    AGI_COMMAND cmd_lindirectn,$280,VmPlatformUnsupported,0 *l indirect n
                    AGI_COMMAND CmdSetImpl,$100,VmPlatformUnsupported,0 *set
                    AGI_COMMAND CmdResetImpl,$100,VmPlatformUnsupported,0 *reset
                    AGI_COMMAND CmdToggleImpl,$100,VmPlatformUnsupported,0 *toggle
                    AGI_COMMAND CmdSetVImpl,$180,VmPlatformUnsupported,0 *set v
                    AGI_COMMAND CmdResetVImpl,$180,VmPlatformUnsupported,0 *reset v
                    AGI_COMMAND CmdToggleVImpl,$180,VmPlatformUnsupported,0 *toggle v
                    AGI_COMMAND cmd_new_room,$100,VmCommandNewRoom,0 *new room
                    AGI_COMMAND cmd_new_room_v,$180,VmCommandNewRoomVariable,0 *new room v
                    AGI_COMMAND cmd_load_logics,$100,VmCommandLoadLogic,0 *load logics
                    AGI_COMMAND cmd_load_logics_v,$180,VmCommandLoadLogicVariable,0 *load logics v
                    AGI_COMMAND cmd_call,$100,VmCommandCallLogic,0 *call
                    AGI_COMMAND cmd_call_v,$180,VmCommandCallLogicVariable,0 *call v
                    AGI_COMMAND cmd_load_pic,$180,GameLoadPicture,1 *load pic
                    AGI_COMMAND cmd_draw_pic,$180,GameDrawPicture,1 *draw pic
                    AGI_COMMAND cmd_show_pic,$0000,GameShowPicture,1 *show pic
                    AGI_COMMAND cmd_discard_pic,$180,GameDiscardPicture,1 *discard overlay
                    AGI_COMMAND cmd_overlay_pic,$180,VmPlatformUnsupported,0 *animate obj
                    AGI_COMMAND CmdSaveGame,$0000,VmPlatformUnsupported,0 *show pri
                    AGI_COMMAND cmd_load_view,$100,VmCommandLoadView,0 *load view
                    AGI_COMMAND cmd_load_view_v,$180,VmCommandLoadViewVariable,0 *load view v
                    AGI_COMMAND cmd_discard_view,$100,VmCommandDiscardView,0 *discard view
                    AGI_COMMAND CmdAnimateObj,$100,ObjectCommand,0 *animate obj
                    AGI_COMMAND CmdUnanimateAll,$0000,ObjectCommand,0 *unanumate all
                    AGI_COMMAND CmdDrawImpl,$100,GameObjectVisibility,1 *draw
                    AGI_COMMAND CmdEraseImpl,$100,GameObjectVisibility,1 *erase
                    AGI_COMMAND cmd_position,$300,ObjectCommand,0 *position
                    AGI_COMMAND cmd_position_v,$360,ObjectCommand,0 *position v
                    AGI_COMMAND cmd_get_position,$360,ObjectCommand,0 *get position
                    AGI_COMMAND cmd_reposition,$360,GameReposition,1 *reposition
                    AGI_COMMAND cmd_set_view,$200,ViewCommand,0 *set view
                    AGI_COMMAND cmd_set_view_v,$240,ViewCommand,0 *set view v
                    AGI_COMMAND cmd_set_loop,$200,ViewCommand,0 *set loop
                    AGI_COMMAND cmd_set_loop_v,$240,ViewCommand,0 *set loop v
                    AGI_COMMAND CmdFixLoop,$100,ObjectCommand,0 *fix loop
                    AGI_COMMAND CmdReleaseLoop,$100,ObjectCommand,0 *release loop
                    AGI_COMMAND cmd_set_cel,$200,ViewCommand,0 *set cel
                    AGI_COMMAND cmd_set_cel_v,$240,ViewCommand,0 *set cel v
                    AGI_COMMAND cmd_last_cel,$240,ViewCommand,0 *last cel
                    AGI_COMMAND cmd_current_cel,$240,ViewCommand,0 *current cel
                    AGI_COMMAND cmd_current_loop,$240,ViewCommand,0 *current loop
                    AGI_COMMAND cmd_current_view,$240,ViewCommand,0 *current view
                    AGI_COMMAND cmd_number_of_loops,$240,ViewCommand,0 *number of loops
                    AGI_COMMAND cmd_set_priority,$200,ObjectCommand,0 *set priority
                    AGI_COMMAND cmd_set_priority_v,$240,ObjectCommand,0 *set priority v
                    AGI_COMMAND cmd_release_priority,$100,ObjectCommand,0 *release priority
                    AGI_COMMAND cmd_get_priority,$240,ObjectCommand,0 *get priority
                    AGI_COMMAND CmdStopUpdate,$100,ObjectCommand,0 *stop update
                    AGI_COMMAND CmdStartUpdate,$100,ObjectCommand,0 *start update
                    AGI_COMMAND CmdForceUpdate,$100,GameForceUpdate,1 *force update
                    AGI_COMMAND cmd_ignore_horizon,$100,ObjectFlagCommand,0 *ignore horizon
                    AGI_COMMAND cmd_observe_horizon,$100,ObjectFlagCommand,0 *observe horizon
                    AGI_COMMAND cmd_set_horizon,$100,ObjectFlagCommand,0 *set horizon
                    AGI_COMMAND cmd_obj_on_water,$100,ObjectFlagCommand,0 *obj on water
                    AGI_COMMAND cmd_obj_on_land,$100,ObjectFlagCommand,0 *obj on land
                    AGI_COMMAND cmd_obj_on_anything,$100,ObjectFlagCommand,0 *obj on anything
                    AGI_COMMAND CmdIgnoreObjects,$100,ObjectFlagCommand,0 *ignore objects
                    AGI_COMMAND CmdObserveObjects,$100,ObjectFlagCommand,0 *observe objects
                    AGI_COMMAND CmdDistance,$320,ObjectDistanceCommand,0 *distance
                    AGI_COMMAND CmdStopCycling,$100,ObjectCycleCommand,0 *stop cycling
                    AGI_COMMAND CmdStartCycling,$100,ObjectCycleCommand,0 *start cycling
                    AGI_COMMAND CmdNormalCycle,$100,ObjectCycleCommand,0 *normal cycle
                    AGI_COMMAND CmdEndOfLoop,$200,ObjectCycleCommand,0 *end of loop
                    AGI_COMMAND CmdReverseCycle,$100,ObjectCycleCommand,0 *reverse cycle
                    AGI_COMMAND CmdReverseLoop,$200,ObjectCycleCommand,0 *reverse loop
                    AGI_COMMAND CmdSetCycleTime,$240,ObjectCycleCommand,0 *cycle time
                    AGI_COMMAND cmd_stop_motion,$100,ObjectCycleCommand,0 *stop motion
                    AGI_COMMAND cmd_start_motion,$100,ObjectCycleCommand,0 *start motion
                    AGI_COMMAND cmd_step_size_v,$240,ObjectCycleCommand,0 *step size
                    AGI_COMMAND cmd_step_time,$240,ObjectCycleCommand,0 *step time
                    AGI_COMMAND cmd_move_obj,$500,GameMoveCommand,1 *move obj
                    AGI_COMMAND cmd_move_obj_v,$570,GameMoveCommand,1 *move obj v
                    AGI_COMMAND cmd_follow_ego,$300,GameFollowCommand,1 *follow ego
                    AGI_COMMAND cmd_wander,$100,GameWanderCommand,1 *wander
                    AGI_COMMAND cmd_normal_motion,$100,ObjectCycleCommand,0 *normal motion
                    AGI_COMMAND cmd_set_dir,$240,ObjectCommand,0 *set dir
                    AGI_COMMAND cmd_get_dir,$240,ObjectCommand,0 *get dir
                    AGI_COMMAND CmdIgnoreBlocks,$100,ObjectFlagCommand,0 *ignore blocks
                    AGI_COMMAND CmdObserveBlocks,$100,ObjectFlagCommand,0 *observe blocks
                    AGI_COMMAND CmdSetBlock,$400,GameBlockCommand,1 *block
                    AGI_COMMAND CmdClearBlock,$0000,GameBlockCommand,1 *unblock
                    AGI_COMMAND cmd_get,$100,InventoryCommand,1 *get
                    AGI_COMMAND cmd_get_v,$180,InventoryCommand,1 *get v
                    AGI_COMMAND cmd_drop,$100,InventoryCommand,1 *drop
                    AGI_COMMAND cmd_put,$200,InventoryCommand,1 *put
                    AGI_COMMAND cmd_put_v,$240,InventoryCommand,1 *put v
                    AGI_COMMAND cmd_get_room_v,$2c0,InventoryCommand,1 *get room v
                    AGI_COMMAND cmd_load_sound,$100,VmCommandLoadSound,0 *load sound
                    AGI_COMMAND cmd_sound,$200,GameSoundCommand,1 *sound
                    AGI_COMMAND NoopCmdsRet,$0000,GameSoundCommand,1 *stop sound
                    AGI_COMMAND cmd_print,$100,GamePrintCommand,1 *print
                    AGI_COMMAND cmd_print_v,$180,GamePrintCommand,1 *print v
                    AGI_COMMAND cmd_display,$300,GameDisplayCommand,1 *display
                    AGI_COMMAND cmd_display_v,$3e0,GameDisplayCommand,1 *display v
                    AGI_COMMAND cmd_clear_lines,$300,GameClearLines,1 *clear lines
                    AGI_COMMAND cmd_text_screen,$0000,VmPlatformUnsupported,0 *text screen
                    AGI_COMMAND cmd_graphics,$0000,VmPlatformUnsupported,0 *graphics
                    AGI_COMMAND cmd_set_cursor_char,$100,ScreenCommand,0 *set cursor char
                    AGI_COMMAND cmd_set_text_attribute,$200,ScreenCommand,0 *set text attribute
                    AGI_COMMAND cmd_shake_screen,$100,VmPlatformUnsupported,0 *shake screen
                    AGI_COMMAND cmd_config_screen,$300,ScreenCommand,0 *config screen
                    AGI_COMMAND cmd_status_line_on,$0000,ScreenCommand,0 *status line on
                    AGI_COMMAND cmd_status_line_off,$0000,ScreenCommand,0 *status line off
                    AGI_COMMAND cmd_set_string,$200,SetStringCommand,0 *set string
                    AGI_COMMAND cmd_get_string,$500,GameGetInput,1 *get string
                    AGI_COMMAND cmd_word_to_string,$200,GameWordToString,1 *word to string
                    AGI_COMMAND cmd_parse,$100,ParserCommand,1 *parse
                    AGI_COMMAND CmdObjStatus,$240,GameGetInput,1 *get num
                    AGI_COMMAND cmd_prevent_input,$0000,ScreenCommand,0 *prevent input
                    AGI_COMMAND cmd_accept_input,$0000,ScreenCommand,0 *accept inpur
                    AGI_COMMAND CmdSetKey,$300,SetKeyCommand,0 *set key
                    AGI_COMMAND cmd_add_to_pic,$700,GameAddToPicture,1 *add to pic
                    AGI_COMMAND cmd_add_to_pic_v,$7fe,GameAddToPicture,1 *add to pic v
                    AGI_COMMAND cmd_status,$0000,InventoryStatus,1 *status
                    AGI_COMMAND cmd_save_game,$0000,VmPlatformUnsupported,0 *save game
                    AGI_COMMAND cmd_restore_game,$0000,VmPlatformUnsupported,0 *restore game
                    AGI_COMMAND NoopCmdsRet,$0000,VmPlatformUnsupported,0 *init disk
                    AGI_COMMAND cmd_restart_game,$0000,VmPlatformUnsupported,0 *restart game
                    AGI_COMMAND cmd_show_obj,$100,VmPlatformUnsupported,0 *sow obj
                    AGI_COMMAND CmdRandomImpl,$320,GameRandomCommand,1 *random
                    AGI_COMMAND cmd_program_control,$0000,VmProgramControl,0 *program control
                    AGI_COMMAND cmd_player_control,$0000,VmSetPlayerControl,0 *player control
                    AGI_COMMAND CmdObjStatusV,$180,VmPlatformUnsupported,0 *obj status v
                    AGI_COMMAND CmdQuitImpl,$100,GameQuitCommand,1 *quit
                    AGI_COMMAND CmdShowMemInfo,$0000,VmPlatformUnsupported,0 *show mem
                    AGI_COMMAND CmdPauseImpl,$0000,GamePauseCommand,1 *pause
                    AGI_COMMAND cmd_echo_line,$0000,GameEchoLine,1 *echo line
                    AGI_COMMAND cmd_cancel_line,$0000,GameCancelLine,1 *cancel line
                    AGI_COMMAND cmd_init_joy,$0000,VmPlatformUnsupported,0 *init joy
                    AGI_COMMAND cmd_toggle_monitor,$0000,VmPlatformUnsupported,0 *toggle monitor
                    AGI_COMMAND CmdShowAgiInfo,$0000,VmPlatformUnsupported,0 *version
                    AGI_COMMAND cmd_script_size,$100,ReplayInitialize,0 *script size
                    AGI_COMMAND cmd_set_game_id,$100,VmCommandGameId,0 *set game id
                    AGI_COMMAND cmd_shake_screen,$100,VmPlatformUnsupported,0 *log
                    AGI_COMMAND cmd_set_scan_start,$0000,VmCommandScanStart,0 *set scan start
                    AGI_COMMAND cmd_reset_scan_start,$0000,VmCommandScanReset,0 *reset scan start
                    AGI_COMMAND cmd_reposition_to,$300,GameReposition,1 *reposition to
                    AGI_COMMAND cmd_reposition_to_v,$360,GameReposition,1 *reposition to v
                    AGI_COMMAND cmd_trace_on,$0000,VmPlatformUnsupported,0 *trace on
                    AGI_COMMAND cmd_trace_info,$300,VmPlatformUnsupported,0 *trace info
                    AGI_COMMAND cmd_print_at,$400,VmPlatformUnsupported,0 *print at
                    AGI_COMMAND cmd_print_at_v,$480,VmPlatformUnsupported,0 *print at v
                    AGI_COMMAND cmd_discard_view_v,$180,VmCommandDiscardViewVariable,0 *discard view v
                    AGI_COMMAND cmd_clear_text_rect,$500,VmPlatformUnsupported,0 *clear text rect
                    AGI_COMMAND cmd_set_upper_left,$200,VmPlatformUnsupported,0 *set upper left
                    AGI_COMMAND cmd_set_menu,$100,MenuCommand,0 *set menu
                    AGI_COMMAND cmd_set_menu_item,$200,MenuCommand,0 *set menu item
                    AGI_COMMAND cmd_submit_menu,$0000,MenuCommand,0 *submit menu
                    AGI_COMMAND cmd_enable_item,$100,MenuCommand,0 *enable item
                    AGI_COMMAND cmd_disable_item,$100,MenuCommand,0 *disable item
                    AGI_COMMAND cmd_menu_input,$0000,GameMenuInput,1 *menu input
                    AGI_COMMAND cmd_show_obj_v,$100,VmPlatformUnsupported,0 *show obj v
                    AGI_COMMAND NoopCmdsRet,$0000,VmPlatformUnsupported,0 *open dialogue
                    AGI_COMMAND NoopCmdsRet,$0000,VmPlatformUnsupported,0 *close dialogue
                    AGI_COMMAND cmd_multn,$280,GameMathCommand,1 *mult n
                    AGI_COMMAND cmd_multv,$2c0,GameMathCommand,1 *mult v
                    AGI_COMMAND cmd_divn,$280,GameMathCommand,1 *div n
                    AGI_COMMAND cmd_divv,$2c0,GameMathCommand,1 *div v
                    AGI_COMMAND cmd_close_window,$0000,GameCloseWindow,1 *close window
                    AGI_COMMAND cmd_set_simple,$100,VmPlatformUnsupported,0 *set simple
                    AGI_COMMAND cmd_push_script,$0000,ReplaySaveCheckpoint,0 *push script
                    AGI_COMMAND cmd_pop_script,$0000,ReplayRestore,0 *pop script
                    AGI_COMMAND NoopCmdsRet,$0000,VmPlatformUnsupported,0 *hold key
                    AGI_COMMAND SetPriBaseStub,$100,VmPlatformUnsupported,0 *set pri base, via patch stub
                    AGI_COMMAND cmd_shake_screen,$180,VmPlatformUnsupported,0 *discard sound
                    AGI_COMMAND NoopCmdsRet,$0000,VmPlatformUnsupported,0 *do nothing
                    AGI_COMMAND cmd_show_menu,$100,VmPlatformUnsupported,0
                    AGI_COMMAND NoopCmdsRet,$0000,VmPlatformUnsupported,0 *do nothing
                    AGI_COMMAND cmd_hide_mouse,$400,VmPlatformUnsupported,0 *hide mouse
                    AGI_COMMAND cmd_set_upper_left,$2c0,VmPlatformUnsupported,0 *allow menu
                    AGI_COMMAND NoopCmdsRet,$0000,VmPlatformUnsupported,0 *do nothing
