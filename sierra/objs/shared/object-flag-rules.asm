* Handler, opcode, record offset, AND mask, OR mask, legacy pointer register.
                    OBJECT_FLAG_RULE CmdFixLoop,45,$25,$FF,$20,x
                    OBJECT_FLAG_RULE CmdReleaseLoop,46,$25,$DF,$00,x
                    OBJECT_FLAG_RULE cmd_release_priority,56,$26,$FB,$00,u
                    OBJECT_FLAG_RULE cmd_ignore_horizon,61,$26,$FF,$08,u
                    OBJECT_FLAG_RULE cmd_observe_horizon,62,$26,$F7,$00,u
                    OBJECT_FLAG_RULE cmd_obj_on_water,64,$25,$FF,$01,u
                    OBJECT_FLAG_RULE cmd_obj_on_land,65,$25,$FF,$08,u
                    OBJECT_FLAG_RULE cmd_obj_on_anything,66,$25,$F6,$00,u
                    OBJECT_FLAG_RULE CmdIgnoreObjects,67,$25,$FF,$02,u
                    OBJECT_FLAG_RULE CmdObserveObjects,68,$25,$FD,$00,u
                    OBJECT_FLAG_RULE CmdStopCycling,70,$26,$DF,$00,u
                    OBJECT_FLAG_RULE CmdStartCycling,71,$26,$FF,$20,u
                    OBJECT_FLAG_RULE CmdIgnoreBlocks,88,$26,$FF,$02,u
                    OBJECT_FLAG_RULE CmdObserveBlocks,89,$26,$FD,$00,u
