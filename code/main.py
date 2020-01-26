import threading
import time

from flask import Flask
from flaskUtils import app
from LEDUtils import PPB
from neopixel import *

if __name__ == '__main__':
	# Start the flask server
	x = threading.Thread(target=app.run, args=())
	x.daemon = True
	x.start()
	
	# Start the clock server
	PPB.clock()
