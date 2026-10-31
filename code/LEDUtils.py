import argparse
import copy
import json
import math
import random
import signal
import sys
import threading
import time
from pathlib import Path

import requests
from rpi_ws281x import Color, PixelStrip
from Utils import *
import storage

CODE_DIR = Path(__file__).resolve().parent

# This is the PingPongBoard class that drives everything. All functions related to lighting and writing are in here. 
class PingPongBoard:
	def __init__(self):
		self._settingsLock = threading.RLock()
		self.pendingBoardConfig = None
		self.restart_at = None
		self.num_balls = NUM_BALLS		# Needed for changing board type
		self.num_rows = NUM_ROWS		# Needed for changing board type
		self.num_cols = NUM_COLS		# Needed for changing board type

		self.animationFrame = [0, 0]			# Separate background and text animation frames
		self.animationStartTime = [0,0]		# Used for animations and when to move the string
		self.animationTimeElapsed = [0,0]	# Used for animations and when to move the string
		self.breathColor = None				# Necessary for the breathing animation
		self.twinkleStartTime = 0			# Used for timing when to initate a twinkle
		self.twinkleTimeElapsed = 0			# Used for timing when to initate a twinkle
		self.twinkleWaitTime = 0
		self._twinkleFrameTime = None

		self.fontChanged = False				# Store whether or not the font has changed
		self.textOriginMoved = [False, False]	# Store whether or not the origin of the display string has changed
		self.displayString = ['', '']			# This is the string that will be ultimately displayed on screen
		self.displayStringPrev = ['', '']		# This is what the display string was during the previous loop
		self.displayStringLength = [0, 0]		# This is calculated and used to determine when we have cycled through an entire string during animations

		self.weatherResponse = None
		self._weatherRequest = None
		self._weatherResult = None
		self._weatherConfig = None
		self._weatherNextAttempt = 0
		self._weatherLock = threading.Lock()

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
		self.strip = PixelStrip(self.led_count, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, self.brightness, LED_CHANNEL, LED_STRIP)
		self.strip.begin()

	# Sets up a ball object for every single ball on the board. The ball object definition can be found in Utils
	def setupBalls(self):
		for y in range(self.num_rows):
			for x in range(self.num_cols):
				self.balls[y][x] = Ball([y,x],self.boardType)    #passes [row,col], and the type of board which is used for the ledAdresses

	def frameSnapshot(self):
		return {
			'boardType': self.boardType,
			'brightness': self.brightness,
			'rows': [[ball.color if 0 <= ball.ledNum < self.num_balls else None
			          for ball in row] for row in reversed(self.balls)],
		}

	# Actually lights a specic ball (LED) with the color provided to the function. This will check to see if the color is different than the one already set for the ball first. If it is the same then it will not rewrite.
	def writeBallColor(self,col,row,color):
		# Do not proceed if bad coordinates (could maybe replace with try/catch)
		if col < 0 or col >= self.num_cols or row < 0 or row >= self.num_rows:
			return

		# Some grid positions do not correspond to a physical ball.
		if not 0 <= self.balls[row][col].ledNum < self.num_balls:
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

		glyph = font.get(ord(char), font.get(ord('?'), font[ord(' ')]))

		# Determine the distance to the next character based on the current character and the spacing setting
		if char.isspace():
			distanceToNext = 4
		else:
			distanceToNext = len(glyph[0]) + self.textSpacing

		# Do not write characters outside of the display area
		if col <= -4 or col > self.num_cols:
			return distanceToNext
		if row < -5 or row >= self.num_rows:
			return distanceToNext

		#Step through the rows and columns of the character and write each pixel/ball/LED
		for y in range(len(glyph)):
			for x in range(len(glyph[-(y+1)])): #Using -y to access the font row the way it was written in the font file. It is easier to write the font file visually. This accommodates that.
				if glyph[-(y+1)][x]:
					self.writeBallTextState(col+x,row+y,textBool)
				else:
					self.writeBallTextState(col+x,row+y,False)	#write the text to false so that it will be overwritten
		self.strip.show()

		# Returns the distance to the next character. Used for display string length calcs and to find the location of the next character.
		return distanceToNext

	# Writes the display string if some conditions are met. 
	def updateDisplayString(self):
		if not (self.fontChanged or any(self.textOriginMoved[:self.lineCount]) or
				self.displayString[:self.lineCount] != self.displayStringPrev[:self.lineCount] or
				any(self.displayStringPrev[self.lineCount:])):
			return

		self.textStateWipe()
		for i in range(self.lineCount):
			x, y = self.textOrigin[i]
			for char in self.displayString[i]:
				x += self.writeChar(x, y, char)
			self.textOriginMoved[i] = False
			self.displayStringPrev[i] = self.displayString[i]
			self.displayStringLength[i] = x - self.textOrigin[i][0]
		for i in range(self.lineCount, len(self.displayStringPrev)):
			self.displayStringPrev[i] = ''
		self.fontChanged = False
		self.textDisplayChanged = True
		self.bgDisplayChanged = True

	# This steps the animation frame by one. If the animation frame has reached animationEnd, reset the frame to 0
	def updateFrame(self, animationEnd, text=False):
		self.animationFrame[text] = (self.animationFrame[text] + 1) % animationEnd
		return self.animationFrame[text]

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
	def updateTextAnimation(self, lineNum):
		# If start time has not been defined, do so
		if self.animationStartTime[lineNum] == 0:
			self.animationStartTime[lineNum] = time.time()
		
		nowTime = time.time()

		# Determine the time elapsed since the start time
		self.animationTimeElapsed[lineNum]= nowTime - self.animationStartTime[lineNum]

		# If the time elapsed is >= the time one frame should take for our set speed, do the things
		if self.animationSpeed[lineNum] != 0 and self.animationTimeElapsed[lineNum] >= 1/self.animationSpeed[lineNum]:
			#Indicate the display has changed
			self.textOriginMoved[lineNum] = True

			# Move the text one space to the left
			self.textOrigin[lineNum][0] -= 1

			# Reset the x text origin to 20 if it gets through the screen
			if self.textOrigin[lineNum][0] < -1 * self.displayStringLength[lineNum]:
				self.textOrigin[lineNum][0] = 23

			# Set the start time to this time now
			self.animationStartTime[lineNum] = nowTime

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
		j = self.updateFrame(256)

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
		j = self.updateFrame(256, True)

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
		j = self.updateFrame(256)

		for x in range(self.num_cols):
			for y in range(self.num_rows):
				i = x*self.num_rows + y
				if self.balls[y][x].text == False:
					self.writeBallColor(x,y,self.wheel((((i*PIXEL_RATIO)//(self.num_balls*PIXEL_RATIO))+j) & 255))
		self.strip.show()
		time.sleep(wait_ms/1000.0)

		# Rainbow cycle makes all of the text the same color and changes the color over time
	def rainbowCycleText(self,wait_ms=20):
		# Draw rainbow that uniformly distributes itself across all pixels.
		j = self.updateFrame(256, True)

		for x in range(self.num_cols):
			for y in range(self.num_rows):
				i = x*self.num_rows + y
				if self.balls[y][x].text == True:
					self.writeBallColor(x,y,self.wheel((((i*PIXEL_RATIO)//(self.num_balls*PIXEL_RATIO))+j) & 255))
		self.strip.show()
		time.sleep(wait_ms/1000.0)

	# Breathing color animation. Uses the random color list in Utils
	def breathing(self,text=False,wait_ms=20):
		# Cycle in and out of random colors from colorList
		j = self.updateFrame(100, text)

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
		frameTime = time.monotonic()
		if self._twinkleFrameTime is not None and frameTime - self._twinkleFrameTime < 0.02:
			return
		self._twinkleFrameTime = frameTime

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
				if self.balls[y][x].twinkle and not self.balls[y][x].text:
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
			if not self.balls[row][col].text and not self.balls[row][col].twinkle and self.balls[row][col].ledNum < self.num_balls:
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
		if hours < 10 and self.animationSpeed[lineNum] == 0:
			if self.timeFormat == '12h':
				hourStr = ' ' + str(hours)
			elif self.timeFormat == '24h':
				hourStr = '0' + str(hours)
		else:
			hourStr = str(hours)

		# Used to determine colon lit state
		if secs % 2 == 1 and self.animationSpeed[lineNum] <= 5.0 and self.lineCount == 1:
			# Even seconds, concatenate the strings with a colon in the middle
			timeStr = hourStr + ';' + minStr
		else:
			# Odd seconds, concatenate the strings with a semicolon(blank) in the middle
			timeStr = hourStr + ':' + minStr 

		# Concatenate the date string to the master string with a space termination
		if lineNum == 0:
			self.displayString[0] += timeStr + ' '
		elif lineNum == 1:
			self.displayString[1] += timeStr + ' '

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
			self.displayString[0] += dateStr + ' '
		elif lineNum == 1:
			self.displayString[1] += dateStr + ' '

	# This function concatenates the custom text to the display string
	def text(self, lineNum):
		textStr = self.customText.upper()

		if lineNum == 0:
			self.displayString[0] += textStr + ' '
		elif lineNum == 1:
			self.displayString[1] += textStr + ' '

	# This function obtains the weather and concatenates it to the display string
	def _fetchWeather(self, config):
		key, zipcode, city = config
		params = {'appid': key, 'zip': zipcode} if zipcode else {'appid': key, 'q': city}
		try:
			response = requests.get('https://api.openweathermap.org/data/2.5/weather', params=params, timeout=10)
			data = response.json()
			if not isinstance(data, dict):
				data = None
			elif 'cod' not in data and response.status_code in (401, 404):
				data['cod'] = response.status_code
		except (requests.RequestException, ValueError, TypeError):
			data = None
		with self._weatherLock:
			self._weatherResult = (config, data)

	def weather(self, lineNum):
		config = (self.openWeatherKey, self.weatherZipLocation, self.weatherCityLocation)
		now = time.monotonic()
		if config != self._weatherConfig:
			self._weatherConfig = config
			self.weatherResponse = None
			self._weatherNextAttempt = 0
			self.updateWeather = True

		with self._weatherLock:
			result = self._weatherResult
			self._weatherResult = None
		if result is not None:
			self._weatherRequest = None
			if result[0] == config and result[1] is not None:
				self.weatherResponse = result[1]

		if self._weatherRequest is None and now >= self._weatherNextAttempt:
			self._weatherRequest = threading.Thread(target=self._fetchWeather, args=(config,), daemon=True)
			self._weatherNextAttempt = now + 60
			self.updateWeather = False
			self._weatherRequest.start()

		data = self.weatherResponse
		weatherStr = 'error'
		if isinstance(data, dict):
			code = str(data.get('cod', ''))
			if code == '401':
				weatherStr = 'key error'
			elif code == '404':
				weatherStr = 'city not found'
			elif code == '200':
				try:
					temperature = float(data['main']['temp'])
					description = data['weather'][0]['description']
					if not isinstance(description, str) or not math.isfinite(temperature):
						raise ValueError('Invalid weather data')
					if self.tempUnits == 'k':
						unit = ' K '
					elif self.tempUnits == 'c':
						temperature -= 273.15
						unit = '`C '
					elif self.tempUnits == 'f':
						temperature = temperature * (9.0 / 5) - 459.67
						unit = '`F '
					else:
						raise ValueError('Invalid temperature unit')
					weatherStr = str(int(round(temperature))) + unit + description
				except (KeyError, IndexError, TypeError, ValueError, OverflowError):
					pass
		self.displayString[lineNum] += weatherStr.upper() + ' '

# SETTING HANDLING -------------------------------------------------------------------

	def settingsSnapshot(self):
		with self._settingsLock:
			settings = {key: copy.deepcopy(getattr(self, key)) for key in (
				'animationSpeed', 'textColor', 'fontName', 'textSpacing', 'customText',
				'weatherZipLocation', 'weatherCityLocation', 'tempUnits', 'content',
				'bgColor', 'brightness', 'timeFormat', 'boardType', 'lineCount')}
			if self.pendingBoardConfig is not None:
				settings.update(self.pendingBoardConfig)
			return settings

	def dumpSettings(self):
		with self._settingsLock:
			storage.save_state('settings.json', self.settingsSnapshot(), storage.device_settings)

	def changeBoardType(self, boardType):
		if boardType not in ('normal', 'xl'):
			raise ValueError('Invalid board type')
		with self._settingsLock:
			settings = self.settingsSnapshot()
			settings['boardType'] = boardType
			if boardType == 'normal':
				settings['lineCount'] = 1
			storage.save_state('settings.json', settings, storage.device_settings)
			if boardType == self.boardType:
				self.pendingBoardConfig = None
				self.restart_at = None
			else:
				self.pendingBoardConfig = {'boardType': boardType, 'lineCount': settings['lineCount']}
				self.restart_at = time.monotonic() + 2

	def loadSettings(self, bootup=True):
		with self._settingsLock:
			settings = storage.load_state('settings.json', CODE_DIR / 'settings.txt', storage.device_settings)
			apikeys = storage.load_state('apikeys.json', CODE_DIR / 'apikeys.txt', storage.api_keys)
			storage.device_settings(settings)
			storage.api_keys(apikeys)
			self.openWeatherKey = apikeys['openweather']
			for key in ('animationSpeed', 'textColor', 'fontName', 'textSpacing', 'customText',
					'weatherZipLocation', 'weatherCityLocation', 'tempUnits', 'content',
					'bgColor', 'brightness', 'timeFormat'):
				setattr(self, key, copy.deepcopy(settings[key]))
			if bootup:
				self.boardType = settings['boardType']
				self.lineCount = settings['lineCount']
				self.num_balls, self.num_rows, self.num_cols = (
					(257, 13, 23) if self.boardType == 'xl' else (NUM_BALLS, NUM_ROWS, NUM_COLS))
				self.led_count = self.num_balls * PIXEL_RATIO
			elif settings['boardType'] == self.boardType:
				self.lineCount = settings['lineCount']
				self.pendingBoardConfig = None
				self.restart_at = None
			else:
				self.pendingBoardConfig = {key: settings[key] for key in ('boardType', 'lineCount')}
				self.restart_at = time.monotonic() + 2
			self.bgDisplayChanged = True
			self.textDisplayChanged = True
			self.updateWeather = True
			self.textOrigin = [[1, 1], 0]
			if self.boardType == 'xl':
				self.textOrigin = [[2, 4], 0] if self.lineCount == 1 else [[4, 1], [1, 7]]
			self.font = slanted if self.fontName == 'slanted' else digits
			self.fontChanged = True
			if not bootup:
				self.strip.setBrightness(self.brightness)

# Initialize an instance of the LEDStrip class
PPB = PingPongBoard()
