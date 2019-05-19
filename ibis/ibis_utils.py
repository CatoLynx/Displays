# Copyright (C) 2016 Julian Metzler
# -*- coding: utf-8 -*-

import json

def prepare_text(message):
    def _do_replace(message):
        message = message.replace(u"ä", "{")
        message = message.replace(u"ö", "|")
        message = message.replace(u"ü", "}")
        message = message.replace(u"ß", "~")
        message = message.replace(u"Ä", "[")
        message = message.replace(u"Ö", "\\")
        message = message.replace(u"Ü", "]")
        message = message.encode('utf-8')
        return message
    
    try:
        message = _do_replace(message)
    except UnicodeDecodeError:
        message = message.decode('utf-8')
        message = _do_replace(message)
    
    return message

def vdvhex(num):
    return "0123456789:;<=>?"[num]