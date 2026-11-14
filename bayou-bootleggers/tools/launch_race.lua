manager.machine.ioport.ports[":screen_config"].fields["Monitor Type"].user_value=1
manager.machine.natkeyboard.in_use=true
manager.machine.natkeyboard:post("DOS\r")
emu.wait(40)
manager.machine.natkeyboard:post("teeboy\r")
emu.wait(26)
local snapshots=os.getenv("BAYOU_SNAPDIR")
if snapshots then manager.machine.screens[":screen"]:snapshot(snapshots.."/race-launched-title.png") end
-- Use direct matrix input for held movement and simultaneous game buttons.
manager.machine.natkeyboard.in_use=false
manager.machine.video.throttled=true
print("Linzay Downs title screen ready")
