* View-state handlers use the common record-to-variable query implementation.
                    OBJECT_FIELD_QUERY cmd_last_cel,$0F,1
                    OBJECT_FIELD_QUERY cmd_current_cel,$0E,0
                    OBJECT_FIELD_QUERY cmd_current_loop,$0A,0
                    OBJECT_FIELD_QUERY cmd_current_view,$05,0
                    OBJECT_FIELD_QUERY cmd_number_of_loops,$0B,0
