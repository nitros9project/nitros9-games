-- Native race smoke check: title, gallop/sprint, finish, and return to shell.
local snapshots=os.getenv("BAYOU_SNAPDIR") or "screenshots"
manager.machine.ioport.ports[":screen_config"].fields["Monitor Type"].user_value=1
manager.machine.natkeyboard.in_use=true
manager.machine.natkeyboard:post("DOS\r")
emu.wait(32)
manager.machine.natkeyboard:post("teeboy\r")
emu.wait(26)
manager.machine.natkeyboard.in_use=false
manager.machine.screens[":screen"]:snapshot(snapshots.."/race-title.png")
manager.machine.ioport.ports[":row3"].fields["SPACE"]:set_value(1)
emu.wait(2)
manager.machine.ioport.ports[":row3"].fields["SPACE"]:set_value(0)
manager.machine.ioport.ports[":row3"].fields["RIGHT"]:set_value(1)
for i=1,14 do
 emu.wait(1)
 manager.machine.screens[":screen"]:snapshot(snapshots.."/crowd-"..i..".png")
end
manager.machine.screens[":screen"]:snapshot(snapshots.."/race-start.png")
manager.machine.ioport.ports[":row3"].fields["RIGHT"]:set_value(1)
for i=1,12 do
 manager.machine.ioport.ports[":row3"].fields["SPACE"]:set_value(1)
 emu.wait(2)
 manager.machine.ioport.ports[":row3"].fields["SPACE"]:set_value(0)
 emu.wait(3)
 if i==2 then manager.machine.screens[":screen"]:snapshot(snapshots.."/race-mid.png") end
end
manager.machine.ioport.ports[":row3"].fields["RIGHT"]:set_value(0)
manager.machine.screens[":screen"]:snapshot(snapshots.."/race-finish.png")
manager.machine.natkeyboard:post("r")
emu.wait(10)
manager.machine.screens[":screen"]:snapshot(snapshots.."/race-restart.png")
manager.machine.natkeyboard:post("q")
emu.wait(3)
manager.machine.screens[":screen"]:snapshot(snapshots.."/race-quit.png")
manager.machine:exit()
