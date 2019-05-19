"""
(C) 2016 Julian Metzler
"""

import math

from .display_bitmap import BitmapDisplay

class ADtranzLCDisplay(BitmapDisplay):
    """
    Modified ADtranz LC display
    """
    
    DEFAULT_FONT = "Luminator16_Bold"
    
    def __str__(self):
        return "ADtranz LCD Display '{name}' ({width} x {height})".format(
            name = self.name, width = self.width, height = self.height)

    def commit(self):
        """
        Send the current internal bitmap to the display.
        
        BITMAP FORMAT:
        A list of bytes, each one representing a horizontal slice of 8 pixels,
        slices going from top to bottom, columns of slices going left to right
        """
        
        pixels = self.img.load()
        width, height = self.img.size
        bitmap = [0] * height * math.ceil(width/8)
        for x in range(width):
            for y in range(height):
                bitmap[x//8*height + y] |= (pixels[x, y] > 127) << x%8
        
        self.init_image()
        return self.send_message(
            [0xFF, 0xA0, len(bitmap) >> 8 & 0xFF, len(bitmap) & 0xFF] + bitmap)
    
    def set_backlight(self, level):
        """
        Set background light level.
        
        level:
        Either 0, 1 or 2, 0 being off and 2 being full brightness
        """
        
        return self.set_option(1, level)