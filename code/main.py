import threading
import time

import LEDUtils
from flask import Flask
from flaskUtils import app
from neopixel import *

print "initializing..."

#Establish variables that will be used
hoursPrev = 99  #used for clock updating
minsPrev = 99   #used for clock updating
secsPrev = 99   #used for clock updating
colonLit = False

if __name__ == '__main__':
	# Initialize the LEDs
	LED = LEDUtils.LEDStrip()

	x = threading.Thread(target=LED.clock, args=())
	x.daemon = True
	x.start()
	
	# Start the flask server
	app.run(host='0.0.0.0', port=80)
