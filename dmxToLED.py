from __future__ import annotations
import numpy as np
from strip import LEDPixel, Strip
from enum import Enum
import random
#from colour import Color

class Modes(Enum):
    off = 0
    solid = 1
    alternate = 2
    gradient_scroll = 3
    random_strobe = 4  #Chunks of size, at rate
    rainbow = 5
#TODO: How to center

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
        pass


def control(strip:Strip, c1:Color, c2:Color, intensity:int, mode:Modes, parameter1:int, parameter2:int, parameter3:int, startIndex:int, stopIndex:int, align:Align):
    #c1 = Color(color1)
    #c2 = Color(color2)

    width = parameter1*3 + 1
    size = parameter2
    shift = parameter3-128 #Its signed
    
    if align == Align.center:
        halfStripWidth = (stopIndex - startIndex)//2
        stripCenter = startIndex + halfStripWidth

    if mode == Modes.gradient_scroll:
        gradient = list(c1.range_to(c2, 128))
        gradient += gradient[::-1] #Mirror the list!
    elif mode == Modes.rainbow:
        gradient = [Color(hue=theta, saturation=1, luminance=0.5) for theta in np.linspace(0.,1., 256, endpoint=False)]

    for i, p in enumerate(strip):
        if i<int(startIndex) or i>int(stopIndex):
            p.intensity5bit=0
        else:
            p.intensity5bit = int(intensity)

            if align == Align.left:
                i = i-startIndex
            elif align == Align.center:
                i = abs(stripCenter-i)
            elif align == Align.right:
                i = stopIndex-i

            index = (int((i%width)*(256.0/width))+shift)%256

            if mode == Modes.off:
                p.rgb8bit = (0,0,0)
            elif mode == Modes.solid:
                p.rgb8bit = c1.rgb
            elif mode == Modes.alternate:
                if (index < (size*2)) and ((size*2-256)<=index):
                    p.rgb8bit = c2.rgb
                else:
                    p.rgb8bit = c1.rgb  
            elif mode in (Modes.gradient_scroll, Modes.rainbow):
                p.rgb8bit = gradient[int(index-size)].rgb
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
                #Color(f"#{data[1]:02x}{data[2]:02x}{data[3]:02x}"),
                #Color(f"#{data[4]:02x}{data[5]:02x}{data[6]:02x}"),
                data[0]%32,
                mode,
                data[8],
                data[9],
                data[10],
                data[11]*256+data[12],
                data[13]*256+data[14],
                align
                )