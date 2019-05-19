#!/usr/bin/env python3

import datetime
import displays
import time
import traceback
import wettercom

from wettercom_apikey import API_KEY

client = displays.DisplayClient("localhost")
weather = wettercom.WetterCom('flipdot', API_KEY)

fc = weather.get_forecast("DE0003317005") # Meerholz
#fc = weather.get_forecast("DE0001961") # Darmstadt
now = datetime.datetime.now()

if now.hour > 8:
    day = (now + datetime.timedelta(days = 1)).strftime("%Y-%m-%d")
else:
    day = now.strftime("%Y-%m-%d")

displayed_forecasts = [
    fc[day]["06:00"],
    fc[day]["11:00"],
    fc[day]["17:00"],
]

width = 43
for index, w in enumerate(displayed_forecasts):
    xbase = width*index
    client.bitmap('front', "bitmaps/weather_icons/wettercom/{w:.1}.png".format(**w), left = xbase, top = 0)
    client.text('front', "{tn}/{tx}°".format(**w), font = "Flipdot8_Narrow", left = xbase+17, top = 0)
    client.text('front', "{ws}kmh".format(**w), font = "Flipdot8_Narrow", left = xbase+17, top = 9)

client.line('front', [width-2, 0, width-2, 15], width = 1)
client.line('front', [2*width-2, 0, 2*width-2, 15], width = 1)
client.commit('front')
client.sendall()
