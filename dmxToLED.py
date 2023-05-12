from __future__ import annotations
import numpy as np
from strip import Strip, StripHW, ColorRecordDType
from enum import Enum
from color import Color
import random
import math

class Modes(Enum):
    off = 0
    solid = 1
    alternate = 2
    gradient_hsv = 3
    random_strobe = 4  #Chunks of size, at rate
    rainbow = 5
    gradient_linear = 6
    gradient_oneway = 7 #TODO
    gradient_hsv_oneway = 8 #TODO
    matrix = 9 #todo
    

class Align(Enum):
    left = 0
    center = 1
    invertCenter = 2
    right = 3

def mirror(a):
    return np.concatenate( (a, np.flip(a, axis=0)), axis=0)

def control(strip:Strip|StripHW, c1:Color, c2:Color, intensity:int, mode:Modes, parameter1:int, parameter2:int, parameter3:int, startIndex:int, stopIndex:int, align:Align):
    if startIndex > stopIndex:
        startIndex, stopIndex = stopIndex, startIndex
    startIndex = min(startIndex, len(strip)-1)
    stopIndex = min(stopIndex, len(strip)-1)
    
    #print(startIndex, stopIndex)
    #Base parameters
    width = parameter1*3 + 2
    widthScale = 256.0/width
    size = parameter2
    shift = parameter3-128 #Its signed
    shiftUnsigned = parameter3

    if isinstance(strip, StripHW): 
        strip[:startIndex].i = 0xe0
        strip[startIndex:stopIndex+1].i = intensity | 0xe0 #StripHW is only used for HW modes, so we need to set this.
        strip[stopIndex+1:].i = 0xe0

        if align == Align.left:
            strip = strip[startIndex:stopIndex+1]
        elif align == Align.center:
            centerIndex = (startIndex + stopIndex)//2
            stripfirst = strip[startIndex:centerIndex+1]
            if (stopIndex-startIndex)%2 == 1: #Odd length, overlap 1 pix
                stripmirror = strip[centerIndex+1:stopIndex+1][::-1]
            else:
                stripmirror = strip[centerIndex+1:stopIndex+1][::-1]
            strip = stripfirst
        elif align == Align.invertCenter:
            centerIndex = (startIndex + stopIndex)//2
            stripfirst = strip[startIndex:centerIndex+1][::-1]
            if (stopIndex-startIndex)%2 == 1: #Odd length, overlap 1 pix
                stripmirror = strip[centerIndex+1:stopIndex+1]
            else:
                stripmirror = strip[centerIndex:stopIndex+1]
            strip = stripfirst
        elif align == Align.right:
            strip = strip[startIndex:stopIndex+1][::-1]
        else: 
            return
        
        if mode == Modes.off:
            strip.c = (0,0,0)
        elif mode == Modes.solid:
            strip.c = c1.bgr
        elif mode == Modes.alternate: ##FUTURE ME: Why did I write this while half asleep? Chance of this working: ~10%
            activeWidth = stopIndex - startIndex
            reps = activeWidth / width
            if width > reps: #If there are more pixels in each width than there are repititions, then the outer loop should be repititions
                lc = (shift         ) %256
                uc = (shift + size*2) %256
                lower_cutoff = int(lc/widthScale)
                upper_cutoff = int(uc/widthScale)
                invert = lc > uc
                if invert:
                    lower_cutoff, upper_cutoff = upper_cutoff, lower_cutoff
                if invert ^ (size>=128):
                    rgb1 = c1.bgr
                    rgb2 = c2.bgr
                else:
                    rgb1 = c2.bgr
                    rgb2 = c1.bgr

                for subStrip in np.split(strip, range(width, len(strip)+width-1, width)):
                    subStrip[:lower_cutoff].c = rgb1
                    subStrip[lower_cutoff:upper_cutoff].c = rgb2
                    subStrip[upper_cutoff:].c = rgb1
            else: #Outer loop over inner pixels
                rgb1 = c1.bgr
                rgb2 = c2.bgr
                for i in range(width):
                    if size*2-256 <= (i*widthScale - shift)%256 < size*2:   #( - size)
                        strip[i::width].c = rgb1
                    else:
                        strip[i::width].c = rgb2

        elif mode in (Modes.gradient_linear, Modes.gradient_oneway, Modes.gradient_hsv, Modes.gradient_hsv_oneway, Modes.rainbow, Modes.matrix):
            if mode == Modes.gradient_linear:
                gradient = mirror(c1.np_range_to_linear(c2, width))
            elif mode == Modes.gradient_oneway:
                gradient = c1.np_range_to_linear(c2, width*2)
            elif mode == Modes.gradient_hsv:
                gradient = mirror(c1.np_range_to_hsv(c2, width))
            elif mode == Modes.gradient_hsv_oneway:
                gradient = c1.np_range_to_hsv(c2, width*2)
            elif mode == Modes.rainbow:
                gradient = c1.np_range_rainbow(width*2)
            elif mode == Modes.matrix:
                gradient = c1.matrix(width*2, size)
            
            shiftRollover = math.ceil(2*shiftUnsigned/widthScale)-2*width
            for offset in range(startIndex+shiftRollover, stopIndex, 2*width):
                if offset<=0 and offset > -2*width:
                    z = strip[0:offset+2*width]
                    z.c = gradient[-len(z):]
                else:
                    z = strip[offset:offset+2*width]
                    z.c = gradient[:len(z)]

        elif mode == Modes.random_strobe:
            strip.c = c2.bgr
            #parameter 1 = width base
            #parameter 2 = frequency (chance per frame, basically. Framerate = dmx rate)
            #parameter 3 = width spread (in percent)
            
            #Flash?
            if random.randrange(255) < parameter2:
                spread = parameter3/100.
                w = random.randint(int(max(0, width*(1-spread))), int(width*(1+spread)))
                if w>=stopIndex-startIndex: #Flash the entire thing!
                    strip.c = c1.bgr
                else:
                    baseLoc = random.randint(0, stopIndex-startIndex-w)
                    strip[baseLoc : baseLoc+w].c = c1.bgr
            

        if align==Align.invertCenter or align==Align.center:
           stripmirror[:] = strip

    else:

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
        
        ## ~~~ Renderers ~~~
        if mode in (Modes.off, Modes.solid):
            if mode == Modes.off:
                rgb = (0,0,0)
            else:
                rgb = c1.rgb
            [p.setRGB8bit(rgb) for i,p in livePix]

        elif mode in (Modes.gradient_linear, Modes.rainbow):
            if mode == Modes.gradient_linear:
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
            [p.setRGB8bit( rgb1 if (lower_cutoff <= (int((i%width)*widthScale)+shift)%256 < upper_cutoff) else rgb2 ) for i,p in livePix]

        elif mode == Modes.random_strobe:
            pass


def dmx(universe_data, patch):
    for address, st in patch:
        data = universe_data[address-1:address+14]
        if (data[7] >= 100) or (data[0] >= 128):
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