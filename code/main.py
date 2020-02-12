#!/usr/bin/env python
import threading
import time

from flask import Flask
from flaskUtils import app
from LEDUtils import PPB
from neopixel import *

if __name__ == '__main__':
	# Start the flask server
	x = threading.Thread(target=app.run, kwargs=dict(host='0.0.0.0',port=5000))
	x.daemon = True
	x.start()
	
	while(True):

		# Reset the string at the beginning of each loop
		PPB.displayString = ''

		# Get the display string components
		for x in PPB.content:
			if x == 'time':
				PPB.time()
			elif x == 'date':
				PPB.date()
			elif x == 'text':
				PPB.text()
			elif x == 'weather':
				PPB.weather()

		# If the animation speed is not 0, then update the animation
		if PPB.animationSpeed != 0:
			PPB.updateTextAnimation()

		# Write the display string text state if the string is different than last loop
		PPB.updateDisplayString()

		# Update the actual ball color light
		PPB.updateBoardColors()