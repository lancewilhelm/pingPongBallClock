import argparse
import json
import math
import signal
import sys
import time

import requests
from neopixel import *
from Utils import *


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

		self.font = digits
		self.fontChanged = False
		self.textOriginMoved = False
		self.displayString = ''
		self.displayStringPrev = ''
		self.displayStringLength = 0

		self.weatherResponse = None

		self.minsPrev = None

		# Load settings that are saved to a file 
		self.loadSettings()

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
		# This makes sure that all text is written in the slanted font despite any other font being set
		if char.isdigit() == False and char != ':' and char != ';':
			font = slanted
		else:
			font = self.font

		# Determine the distance to the next character based on the current character and the spacing setting
		if char.isspace():
			distanceToNext = 4
		else:
			distanceToNext = len(font[ord(char)][0]) + self.textSpacing

		# Do not write characters outside of the display area
		if col <= -4 or col > 20:
			return distanceToNext
		if row < -5 or row >= 7:
			return distanceToNext

		for y in range(len(font[ord(char)])):
			for x in range(len(font[ord(char)][-(y+1)])): #Using -y to access the font row the way it was written in the font file. It is easier to write the font file visually. This accommodates that.
				if font[ord(char)][-(y+1)][x]:
					self.writeBallTextState(col+x,row+y,textBool)
				else:
					self.writeBallTextState(col+x,row+y,False)	#write the text to false so that it will be overwritten
		self.strip.show()

		return distanceToNext

	def updateDisplayString(self):
		if self.displayString != self.displayStringPrev or self.textOriginMoved or self.fontChanged:
			x = self.textOrigin[0] 
			y = self.textOrigin[1]
			for i in range(len(self.displayString)):
				distanceToNext = self.writeChar(x,y,self.displayString[i])
				x += distanceToNext

			# After we write a new string, reset/set booleans and set the prev variable to the current string
			self.textOriginMoved = False						# We just addressed this change, so change it back to false
			self.fontChanged = False							# We just addressed this change, so change it back to false
			self.displayChanged = True							# We have written a new string, so the display has changed
			self.displayStringPrev = self.displayString			# Set the displayStringPrev to the current string
			self.displayStringLength = x - self.textOrigin[0]	# This so happens to show up after we are done here. Useful for the animation scroll

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

	def updateBoardColors(self):
		# Write the BG. Will not overwrite text per the function
		if self.bgColor[0] == "animation":
			if self.bgColor[1] == "rainbow":
				self.rainbow()
			elif self.bgColor[1] == "rainbowCycle":
				self.rainbowCycle()
		elif self.bgColor[0] == "solid" and self.displayChanged:
			# print "writing BG color..."	#debugging
			self.colorFill(self.bgColor[1])

		# Color the Text
		# Check to see if we have a text color animation
		if self.textColor[0] == "animation":
			if self.textColor[1] == "rainbow":
				self.rainbowText()
			elif self.textColor[1] == "rainbowCycle":
				self.rainbowCycleText()
		# Else, check for solid notification
		elif self.textColor[0] == 'solid' and self.displayChanged:
			# print "writing TEXT color..."		#debugging
			for y in range(self.numRows):
				for x in range(self.numCols):
					if self.balls[y][x].text == True:
						if self.textColor[0] == 'animation':
							return
						else:
							self.writeBallColor(x,y,self.textColor[1])
			self.strip.show()

		# Reset the display changed boolean now that it has been updated
		self.displayChanged = False

	def updateTextAnimation(self):
		# Used to determine whether or not we have scrolled through the whole string
		# self.displayStringLength = len(self.displayString)*len(self.font[ord(' ')][0])

		# If start time has not been defined, do so
		if self.startTime == 0:
			self.startTime = time.time()
		
		nowTime = time.time()

		# Determine the time elapsed since the start time
		self.timeElapsed = nowTime - self.startTime

		# If the time elapsed is >= the time one frame should take for our set speed, do the things
		if self.timeElapsed >= 1/self.animationSpeed and self.animationSpeed != 0:
			#Indicate the display has changed
			self.textOriginMoved = True

			# Move the text one space to the left
			self.textOrigin[0] -= 1

			# Reset the x text origin to 20 if it gets through the screen
			if self.textOrigin[0] < -1 * self.displayStringLength:
				self.textOrigin[0] = 20

			# Set the start time to this time now
			self.startTime = nowTime

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
		if secs % 2 == 1 and self.animationSpeed <= 5.0:
			# Even seconds, concatenate the strings with a colon in the middle
			timeStr = hourStr + ';' + minStr
		else:
			# Odd seconds, concatenate the strings with a semicolon(blank) in the middle
			timeStr = hourStr + ':' + minStr 

		# Concatenate the date string to the master string with a space termination
		self.displayString += timeStr + ' '

		# Check to see if the minute has changed this is to update the weather. 
		if mins != self.minsPrev:
			self.updateWeather = True
			self.minsPrev = mins

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

	def text(self):
		textStr = self.customText.upper()

		self.displayString += textStr + ' '

	def weather(self):
		apiKey = '68ba9f27bc6d081421c5d2707f019a9a'

		# base_url variable to store url //
		base_url = "http://api.openweathermap.org/data/2.5/weather?"
		complete_url = base_url + "appid=" + apiKey + "&zip=" + self.weatherLocation
		
		if self.updateWeather:
			response = requests.get(complete_url) 
			self.weatherResponse = response.json()
			self.updateWeather = False

		if self.weatherResponse['cod'] != '404':
			y = self.weatherResponse['main']

			current_temperature = float(y['temp'])

			if self.tempUnits == 'k':
				current_temperature = str(int(round(current_temperature)))
				unit = ' K '
			elif self.tempUnits == 'c':
				current_temperature = str(int(round(current_temperature - 273.15)))
				unit = '`C '
			elif self.tempUnits == 'f':
				current_temperature = str(int(round(current_temperature * (9.0/5) - 459.67)))	
				unit = '`F '	# Convert to fahrenheit

			weather_description = self.weatherResponse['weather'][0]['description']

			weatherStr = current_temperature + unit + weather_description

		else:
			weatherStr = 'City Not Found'

		# Concatenate the weather string to the display string
		weatherStr = weatherStr.upper() 	# Uppercase the string

		self.displayString += weatherStr + ' '

	def dumpSettings(self):
		# Create a settings dictionary
		settings = {
			'animationSpeed' : self.animationSpeed,									 # Balls/s for animations. Needs to be a float (.0). Static default
			'textColor' : self.textColor,
			'fontName' : self.fontName,
			'textSpacing' : self.textSpacing,
			'customText' : self.customText,
			'weatherLocation' : self.weatherLocation,
			'tempUnits' : self.tempUnits,
			'content' : self.content,
			'bgColor' : self.bgColor,
		}

		# Dump the settings to settings.txt
		with open('/home/pi/pingPongBallClock/code/settings.txt', 'w') as filehandle:
			json.dump(settings, filehandle)

	def loadSettings(self):
		# Get the settings dictionary from settings.txt
		with open('/home/pi/pingPongBallClock/code/settings.txt', 'r') as filehandle:
			settings = json.load(filehandle)
		
		# Set variables from the settings 
		self.animationSpeed = settings['animationSpeed']									 # Balls/s for animations. Needs to be a float (.0). Static default
		self.textColor = settings['textColor']
		self.fontName = settings['fontName']
		self.textSpacing = settings['textSpacing']
		self.customText = settings['customText']
		self.weatherLocation = settings['weatherLocation']
		self.tempUnits = settings['tempUnits']
		self.content = settings['content']
		self.bgColor = settings['bgColor']

		# Reset the origin to [1,1]
		self.displayChanged = True
		self.updateWeather = True
		self.textOrigin = [1,1]

		# Address possible font change
		if self.fontName == 'slanted':
			self.font = slanted
		elif self.fontName == 'digits':
			self.font = digits

		# Fix unicode content list
		for i in range(len(self.content)):
			self.content[i] = str(self.content[i])

# Initialize an instance of the LEDStrip class
PPB = PingPongBoard()
