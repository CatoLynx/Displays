"""
(C) 2016 Julian Metzler

This file contains the code for controlling the display multiplex board.
"""

import serial
from .error import DisplayError, DisplayManagerError

class DummyDisplayManager:
    """
    A dummy class to be used when the "real" display manager
    has not yet been initialised.
    """
    
    def __getattr__(self, key):
        raise DisplayManagerError(
            "Display is not registered to a display manager")

class DisplayManager:
    """
    Controller for the multiplexer board which receives serial data
    and forwards it to one of several displays.
    """
    
    def __init__(self, port, baudrate = 57600, timeout = 1.0):
        """
        port:
        The serial port name to use for communication with
        the multiplex board
        
        baudrate:
        The baud rate to use for communication with the multiplex board
        
        timeout:
        The serial port timeout in milliseconds
        """
        
        self.baudrate = baudrate
        # Timeout set to 1 until a reliable method for receiving data is found
        self.port = serial.serial_for_url(port,
            baudrate = baudrate, timeout = timeout)
        self.displays = {}
    
    def register_display(self, port, display):
        """
        Register the specified display on the specified port.
        
        port:
        The ID of the port to register the display on
        
        display:
        The display instance to be registered
        """
        
        if port in self.displays:
            # There already is a display registered on this port
            raise DisplayManagerError(
                "Cannot register {display} on port #{port}: "
                "Occupied by {existing_display}".format(
                    display = display,
                    port = port,
                    existing_display = self.displays[port]))
        
        # Register the display
        display.manager = self
        display.port = port
        self.displays[port] = display
    
    def unregister_display(self, port):
        """
        Unregister the display on the specified port
        
        port:
        The ID of the port whose display should be unregistered
        """
        
        if port not in self.displays:
            # There is no display registered on this port
            raise DisplayManagerError(
                "Cannot unregister display on port #{port}: "
                "No display registered".format(port = port))
        
        self.displays[port].manager = DummyDisplayManager()
        self.displays[port].port = None
        del self.displays[port]

    def write(self, data):
        if type(data) is int:
            data = bytes([data])
        elif type(data) in (list, tuple):
            data = bytearray(data)
        print("S", data)
        return self.port.write(data)

    def check_status(self):
        """
        Check the response to a command.
        """
        
        status = self.port.read(1)
        #print("R", status)
        self.port.read(self.port.inWaiting()) # Discard garbage
        if status:
            status = ord(status)
        else:
            status = 0x00
        if status != 0xFF:
            pass # Bypass until reliability is improved
            # raise DisplayError(response = status)
        return status
    
    def send_header(self, port, message_length):
        """
        Select a target port on the multiplexer
        and prepare it for the pending message.
        
        port:
        The number of the port on the multiplex board
        
        message_length:
        The length (in bytes) of the message that should be forwarded
        """
        
        data = bytearray()
        data.append(0xF0)
        data.append(0xC0 + port)
        data.append(message_length >> 8 & 0xFF)
        data.append(message_length & 0xFF)
        self.write(data)
    
    def send_message(self, port, message, expect_reply = True):
        """
        Send a message to the selected target port.
        
        port:
        The number of the port on the multiplex board
        
        message:
        The message to forward to the selected port
        
        expect_reply:
        Whether to wait for a reply from the display
        """
        
        self.send_header(port, len(message))
        self.write(message)
        return self.check_status() if expect_reply else None
    
    def set_programming(self, port):
        """
        Set up the selected port (and display) for programming mode.
        This includes:
            - Resetting the display connected to the port
            - Setting the baudrate of the selected port to 57600 baud
            - Setting up the port for permanent forwarding (until reset)
        
        port:
        The number of the port on the multiplex board
        """
        
        # Reset display
        self.displays[port].set_programming()
        
        # Set up permanent forwarding
        # and change baudrate to 57600 for programming
        self.write(bytearray([0xF0, 0xC0+port, 0x00, 0x00]))