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

class PingPongBoard:
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
		self.font = digits
		self.textSpacing = 0

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
		# Convert the char to the ASCII value
		char = ord(char)
		for y in range(len(self.font[char])):
			for x in range(len(self.font[char][-(y+1)])): #Using -j to access the font row the way it was written in the font file. It is easier to write the font file visually. This accommodates that.
				if self.font[char][-(y+1)][x]:
					self.writeBall(col+x,row+y,color,textBool)
				else:
					self.writeBall(col+x,row+y,self.balls[row+y][col+x].color,False)
		self.strip.show()

	def writeString(self,col,row,string,color,textBool=True):
		distanceToNext = 0 # For the first character it does not matter
		for i in range(len(string)):
			print (col + i*distanceToNext), " ", row
			self.writeChar((col + i*distanceToNext),row,string[i],color)
			distanceToNext = len(self.font[ord(string[i])][0]) + self.textSpacing

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

	def clock(self, origin):
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

		# Create the minute string
		if mins < 10:
			minStr = '0' + str(mins)
		else:
			minStr = str(mins)

		# Create the hour string
		if hours < 10:
			hourStr = ' ' + str(hours)
		else:
			hourStr = str(hours)

		# Concatenate the strings with a colon in the middle
		timeStr = hourStr + ':' + minStr
		print timeStr	#debugging

		# Check to see if the minute has changed. If it has, write the the new time
		if mins != self.minsPrev:    
			# Write the string
			self.writeString(origin[0],origin[1],timeStr,self.textColor[1])

			self.minsPrev = mins

# Initialize an instance of the LEDStrip class
PPB = PingPongBoard()

