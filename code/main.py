import threading
import time

from flask import Flask
from flaskUtils import app
from LEDUtils import PPB
from neopixel import *

if __name__ == '__main__':
	# Start the flask server
	x = threading.Thread(target=app.run, kwargs=dict(host='0.0.0.0',port=80))
	x.daemon = True
	x.start()
	
	while(True):
		PPB.updateBGColor()
		PPB.clock()
		PPB.updateTextColor()
	