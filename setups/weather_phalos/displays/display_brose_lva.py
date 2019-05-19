"""
(C) 2016 Julian Metzler
"""

import time

from .display_base import BaseDisplay

class BroseLVADisplay(BaseDisplay):
    """
    Original Brose LVA display with VFDs
    """
    
    def __init__(self, address, name = None):
        """
        address:
        The IBIS address of the display (0 to 15)
        
        name:
        A name to identify the display
        """
        
        super().__init__(name)
        self.address = address
    
    def __str__(self):
        return "BROSE LVA Display '{name}' (Address {address})".format(
            name = self.name, address = self.address)
    
    def _vdvhex(self, num):
        return "0123456789:;<=>?"[num]
    
    def _vdv_replace(self, message):
        message = message.replace("ä", "{")
        message = message.replace("ö", "|")
        message = message.replace("ü", "}")
        message = message.replace("ß", "~")
        message = message.replace("Ä", "[")
        message = message.replace("Ö", "\\")
        message = message.replace("Ü", "]")
        return message
    
    def _hash(self, message):
        message = self._vdv_replace(message)
        message += "\r"
        check_byte = 0x7F
        
        for char in message:
            byte = ord(char)
            check_byte = check_byte ^ byte
        
        message += chr(check_byte)
        return message
    
    def send_message(self, *args, **kwargs):
        result = super().send_message(*args, **kwargs)
        time.sleep(0.35)
        return result
    
    def set_option(self, option, value):
        raise NotImplementedError
    
    def set_programming(self):
        raise NotImplementedError
    
    def set_line_number(self, number):
        """
        Set the line number.
        
        number:
        A number from 0 to 999
        """
        
        return self.send_message(
            self._hash("l{0:03}".format(number)).encode('ascii'),
            expect_reply = False)
    
    def set_stop_index(self, index):
        """
        Set the index of the stop to be displayed.
        
        index:
        The desired index
        """
        
        return self.send_message(
            self._hash("xI{0:02}".format(index)).encode('ascii'),
            expect_reply = False)
    
    def add_stop(self, index, stop, centered = True):
        """
        Add a stop to the list.
        
        index:
        The index of the stop in the list
        
        stop:
        The name of the stop
        
        centered:
        Whether the text should appear centered on the display
        """
        
        data = "%(chr03)s%(pos)02i%(chr04)s%(text)s%(chr05)s%(change)s" % {
            'chr03': chr(3),
            'pos': index,
            'chr04': chr(4),
            'text': stop.center(20) if centered else stop,
            'chr05': chr(5),
            'change': ""
        }

        num_blocks, extra_chars = divmod(len(data), 16)
        telegram = "aL%(id)s%(num_blocks)s%(extra_chars)s%(data)s" % {
            'id': self._vdvhex(self.address),
            'num_blocks': self._vdvhex(num_blocks),
            'extra_chars': self._vdvhex(extra_chars),
            'data': data
        }
        
        return self.send_message(
            self._hash(telegram).encode('ascii'),
            expect_reply = False)
    
    def set_final_stop(self):
        """
        Copy the last stop in the list to the "final stop" display.
        """
        
        return self.add_stop(99, "")
    
    def disable(self):
        """
        Disable the displays.
        """
        
        return self.set_stop_index(0)