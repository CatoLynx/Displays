#!/usr/bin/env python3

import argparse
import datetime
import displays
import time

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--display', type = str, required = True)
parser.add_argument('-m', '--minutes', type = int, required = True)
args = parser.parse_args()

client = displays.DisplayClient("localhost")

target = datetime.datetime.now() + datetime.timedelta(minutes = args.minutes)

while datetime.datetime.now() < target:
    seconds = (target-datetime.datetime.now()).total_seconds()
    minutes, seconds = divmod(seconds, 60)
    client.text(args.display, "%04i" % (minutes+1), font = "Luminator16_Bold")
    client.commit(args.display)
    client.sendall()
    time.sleep(60)

client.text(args.display, "END", font = "Luminator7_Bold")
client.commit(args.display)
client.sendall()