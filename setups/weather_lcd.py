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
    day = (now + datetime.timedelta(days = 1))
else:
    day = now

times = ("06:00", "11:00", "17:00")
displayed_forecasts = [
    fc[day.strftime("%Y-%m-%d")][times[0]],
    fc[day.strftime("%Y-%m-%d")][times[1]],
    fc[day.strftime("%Y-%m-%d")][times[2]],
]

width = 48
for index, w in enumerate(displayed_forecasts):
    xbase = width*index
    client.bitmap('lcd', "bitmaps/weather_icons/wettercom/{w:.1}.png".format(**w), left = xbase, bottom = 25)
    client.text('lcd', "{tn}/{tx}°C".format(**w), font = "Flipdot8_Narrow", left = xbase+18, bottom = 18)
    client.text('lcd', "{ws}km/h".format(**w), font = "Flipdot8_Narrow", left = xbase+18, bottom = 26)

client.text('lcd', "{0} {1}".format(day.strftime("%a"), times[0]), font = "Flipdot8_Narrow", top = 0, center = 24)
client.text('lcd', "{0} {1}".format(day.strftime("%a"), times[1]), font = "Flipdot8_Narrow", top = 0, center = 24 + width)
client.text('lcd', "{0} {1}".format(day.strftime("%a"), times[2]), font = "Flipdot8_Narrow", top = 0, center = 24 + 2*width)
client.commit('lcd')
client.sendall()
