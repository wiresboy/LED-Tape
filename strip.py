import numpy as np

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
	
	#faster to look up:
	def setRGB8bit(self,rgb):
		self.c = rgb
	def setIntensity5bit(self, intensity):
		self.i = intensity

class Strip(tuple):
	def __new__(self, length:int, **kwargs) -> tuple[LEDPixel]:
		"""length: Number of pixels in this particular strip"""
		return super().__new__(self, tuple([LEDPixel() for z in range(length)]), **kwargs)

	def update(self):
		for p in self:
			p.update()

	def __bytes__(self):# SK9822 formatted data
		return bytes([b for p in self[::-1] for b in (*p.c, (0xe0 | p.i))][::-1])  #Somehow the reverse operation actually makes this faster! 


	def __getitem__(self, index) -> LEDPixel:
		return super().__getitem__(index)


ColorRecordDType = [
	("b", np.uint8),
	("g", np.uint8),
	("r", np.uint8)]
PixelRecordDType = [
	("i", np.uint8),
	("c", ColorRecordDType)]

class StripHW(np.recarray):
	def __new__(cls, length):
		return np.zeros(shape=length, dtype=PixelRecordDType).view(cls)
	
	def update(self):
		raise Exception("Incorrect class type: This is for the real hardware!")

	#Remainder from https://stackoverflow.com/a/60216773
	def __array_finalize__(self, obj: object) -> None:
		if obj is None: 
			return
		#default_attributes = {"attr": 1}
		#self.__dict__.update(default_attributes)  # another way to set attributes
	
	def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):  # this method is called whenever you use a ufunc
		'''this implementation of __array_ufunc__ makes sure that all custom attributes are maintained when a ufunc operation is performed on our class.'''

		# convert inputs and outputs of class ArraySubclass to np.ndarray to prevent infinite recursion
		args = ((i.view(np.ndarray) if isinstance(i, StipHW) else i) for i in inputs)
		outputs = kwargs.pop('out', None)
		if outputs:
			kwargs['out'] = tuple((o.view(np.ndarray) if isinstance(o, StipHW) else o) for o in outputs)
		else:
			outputs = (None,) * ufunc.nout
		# call numpys implementation of __array_ufunc__
		results = super().__array_ufunc__(ufunc, method, *args, **kwargs)  # pylint: disable=no-member
		if results is NotImplemented:
			return NotImplemented
		if method == 'at':
			# method == 'at' means that the operation is performed in-place. Therefore, we are done.
			return
		# now we need to make sure that outputs that where specified with the 'out' argument are handled corectly:
		if ufunc.nout == 1:
			results = (results,)
		results = tuple((self._copy_attrs_to(result) if output is None else output)
						for result, output in zip(results, outputs))
		return results[0] if len(results) == 1 else results

	def _copy_attrs_to(self, target):
		'''copies all attributes of self to the target object. target must be a (subclass of) ndarray'''
		target = target.view(StipHW)
		try:
			target.__dict__.update(self.__dict__)
		except AttributeError:
			pass
		return target