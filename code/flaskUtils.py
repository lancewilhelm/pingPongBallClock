import os
import sys

from flask import Flask, render_template, request
from LEDUtils import *
from Utils import *

#Setup the flask object and get it going
app = Flask(__name__)

# Flask Index
@app.route("/", methods=['GET'])
def index():
	return render_template('index.html')

# Flask BG Color API
@app.route("/api/bgcolor", methods=['POST'])
def setBGColor():
	# Read the values from the POST
	program = request.form['color']
	red = int(request.form['red'])
	green = int(request.form['green'])
	blue = int(request.form['blue'])
	
	PPB.bgDisplayChanged = True
	# Change the bg color accordingly
	if program == "solid":
		PPB.bgColor = ["solid", Color(red,green,blue)]
	else:
		PPB.bgColor = ["animation", program]
	return ""

# Flask Text Color API
@app.route("/api/textcolor", methods=['POST'])
def setTextColor():
	# Read the values from the POST
	program = request.form['color']
	red = int(request.form['red'])
	green = int(request.form['green'])
	blue = int(request.form['blue'])
	
	PPB.textDisplayChanged = True
	# Change the bg color accordingly
	if program == "solid":
		PPB.textColor = ["solid", Color(red,green,blue)]
	else:
		PPB.textColor = ["animation", program]
	return ""

# Flask Font API
@app.route("/api/font", methods=['POST'])
def setFont():
	# Read the values from the POST
	font = request.form['font']
	
	# Assign the font variable in LED class
	if font == "slanted":
		PPB.font = slanted
	elif font == "digits":
		PPB.font = digits

	PPB.fontName = font
	PPB.fontChanged = True
	PPB.updateDisplayString()

	return ""

# Flask Text Animation API
@app.route("/api/textanimation", methods=['POST'])
def setTextAnimation():
	# Read the values from the POST
	animation = str(request.form['animation'])
	lineNum = int(request.form['lineNum'])

	if animation == "static":
		if PPB.boardType == 'normal':
			PPB.textOrigin[0] = [1,1]
		elif PPB.boardType == 'xl':
			if PPB.lineCount == 1:
				PPB.textOrigin[0] = [2,4]
			elif PPB.lineCount == 2:
				if lineNum == 0:
					PPB.textOrigin[lineNum] = [4,1]
				elif lineNum == 1:
					PPB.textOrigin[lineNum] = [1,7]
		PPB.animationSpeed[lineNum] = 0
	if animation == "scrolling":
		speed = float(request.form['speed'])
		PPB.animationSpeed[lineNum] = speed

	# Reset the text on the screen
	PPB.textStateWipe()
	PPB.textOriginMoved = [True, True]
	PPB.updateDisplayString()
	return ""

# Flask Select Content API
@app.route("/api/setcontent", methods=['POST'])
def setContent():
	# Read the values from the POST
	content = str(request.form['content'])
	lineNum = str(request.form['lineNum'])
	checked = str(request.form['checked'])

	contentChunk = content + ' ' + lineNum

	if checked == 'true' and (contentChunk in PPB.content) == False:
		PPB.content.append(contentChunk)
	elif checked == 'false' and (contentChunk in PPB.content) == True:
		PPB.content.remove(contentChunk)

	print PPB.content
	PPB.textStateWipe()
	return ""

# Flask Set Custom Text API
@app.route("/api/setcustomtext", methods=['POST'])
def setCustomText():
	# Read the values from the POST
	text = str(request.form['text'])

	PPB.customText = text
	return ""

# Flask Set Custom Text API
@app.route("/api/weather", methods=['POST'])
def setWeather():
	# Read the values from the POST
	PPB.tempUnits = str(request.form['unit'])
	PPB.weatherZipLocation = str(request.form['zip'])
	PPB.weatherCityLocation = str(request.form['city'])

	PPB.updateWeather = True
	return ""

# Flask Settings API
@app.route("/api/settings", methods=['POST'])
def updateSettings():
	# Read the values from the POST
	action = str(request.form['action'])

	if action == 'save':
		PPB.dumpSettings('settings')

	return ""

# Flask Board Config API
@app.route("/api/configuration", methods=['GET','POST'])
def updateConfiguration():

	if request.method == 'POST':
		# Read the values from the POST
		action = str(request.form['action'])
		filename = str(request.form['filename'])
		
		if action == 'save':
			PPB.configs.append(filename)
			PPB.dumpSettings(filename)
		elif action == 'load':
			PPB.loadSettings(filename, False)
		elif action == 'delete':
			PPB.configs.remove(filename)
			os.remove('configurations/' + filename + '.txt')

		return ""
	
	elif request.method == 'GET':
		# Get the configs list from configs_list.txt and return it
		with open('/home/pi/pingPongBallClock/code/configurations/configs_list.txt', 'r') as filehandle:
			return filehandle.read()
	

# Flask Set Brightness API
@app.route("/api/brightness", methods=['POST'])
def setBrightness():
	# Read the values from the POST
	brightness = int(request.form['brightness'])

	PPB.strip.setBrightness(brightness)

	return ""

# Flask Set Brightness API
@app.route("/api/timeformat", methods=['POST'])
def setTimeFormat():
	# Read the values from the POST
	timeFormat = str(request.form['timeFormat'])

	PPB.timeFormat = timeFormat

	return ""

# Flask Web PageSettings API
@app.route("/api/webpagesettings", methods=['GET','POST'])
def updateWebPageSettings():
	if request.method == 'GET':
		# Get the web page settings from webpagesettings.txt
		with open('/home/pi/pingPongBallClock/code/webpagesettings.txt', 'r') as filehandle:
			return filehandle.read()
	
	elif request.method == 'POST':
		settings = str(request.form['settings'])
		# Write the settings to webpagesettings.txt
		with open('/home/pi/pingPongBallClock/code/webpagesettings.txt', 'w') as filehandle:
			filehandle.write(settings)
		return ""

# Board Type API
@app.route("/api/boardtype", methods=['POST'])
def setBoardType():
	# Read the values from the POST
	boardType = str(request.form['boardType'])

	if boardType == 'normal':
		PPB.lineCount = 1

	# Change the board type and save the settings
	PPB.boardType = boardType
	PPB.dumpSettings()

	return ""

# XL Settings API
@app.route("/api/xlsettings", methods=['POST'])
def setXLSettings():
	# Read the values from the POST
	lineCount = int(request.form['lineCount'])

	PPB.lineCount = lineCount

	if PPB.boardType == 'xl':
		if PPB.lineCount == 1:
			PPB.textOrigin[0] = [2,4]
		elif PPB.lineCount == 2:
			PPB.textOrigin[0] = [4,1]
			PPB.textOrigin[1] = [1,7]
	else: 
		print "Board is not set to XL"

	# Perform a reset of the board to eliminate the ghost text balls
	PPB.colorFill(Color(0,0,0), True)

	return ""
