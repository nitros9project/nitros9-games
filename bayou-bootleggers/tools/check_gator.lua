-- Alligator approach/lunge smoke check; use BAYOU_SNAPDIR for captures.
local snapshots=os.getenv("BAYOU_SNAPDIR") or "screenshots"
manager.machine.ioport.ports[":screen_config"].fields["Monitor Type"].user_value=1
manager.machine.natkeyboard.in_use=true
manager.machine.natkeyboard:post("DOS\r")
emu.wait(32)
manager.machine.natkeyboard:post("bayou\r")
emu.wait(26)
manager.machine.natkeyboard.in_use=false
assert(not manager.machine.natkeyboard.in_use, "Gameplay requires emulated keyboard mode")
manager.machine.screens[":screen"]:snapshot(snapshots.."/gator-title.png")
manager.machine.ioport.ports[":row3"].fields["SPACE"]:set_value(1)
emu.wait(3)
manager.machine.ioport.ports[":row3"].fields["SPACE"]:set_value(0)
emu.wait(12)
manager.machine.screens[":screen"]:snapshot(snapshots.."/gator-lurk.png")
manager.machine.ioport.ports[":row3"].fields["RIGHT"]:set_value(1)
emu.wait(3.5)
manager.machine.ioport.ports[":row3"].fields["RIGHT"]:set_value(0)
manager.machine.ioport.ports[":row3"].fields["DOWN"]:set_value(1)
emu.wait(0.8)
manager.machine.ioport.ports[":row3"].fields["DOWN"]:set_value(0)
for i=1,8 do
 manager.machine.screens[":screen"]:snapshot(snapshots.."/gator-"..i..".png")
 emu.wait(0.25)
end
manager.machine.natkeyboard:post("q")
emu.wait(3)
manager.machine:exit()
