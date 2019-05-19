"""
(C) 2016 Julian Metzler

This file contains the code for a font handler class.
"""

import os
import subprocess

from PIL import ImageFont

class FontHandler:
    """
    A class for retrieving and using fonts of various formats.
    """
    
    FONT_DIR = "fonts"
    
    def __init__(self):
        self.font_list = {}
        self.load_fonts()

    def _nice_font_name(self, name):
        """
        Bring a font name into a definitive scheme
        
        name:
        The font name to convert
        """
        
        name = name.lower()
        name = name.replace(",", " ")
        name = " ".join(sorted(set(name.split())))
        return name
    
    def load_fonts(self):
        """
        Scan for available fonts to use.
        """
        
        def _parse_line(line):
            """
            Parse a single line from the output of fc-list
            """
            
            try:
                path, name, style = [part.strip() for part in line.split(":")]
            except ValueError:
                return (None, None)
            style = style.lower()
            styles = []
            if "bold" in style:
                styles.append("Bold")
            if "italic" in style:
                styles.append("Italic")
            if "narrow" in style:
                styles.append("Narrow")
            if "regular" in style:
                styles.append("Regular")
            if "oblique" in style:
                styles.append("Oblique")
            if "condensed" in style:
                styles.append("Condensed")
            if "black" in style:
                styles.append("Black")
            combined_name = name + " " + " ".join(styles)
            return (path, combined_name)
        
        """raw_list = subprocess.check_output(
            ("fc-list", "-f", "%{file}:%{family}:%{style}\n",
             ":fontformat=TrueType")).decode('utf-8')"""
        raw_list = ""
        font_list = dict([_parse_line(line) for line in raw_list.splitlines()])
        for path, name in font_list.items():
            if path and name:
                _name = self._nice_font_name(name)
                self.font_list[_name] = path
    
    def get_font_path(self, query):
        """
        Retrieve a font's path by its name
        
        query:
        The query to look up
        """
        
        # Perform a direct lookup first
        path = self.font_list.get(self._nice_font_name(query))
        if path:
            return path

        # Then check for a font called "... Regular"
        path = self.font_list.get(self._nice_font_name(query + " Regular"))
        if path:
            return path
        else:
            raise ValueError("No font found for query '{0}'.".format(query))

    def get_imagefont(self, font, size = None):
        """
        Get an ImageFont instance for the specified search query
        
        font:
        The query to look up fonts with
        
        size:
        If using a truetype font, the size of the desired ImageFont
        """
        
        try:
            # font parameter as ttf filename
            return ImageFont.truetype(font, size), True
        except OSError:
            pass

        try:
            # font parameter as ttf filename in font dir
            _font = font
            if not _font.endswith(".ttf"):
                _font += ".ttf"
            return ImageFont.truetype(
                os.path.join(self.FONT_DIR, _font), size), True
        except OSError:
            pass

        try:
            # font parameter as PIL bitmap font filename
            _font = font
            if not _font.endswith(".pil"):
                _font += ".pil"
            return ImageFont.load(os.path.join(self.FONT_DIR, _font)), False
        except OSError:
            pass

        try:
            # font parameter as font name
            return ImageFont.truetype(self.get_font_path(font), size), True
        except (OSError, ValueError):
            pass

        raise ValueError("No font found for query '{0}'.".format(font))