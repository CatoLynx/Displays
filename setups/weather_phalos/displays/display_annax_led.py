"""
(C) 2016 Julian Metzler
"""

import math

from .display_bitmap import BitmapDisplay

class AnnaxLEDDisplay(BitmapDisplay):
    """
    Modified ANNAX LED display
    """
    
    DEFAULT_FONT = "Flipdot8_Narrow"
    
    def __str__(self):
        return "ANNAX LED Display '{name}' ({width} x {height})".format(
            name = self.name, width = self.width, height = self.height)

    def commit(self):
        """
        Send the current internal bitmap to the display.
        
        BITMAP FORMAT:
        Whole rows (left to right), going from top to bottom
        """
        
        pixels = self.img.load()
        width, height = self.img.size
        bitmap = []
        for y in range(height):
            for x in range(0, width, 8):
                byte = 0x00
                for xoff in range(8):
                    if x+xoff >= width:
                        continue
                    byte |= (pixels[x+xoff, y] > 127) << (7-xoff)
                bitmap.append(byte)
        
        self.init_image()
        return self.send_message(
            [0xFF, 0xA0, len(bitmap) >> 8 & 0xFF, len(bitmap) & 0xFF] + bitmap)
    
    def set_display_mode(self, mode):
        """
        Set the display mode.
        
        mode:
        0: Static
        1: Scrolling
        2: Automatic
        """
        
        if not isinstance(mode, int):
            mode = ('static', 'scroll', 'auto').index(mode)
        return self.set_option(1, mode)
    
    def set_scroll_speed(self, speed):
        """
        Set the speed of the scrolling text.
        
        speed:
        The speed
        """
        
        return self.set_option(2, speed)
    
    def set_scroll_direction(self, direction):
        """
        Set the direction of the scrolling text.
        
        direction:
        0: Left
        1: Right
        """
        
        if not isinstance(direction, int):
            direction = ('left', 'right').index(direction)
        
        return self.set_option(3, direction)
    
    def set_scroll_mode(self, mode):
        """
        Set the scroll mode of the text.
        
        mode:
        0: Repeat on visibility of end
        1: Repeat on disappearance
        2: Repeat after gap
        """
        
        if not isinstance(mode, int):
            mode = ('repeat-on-end', 'repeat-on-disappearance',
                'repeat-after-gap').index(mode)
        
        return self.set_option(4, mode)
    
    def set_scroll_gap(self, gap):
        """
        Set the gap behind the scrolling text.
        
        gap:
        The gap in blocks of 8 pixels
        """
        
        return self.set_option(5, gap)
    
    def set_power_state(self, state):
        """
        Set the power state of the display.
        
        state:
        0: Off
        1: On
        """
        
        if isinstance(state, bool):
            state = int(state)
        
        return self.set_option(6, state)
    
    def set_blink_frequency(self, frequency):
        """
        Set the blink frequency of the text.
        
        frequency:
        The frequency in multiplex cycles
        """
        
        return self.set_option(7, frequency)
    
    def set_stop_indicator(self, state):
        """
        Enable or disable the stop indicator.
        
        state:
        Either 0 or 1, representing ON or OFF respectively
        """
        
        return self.set_option(8, 0x01 if state else 0)
    
    def set_scroll_step(self, step):
        """
        Set the number of steps the scrolling text should advance.
        
        step:
        The number of steps
        """
        
        return self.set_option(9, step)
    
    def set_stop_indicator_blink_frequency(self, frequency):
        """
        Set the blink frequency of the stop indicator.
        
        frequency:
        The frequency in multiplex cycles
        """
        
        return self.set_option(10, frequency)