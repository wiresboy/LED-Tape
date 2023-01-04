from __future__ import annotations
import numpy as np
#from strip import LEDPixel, Strip
from enum import Enum
import random





class Modes(Enum):
    off = 0
    solid = 1
    alternate = 2
    gradient_scroll = 3
    random_strobe = 4  #Chunks of size, at rate
    rainbow = 5

class Align(Enum):
    left = 0
    center = 1
    right = 2

class Color(): #8bit color math! All values live as 8 bit RGB
    def __init__(self, *args, **kwargs):#r:int, g:int, b:int):
        if len(args)==3:
            self.r = args[0]
            self.g = args[1]
            self.b = args[2]
        elif len(args)==1 and isinstance(args[0], str): #"WEB" mode
            self.r = int(args[0][1:3], 16)
            self.g = int(args[0][3:5], 16)
            self.b = int(args[0][5:7], 16)
        elif (("h" in kwargs) and ("s" in kwargs) and ("v" in kwargs)):
            self.r=255
            self.g=255
            self.b=255
            pass #TODO rgb from HSV?
        elif (("r" in kwargs) and ("g" in kwargs) and ("b" in kwargs)):
            self.r = kwargs["r"]
            self.g = kwargs["g"]
            self.b = kwargs["b"]
        else:
            self.r=255
            self.g=60
            self.b=60

    @property
    def rgb(self):
        return (self.r,self.g,self.b)
    @rgb.setter
    def rgb(self,rgb):
        self.r, self.g, self.b = rgb

    def range_to(self, color2:Color, length:int):
        return [self]*length

def control(strip, c1:Color, c2:Color, intensity:int, mode:Modes, parameter1:int, parameter2:int, parameter3:int, startIndex:int, stopIndex:int, align:Align):
    #c1 = Color(color1)
    #c2 = Color(color2)

    #Base parameters
    width = parameter1*3 + 1
    widthScale = 256.0/width
    size = parameter2
    shift = parameter3-128 #Its signed

    [p.setIntensity5bit(0) for p in strip[:startIndex]]
    [p.setIntensity5bit(intensity) for p in strip[startIndex:stopIndex+1]]
    [p.setIntensity5bit(0) for p in strip[stopIndex+1:]]

    
    # Handle alignment modes
    if align == Align.left:
        livePix = enumerate(strip[startIndex:stopIndex+1])
    elif align == Align.center:
        halfStripWidth = (stopIndex - startIndex)//2
        stripCenter = startIndex + halfStripWidth
        i = abs(stripCenter-i)
        livePix = enumerate(strip) #TODO
    elif align == Align.right:
        livePix = enumerate(strip[stopIndex:startIndex-1:-1])
    else: 
        livePix = []
    
    if mode in (Modes.off, Modes.solid):
        if mode == Modes.off:
            rgb = (0,0,0)
        else:
            rgb = c1.rgb
        [p.setRGB8bit(rgb) for i,p in livePix]

    elif mode in (Modes.gradient_scroll, Modes.rainbow):
        if mode == Modes.gradient_scroll:
            gradient = list(c1.range_to(c2, 128))
            gradient += gradient[::-1] #Mirror the list!
        elif mode == Modes.rainbow:
            gradient = [Color(hue=theta, saturation=1, luminance=0.5) for theta in np.linspace(0.,1., 256, endpoint=False)]

        [p.setRGB8bit( gradient[ (int((i%width)*widthScale)+shift-size)%256 ].rgb ) for i,p in livePix]

    elif mode == Modes.alternate:
        rgb1 = c1.rgb
        rgb2 = c2.rgb
        upper_cutoff = (size*2)
        lower_cutoff = (size*2-256)
        [p.setRGB8bit( rgb1 if (lower_cutoff <= (int((i%width)*widthScale)+shift-size)%256 < upper_cutoff) else rgb2 ) for i,p in livePix]

    elif mode == Modes.random_strobe:
        pass



def dmx(universe_data, patch):
    #print(universe_data)
    for address, st in patch:
        data = universe_data[address-1:address+14]
        if (data[7] >= 60) or (data[0] >= 96):
            return None ##There was an error, probably bc of previs software trying to be secure
        mode = Modes(data[7] // 10)
        align = Align(data[0] // 32)

        control(st, 
                Color(data[1],data[2],data[3]),
                Color(data[4],data[5],data[6]),
                data[0]%32,
                mode,
                data[8],
                data[9],
                data[10],
                data[11]*256+data[12],
                data[13]*256+data[14],
                align
                )
