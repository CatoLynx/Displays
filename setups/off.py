#!/usr/bin/env python3

import displays

client = displays.DisplayClient("localhost")

client.clear('desk')
client.clear('front')
client.clear('side')
client.clear('door')

client.commit('desk')
client.commit('front')
client.commit('side')
client.commit('door')

client.set_backlight('desk', False)
client.set_backlight('side', False)
client.set_backlight('front', False)
client.set_backlight('door', False)

client.sendall()
