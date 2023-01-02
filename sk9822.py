from strip import Strip, LEDPixel
from spidev import SpiDev

class SPIInterface:
    def __init__(self, strip:Strip, interface:SpiDev):
        self.interface = interface
        self.strip = strip
    
    def drawFrame(self):
        self.interface.xfer3("\0\0\0\0") #Start
        self.interface.xfer3(bytes(self.strip))
        self.interface.xfer3("\0\0\0\0") #End
