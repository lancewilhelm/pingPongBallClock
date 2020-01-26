import threading
import time

from flask import Flask
from flaskUtils import app
from LEDUtils import PPB
from neopixel import *

if __name__ == '__main__':
	# Start the flask server
	x = threading.Thread(target=app.run, kwargs=dict(debug=False, use_reloader=False))
	x.daemon = True
	x.start()
	
	PPB.clock()
