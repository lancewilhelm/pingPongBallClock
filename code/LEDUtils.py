# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
import time

from neopixel import *
from Utils import *

import argparse
import signal
import sys
import math

def signal_handler(signal, frame):
	colorWipe(self.strip, Color(0,0,0))
	sys.exit(0)

# LED strip configuration:
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
LED_COUNT      = 256
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 125     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_GRB   # Strip type and colour ordering

class LEDStrip:
	def __init__(self):
		# Intialize the library (must be called once before other functions).
		self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
		self.strip.begin()

		self.numBalls = 128
		self.numRows = 7
		self.numCols = 20

		self.animationFrame = 0
		self.animationEnd = 1

		self.textColor = ["solid", Color(255,255,255)]
		self.textColorChange = False
		self.font = "digits"

		self.bgColor = ["solid", Color(0,0,255)]
		self.bgColorChange = False

		#Establish variables that will be used for the clock
		self.hoursPrev = 99  #used for clock updating
		self.minsPrev = 99   #used for clock updating
		self.secsPrev = 99   #used for clock updating
		self.colonLit = False

		# Set up the ball objects
		self.balls = [
			[0] * self.numCols,
			[0] * self.numCols,
			[0] * self.numCols,
			[0] * self.numCols,
			[0] * self.numCols,
			[0] * self.numCols,
			[0] * self.numCols,
			]
		self.setupBalls()

	def setupBalls(self):
		for y in range(self.numRows):
			for x in range(self.numCols):
				self.balls[y][x] = Ball([y,x])    #passes [row,col]

	def writeBall(self,col,row,color,text):
		# Do not proceed if bad coordinates (could maybe replace with try/catch)
		if col < 0 or col >= 20 or row < 0 or row >= 7:
			return

		# If the color is different than what the buffer has stored, write it and show it
		if self.balls[row][col].color != color or self.balls[row][col].text != text:
			self.strip.setPixelColor((self.balls[row][col].ledNum)*2,color)
			self.balls[row][col].color = color
			self.balls[row][col].text = text

	def writeChar(self,col,row,char,color,textBool=True):
		if self.font == "slanted":
			font = slanted
		elif self.font == "digits":
			font = digits

		for y in range(len(font[char])):
			for x in range(len(font[char][-(y+1)])): #Using -j to access the font row the way it was written in the font file. It is easier to write the font file visually. This accommodates that.
				if font[char][-(y+1)][x]:
					self.writeBall(col+x,row+y,color,textBool)
				else:
					self.writeBall(col+x,row+y,self.balls[row+y][col+x].color,False)
		self.strip.show()

	def updateFrame(self, animationEnd):
		self.animationFrame += 1
		self.animationEnd = animationEnd
		if(self.animationFrame>=self.animationEnd):
			self.animationFrame = 0
		return self.animationFrame

	def colorFill(self,color,fullwipe=False):
		if fullwipe:
			for y in range(self.numRows):
				for x in range(self.numCols):
					self.writeBall(x,y,color,False)
		else:
			for y in range(self.numRows):
				for x in range(self.numCols):
					if self.balls[y][x].text == False:
						self.writeBall(x,y,color,False)
		self.strip.show()

	def changeTextColor(self, color):
		for y in range(self.numRows):
			for x in range(self.numCols):
				if self.balls[y][x].text == True:
					self.writeBall(x,y,color,True)

		self.strip.show()

	def wheel(self,pos):
		# Generate rainbow colors across 0-255 positions.
		if pos < 85:
			return Color(pos * 3, 255 - pos * 3, 0)     #green to red
		elif pos < 170:
			pos -= 85
			return Color(255 - pos * 3, 0, pos * 3)     #red to blue
		else:
			pos -= 170
			return Color(0, pos * 3, 255 - pos * 3)     #blue to green

	def wheelOpp(self,pos):
		# Generate rainbow colors across 0-255 positions.
		if pos < 85:
			return Color(255 - pos * 3, pos * 3, 0)
		elif pos < 170:
			pos -= 85
			return Color(pos * 3, 0, 255 - pos * 3)
		else:
			pos -= 170
			return Color(0, 255 - pos * 3, pos * 3)

	def rainbow(self,wait_ms=20):
		# Draw rainbow that fades across all pixels at once.
		j = self.updateFrame(256)

		for x in range(self.numCols):
			for y in range(self.numRows):
				i = x*self.numRows + y
				if self.balls[y][x].text == False:
					self.writeBall(x,y,self.wheel(((i*2)+j) & 255),False)
		self.strip.show()
		time.sleep(wait_ms/1000.0)

	def rainbowCycle(self,wait_ms=20):
		# Draw rainbow that uniformly distributes itself across all pixels.
		j = self.updateFrame(256)

		for x in range(self.numCols):
			for y in range(self.numRows):
				i = x*self.numRows + y
				if self.balls[y][x].text == False:
					self.writeBall(x,y,self.wheel((((i*2)/(self.numBalls*2))+j) & 255),False)
		self.strip.show()
		time.sleep(wait_ms/1000.0)

	def clock(self):
		while(True):
			# Write the BG. Will not overwrite text per the function
			if self.bgColor[0] == "solid":
				self.colorFill(self.bgColor[1])
			elif self.bgColor[0] == "animation":
				if self.bgColor[1] == "rainbow":
					self.rainbow()
				elif self.bgColor[1] == "rainbowCycle":
					self.rainbowCycle()

			# Get the current local time and parse it out to usable variables
			t = time.localtime()
			hours = t.tm_hour
			mins = t.tm_min
			secs = t.tm_sec

			# Convert 24h time to 12h time
			if hours > 12:
				hours -= 12

			# If it is midnight, change the clock to 12
			if hours == 0:
				hours = 12

			# Check to see if the second has changed. If it has, changed the colonLit activation
			if secs != self.secsPrev:
				self.colonLit ^= True  #flip the colonLit bool

				if self.colonLit:
					self.writeChar(9,2,':',self.textColor[1])
					# self.writeBall(9,4,self.textColor[1],True)
					# self.writeBall(10,2,self.textColor[1],True)
					# self.strip.show()
				else: 
					self.writeChar(9,2,':',self.textColor[1],False)	#Keep the color white, but we toggle the text to False so that it will be overwritten by the bg
					# self.writeBall(9,4,self.textColor[1],False)     #Keep the color white, but we toggle the text to False so that it will be overwritten by the bg
					# self.writeBall(10,2,self.textColor[1],False)     #Keep the color white, but we toggle the text to False so that it will be overwritten by the rainbow
					self.strip.show()

				self.secsPrev = secs

			# Check to see if the minute has changed. If it has, write the new minute
			if mins != self.minsPrev:    
				# Convert the mins to a string so that we can parse the individual numbers for display
				minsStr = str(mins)

				# Write the actual numerals
				if mins < 10:
					self.writeChar(11,1,0,self.textColor[1])
					self.writeChar(15,1,int(minsStr[0]),self.textColor[1])
				else:
					self.writeChar(11,1,int(minsStr[0]),self.textColor[1])
					self.writeChar(15,1,int(minsStr[1]),self.textColor[1])
				self.minsPrev = mins

			# Check to see if the hour has changed. If it has, write the new hour
			if hours != self.hoursPrev:
				
				# Convert the mins to a string so that we can parse the individual numbers for display
				hoursStr = str(hours)

				if hoursPrev >= 10 and hours < 10:
					self.writeChar(1,1,'blank',self.textColor[1])
					self.writeChar(5,1,int(hoursStr[0]),self.textColor[1])
				elif hours < 10:
					self.writeChar(5,1,int(hoursStr[0]),self.textColor[1])
				else:
					self.writeChar(1,1,int(hoursStr[0]),self.textColor[1])
					self.writeChar(5,1,int(hoursStr[1]),self.textColor[1])
				self.hoursPrev = hours

			# If there was a chnaged text color, indicate that we have taken care of it
			self.textColorChange = False
