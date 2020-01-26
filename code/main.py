from flask import Flask, request, render_template
import threading
from neopixel import *
import LEDUtil
import time

print "initializing..."

#Establish variables that will be used
hoursPrev = 99  #used for clock updating
minsPrev = 99   #used for clock updating
secsPrev = 99   #used for clock updating
colonLit = False

# Initialize the LED class, start up the LED strip
LED = LEDUtil.LEDStrip()

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
	
	# Change the bg color accordingly
	if program == "solid":
		LED.bgColor = ["solid", Color(red,green,blue)]
	else:
		LED.bgColor = ["animation", program]
	return ""

# Flask Text Color API
@app.route("/api/textcolor", methods=['POST'])
def setTextColor():
	# Read the values from the POST
	program = request.form['color']
	red = int(request.form['red'])
	green = int(request.form['green'])
	blue = int(request.form['blue'])
	
	# Change the bg color accordingly
	if program == "solid":
		LED.textColor = ["solid", Color(red,green,blue)]
		LED.changeTextColor(LED.textColor[1])
	else:
		LED.textColor = ["animation", program]
	return ""

	# Flask Font API
@app.route("/api/font", methods=['POST'])
def setFont():
	# Read the values from the POST
	font = request.form['font']
	
	# Assign the font variable in LED class
	LED.font = font
	print "changing font to", LED.font

	# Reset the background and variables to make the screen refresh completely on next loop iteration
	LED.colorFill(LED.bgColor[1], True)		# True boolean to make sure that the whole screen wipes including text
	secsPrev = 99
	minsPrev = 99
	hoursPrev = 99
	return ""

def clock():
	global hoursPrev
	global minsPrev
	global secsPrev
	global colonLit

	while(True):
		# Write the BG. Will not overwrite text per the function
		if LED.bgColor[0] == "solid":
			LED.colorFill(LED.bgColor[1])
		elif LED.bgColor[0] == "animation":
			if LED.bgColor[1] == "rainbow":
				LED.rainbow()
			elif LED.bgColor[1] == "rainbowCycle":
				LED.rainbowCycle()

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
		if secs != secsPrev:
			colonLit ^= True  #flip the colonLit bool

			if colonLit:
				LED.writeBall(9,4,LED.textColor[1],True)
				LED.writeBall(10,2,LED.textColor[1],True)
				LED.strip.show()
			else: 
				LED.writeBall(9,4,LED.textColor[1],False)     #Keep the color white, but we toggle the text to False so that it will be overwritten by the rainbow
				LED.writeBall(10,2,LED.textColor[1],False)     #Keep the color white, but we toggle the text to False so that it will be overwritten by the rainbow
				LED.strip.show()

			secsPrev = secs

		# Check to see if the minute has changed. If it has, write the new minute
		if mins != minsPrev:    
			# Convert the mins to a string so that we can parse the individual numbers for display
			minsStr = str(mins)

			# Write the actual numerals
			if mins < 10:
				LED.writeChar(11,1,0,LED.textColor[1])
				LED.writeChar(15,1,int(minsStr[0]),LED.textColor[1])
			else:
				LED.writeChar(11,1,int(minsStr[0]),LED.textColor[1])
				LED.writeChar(15,1,int(minsStr[1]),LED.textColor[1])
			minsPrev = mins

		# Check to see if the hour has changed. If it has, write the new hour
		if hours != hoursPrev:
			
			# Convert the mins to a string so that we can parse the individual numbers for display
			hoursStr = str(hours)

			if hoursPrev >= 10 and hours < 10:
				LED.writeChar(1,1,'blank',LED.textColor[1])
				LED.writeChar(5,1,int(hoursStr[0]),LED.textColor[1])
			elif hours < 10:
				LED.writeChar(5,1,int(hoursStr[0]),LED.textColor[1])
			else:
				LED.writeChar(1,1,int(hoursStr[0]),LED.textColor[1])
				LED.writeChar(5,1,int(hoursStr[1]),LED.textColor[1])
			hoursPrev = hours

		# If there was a chnaged text color, indicate that we have taken care of it
		LED.textColorChange = False

if __name__ == '__main__':
	x = threading.Thread(target=clock, args=())
	x.daemon = True
	x.start()
	
	app.run(host='0.0.0.0', port=80)
