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
		PPB.displayStringLine1 = ''
		PPB.displayStringLine2 = ''

		# Get the display string components
		for x in PPB.content:
			x = list(x.split(' '))		# Split the content list item into a list with a space as a delimeter. This gives us what the content is and the line number.
			
			# If the content title matches the cases, go to that function and pass the line number
			if x[0] == 'time':
				PPB.time(int(x[1]))
			elif x[0] == 'date':
				PPB.date(int(x[1]))
			elif x[0] == 'text':
				PPB.text(int(x[1]))
			elif x[0] == 'weather':
				PPB.weather(int(x[1]))

		# If the animation speed is not 0, then update the animation
		if PPB.animationSpeed[0] != 0:
			PPB.updateTextAnimation()

		# Write the display string text state if the string is different than last loop
		PPB.updateDisplayString()

		# Update the actual ball color light
		PPB.updateBoardColors()