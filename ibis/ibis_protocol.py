# Copyright (C) 2016 Julian Metzler
# -*- coding: utf-8 -*-

"""
Main protocol library
"""

import serial
import time
from .ibis_utils import prepare_text, vdvhex

class IBISMaster(object):
    def __init__(self, port):
        self.port = port
        self.device = serial.Serial(
            self.port,
            baudrate = 1200,
            bytesize = serial.SEVENBITS,
            parity = serial.PARITY_EVEN,
            stopbits = serial.STOPBITS_TWO
        )
    
    def hash(self, message):
        check_byte = 0x7F
        
        for char in message:
            byte = ord(char)
            check_byte = check_byte ^ byte
        
        message += chr(check_byte)
        return message
    
    def send_raw(self, data):
        hex_data = ""
        for byte in data:
            hex_data += "<%s>" % hex(ord(byte))[2:].upper().rjust(2, "0")
        length = self.device.write(data.encode('ascii'))
        time.sleep(length * (12 / 1200.0))
        return length
    
    def send_message(self, message):
        message = self.hash(message + "\r")
        return self.send_raw(message)
    
    def send_001(self, line_number):
        message = "l%03i" % line_number
        return self.send_message(message)
    
    def send_special_character(self, character):
        message = "lE%02i" % character
        return self.send_message(message)
    
    def send_target_number(self, target_number):
        message = "z%03i" % target_number
        return self.send_message(message)
    
    def send_time(self, hours, minutes):
        message = "u%02i%02i" % (hours, minutes)
        return self.send_message(message)
    
    def send_date(self, day, month, year):
        message = "d%02i%02i%i" % (day, month, year)
        return self.send_message(message)
    
    def send_003a(self, text):
        text = prepare_text(text)
        blocks, remainder = divmod(len(text), 16)
        
        if remainder:
            blocks += 1
            text += " " * (16 - remainder)
        
        message = "zA%i%s" % (blocks, text.upper())
        return self.send_message(message)
    
    def send_021(self, text, id):
        text = prepare_text(text)
        blocks, remainder = divmod(len(text), 16)
        
        if remainder:
            blocks += 1
            text += " " * (16 - remainder)
        
        message = "aA%i%i%s" % (id, blocks, text.upper())
        return self.send_message(message)
    
    def send_009(self, next_stop, length = 16):
        next_stop = prepare_text(next_stop)
        message = "v%s" % next_stop.upper().ljust(length)
        return self.send_message(message)
    
    def send_003c(self, next_stop):
        next_stop = prepare_text(next_stop)
        blocks, remainder = divmod(len(next_stop), 4)
        
        if remainder:
            blocks += 1
            next_stop += " " * (4 - remainder)
        
        message = "zI%i%s" % (blocks, next_stop)
        return self.send_message(message)
    
    def send_021t(self, texts, id, cycle):
        id = vdvhex(id)
        cycle = vdvhex(cycle)
        
        data = "A" + cycle
        for top_line, bottom_line in texts:
            data += prepare_text(top_line) + "\n"
            data += prepare_text(bottom_line) + "\n\n"
        
        num_blocks, remainder = divmod(len(data), 16)
        if remainder:
            num_blocks += 1
            data += " " * (16 - remainder)
        
        message = "aA%s%i%s" % (id, num_blocks, data)
        return self.send_message(message)

    def send_010(self, pos):
        message = "xI%02i" % pos
        return self.send_message(message)

    def send_021a(self, id, pos, text, change = ""):
        data = "%(chr03)s%(pos)02i%(chr04)s%(text)s%(chr05)s%(change)s" % {
            'chr03': chr(3),
            'pos': pos,
            'chr04': chr(4),
            'text': text,
            'chr05': chr(5),
            'change': change
        }

        num_blocks, extra_chars = divmod(len(data), 16)
        telegram = "aL%(id)s%(num_blocks)s%(extra_chars)s%(data)s" % {
            'id': vdvhex(id),
            'num_blocks': vdvhex(num_blocks),
            'extra_chars': vdvhex(extra_chars),
            'data': data
        }
        return self.send_message(telegram)