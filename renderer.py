# LED tape simulator

import math
import pyglet
import numpy as np
from strip import LEDPixel, Strip

pyglet.gl.glClearColor(0.,1.,0.,1.)

class Renderer(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        if "background" in kwargs:
            self.background = kwargs["background"]
            kwargs["width"] = self.background.width
            kwargs["height"] = self.background.height
            del kwargs["background"]
        else:
            self.background = None

        super().__init__(*args, **kwargs)
        self.batch = pyglet.graphics.Batch()
        self.strips = []
        self.locations = []

    def addPixel(self, pixelRef: LEDPixel, x:float, y:float, r:float):
        c = pyglet.shapes.Circle(x,y,r, batch = self.batch)
        pixelRef.linkRenderer(c)

    def addStrip(self, stripRef: Strip, x1:float, y1:float, x2:float, y2:float, r:float=None):
        numPix = len(stripRef)
        if r is None:
            r = math.sqrt((x2-x1)**2 + (y2-y1)**2) / (2. * numPix)
        linx = np.linspace(x1, x2, num=numPix)
        liny = np.linspace(y1, y2, num=numPix)
        for x,y,p in zip(linx, liny, stripRef):
            self.addPixel(p, x, y, r)
        
        self.strips.append(stripRef)

    def on_draw(self, *args):
        self.render(None)
    def render(self, *args):
        for s in self.strips:
            s.update()
        self.clear()
        if self.background is not None:
            self.background.blit(0,0)
        self.batch.draw()
        self.dispatch_events() #################
        self.flip()

    def on_mouse_press(self, x, y, button, modifiers):
        self.locations += [(x,y)]
