import serial
import time
from PIL import Image

port = serial.Serial("/dev/ttyUSB0", baudrate=57600)
img = Image.open("test.png").convert('L')

pixels = img.load()
width, height = img.size
bitmap = []
for x in range(width):
    col_byte = 0x00
    for y in range(height):
        if pixels[x, y] > 127:
            col_byte += 1 << (8 - y%8 - 1)
        if (y+1) % 8 == 0:
            bitmap.append(col_byte)
            col_byte = 0x00

port.write([0xFF, 0xA0, len(bitmap)] + bitmap)
time.sleep(1) # to prevent serial transmission from being cut off