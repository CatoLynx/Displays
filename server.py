#!/usr/bin/env python3

import argparse
import displays

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', type = str, required = True)
args = parser.parse_args()

h = displays.FontHandler()
m = displays.DisplayManager(args.port)

front = displays.LAWOFlipdotDisplay(126, 16, font_handler = h,
    name = 'front')
side = displays.LAWOFlipdotDisplay(84, 16, font_handler = h, name = 'side')
desk = displays.LAWOFlipdotDisplay(28, 16, font_handler = h, name = 'desk')
door = displays.LAWOFlipdotDisplay(28, 16, font_handler = h, name = 'door')
lcd = displays.ADtranzLCDisplay(144, 26, font_handler = h, name = 'lcd')
lva = displays.BroseLVADisplay(9, name = 'lva')
led = displays.AnnaxLEDDisplay(120, 8, bitmap_width = 800,
    font_handler = h, name = 'led')

m.register_display(0, side)
m.register_display(1, front)
m.register_display(2, desk)
m.register_display(3, door)
#m.register_display(8, lcd)
#m.register_display(5, lva)
#m.register_display(6, led)

server = displays.DisplayServer(m, verbose = True)
server.run()
