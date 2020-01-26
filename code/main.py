import threading
import time

from flask import Flask
from flaskUtils import app
from LEDUtils import PPB
from neopixel import *

if __name__ == '__main__':
	# Start the clock function
	x = threading.Thread(target=PPB.clock, args=())
	x.daemon = True
	x.start()
	
	# Start the flask server
	app.run(host='0.0.0.0', port=80)
