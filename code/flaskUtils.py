from flask import Flask, request, render_template
from LEDUtils import *

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
	animation = request.form['animation']

	if animation == "static":
		PPB.textOrigin = [1,1]
		PPB.animationSpeed = 0
	if animation == "scrolling":
		speed = float(request.form['speed'])
		PPB.animationSpeed = speed

	# Wipe the screen
	PPB.textStateWipe()
	return ""

# Flask Select Content API
@app.route("/api/setcontent", methods=['POST'])
def setContent():
	# Read the values from the POST
	content = str(request.form['content'])
	checked = str(request.form['checked'])

	if checked == 'true' and (content in PPB.content) == False:
		PPB.content.append(content)
	elif checked == 'false' and (content in PPB.content) == True:
		PPB.content.remove(content)

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
		PPB.dumpSettings()
	elif action == 'load':
		PPB.loadSettings(False)

	return ""

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
@app.route("/api/webpagesettings", methods=['GET'])
def updateWebPageSettings():

	# Get the web page settings dictionary from webpagesettings.txt
	with open('/home/pi/pingPongBallClock/code/webpagesettings.txt', 'r') as filehandle:
	webPageSettings = filehandle.read()
	
	print webPageSettings

	return webPageSettings