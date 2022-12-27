import struct

class LEDPixel:
	def __init__(self):
		self.c = (0,0,0)
		self.i = 31
	
	floatDivisor = float(31*255)

	## LED properties
	@property
	def rgb(self):
		return (self.c[0]*self.i / LEDPixel.floatDivisor, 
				self.c[1]*self.i / LEDPixel.floatDivisor, 
				self.c[2]*self.i / LEDPixel.floatDivisor )
	
	@rgb.setter
	def rgb(self, rgbColor):
		self.c = (	int( rgbColor[0] *255),
					int( rgbColor[1] *255),
					int( rgbColor[2] *255) )
	
	@property
	def intensity(self):
		return self.i / 31.0
	
	@intensity.setter
	def intensity(self, intensity):
		self.i = int(intensity*31)
	
	## Simulator
	def linkRenderer(self, object):
		self.renderer = object
	
	def update(self):
		self.renderer.color = [int( v * self.intensity) for v in self.rgb8bit]

	## SK9822-oriented values
	@property
	def intensity5bit(self):
		return self.i
	@intensity5bit.setter
	def intensity5bit(self, intensity):
		self.i = intensity

	@property
	def rgb8bit(self):
		return self.c
	@rgb8bit.setter
	def rgb8bit(self, rgb):
		self.c = rgb

	#@property
	#def bgr8bit(self):
	#	return (self.c[2],self.c[1],self.c[0])

	#@property
	#def sk9822val(self):
	#	return struct.pack(">BBBB", (0xe0 | self.i), self.c[2],self.c[1],self.c[0])

class Strip(tuple):
	def __new__(self, length:int) -> tuple[LEDPixel]:
		"""length: Number of pixels in this particular strip"""
		return super().__new__(self, tuple([LEDPixel() for z in range(length)]))

	def update(self):
		for p in self:
			p.update()

	def __bytes__(self):# SK9822 formatted data
		return bytes([b for p in self[::-1] for b in (*p.c, (0xe0 | p.i))][::-1])  #Somehow the reverse operation actually makes this faster! 


	def __getitem__(self, index) -> LEDPixel:
		return super().__getitem__(index)

	