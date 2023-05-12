from __future__ import annotations
import numpy as np
from strip import ColorRecordDType
import math
def RGB_2_HSV(RGB):
    ''' Converts an integer RGB tuple (value range from 0 to 255) to an HSV tuple '''

    # Unpack the tuple for readability
    R, G, B = RGB

    # Compute the H value by finding the maximum of the RGB values
    RGB_Max = max(RGB)
    RGB_Min = min(RGB)

    # Compute the value
    V = RGB_Max
    if V == 0:
        H = S = 0
        return (H,S,V)


    # Compute the saturation value
    S = 255 * (RGB_Max - RGB_Min) // V

    if S == 0:
        H = 0
        return (H, S, V)

    # Compute the Hue
    if RGB_Max == R:
        H = 0 + 43*(G - B)//(RGB_Max - RGB_Min)
    elif RGB_Max == G:
        H = 85 + 43*(B - R)//(RGB_Max - RGB_Min)
    else: # RGB_MAX == B
        H = 171 + 43*(R - G)//(RGB_Max - RGB_Min)

    return (H, S, V)

def HSV_2_RGB(H, S, V):
    ''' Converts an integer HSV tuple (value range from 0 to 255) to an RGB tuple '''

    #https://stackoverflow.com/questions/24152553/hsv-to-rgb-and-back-without-floating-point-math-in-python

    # Check if the color is Grayscale
    if S == 0:
        return (V,V,V)

    # Make hue 0-5
    region = H // 43

    # Find remainder part, make it from 0-255
    #remainder = (H - (region * 43)) * 6
    remainder = (H%43) * 6

    # Calculate temp vars, doing integer multiplication
    P = (V * (255 - S)) >> 8
    Q = (V * (255 - ((S * remainder) >> 8))) >> 8
    T = (V * (255 - ((S * (255 - remainder)) >> 8))) >> 8

    # Assign temp vars based on color cone region
    return ( #RGB, 8bit
        (V,T,P),
        (Q,V,P),
        (P,V,T),
        (P,V,Q),
        (T,P,V),
        (V,P,Q)
    )[region]



def NP_HSV_TO_BGR_ColorRecordDType(array:np.ndarray) -> np.recarray[ColorRecordDType]:
    H = array[:,0]
    S = array[:,1]
    V = array[:,2]

    region = H//43
    remainder = (H%43) * 6

    P = (V * (255 - S))
    Q = (V * (255 - (S * remainder)))
    T = (V * (255 - (S * (255 - remainder))))

    lookup = np.array([ #BGR, 8bit
        (P,T,V),
        (P,V,Q),
        (T,V,P),
        (Q,V,P),
        (V,P,T),
        (Q,P,V)
    ])

    return lookup[region,...,range(len(array))].view(ColorRecordDType)[:,0]


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
    
    def rgbNP(self):
        return np.array([self.bgr], dtype = ColorRecordDType)
    
    @property
    def bgr(self):
        return (self.b,self.g,self.r)

    def range_to(self, color2:Color, length:int):
        return [self]*length

    def np_range_to_linear(self, color2:Color, length:int) -> np.recarray[ColorRecordDType]:
        return np.linspace( self.rgb, color2.rgb, length, axis=0).astype(np.uint8).view(ColorRecordDType)[:,0]

    def np_range_to_hsv(self, color2:Color, length:int) -> np.recarray[ColorRecordDType]:
        #TODO linspace should wrap around for hue!
        hsv1 = RGB_2_HSV(self.rgb)
        hsv2 = RGB_2_HSV(color2.rgb)
        hsvspace = np.linspace( hsv1, hsv2, length, axis=0).astype(np.uint8)

        return NP_HSV_TO_BGR_ColorRecordDType(hsvspace)


    def np_range_rainbow(self, length:int) -> np.recarray[ColorRecordDType]:
        hsvspace = np.linspace( (0,255,255) , (255,255,255), length , axis=0).astype(np.uint8)
        return NP_HSV_TO_BGR_ColorRecordDType(hsvspace)
    
    def matrix(self, totalsize:int, activeFraction:int) -> np.recarray[ColorRecordDType]:
        m = np.zeros(totalsize, dtype = ColorRecordDType)
        activeLen = math.floor(min(totalsize*activeFraction/256, totalsize-2))
        m[0:activeLen] = self.np_range_to_linear(Color(0,0,0), activeLen)[::-1]
        m[activeLen] = (255,255,255)
        return m