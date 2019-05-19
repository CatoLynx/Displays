#!/usr/bin/env python3

import displays

client = displays.DisplayClient("localhost")

client.text('desk', "%H%M", timestring = True, font = "Luminator16_Bold",
    left = 1, refresh_interval = 'minute')
client.set_backlight('desk', True)
client.commit('desk')

client.sendall()