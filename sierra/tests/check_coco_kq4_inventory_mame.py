#!/usr/bin/env python3
"""Capture CoCo 3 KQ4 Inventory and scene restoration in MAME."""
import argparse
import json
from pathlib import Path
import subprocess

from check_wbpic_mame import png_rgb


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mame', required=True, type=Path)
    parser.add_argument('--rompath', required=True, type=Path)
    parser.add_argument('--disk1', required=True, type=Path)
    parser.add_argument('--disk2', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    disk2 = json.dumps(str(args.disk2.resolve()))
    shots = json.dumps(str(output))
    lua = f'''local frames=0
local function shot(name)
 manager.machine.screens[":screen"]:snapshot({shots}.."/"..name..".png")
end
local function post(text) manager.machine.natkeyboard:post(text) end
sub=emu.add_machine_frame_notifier(function()
 frames=frames+1
 if frames==3000 then post("DOS\\r") end
 if frames==8000 then
  manager.machine.ioport.ports[":row6"].fields["CTRL"]:set_value(1)
  manager.machine.ioport.ports[":row6"].fields["BREAK"]:set_value(1)
 end
 if frames==8010 then
  manager.machine.ioport.ports[":row6"].fields["CTRL"]:set_value(0)
  manager.machine.ioport.ports[":row6"].fields["BREAK"]:set_value(0)
 end
 if frames==19000 then shot("intro-1") end
 if frames==20000 then post(" ") end
 if frames==26000 then shot("intro-2") end
 if frames==27000 then post(" ") end
 if frames==33000 then shot("intro-3") end
 if frames==34000 then post(" ") end
 if frames==40000 then shot("intro-4") end
 if frames==41000 then post(" ") end
 if frames==47000 then shot("intro-5") end
 if frames==48000 then post("look\\r") end
 if frames==55000 then shot("look") end
 if frames==56000 then post(" ") end
 if frames==58000 then shot("look-restored") end
 if frames==59000 then post("inventory\\r") end
 if frames==62000 then shot("inventory-disk-prompt") end
 if frames==63000 then
  local disk=nil
  for _,candidate in pairs(manager.machine.images) do
   if candidate.instance_name=="floppydisk1" then disk=candidate end
  end
  assert(disk,"floppydisk1 image missing")
  disk:unload()
  local err=disk:load({disk2})
  assert(not err,err)
 end
 if frames==63100 then post("\\r") end
 if frames==64000 then post("inventory\\r") end
 if frames==69000 then shot("inventory") end
 if frames==70000 then post(" ") end
 if frames==72000 then shot("inventory-restored") end
 if frames==72500 then post("look room\\r") end
 if frames==80000 then shot("look-room") end
 if frames==82000 then manager.machine:exit() end
end)
'''
    lua_path = output / 'capture.lua'
    lua_path.write_text(lua)
    command = [str(args.mame.resolve()), 'coco3', '-rompath', str(args.rompath.resolve()),
               '-ext', 'fdc', '-ext:fdc:wd17xx:0', '525qd',
               '-flop1', str(args.disk1.resolve()), '-video', 'none', '-sound', 'none',
               '-skip_gameinfo', '-nothrottle', '-autoboot_script', str(lua_path),
               '-seconds_to_run', '1390', '-cfg_directory', str(output / 'cfg')]
    (output / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
    with (output / 'mame.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=240)

    inventory = png_rgb(output / 'inventory.png')
    restored = png_rgb(output / 'inventory-restored.png')
    width, height, pixels = inventory
    colors = set(pixels[index:index + 3]
                 for index in range(0, len(pixels), 3))
    white = pixels.count(bytes((255, 255, 255)))
    black = pixels.count(bytes(3))
    assert (width, height) == (640, 239), (width, height)
    assert colors == {bytes(3), bytes((255, 255, 255))}, colors
    assert white > 100_000 and black > 10_000, (white, black)
    restored_colors = set(restored[2][index:index + 3]
                          for index in range(0, len(restored[2]), 3))
    assert len(restored_colors) >= 10, len(restored_colors)
    assert inventory != restored, 'CoCo Inventory dismissal did not restore its picture'
    look = png_rgb(output / 'look.png')
    look_closed = png_rgb(output / 'look-restored.png')
    assert look[:2] == look_closed[:2] == (640, 239)

    def region_stats(image, box):
        x0, y0, x1, y1 = box
        colors = set()
        white = black = 0
        for y in range(y0, y1):
            for x in range(x0, x1):
                color = image[(y * 640 + x) * 3:(y * 640 + x) * 3 + 3]
                colors.add(color)
                white += color == bytes((255, 255, 255))
                black += color == bytes(3)
        area = (x1 - x0) * (y1 - y0)
        return {'colors': len(colors), 'white_fraction': white / area,
                'black_fraction': black / area}

    look_popup = region_stats(look[2], (20, 25, 620, 87))
    closed_scene = region_stats(look_closed[2], (20, 25, 620, 87))
    look_colors = set(look[2][index:index + 3]
                      for index in range(0, len(look[2]), 3))
    closed_colors = set(look_closed[2][index:index + 3]
                        for index in range(0, len(look_closed[2]), 3))
    assert look_popup['white_fraction'] > 0.55 and \
        look_popup['black_fraction'] > 0.18, look_popup
    assert closed_scene['white_fraction'] < 0.25 and len(closed_colors) >= 10, \
        (closed_scene, len(closed_colors))
    assert closed_colors == look_colors, 'CoCo close.window changed scene palette'
    look = png_rgb(output / 'look-room.png')
    look_width, look_height, look_pixels = look
    assert (look_width, look_height) == (640, 239), (look_width, look_height)

    popup = region_stats(look_pixels, (76, 83, 562, 143))
    left_scene = region_stats(look_pixels, (0, 8, 75, 180))
    right_scene = region_stats(look_pixels, (562, 8, 640, 180))
    assert popup['white_fraction'] > 0.70 and popup['black_fraction'] > 0.12, popup
    assert left_scene['colors'] >= 4 and right_scene['colors'] >= 8, \
        ('CoCo look popup obscured the scene outside its bounds', left_scene, right_scene)
    result = {'inventory_resolution': [width, height],
              'inventory_black_pixels': black,
              'inventory_white_pixels': white,
              'restored_scene_colors': len(restored_colors),
              'ordinary_look_popup': look_popup,
              'look_closed_scene': closed_scene,
              'look_closed_scene_colors': len(closed_colors),
              'look_popup': popup,
              'look_scene_left_colors': left_scene['colors'],
              'look_scene_right_colors': right_scene['colors']}
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: CoCo 3 KQ4 Inventory is a full black-on-white text screen; fresh Space restores the game picture; ordinary look text overlays the scene and dismissal restores its 16-color display', result)


if __name__ == '__main__':
    main()
