import math

from neopixel import *

#-----------------------------------------------------------------------------------------
# CONGIFURE YOUR BOARD HERE!
# LED strip configuration:
NUM_BALLS		= 128				# Number of balls on your board
NUM_ROWS		= 7					# How many rows of balls are on your board
NUM_COLS		= 20				# How many effective columns are on your board. This is equal to your widest row.
PIXEL_DENSITY	= 60				# This is how dense your strip is with pixels. 30 is the ideal density to buy (LEDs/meter)
PIXEL_RATIO		= PIXEL_DENSITY/30	# Needed for the odd strips like mine
LED_COUNT		= NUM_BALLS*PIXEL_RATIO
LED_PIN        	= 18      			# GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    	= 800000  			# LED signal frequency in hertz (usually 800khz)
LED_DMA        	= 10       			# DMA channel to use for generating signal (try 5)
LED_INVERT     	= False   			# True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    	= 0       			# set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      	= ws.WS2811_STRIP_GRB   # Strip type and colour ordering

# Define the rows the grid by defining the ball numbers. THIS IS IMPORTANT
# This is the only way the program knows the correct LED numbers for each ball
ledAddresses = [
[999,999,999,3,16,17,30,31,44,45,58,59,72,73,86,87,100,101,114,115],    #0 row
[999,999,4,15,18,29,32,43,46,57,60,71,74,85,88,99,102,113,116,126],     #1 row
[999,2,5,14,19,28,33,42,47,56,61,70,75,84,89,98,103,112,117,125],      #2 row
[1,6,13,20,27,34,41,48,55,62,69,76,83,90,97,104,111,118,124,127],       #3 row
[0,7,12,21,26,35,40,49,54,63,68,77,82,91,96,105,110,119,123,999],       #4 row
[8,11,22,25,36,39,50,53,64,67,78,81,92,95,106,109,120,122,999,999],     #5 row
[9,10,23,24,37,38,51,52,65,66,79,80,93,94,107,108,121,999,999,999]      #6 row
]

#-----------------------------------------------------------------------------------------

colorListColor = [
	Color(255,0,0),		# Red
	Color(255,255,0),	# Yellow
	Color(255,0,255),	# Pink
	Color(0,255,255),	# Teal
	Color(0,255,0),		# Green
	Color(0,0,255),		# Blue
	Color(125,0,255),	# Fuscia
	Color(200,255,0),	# Optic Yellow
	Color(50,0,255),	# Purple
	Color(255,125,0),	# Orange
	Color(255,0,50)		# Hot Pink
]

colorListRGB = [
	[255,0,0],		# Red
	[255,255,0],	# Yellow
	[255,0,255],	# Pink
	[0,255,255],	# Teal
	[0,255,0],		# Green
	[0,0,255],		# Blue
	[125,0,255],	# Fuscia
	[200,255,0],	# Optic Yellow
	[50,0,255],		# Purple
	[255,125,0],	# Orange
	[255,0,50]		# Hot Pink
]
class Ball:
	def __init__(self, location):   #location is a list of two variables, [row, col]
		self.location = location    #[row,col]
		self.ledNum = ledAddresses[self.location[0]][self.location[1]]   #[row,col]
		self.text = False           #this is used to determine whether the ball is being used for text display or not
		self.color = Color(0,0,0)   #current ball color

		self.twinkle = False		# Is the ball currently being used for a twinkle animation
		self.twinkleLength = None	# How many frames long is the twinkle animation
		self.twinkleFrame = 0		# What frame is the twinkle animation currently on if it is twinkling

	def brightnessFactor(self):
		print self.twinkleFrame, self.twinkleLength
		return math.sin(self.twinkleFrame*(math.pi/self.twinkleLength))

	def twinkleStep(self):
		self.twinkleFrame += 1
		if self.twinkleFrame >= (self.twinkleLength - 1):
			self.twinkle = False
			self.twinkleFrame = 0
			self.twinkleLength = None
		
# Buffer
buffer = [                          # This is tricky and must be defined this way. I'm creating 7 instances of a list that contains 20 instances of Color(0,0,0). They must all be separately defined
	[Color(0,0,0)] * 20,
	[Color(0,0,0)] * 20,
	[Color(0,0,0)] * 20,
	[Color(0,0,0)] * 20,
	[Color(0,0,0)] * 20,
	[Color(0,0,0)] * 20,
	[Color(0,0,0)] * 20
]      

# -------------------------------------------------
# Fonts
#--------------------------------------------------
# Slanted Numeral Font ----------------------------
slanted = {}    #Define the slanted font dictionary

slanted[ord('0')] = [
	[1,1,1,0],
	[1,0,1,0],
	[1,0,1,0],
	[1,0,1,0],
	[1,1,1,0]
]
slanted[ord('1')] = [
	[0,0,1,0],
	[0,0,1,0],
	[0,0,1,0],
	[0,0,1,0],
	[0,0,1,0]
]
slanted[ord('2')] = [
	[1,1,1,0],
	[0,0,1,0],
	[1,1,1,0],
	[1,0,0,0],
	[1,1,1,0]
]
slanted[ord('3')] = [
	[1,1,1,0],
	[0,0,1,0],
	[0,1,1,0],
	[0,0,1,0],
	[1,1,1,0]
]
slanted[ord('4')] = [
	[1,0,1,0],
	[1,0,1,0],
	[1,1,1,0],
	[0,0,1,0],
	[0,0,1,0]
]
slanted[ord('5')] = [
	[1,1,1,0],
	[1,0,0,0],
	[1,1,1,0],
	[0,0,1,0],
	[1,1,1,0]
]
slanted[ord('6')] = [
	[1,0,0,0],
	[1,0,0,0],
	[1,1,1,0],
	[1,0,1,0],
	[1,1,1,0]
]
slanted[ord('7')] = [
	[1,1,1,0],
	[1,0,1,0],
	[0,0,1,0],
	[0,0,1,0],
	[0,0,1,0]
]
slanted[ord('8')] = [
	[1,1,1,0],
	[1,0,1,0],
	[1,1,1,0],
	[1,0,1,0],
	[1,1,1,0]
]
slanted[ord('9')] = [
	[1,1,1,0],
	[1,0,1,0],
	[1,1,1,0],
	[0,0,1,0],
	[0,0,1,0]
]
slanted[ord(' ')] = [
	[0,0,0,0],
	[0,0,0,0],
	[0,0,0,0],
	[0,0,0,0],
	[0,0,0,0]
]
slanted[ord('-')] = [
	[0,0,0],
	[0,0,0],
	[1,1,0],
	[0,0,0],
	[0,0,0]
]
slanted[ord(':')] = [
	[1,0],
	[0,0],
	[1,0],
	[0,0]
]
slanted[ord(';')] = [
	[0,0],
	[0,0],
	[0,0],
	[0,0]
]
slanted[ord('A')] = [
	[1,1,1,0,0],
	[1,0,0,1,0],
	[1,0,0,1,0],
	[1,1,1,1,0],
	[1,0,0,1,0]
]
slanted[ord('B')] = [
	[1,1,1,0,0],
	[1,0,0,1,0],
	[1,1,1,1,0],
	[1,0,0,1,0],
	[1,1,1,1,0]
]
slanted[ord('C')] = [
	[1,1,1,1,0],
	[1,0,0,0,0],
	[1,0,0,0,0],
	[1,0,0,0,0],
	[1,1,1,1,0]
]
slanted[ord('D')] = [
	[1,1,1,0,0],
	[1,0,0,1,0],
	[1,0,0,1,0],
	[1,0,0,1,0],
	[1,1,1,1,0]
]
slanted[ord('E')] = [
	[1,1,1,1,0],
	[1,0,0,0,0],
	[1,1,1,0,0],
	[1,0,0,0,0],
	[1,1,1,1,0]
]
slanted[ord('F')] = [
	[1,1,1,1,0],
	[1,0,0,0,0],
	[1,1,1,0,0],
	[1,0,0,0,0],
	[1,0,0,0,0]
]
slanted[ord('G')] = [
	[1,1,1,1,0],
	[1,0,0,0,0],
	[1,0,1,0,0],
	[1,0,0,1,0],
	[0,1,1,1,0]
]
slanted[ord('H')] = [
	[1,0,0,1,0],
	[1,0,0,1,0],
	[1,1,1,1,0],
	[1,0,0,1,0],
	[1,0,0,1,0]
]
slanted[ord('I')] = [
	[1,1,1,1,0],
	[0,1,0,0,0],
	[0,1,0,0,0],
	[0,1,0,0,0],
	[1,1,1,1,0]
]
slanted[ord('J')] = [
	[0,1,1,1,0],
	[0,0,0,1,0],
	[1,0,0,1,0],
	[1,0,0,1,0],
	[0,1,1,1,0]
]
slanted[ord('K')] = [
	[1,0,0,1,0],
	[1,0,1,1,0],
	[1,1,1,0,0],
	[1,0,1,0,0],
	[1,0,0,1,0]
]
slanted[ord('L')] = [
	[1,0,0,0,0],
	[1,0,0,0,0],
	[1,0,0,0,0],
	[1,0,0,0,0],
	[1,1,1,1,0]
]
slanted[ord('M')] = [
	[1,0,0,1,0],
	[1,1,1,1,0],
	[1,0,0,1,0],
	[1,0,0,1,0],
	[1,0,0,1,0]
]
slanted[ord('N')] = [
	[1,0,0,1,0],
	[1,1,0,1,0],
	[1,0,1,1,0],
	[1,0,0,1,0],
	[1,0,0,1,0]
]
slanted[ord('O')] = [
	[1,1,1,1,0],
	[1,0,0,1,0],
	[1,0,0,1,0],
	[1,0,0,1,0],
	[1,1,1,1,0]
]
slanted[ord('P')] = [
	[1,1,1,1,0],
	[1,0,0,1,0],
	[1,1,1,1,0],
	[1,0,0,0,0],
	[1,0,0,0,0]
]
slanted[ord('Q')] = [
	[1,1,1,0,0],
	[1,0,1,0,0],
	[1,0,1,0,0],
	[1,0,1,0,0],
	[1,1,1,1,0]
]
slanted[ord('R')] = [
	[1,1,1,1,0],
	[1,0,0,1,0],
	[1,1,1,1,0],
	[1,0,1,0,0],
	[1,0,0,1,0]
]
slanted[ord('S')] = [
	[1,1,1,1,0],
	[1,0,0,0,0],
	[0,1,1,1,0],
	[0,0,0,1,0],
	[1,1,1,1,0]
]
slanted[ord('T')] = [
	[1,1,1,1,0],
	[0,0,1,0,0],
	[0,0,1,0,0],
	[0,0,1,0,0],
	[0,0,1,0,0]
]
slanted[ord('U')] = [
	[1,0,0,1,0],
	[1,0,0,1,0],
	[1,0,0,1,0],
	[1,0,0,1,0],
	[1,1,1,1,0]
]
slanted[ord('V')] = [
	[1,0,0,1,0],
	[1,0,0,1,0],
	[0,1,0,1,0],
	[0,0,1,1,0],
	[0,0,0,1,0]
]
slanted[ord('W')] = [
	[1,0,0,0,1,0],
	[1,0,0,0,1,0],
	[1,0,1,0,1,0],
	[1,0,1,0,1,0],
	[1,1,1,1,1,0]
]
slanted[ord('X')] = [
	[1,0,0,1,0,0],
	[0,1,1,1,0,0],
	[0,0,1,0,0,0],
	[0,1,1,1,0,0],
	[0,1,0,0,1,0]
]
slanted[ord('Y')] = [
	[1,0,0,1,0],
	[0,1,0,1,0],
	[0,0,1,1,0],
	[0,0,0,1,0],
	[0,0,0,1,0]
]
slanted[ord('Z')] = [
	[1,1,1,1,0],
	[0,0,1,0,0],
	[0,1,1,0,0],
	[1,1,0,0,0],
	[1,1,1,1,0]
]
slanted[ord('?')] = [
	[1,1,1,1,0],
	[0,0,0,1,0],
	[0,1,1,1,0],
	[0,0,0,0,0],
	[0,1,0,0,0]
]
slanted[ord('!')] = [
	[1,0],
	[1,0],
	[1,0],
	[0,0],
	[1,0]
]
slanted[ord('.')] = [
	[0,0],
	[0,0],
	[0,0],
	[0,0],
	[1,0]
]
slanted[ord('`')] = [
	[1,1,0],
	[1,1,0],
	[0,0,0],
	[0,0,0],
	[0,0,0]
]
# Dig1ts Numeral Font ----------------------------
digits = {}    #Define the slanted font dictionary

digits[ord('0')]= [
	[1,1,0,0],
	[1,0,1,0],
	[1,0,0,1],
	[0,1,0,1],
	[0,0,1,1]
]
digits[ord('1')]= [
	[0,1,0,0],
	[0,1,0,0],
	[0,0,1,0],
	[0,0,1,0],
	[0,0,0,1]
]
digits[ord('2')]= [
	[1,1,0,0],
	[0,0,1,0],
	[0,1,1,0],
	[0,1,0,0],
	[0,0,1,1]
]
digits[ord('3')]= [
	[1,1,0,0],
	[0,0,1,0],
	[0,1,1,0],
	[0,0,0,1],
	[0,0,1,1]
]
digits[ord('4')]= [
	[1,0,0,0],
	[1,0,1,0],
	[1,1,1,0],
	[0,0,1,0],
	[0,0,0,1]
]
digits[ord('5')]= [
	[1,1,0,0],
	[1,0,0,0],
	[1,1,1,0],
	[0,0,0,1],
	[0,0,1,1]
]
digits[ord('6')]= [
	[0,1,0,0],
	[0,1,0,0],
	[0,1,1,0],
	[0,1,0,1],
	[0,0,1,1]
]
digits[ord('7')]= [
	[1,1,0,0],
	[0,0,1,0],
	[0,0,1,0],
	[0,0,1,0],
	[0,0,1,0]
]
digits[ord('8')]= [
	[1,1,0,0],
	[1,0,1,0],
	[0,1,1,0],
	[0,1,0,1],
	[0,0,1,1]
]
digits[ord('9')]= [
	[1,1,0,0],
	[1,0,1,0],
	[0,1,1,0],
	[0,0,1,0],
	[0,0,1,0]
]
digits[ord(' ')] = [
	[0,0,0,0],
	[0,0,0,0],
	[0,0,0,0],
	[0,0,0,0],
	[0,0,0,0]
]
digits[ord('-')] = [
	[0,0,0,0],
	[0,0,0,0],
	[0,1,1,0],
	[0,0,0,0],
	[0,0,0,0]
]
digits[ord('.')] = [
	[0,0,0],
	[0,0,0],
	[0,0,0],
	[0,0,0],
	[0,1,0]
]
digits[ord(':')] = [
	[1,0],
	[0,0],
	[0,1],
	[0,0]
]
digits[ord(';')] = [
	[0,0],
	[0,0],
	[0,0],
	[0,0]
]
