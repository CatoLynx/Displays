import configparser
import datetime
import displays
import json
import os
import requests
import time
import traceback


class WeatherDisplay:
    def __init__(self, port, location, api_key):
        self.port = port
        self.location = location
        self.api_key = api_key
        self.weather = None
        self.display_manager = displays.DisplayManager(self.port)
        self.display = displays.LAWOFlipdotDisplay(28, 16, font_handler=None, name='flipdot')
        self.display_manager.register_display(0, self.display)
    
    def _load_weather(self):
        data = requests.get("https://api.openweathermap.org/data/2.5/forecast?APPID={}&lat={}&lon={}".format(self.api_key, self.location[0], self.location[1])).json()
        #with open("out.json", "w") as f:
        #    json.dump(data, f, indent=4, sort_keys=True)
        #with open("out.json", "r") as f:
        #    data = json.load(f)
        self.weather = data['list']
    
    def update(self):
        self._load_weather()
        now = datetime.datetime.now()
        epoch_in_12_h = int((now + datetime.timedelta(seconds=60*60*12)).timestamp())
        closest_index = -1
        closest_epoch_diff = 999999999999999
        for index, data in enumerate(self.weather):
            epoch_diff = abs(data['dt'] - epoch_in_12_h)
            if epoch_diff < closest_epoch_diff:
                closest_epoch_diff = epoch_diff
                closest_index = index
        next_weather = self.weather[closest_index]
        temp_high = round(next_weather['main']['temp_max'] - 273.15)
        temp_high_str = str(temp_high).rjust(2, '0')
        icon = next_weather['weather'][0]['icon']
        
        dirname = os.path.dirname(__file__)
        self.display.clear()
        # Render icon
        self.display.bitmap(os.path.join(dirname, "icons/weather/{}.png".format(icon)), right=27, top=1)
        # Render temperature sign
        if temp_high > 0:
            self.display.bitmap(os.path.join(dirname, "icons/text/plus.png"), left=0, top=1)
        elif temp_high < 0:
            self.display.bitmap(os.path.join(dirname, "icons/text/minus.png"), left=0, top=1)
        # Render temperature
        self.display.bitmap(os.path.join(dirname, "icons/text/{}.png".format(temp_high_str[0])), left=0, top=7)
        self.display.bitmap(os.path.join(dirname, "icons/text/{}.png".format(temp_high_str[1])), left=4, top=7)
        self.display.commit()


def main():
    basename = os.path.splitext(os.path.basename(__file__))[0]
    config_parser = configparser.ConfigParser()
    config_parser.read("{}.ini".format(basename))
    config = config_parser['WeatherDisplay']
    location = (float(config['LocationLat']), float(config['LocationLon']))
    weather_display = WeatherDisplay(config['Port'], location, config['ApiKey'])
    weather_display.update()

if __name__ == "__main__":
    main()