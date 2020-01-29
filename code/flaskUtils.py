# -*- coding: latin-1 -*-

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
	
	PPB.displayChanged = True
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
	
	PPB.displayChanged = True
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

	if checked == 'true':
		PPB.content.append(content)
	else:
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

