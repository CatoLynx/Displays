"""
(C) 2016 Julian Metzler
"""

from .display_bitmap import BitmapDisplay

class LAWOFlipdotDisplay(BitmapDisplay):
    """
    Modified LAWO Flipdot display
    """
    
    DEFAULT_FONT = "Luminator16_Bold"
    
    def __str__(self):
        return "LAWO Flipdot Display '{name}' ({width} x {height})".format(
            name = self.name, width = self.width, height = self.height)

    def commit(self):
        """
        Send the current internal bitmap to the display.
        
        BITMAP FORMAT:
        A list of bytes, two consecutive bytes representing a 16-pixel
        display column from top to bottom.
        """
        
        pixels = self.img.load()
        width, height = self.img.size
        bitmap = []
        for x in range(width):
            col_byte = 0x00
            for y in range(height):
                if pixels[x, y] > 127:
                    col_byte += 1 << (8 - y%8 - 1)
                if (y+1) % 8 == 0:
                    bitmap.append(col_byte)
                    col_byte = 0x00
        
        self.init_image()
        return self.send_message(
            [0xFF, 0xA0, len(bitmap)] + bitmap)
    
    def set_backlight(self, state):
        """
        Enable or disable the LED pixel illumination.
        
        state:
        Either 0 or 1, representing ON or OFF respectively
        """
        
        return self.set_option(1, 0x01 if state else 0)
    
    def set_inverting(self, state):
        """
        Enable or disable pixel inverting.
        
        state:
        Either 0 or 1, representing ON or OFF respectively
        """
        
        return self.set_option(2, 0x01 if state else 0)
    
    def set_active(self, state):
        """
        Enable or disable the matrix.
        
        state:
        Either 0 or 1, representing ON or OFF respectively
        """
        
        return self.set_option(3, 0x01 if state else 0)
    
    def set_quick_update(self, state):
        """
        Enable or disable quick pixel updating.
        
        state:
        Either 0 or 1, representing ON or OFF respectively
        """
        
        return self.set_option(4, 0x01 if state else 0)