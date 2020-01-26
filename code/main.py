from flask import Flask
import threading
from neopixel import *
from utils import LEDUtils
from utils.flaskUtils import app
import time

print "initializing..."

#Establish variables that will be used
hoursPrev = 99  #used for clock updating
minsPrev = 99   #used for clock updating
secsPrev = 99   #used for clock updating
colonLit = False

if __name__ == '__main__':
	# Initialize the LEDs
	LED = LEDUtils.LEDStrip()

	x = threading.Thread(target=clock, args=())
	x.daemon = True
	x.start()
	
	# Start the flask server
	app.run(host='0.0.0.0', port=80)
