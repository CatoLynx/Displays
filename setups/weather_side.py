#!/usr/bin/env python3

import displays
import re
import requests
import time
import traceback
import wettercom

from lxml import html
from wettercom_apikey import API_KEY

def upperfirst(x):
    return x[0].upper() + x[1:]

def _prepare_status(status):
    replacements = {
        "Leichter Schneefall": "Leicht. Schneefall",
        "Glatteisregen Orange": "Glatteisregen Orng",
        "Leichter Regen - Schauer": "L. Regen/Schauer",
    }
    status = upperfirst(status)
    for orig, repl in replacements.items():
        status = status.replace(orig, repl)
    return status

client = displays.DisplayClient("localhost")

# Get weather alerts
plz = 63571
page = requests.get("http://www.unwetterzentrale.de/uwz/getwarning_de.php?plz={plz}&uwz=UWZ-DE&lang=de".format(plz = plz))
page.encoding = 'UTF-8'
tree = html.fromstring(page.content)
divs = tree.xpath('//*[@id="content"]/div')
warnings = []
forewarnings = []
for div in divs:
    # Only process divs that contain warnings
    warning = div.xpath('div[1]/div[1]/div[1]')
    if not warning:
        continue
    match = re.match(r"Unwetterwarnung Stufe (?P<level>\w+) vor (?P<what>\w+)", warning[0].text_content())
    match_pre = re.match(r"Vorwarnung vor (?P<what>\w+), Warnstufe (?P<level>\w+) möglich", warning[0].text_content())
    if match:
        data = match.groupdict()
        warnings.append(data)
    elif match_pre:
        data = match_pre.groupdict()
        forewarnings.append(data)
    else:
        continue

if warnings:
    client.set_inverting('side', True)
    client.text('side', warnings[0]['what'].upper(), font = "Luminator7_Bold", halign = 'center', top = 1)
    client.text('side', warnings[0]['level'].upper(), font = "Luminator5_Bold", halign = 'center', top = 10)
else:
    # Get weather
    weather = wettercom.WetterCom('flipdot', API_KEY)
    w = weather.get_current("DE0003317005")
    icon = 'warning' if forewarnings else "wettercom/" + w['w'][0]
    status = _prepare_status("{what} {level}".format(**forewarnings[0]) if forewarnings else w['w_txt'])

    client.set_inverting('side', False)
    client.bitmap('side', "bitmaps/weather_icons/{0}.png".format(icon), left = 0, top = 0)
    client.text('side', status, font = "Flipdot8_Narrow", left = 18, top = 0)
    client.text('side', "{tn}/{tx}° {pc}% {ws}kmh".format(**w), font = "Flipdot8_Narrow", left = 18, top = 9)

client.commit('side')
client.sendall()
