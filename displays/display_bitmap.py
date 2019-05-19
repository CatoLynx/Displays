"""
(C) 2016 Julian Metzler

This file contains the code for basic bitmap display functionality.
Other classes are built upon it.
"""

import datetime
import math

from .display_base import BaseDisplay
from .font_handler import FontHandler
from PIL import Image, ImageDraw

class BitmapDisplay(BaseDisplay):
    """
    An extended base display class with bitmap processing functionality.
    """
    
    DEFAULT_FONT = "Sans"
    
    def __init__(self, width, height, name = None,
        bitmap_width = None, bitmap_height = None, font_handler = None):
        """
        width:
        The width of the display area in pixels
        
        height:
        The height of the display area in pixels
        
        name:
        A name to identify the display
        
        bitmap_width:
        Width of the internal bitmap to be sent to the display.
        Can be bigger than screen width e.g. when the display content
        can be scrolled.
        
        bitmap_height:
        Height of the internal bitmap to be sent to the display.
        Can be bigger than screen height e.g. when the display content
        can be scrolled.
        
        font_handler:
        An instance of FontHandler() used to ease the use of different fonts
        """
        
        super().__init__(name)
        self.width = width
        self.height = height
        self.bitmap_width = bitmap_width or width
        self.bitmap_height = bitmap_height or height
        self.font_handler = font_handler or FontHandler()
        self.init_image()
        
    def init_image(self):
        """
        Prepare or reset the internal bitmap.
        """
        
        self.img = Image.new('L', 
            (self.bitmap_width, self.bitmap_height), 'black')
        self.draw = ImageDraw.Draw(self.img)
        self.draw.fontmode = '1' # No antialiasing
    
    def get_bitmap(self):
        """
        Get the current internal bitmap as a 2D array of boolean values.
        Intended for visualisation purposes, the format is independent of that
        used to communicate with the display.
        
        BITMAP FORMAT:
        An array of column arrays (left to right), each of those containing a
        boolean for every pixel in that column (top to bottom).
        """
        
        pixels = self.img.load()
        width, height = self.img.size
        bitmap = []
        for x in range(width):
            column = []
            for y in range(height):
                column.append(pixels[x, y] > 127)
            bitmap.append(column)
        return bitmap
    
    def bitmap(self, image, halign = None, valign = None, left = None,
            center = None, right = None, top = None, middle = None,
            bottom = None, angle = 0):
        """
        Insert a bitmap.
        
        image:
        The bitmap to insert
        
        halign:
        The align of the bitmap on the horizontal axis (left, center, right)
        
        valign:
        The align of the bitmap on the vertical axis (top, middle, bottom)
        
        left:
        The x position of the left edge of the bitmap
        
        center:
        The x position of the center of the bitmap
        
        right:
        The x position of the right edge of the bitmap
        
        top:
        The y position of the top edge of the bitmap
        
        middle:
        The y position of the middle of the bitmap
        
        bottom:
        The y position of the bottom edge of the bitmap
        
        angle:
        The angle in degrees to rotate the image
        (counterclockwise around its center point)
        """
        
        halign = halign or 'center'
        valign = valign or 'middle'
        if isinstance(image, Image.Image):
            img = image
        else:
            img = Image.open(image).convert('RGBA')

        if angle:
            img = img.rotate(angle, expand = True)

        bwidth, bheight = img.size

        if left is not None:
            bitmapx = left
        elif center is not None:
            bitmapx = round(center - (bwidth/2))
        elif right is not None:
            bitmapx = right - bwidth + 1
        else:
            if halign == 'center':
                bitmapx = round((self.width - bwidth) / 2)
            elif halign == 'right':
                bitmapx = self.width - bwidth
            else:
                bitmapx = 0

        if top is not None:
            bitmapy = top
        elif middle is not None:
            bitmapy = round(middle - (bheight/2))
        elif bottom is not None:
            bitmapy = bottom - bheight + 1
        else:
            if valign == 'middle':
                bitmapy = round((self.height - bheight) / 2)
            elif valign == 'bottom':
                bitmapy = self.height - bheight
            else:
                bitmapy = 0

        self.img.paste(img, (bitmapx, bitmapy), img)

    def text(self, text, font = None, size = 20, color = 'white',
            timestring = False, **kwargs):
        """
        Insert a text.
        
        text:
        The text to insert
        
        font:
        The font to use for the text (font name or file path)
        
        size:
        The size of the font to use (ignored for non-truetype fonts)
        
        color:
        The color to use for the text (only black and white make sense;
        white is "positive" and black is "negative" text)
        
        timestring:
        Whether the text should be parsed as a time format string
        
        kwargs:
        Same as for bitmap()
        """
        
        font = font or self.DEFAULT_FONT
        if timestring:
            text = datetime.datetime.strftime(datetime.datetime.now(), text)

        textfont, truetype = self.font_handler.get_imagefont(font, size)
        approx_tsize = textfont.getsize(text)
        text_img = Image.new('RGBA', approx_tsize, (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_img)
        text_draw.fontmode = "1"
        text_draw.text((0, 0), text, color, font = textfont)
        if truetype:
            # font.getsize is inaccurate on non-pixel fonts
            text_img = text_img.crop(text_img.getbbox())
        else:
            # only crop horizontally with pixel fonts
            bbox = text_img.getbbox()
            text_img = text_img.crop((bbox[0], 0, bbox[2], text_img.size[1]))
        self.bitmap(text_img, **kwargs)

    def vertical_text(self, text, font = None, size = 20, char_align = 'center',
            spacing = 2, color = 'white', timestring = False, **kwargs):
        """
        Insert a vertical text.
        
        text, font, size, color, timestring:
        Same as for text()
        
        char_align:
        The horizontal alignment of the characters (left, center, right)
        
        spacing:
        The vertical spacing of the characters
        
        kwargs:
        Same as for bitmap()
        """
        
        font = font or self.DEFAULT_FONT
        if timestring:
            text = datetime.datetime.strftime(datetime.datetime.now(), text)

        textfont, truetype = self.font_handler.get_imagefont(font, size)
        char_imgs = []
        for char in text:
            approx_csize = textfont.getsize(char)
            # Generate separate image for char (so size can be accurately
            # determined, as opposed to font.getsize)
            char_img = Image.new('RGBA', approx_csize, (0, 0, 0, 0))
            char_draw = ImageDraw.Draw(char_img)
            char_draw.fontmode = "1"
            char_draw.text((0, 0), char, color, font = textfont)
            char_img = char_img.rotate(90, expand = True)
            char_img = char_img.crop(char_img.getbbox())
            char_imgs.append(char_img)
        
        # Width and height are treated looking at the non-rotated matrix
        # from here on        
        twidth, theight = 0, 0
        # Add the spacing to text width
        twidth += spacing * len(char_imgs) - 1
        for char_img in char_imgs:
            cwidth, cheight = char_img.size
            # Text width is the width of the widest char, text height is
            # the sum of char heights plus spacing
            if cheight > theight:
                theight = cheight
            twidth += cwidth
        
        text_img = Image.new('RGBA', (twidth, theight), (0, 0, 0, 0))
        xpos = 0
        for i, char_img in enumerate(char_imgs):
            cwidth, cheight = char_img.size

            if char_align == 'center':
                ypos = int((theight - cheight) / 2)
            elif char_align == 'right':
                ypos = 0
            else:
                ypos = theight - cheight
            
            text_img.paste(char_img, (xpos, ypos), char_img)
            xpos += cwidth + spacing
        self.bitmap(text_img, **kwargs)

    def line(self, points, color = 'white', width = 1):
        """
        Insert a line.
        
        points:
        A list of tuples representing the x and y coordinates of points
        defining the line
        
        color:
        Same as for text()
        
        width:
        The width of the line
        """
        
        self.draw.line(points, fill = color, width = width)

    def rectangle(self, points, color = 'white', fill = False):
        """
        Insert a rectangle.
        
        points:
        A list of tuples representing the x and y coordinates of points
        defining the upper left and lower right corners of the rectangle
         
        color:
        Same as for text()
        
        fill:
        Whether to draw a filled or an outlined rectangle
        """
        
        self.draw.rectangle(points, fill = color if fill else None,
            outline = color)

    def clear(self):
        """
        Clear the entire bitmap. (Similar to init_image)
        """
        
        img = Image.new('RGBA', (self.bitmap_width, self.bitmap_height),
            'black')
        self.bitmap(img)

    def fill(self):
        """
        Fill the entire bitmap with white.
        """
        
        img = Image.new('RGBA', (self.bitmap_width, self.bitmap_height),
            'white')
        self.bitmap(img)

    def binary_clock(self, block_width = 3, block_height = 3,
            block_spacing_x = 1, block_spacing_y = 1, **kwargs):
        """
        Insert a binary clock.
        
        block_width:
        Width of the bit blocks
        
        block_height:
        Height of the bit blocks
        
        block_spacing_x:
        Horizontal spacing of the bit blocks
        
        block_spacing_y:
        Vertical spacing of the bit blocks
        
        kwargs:
        Same as for bitmap()
        """
        
        width = 6*block_width + 5*block_spacing_x
        height = 2*block_height + block_spacing_y
        img = Image.new('RGBA', (width, height), 'black')
        draw = ImageDraw.Draw(img)
        now = datetime.datetime.now()
        hour_bits = [now.hour >> i & 1 for i in range(7, -1, -1)][-6:]
        minute_bits = [now.minute >> i & 1 for i in range(7, -1, -1)][-6:]
        
        y = 0
        for pos, bit in enumerate(hour_bits):
            x = pos * (block_width + block_spacing_x)
            draw.rectangle((x, y, x + block_width-1, y + block_height-1),
                outline = 'white', fill = 'white' if bit else 'black')

        y = block_height + block_spacing_y
        for pos, bit in enumerate(minute_bits):
            x = pos * (block_width + block_spacing_x)
            draw.rectangle((x, y, x + block_width-1, y + block_height-1),
                outline = 'white', fill = 'white' if bit else 'black')

        self.bitmap(img, **kwargs)

    def analog_clock(self, width = 16, height = 16, **kwargs):
        """
        Insert an analog clock.
        
        width:
        The width of the clock
        
        height:
        The height of the clock
        
        kwargs:
        Same as for bitmap()
        """
        
        def rect(r, theta):
            """
            Convert polar coordinates into rectangular coordinates.
            
            r:
            Length
            
            theta:
            Angle
            """
            
            x = r * math.cos(math.radians(theta))
            y = r * math.sin(math.radians(theta))
            return int(round(x)), int(round(y))

        def ellipse_radius(a, b, angle):
            """
            Calculate the radius of an ellipse with radiuses a and b
            at the specified angle.
            
            a:
            The horizontal radius of the ellipse
            
            b:
            The vertical radius of the ellipse
            
            angle:
            The angle to calculate the radius at, measured counterclockwise
            from the horizontal axis
            """
            
            return (a*b) / math.sqrt(
                a**2 * math.sin(angle)**2 + b**2 * math.cos(angle)**2)

        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        now = datetime.datetime.now()
        draw.rectangle((0, 0, width-1, height-1), outline = 'white')
        center = (width/2, height/2)

        hour_angle = (now.hour % 12) * 360/12 + now.minute * 360/(12*60) - 90
        hour_length = ellipse_radius(width/2, height/2, hour_angle) * 0.3
        hour_hand = rect(hour_length, hour_angle)
        draw.line((center, (hour_hand[0]+center[0], hour_hand[1]+center[1])),
            fill = 'white')

        minute_angle = now.minute * 360/60 - 90
        minute_length = ellipse_radius(width/2, height/2, minute_angle) * 0.8
        minute_hand = rect(minute_length, minute_angle)
        draw.line((center,
            (minute_hand[0]+center[0], minute_hand[1]+center[1])),
            fill = 'white')

        self.bitmap(img, **kwargs)