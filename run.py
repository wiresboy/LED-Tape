#!/bin/python

from strip import StripHW as Strip
from dmxToLED import dmx
from sk9822 import SPIInterface
from spidev import SpiDev
import sacn
import time

uni=3
config = [ #SPI port, num pixels, DMX address
    ((0,0), 900, 1),
    #((0,0), 352, 1),
    #((0,1), 485, 16),
    #((1,0), 618, 31),
    #((1,1), 750, 46)
]

max_speed_hz = 10000000

spiports = []
patch = []

for port, numpix, addr in config:
    spi = SpiDev()
    spi.open(*port)
    spi.max_speed_hz = max_speed_hz
    strip = Strip(numpix)

    patch.append( (addr, strip) )
    spiports.append(SPIInterface(strip, spi))


receiver = sacn.sACNreceiver()
receiver.start()  # start the receiving thread

@receiver.listen_on('universe', universe=uni)
def callback(packet:sacn.DataPacket):
    try:
        dmx(packet.dmxData, patch)
        print(packet.dmxData[:15])
        #for port in spiports:
            #port.drawFrame()
    except Exception as e:
        global lastPacket
        lastPacket = packet
        raise e
    #    print("Bad data?")
    #    print(packet.dmxData)  # print the received DMX data

# optional: if multicast is desired, join with the universe number as parameter
receiver.join_multicast(uni)


try:
    while True:
        time.sleep(0.001)
        for port in spiports:
            port.drawFrame()
except KeyboardInterrupt:
    receiver.leave_multicast(1)
    receiver.stop()
    for s in spiports:
        s.interface.close()
