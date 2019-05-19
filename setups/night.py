#!/usr/bin/env python3

import displays

client = displays.DisplayClient("localhost")

client.text('desk', "%d%m%y", timestring = True, font = "Itty", size = 4, top = 1, refresh_interval = 'minute')
client.binary_clock('desk', block_spacing_x = 2, top = 7, refresh_interval = 'minute')
client.commit('desk')

client.set_backlight('desk', False)
client.set_backlight('side', False)
client.set_backlight('front', False)

client.sendall()