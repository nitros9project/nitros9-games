-- Native gameplay smoke check; set BAYOU_SNAPDIR to an existing directory.
local snapshots=os.getenv("BAYOU_SNAPDIR") or "screenshots"
manager.machine.ioport.ports[":screen_config"].fields["Monitor Type"].user_value=1
manager.machine.natkeyboard.in_use=true
manager.machine.natkeyboard:post("DOS\r")
emu.wait(32)
manager.machine.natkeyboard:post("bayou\r")
emu.wait(26)
manager.machine.natkeyboard.in_use=false
assert(not manager.machine.natkeyboard.in_use, "Gameplay requires emulated keyboard mode")
manager.machine.screens[":screen"]:snapshot(snapshots.."/title.png")
manager.machine.ioport.ports[":row3"].fields["SPACE"]:set_value(1)
emu.wait(3)
manager.machine.ioport.ports[":row3"].fields["SPACE"]:set_value(0)
emu.wait(25)
manager.machine.screens[":screen"]:snapshot(snapshots.."/play.png")
manager.machine.ioport.ports[":row3"].fields["RIGHT"]:set_value(1)
emu.wait(3)
manager.machine.ioport.ports[":row3"].fields["RIGHT"]:set_value(0)
for i=1,4 do
  manager.machine.ioport.ports[":row6"].fields["CTRL"]:set_value(1)
  emu.wait(0.4)
  manager.machine.ioport.ports[":row6"].fields["CTRL"]:set_value(0)
  emu.wait(0.5)
end
manager.machine.screens[":screen"]:snapshot(snapshots.."/fight.png")
manager.machine.natkeyboard:post("q")
emu.wait(3)
manager.machine.screens[":screen"]:snapshot(snapshots.."/quit.png")
manager.machine:exit()
