"""
(C) 2016 Julian Metzler

This file contains the code for basic display functionality.
Other classes are built upon it.
"""

from .manager import DummyDisplayManager

class BaseDisplay:
    """
    A basic implementation of the standard display functionalities
    like message sending and settings.
    """
    
    def __init__(self, name = None):
        """
        name:
        A name to identify the display
        """
        
        # This will be set to a real manager when the display is registered
        self.manager = DummyDisplayManager()
        self.port = None
        self.name = name
    
    def commit(self):
        """
        Dummy so that there will be no error when the server tries to commit
        """
        
        pass
    
    def send_message(self, message, expect_reply = True):
        """
        Send a message to the display using the manager.
        
        message:
        The message to be sent
        
        expect_reply:
        Whether to wait for a reply from the display
        """
        
        return self.manager.send_message(self.port, message, expect_reply)
    
    def set_option(self, option, value):
        """
        Set an option in the display.
        
        option:
        The ID of the setting to change
        
        value:
        The value (one byte) to set the option to
        """
        
        return self.send_message([0xFF, 0xA0+option, value])
    
    def set_programming(self):
        """
        Enter programming mode.
        """
        
        #TODO: Change 0xAF to something else
        return self.send_message([0xFF, 0xAF])