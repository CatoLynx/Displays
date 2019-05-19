#!/usr/bin/env python3

import argparse
import datetime
import displays
import time

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--display', type = str, required = True)
parser.add_argument('-t', '--target', type = str, required = True)
args = parser.parse_args()

client = displays.DisplayClient("localhost")

now = datetime.datetime.now()
target = datetime.datetime.strptime(args.target, "%d.%m.%Y")

if now.date() == target.date():
    days = 0
else:
    days = (target - now).days + 1
client.text(args.display, "{:04d}".format(days), font = "Luminator16_Bold")
client.commit(args.display)
client.sendall()
print(days)
if days == 0:
    time.sleep(2)
    client.text(args.display, "HECK", font = "Luminator16_Bold")
    client.commit(args.display)
    client.sendall()
    time.sleep(2)
    
    client.text(args.display, "IT", font = "Luminator16_Bold")
    client.commit(args.display)
    client.sendall()
    time.sleep(0.5)
    
    client.text(args.display, "DOES", font = "Luminator16_Bold")
    client.commit(args.display)
    client.sendall()
    time.sleep(0.5)
    
    client.text(args.display, "ME", font = "Luminator16_Bold")
    client.commit(args.display)
    client.sendall()
    time.sleep(0.5)
    
    client.text(args.display, "A", font = "Luminator16_Bold")
    client.commit(args.display)
    client.sendall()
    time.sleep(0.5)
    
    client.text(args.display, "BIG", font = "Luminator16_Bold")
    client.commit(args.display)
    client.sendall()
    time.sleep(0.5)
    
    client.text(args.display, "XEW!", font = "Luminator16_Bold")
    client.commit(args.display)
    client.sendall()
    time.sleep(0.5)