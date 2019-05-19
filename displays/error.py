"""
(C) 2016 Julian Metzler

This file contains various exceptions that can occur within this program.
"""

class DisplayError(Exception):
    """
    An Exception related to a single display.
    """
    
    ERR_CODES = {
        0xE0: "Timeout",
        0xEE: "Generic Error",
        0xFF: "Success",
          -1: "No response from controller"
    }

    def __init__(self, code = None, response = None):
        if code is None:
            if response:
                self.code = response
            else:
                self.code = -1
        else:
            self.code = code
        self.description = self.ERR_CODES.get(self.code, "Unknown Error")
    
    def __str__(self):
        return "{0}: {1}".format(self.code, self.description)

class DisplayManagerError(Exception):
    """
    An Exception related to the display manager.
    """
    
    def __init__(self, message):
        self.message = message
    
    def __str__(self):
        return self.message

class DisplayServerError(Exception):
    """
    An Exception related to the display server.
    """
    
    def __init__(self, message):
        self.message = message
    
    def __str__(self):
        return self.message