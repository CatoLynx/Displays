import datetime
import displays
import time
from PIL import Image, ImageSequence

m = displays.DisplayManager("/dev/ttyUSB0", timeout = 0.0)
d = displays.LAWOFlipdotDisplay(126, 16, name = 'front')
m.register_display(6, d)

d.set_backlight(True)

target = datetime.datetime(2016, 12, 29, 20, 19, 0)
while True:
    now = datetime.datetime.now()
    delta = target - now
    total_seconds = round(delta.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    d.vertical_text("{:02d}:{:02d}".format(minutes, seconds), font = "Arial Bold", size = 30)
    d.commit()
    if total_seconds <= 0:
        break
    time.sleep(1)

for n in range(5):
    image = Image.open("new_year.gif")
    for frame in ImageSequence.Iterator(image):
        frame = frame.convert("RGBA")
        d.bitmap(frame)
        d.commit()

d.vertical_text("Frohes Neues", font = "Arial Bold", size = 13)
d.bitmap("champagne.png", left = 61)
d.commit()