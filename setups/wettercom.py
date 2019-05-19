"""
Python wrapper for the wetter.com API
Project Management: http://at.wetter.com/apps_und_mehr/website/api/projekte/
"""

import datetime
import hashlib
import requests

class WetterCom(object):
    def __init__(self, project, key):
        self.project = project
        self.key = key

    def search(self, query):
        query = str(query)
        checksum = hashlib.md5((self.project + self.key + query).encode('utf-8')).hexdigest()
        return requests.get("https://api.wetter.com/location/index/search/{query}/project/{project}/cs/{checksum}?output=json".format(
            query = query, project = self.project, checksum = checksum)).json()

    def search_name(self, query):
        query = str(query)
        checksum = hashlib.md5((self.project + self.key + query).encode('utf-8')).hexdigest()
        return requests.get("https://api.wetter.com/location/name/search/{query}/project/{project}/cs/{checksum}?output=json".format(
            query = query, project = self.project, checksum = checksum)).json()

    def search_plz(self, query):
        query = str(query)
        checksum = hashlib.md5((self.project + self.key + query).encode('utf-8')).hexdigest()
        return requests.get("https://api.wetter.com/location/plz/search/{query}/project/{project}/cs/{checksum}?output=json".format(
            query = query, project = self.project, checksum = checksum)).json()

    def get_forecast(self, city_code):
        checksum = hashlib.md5((self.project + self.key + city_code).encode('utf-8')).hexdigest()
        return requests.get("https://api.wetter.com/forecast/weather/city/{city_code}/project/{project}/cs/{checksum}?output=json".format(
            city_code = city_code, project = self.project, checksum = checksum)).json()['city']['forecast']

    def get_current(self, city_code):
        forecast = self.get_forecast(city_code)
        now = datetime.datetime.now()

        # Flatten the array
        _forecast = {}
        for day, fc_day in forecast.items():
            for time, fc_time in fc_day.items():
                if ":" in time:
                    _forecast[day + " " + time] = fc_time

        # Find the closest forecast to now
        closest_time = ""
        closest_delta = 0
        for timestamp, fc in _forecast.items():
            dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
            delta = abs((dt-now).total_seconds())
            if not closest_delta or delta < closest_delta:
                closest_time = timestamp
                closest_delta = delta
        return _forecast[closest_time]