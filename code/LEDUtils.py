import argparse
import json
import math
import random
import signal
import sys
import time

import requests
from neopixel import *
from Utils import *

# This is the PingPongBoard class that drives everything. All functions related to lighting and writing are in here. 
class PingPongBoard:
	def __init__(self):
		self.num_balls = NUM_BALLS		# Needed for changing board type
		self.num_rows = NUM_ROWS		# Needed for changing board type
		self.num_cols = NUM_COLS		# Needed for changing board type

		self.animationFrame = 0			# Used for animations, start at 0
		self.animationEnd = 1			# Default animation end frame. This is always changed
		self.animationStartTime = 0		# Used for animations and when to move the string
		self.animationTimeElapsed = 0	# Used for animations and when to move the string
		self.breathColor = None			# Necessary for the breathing animation
		self.twinkleStartTime = 0		# Used for timing when to initate a twinkle
		self.twinkleTimeElapsed = 0		# Used for timing when to initate a twinkle
		self.twinkleWaitTime = 0

		self.fontChanged = False				# Store whether or not the font has changed
		self.textOriginMoved = False			# Store whether or not the origin of the display string has changed
		self.displayStringLine1 = ''			# This is the string that will be ultimately displayed on screen
		self.displayStringLine1Prev = ''		# This is what the display string was during the previous loop
		self.displayStringLine1Length = 0		# This is calculated and used to determine when we have cycled through an entire string during animations
		self.displayStringLine2 = ''			# This is the string that will be ultimately displayed on screen
		self.displayStringLine2Prev = ''		# This is what the display string was during the previous loop
		self.displayStringLine2Length = 0		# This is calculated and used to determine when we have cycled through an entire string during animations

		self.weatherResponse = None		# This stores the reponse from the OpenWeather API

		self.minsPrev = None			# Used to calculate when a minute has elapsed. This is useful to only update the weather once a minute TODO Change this

		# Load settings that are saved to files 
		self.loadSettings()

		# Set up the ball objects
		self.balls = []
		for i in range(self.num_rows):
			self.balls.append([0] * self.num_cols)

		# Initialize the ball objects
		self.setupBalls()

		#Intialize the strip
		self.strip = Adafruit_NeoPixel(self.led_count, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, self.brightness, LED_CHANNEL, LED_STRIP)
		self.strip.begin()

	# Sets up a ball object for every single ball on the board. The ball object definition can be found in Utils
	def setupBalls(self):
		for y in range(self.num_rows):
			for x in range(self.num_cols):
				self.balls[y][x] = Ball([y,x],self.boardType)    #passes [row,col], and the type of board which is used for the ledAdresses

	# Actually lights a specic ball (LED) with the color provided to the function. This will check to see if the color is different than the one already set for the ball first. If it is the same then it will not rewrite.
	def writeBallColor(self,col,row,color):
		# Do not proceed if bad coordinates (could maybe replace with try/catch)
		if col < 0 or col >= self.num_cols or row < 0 or row >= self.num_rows:
			return

		# If the color is different than what the buffer has stored, write it and show it
		if self.balls[row][col].color != color:
			self.strip.setPixelColor((self.balls[row][col].ledNum)*PIXEL_RATIO,color)
			self.balls[row][col].color = color

	# Changes the text state of a specific ball. This does NOT actually change the color. Merely whether or not the ball is used to display text. Will not rewrite state if the same.
	def writeBallTextState(self,col,row,text):
		# Do not proceed if bad coordinates (could maybe replace with try/catch)
		if col < 0 or col >= self.num_cols or row < 0 or row >= self.num_rows:
			return

		# If the text state is different than what the buffer has stored, change it
		if self.balls[row][col].text != text:
			self.balls[row][col].text = text

	# Takes a single character provided and writes it to a location on the board.
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
		if col <= -4 or col > self.num_cols:
			return distanceToNext
		if row < -5 or row >= self.num_rows:
			return distanceToNext

		#Step through the rows and columns of the character and write each pixel/ball/LED
		for y in range(len(font[ord(char)])):
			for x in range(len(font[ord(char)][-(y+1)])): #Using -y to access the font row the way it was written in the font file. It is easier to write the font file visually. This accommodates that.
				if font[ord(char)][-(y+1)][x]:
					self.writeBallTextState(col+x,row+y,textBool)
				else:
					self.writeBallTextState(col+x,row+y,False)	#write the text to false so that it will be overwritten
		self.strip.show()

		# Returns the distance to the next character. Used for display string length calcs and to find the location of the next character.
		return distanceToNext

	# Writes the display string if some conditions are met. 
	def updateDisplayString(self):
		#Write the string IF the display stirng is different then it last was OR it has moved location OR the font has changed
		if self.displayStringLine1 != self.displayStringLine1Prev or self.textOriginMoved or self.fontChanged:
			x = self.textOrigin[0][0] 
			y = self.textOrigin[0][1]
			for i in range(len(self.displayStringLine1)):
				distanceToNext = self.writeChar(x,y,self.displayStringLine1[i])
				x += distanceToNext

			# After we write a new string, reset/set booleans and set the prev variable to the current string
			self.textOriginMoved = False						# We just addressed this change, so change it back to false
			self.fontChanged = False							# We just addressed this change, so change it back to false
			self.textDisplayChanged = True						# We have written a new string, so the display has changed
			self.bgDisplayChanged = True						# Since we have update the string, the bg needs to be updated to write over the old text balls now as well
			self.displayStringLine1Prev = self.displayStringLine1			# Set the displayStringLine1Prev to the current string
			self.displayStringLine1Length = x - self.textOrigin[0][0]	# This so happens to show up after we are done here. Useful for the animation scroll

	# This steps the animation frame by one. If the animation frame has reached animationEnd, reset the frame to 0
	def updateFrame(self, animationEnd):
		self.animationFrame += 1
		self.animationEnd = animationEnd
		if(self.animationFrame>=self.animationEnd):
			self.animationFrame = 0
		return self.animationFrame

	# This sets every ball's text state to False on the board
	def textStateWipe(self):
		for y in range(self.num_rows):
			for x in range(self.num_cols):
				self.writeBallTextState(x,y,False)

	# Fills sections/the whole board with the provided color. This function can fill: the whole board, only non-text balls, only text balls
	def colorFill(self,color,fullwipe=False,textOnly=False):
		# Fill the full screen
		if fullwipe:
			for y in range(self.num_rows):
				for x in range(self.num_cols):
					self.writeBallTextState(x,y,False)
					self.writeBallColor(x,y,color)
		# Fill only the text
		elif textOnly:
			for y in range(self.num_rows):
				for x in range(self.num_cols):
					if self.balls[y][x].text == True:
						self.writeBallColor(x,y,color)
		# Fill only the non-text
		else:
			for y in range(self.num_rows):
				for x in range(self.num_cols):
					if self.balls[y][x].text == False:
						self.writeBallColor(x,y,color)
		self.strip.show()

	# The core function that updates both the background color and text colors
	def updateBoardColors(self):
		# Write the BG. Will not overwrite text per the function
		if self.bgColor[0] == "animation":
			if self.bgColor[1] == "rainbow":
				self.rainbow()
			elif self.bgColor[1] == "rainbowCycle":
				self.rainbowCycle()
			elif self.bgColor[1] == "breathing":
				self.breathing(False)
			elif self.bgColor[1] == "twinkle":
				self.twinkle()
		elif self.bgColor[0] == "solid" and self.bgDisplayChanged:
			# print "writing BG color..."	#debugging
			self.colorFill(self.bgColor[1])
		self.bgDisplayChanged = False

		# Color the Text
		# Check to see if we have a text color animation
		if self.textColor[0] == "animation":
			if self.textColor[1] == "rainbow":
				self.rainbowText()
			elif self.textColor[1] == "rainbowCycle":
				self.rainbowCycleText()
			elif self.textColor[1] == "breathing":
				self.breathing(True)
		# Else, check for solid notification
		elif self.textColor[0] == 'solid' and self.textDisplayChanged:
			for y in range(self.num_rows):
				for x in range(self.num_cols):
					if self.balls[y][x].text == True:
						if self.textColor[0] == 'animation':
							return
						else:
							self.writeBallColor(x,y,self.textColor[1])
			self.strip.show()

		# Reset the display changed boolean now that it has been updated
		self.textDisplayChanged = False

	# Used to move the string during an animation.
	def updateTextAnimation(self):
		# If start time has not been defined, do so
		if self.animationStartTime == 0:
			self.animationStartTime = time.time()
		
		nowTime = time.time()

		# Determine the time elapsed since the start time
		self.animationTimeElapsed = nowTime - self.animationStartTime

		# If the time elapsed is >= the time one frame should take for our set speed, do the things
		if self.animationTimeElapsed >= 1/self.animationSpeed[0] and self.animationSpeed[0] != 0:
			#Indicate the display has changed
			self.textOriginMoved = True

			# Move the text one space to the left
			self.textOrigin[0][0] -= 1

			# Reset the x text origin to 20 if it gets through the screen
			if self.textOrigin[0][0] < -1 * self.displayStringLine1Length:
				self.textOrigin[0][0] = 20

			# Set the start time to this time now
			self.animationStartTime = nowTime

# COLOR ANIMATIONS ---------------------------------------------------------------------
	# Used in rainbow and rainbowCycle to determine the color during the cycle. Makes for nice smooth transitions
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

	# Rainbow color animation
	def rainbow(self,wait_ms=20):
		# Draw rainbow that fades across all pixels at once.
		j = self.updateFrame(self.led_count)

		for x in range(self.num_cols):
			for y in range(self.num_rows):
				i = x*self.num_rows + y
				if self.balls[y][x].text == False:
					self.writeBallColor(x,y,self.wheel(((i*PIXEL_RATIO)+j) & 255))
		self.strip.show()
		time.sleep(wait_ms/1000.0)

	# Rainbow text color animation
	def rainbowText(self,wait_ms=20):
		# Draw rainbow that fades across all pixels at once.
		j = self.updateFrame(self.led_count)

		for x in range(self.num_cols):
			for y in range(self.num_rows):
				i = x*self.num_rows + y
				if self.balls[y][x].text == True:
					self.writeBallColor(x,y,self.wheel(((i*PIXEL_RATIO)+j) & 255))
		self.strip.show()
		time.sleep(wait_ms/1000.0)

	# Rainbow cycle makes all of the BG balls the same color and changes the color over time
	def rainbowCycle(self,wait_ms=20):
		# Draw rainbow that uniformly distributes itself across all pixels.
		j = self.updateFrame(self.led_count)

		for x in range(self.num_cols):
			for y in range(self.num_rows):
				i = x*self.num_rows + y
				if self.balls[y][x].text == False:
					self.writeBallColor(x,y,self.wheel((((i*PIXEL_RATIO)/(self.num_balls*PIXEL_RATIO))+j) & 255))
		self.strip.show()
		time.sleep(wait_ms/1000.0)

		# Rainbow cycle makes all of the text the same color and changes the color over time
	def rainbowCycleText(self,wait_ms=20):
		# Draw rainbow that uniformly distributes itself across all pixels.
		j = self.updateFrame(self.led_count)

		for x in range(self.num_cols):
			for y in range(self.num_rows):
				i = x*self.num_rows + y
				if self.balls[y][x].text == True:
					self.writeBallColor(x,y,self.wheel((((i*PIXEL_RATIO)/(self.num_balls*PIXEL_RATIO))+j) & 255))
		self.strip.show()
		time.sleep(wait_ms/1000.0)

	# Breathing color animation. Uses the random color list in Utils
	def breathing(self,text=False,wait_ms=20):
		# Cycle in and out of random colors from colorList
		j = self.updateFrame(100)

		# If we are on a new cycle, or a color has not been picked then pick a color
		if j == 0 or self.breathColor == None:
			self.breathColor = random.choice(colorListRGB)

		# The brightness factor 0-1.0. Adjusts the brightness of the color
		brightnessFactor = math.sin(j*(math.pi/100))

		# Apply the brightness factor to the color selected
		self.breathColorModified = [int(i*brightnessFactor) for i in self.breathColor]

		# Color the balls
		self.colorFill(Color(self.breathColorModified[0],self.breathColorModified[1],self.breathColorModified[2]),False,text)
		time.sleep(wait_ms/1000.0)	# wait time

	def twinkle(self):
		# If start time has not been defined, do so
		if self.twinkleStartTime == 0:
			self.twinkleStartTime = time.time()

		# If a twinkle wait time has not been generated then do so
		if self.twinkleWaitTime == 0:
			self.twinkleWaitTime = random.random() * 3	# Pick a random number between 0 and 3 and set the wait time as that
		
		nowTime = time.time()

		# Determine the time elapsed since the start time
		self.twinkleTimeElapsed = nowTime - self.twinkleStartTime

		# Update the twinkles 
		for x in range(self.num_cols):
			for y in range(self.num_rows):
				# If the ball is a current twinkle ball then update the frame and color
				if self.balls[y][x].twinkle:
					colorElement = int(self.balls[y][x].brightnessFactor() * 255)

					# print "color",colorElement,"at",x,y,"brightness factor:",self.balls[y][x].brightnessFactor(),"frame:",self.balls[y][x].twinkleFrame,"length:",self.balls[y][x].twinkleLength
					self.writeBallColor(x,y,Color(colorElement,colorElement,colorElement))

					self.balls[y][x].twinkleStep()
				elif self.balls[y][x].text == False:
					self.writeBallColor(x,y,Color(20,0,110))

		# If the time elapsed is greater than the twinkleWaitTime then initiate a twinkle
		if self.twinkleTimeElapsed >= self.twinkleWaitTime:
			row = int(random.randint(0,self.num_rows-1))
			col = int(random.randint(0,self.num_cols-1))

			# If the ball is text then get out of here. Do one more loop to determine a new ball
			if self.balls[row][col].text or self.balls[row][col].twinkle:
				return

			self.balls[row][col].twinkle = True
			self.balls[row][col].twinkleLength = random.randint(50,100)

			# Set a new twinkle wait time and reset the time elapsed
			self.twinkleStartTime = time.time()
			self.twinkleWaitTime = random.random() * 2	# Pick a random number between 0 and 3 and set the wait time as that

		self.strip.show()

# CONTENT GENERATION --------------------------------------------------------------------

	# This function obtains the time and concatenates it to the display string
	def time(self, lineNum):
		# Get the current local time and parse it out to usable variables
		t = time.localtime()
		hours = t.tm_hour
		mins = t.tm_min
		secs = t.tm_sec

		# If the time format calls for 12 hour, convert the time
		if self.timeFormat == '12h':
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
		if hours < 10 and self.animationSpeed[0] == 0:
			if self.timeFormat == '12h':
				hourStr = ' ' + str(hours)
			elif self.timeFormat == '24h':
				hourStr = '0' + str(hours)
		else:
			hourStr = str(hours)

		# Used to determine colon lit state
		if secs % 2 == 1 and self.animationSpeed[0] <= 5.0:
			# Even seconds, concatenate the strings with a colon in the middle
			timeStr = hourStr + ';' + minStr
		else:
			# Odd seconds, concatenate the strings with a semicolon(blank) in the middle
			timeStr = hourStr + ':' + minStr 

		# Concatenate the date string to the master string with a space termination
		if lineNum == 0:
			self.displayStringLine1 += timeStr + ' '
		elif lineNum == 1:
			self.displayStringLine2 += timeStr + ' '

		# Check to see if the minute has changed this is to update the weather. 
		if mins != self.minsPrev:
			self.updateWeather = True
			self.minsPrev = mins

	# This function obtains the date and concatenates it to the display string
	def date(self, lineNum):
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
		if lineNum == 0:
			self.displayStringLine1 += dateStr + ' '
		elif lineNum == 1:
			self.displayStringLine2 += dateStr + ' '

	# This function concatenates the custom text to the display string
	def text(self, lineNum):
		textStr = self.customText.upper()

		if lineNum == 0:
			self.displayStringLine1 += textStr + ' '
		elif lineNum == 1:
			self.displayStringLine2 += textStr + ' '

	# This function obtains the weather and concatenates it to the display string
	def weather(self, lineNum):
		# In case we are not displaying the time, check the time to see if we need to update the weather
		# Get the current local time and parse it out to usable variables
		t = time.localtime()
		mins = t.tm_min

		# Check to see if the minute has changed this is to update the weather. 
		if mins != self.minsPrev:
			self.updateWeather = True
			self.minsPrev = mins		

		# base_url variable to store url //
		base_url = "http://api.openweathermap.org/data/2.5/weather?"

		# If the zip code field is not empty then use the zip code. Otherwise use the filled city name
		if self.weatherZipLocation != '':
			complete_url = base_url + "appid=" + self.openWeatherKey + "&zip=" + self.weatherZipLocation
		else:
			complete_url = base_url + "appid=" + self.openWeatherKey + "&q=" + self.weatherCityLocation

		if self.updateWeather:
			try:
				response = requests.get(complete_url)
			except:
				return

			self.weatherResponse = response.json()
			self.updateWeather = False

			# Stringify the cod element for error checking
			self.weatherResponse['cod'] = str(self.weatherResponse['cod'])

		if self.weatherResponse['cod'] == '401':
			weatherStr = 'key error'
		if self.weatherResponse['cod'] == '404':
			weatherStr = 'city not found'
		elif self.weatherResponse['cod'] == '200':
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
			weatherStr = 'error'

		# Concatenate the weather string to the display string
		weatherStr = weatherStr.upper() 	# Uppercase the string

		if lineNum == 0:
			self.displayStringLine1 += weatherStr + ' '
		elif lineNum == 1:
			self.displayStringLine2 += weatherStr + ' '

# SETTING HANDLING -------------------------------------------------------------------

	# This will dump the current settings to settings.txt
	def dumpSettings(self):
		# Create a settings dictionary
		settings = {
			'animationSpeed' : self.animationSpeed,		# Balls/s for animations. Needs to be a float (.0). Static default
			'textColor' : self.textColor,
			'fontName' : self.fontName,
			'textSpacing' : self.textSpacing,
			'customText' : self.customText,
			'weatherZipLocation' : self.weatherZipLocation,
			'weatherCityLocation' : self.weatherCityLocation,
			'tempUnits' : self.tempUnits,
			'content' : self.content,
			'bgColor' : self.bgColor,
			'brightness' : self.brightness,
			'timeFormat' : self.timeFormat,
			'boardType'  : self.boardType,
			'lineCount'  : self.lineCount
		}

		# Dump the settings to settings.txt
		with open('/home/pi/pingPongBallClock/code/settings.txt', 'w') as filehandle:
			json.dump(settings, filehandle)

	# This will load the settings from settings.txt
	def loadSettings(self,bootup=True):
		# Get the settings dictionary from settings.txt
		with open('/home/pi/pingPongBallClock/code/settings.txt', 'r') as filehandle:
			settings = json.load(filehandle)

		# Get the API keys from apikeys.txt
		with open('/home/pi/pingPongBallClock/code/apikeys.txt', 'r') as filehandle:
			apikeys = json.load(filehandle)
		
		# Set the API Key variables
		self.openWeatherKey = apikeys['openweather']

		# Set variables from the settings 
		self.animationSpeed = settings['animationSpeed']									 # Balls/s for animations. Needs to be a float (.0). Static default
		self.textColor = settings['textColor']
		self.fontName = settings['fontName']
		self.textSpacing = settings['textSpacing']
		self.customText = settings['customText']
		self.weatherZipLocation = settings['weatherZipLocation']
		self.weatherCityLocation = settings['weatherCityLocation']
		self.tempUnits = settings['tempUnits']
		self.content = settings['content']
		self.bgColor = settings['bgColor']
		self.brightness = settings['brightness']
		self.timeFormat = settings['timeFormat']
		self.boardType = settings['boardType']
		self.lineCount = settings['lineCount']

		print self.animationSpeed 

		# Since we have loaded new settings, assume the displays have changed
		self.bgDisplayChanged = True
		self.textDisplayChanged = True
		self.updateWeather = True

		# Establish the text origin list with spaces for 2 lines
		self.textOrigin = [0,0]

		# Address possible different settings based on the board type
		if self.boardType == 'normal':
			self.textOrigin[0] = [1,1]		#[line #][x,y]
		elif self.boardType == 'xl':
			self.num_balls = 257				# Number of balls on your board #CHANGED FOR XL
			self.num_rows = 13				# How many rows of balls are on your board #CHANGED FOR XL
			self.num_cols = 23				# How many effective columns are on your board. This is equal to your widest row. #CHANGED FOR XL

			if self.lineCount == 1:
				self.textOrigin[0] = [2,4]
			elif self.lineCount == 2:
				self.textOrigin[0] = [4,1]
				self.textOrigin[1] = [1,7]

		# Calculate the LED count
		self.led_count = self.num_balls * PIXEL_RATIO

		# Address possible font change
		if self.fontName == 'slanted':
			self.font = slanted
		elif self.fontName == 'digits':
			self.font = digits

		# Fix unicode content list
		for i in range(len(self.content)):
			self.content[i] = str(self.content[i])

		# Set brightness if we are not in bootup
		if bootup == False:
			self.strip.setBrightness(self.brightness)

# Initialize an instance of the LEDStrip class
PPB = PingPongBoard()
