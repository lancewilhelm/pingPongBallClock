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
		self.startTime = 0
		self.timeElapsed = 0
		self.animationSpeed = 10

		self.textColor = ["solid", Color(255,255,255)]
		self.textColorChange = False
		self.font = digits
		self.textSpacing = 0
		self.textOrigin = [20,1]
		self.displayString = ''
		self.displayStringPrev = ''
		self.displayStringLength = 0

		self.bgColor = ["solid", Color(0,0,255)]
		self.bgColorChange = False

		#Establish variables that will be used for the clock
		self.secsPrev = 99   #used for clock updating

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

	def writeBallColor(self,col,row,color):
		# Do not proceed if bad coordinates (could maybe replace with try/catch)
		if col < 0 or col >= 20 or row < 0 or row >= 7:
			return

		# If the color is different than what the buffer has stored, write it and show it
		if self.balls[row][col].color != color:
			self.strip.setPixelColor((self.balls[row][col].ledNum)*2,color)
			self.balls[row][col].color = color

	def writeBallTextState(self,col,row,text):
		# Do not proceed if bad coordinates (could maybe replace with try/catch)
		if col < 0 or col >= 20 or row < 0 or row >= 7:
			return

		# If the color is different than what the buffer has stored, write it and show it
		if self.balls[row][col].text != text:
			self.balls[row][col].text = text

	def writeChar(self,col,row,char,textBool=True):
		# Do not write characters outside of the display area
		if col <= -4 or col > 20:
			return
		if row < -5 or row >= 7:
			return

		# Convert the char to the ASCII value
		char = ord(char)
		for y in range(len(self.font[char])):
			for x in range(len(self.font[char][-(y+1)])): #Using -y to access the font row the way it was written in the font file. It is easier to write the font file visually. This accommodates that.
				if self.font[char][-(y+1)][x]:
					self.writeBallTextState(col+x,row+y,textBool)
				else:
					self.writeBallTextState(col+x,row+y,False)	#write the text to false so that it will be overwritten
		self.strip.show()

	def writeString(self,col,row,string,textBool=True):
		x = col # For the first character it is the col
		for i in range(len(string)):
			self.writeChar(x,row,string[i])
			distanceToNext = len(self.font[ord(string[i])][0]) + self.textSpacing
			x += distanceToNext

	def updateFrame(self, animationEnd):
		self.animationFrame += 1
		self.animationEnd = animationEnd
		if(self.animationFrame>=self.animationEnd):
			self.animationFrame = 0
		return self.animationFrame

	def textStateWipe(self):
		for y in range(self.numRows):
			for x in range(self.numCols):
				self.writeBallTextState(x,y,False)

	def colorFill(self,color,fullwipe=False):
		if fullwipe:
			for y in range(self.numRows):
				for x in range(self.numCols):
					self.writeBallTextState(x,y,False)
					self.writeBallColor(x,y,color)
		else:
			for y in range(self.numRows):
				for x in range(self.numCols):
					if self.balls[y][x].text == False:
						self.writeBallColor(x,y,color)
		self.strip.show()

	def updateTextColor(self):
		print "updating text"
		color = self.textColor[1]	# Capture the color here to prevent errors during color updating
		# Check to see if we have a text color animation
		if self.textColor[0] == "animation":
			if color == "rainbow":
				self.rainbowText()
			elif color == "rainbowCycle":
				self.rainbowCycleText()
		# Else, check for solid notification
		elif self.textColor[0] == 'solid':
			for y in range(self.numRows):
				for x in range(self.numCols):
					if self.balls[y][x].text == True:
						self.writeBallColor(x,y,color)
			self.strip.show()

	def updateTextAnimation(self):
		# If start time has not been defined, do so
		if self.startTime == 0:
			self.startTime = time.time()
		
		nowTime = time.time()

		# Determine the time elapsed since the start time
		self.timeElapsed = nowTime - self.startTime

		# If the time elapsed is >= the time one frame should take for our set speed, do the things
		if self.timeElapsed >= 1/self.animationSpeed:
			# Move the text one space to the left
			self.textOrigin[0] -= 1

			# Reset the x text origin to 20 if it gets through the screen
			if self.textOrigin[0] < -1 * self.displayStringLength:
				self.textOrigin[0] = 20

			# Set the start time to this time now
			self.startTime = nowTime

	def updateBGColor(self):
		# Write the BG. Will not overwrite text per the function
		if self.bgColor[0] == "solid":
			self.colorFill(self.bgColor[1])
		elif self.bgColor[0] == "animation":
			if self.bgColor[1] == "rainbow":
				self.rainbow()
			elif self.bgColor[1] == "rainbowCycle":
				self.rainbowCycle()

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
					self.writeBallColor(x,y,self.wheel(((i*2)+j) & 255))
		self.strip.show()
		time.sleep(wait_ms/1000.0)

	def rainbowText(self,wait_ms=20):
		# Draw rainbow that fades across all pixels at once.
		j = self.updateFrame(256)

		for x in range(self.numCols):
			for y in range(self.numRows):
				i = x*self.numRows + y
				if self.balls[y][x].text == True:
					self.writeBallColor(x,y,self.wheel(((i*2)+j) & 255))
		self.strip.show()
		time.sleep(wait_ms/1000.0)

	def rainbowCycle(self,wait_ms=20):
		# Draw rainbow that uniformly distributes itself across all pixels.
		j = self.updateFrame(256)

		for x in range(self.numCols):
			for y in range(self.numRows):
				i = x*self.numRows + y
				if self.balls[y][x].text == False:
					self.writeBallColor(x,y,self.wheel((((i*2)/(self.numBalls*2))+j) & 255))
		self.strip.show()
		time.sleep(wait_ms/1000.0)

	def rainbowCycleText(self,wait_ms=20):
		# Draw rainbow that uniformly distributes itself across all pixels.
		j = self.updateFrame(256)

		for x in range(self.numCols):
			for y in range(self.numRows):
				i = x*self.numRows + y
				if self.balls[y][x].text == True:
					self.writeBallColor(x,y,self.wheel((((i*2)/(self.numBalls*2))+j) & 255))
		self.strip.show()
		time.sleep(wait_ms/1000.0)

	def time(self):
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
		if hours < 10 and self.animationSpeed == 0:
			hourStr = ' ' + str(hours)
		else:
			hourStr = str(hours)

		# Used to determine colon lit state
		if secs % 2 == 0:
			# Even seconds, concatenate the strings with a colon in the middle
			timeStr = hourStr + ':' + minStr
		else:
			# Odd seconds, concatenate the strings with a semicolon(blank) in the middle
			timeStr = hourStr + ';' + minStr 

		# Concatenate the date string to the master string with a space termination
		self.displayString += timeStr + ' '

	def date(self):
		# Get the current local time and parse it out to usable variables
		t = time.localtime()
		mon = t.tm_mon
		day = t.tm_mday
		year = t.tm_year

		monStr = str(mon)
		dayStr = str(day)
		yearStr = str(year)

		# Write the date string
		dateStr = monStr + '-' + dayStr + '-' + yearStr[-2:]
		
		# Concatenate the date string to the master string with a space termination
		self.displayString += dateStr + ' '

# Initialize an instance of the LEDStrip class
PPB = PingPongBoard()

