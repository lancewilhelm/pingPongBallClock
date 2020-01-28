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

		# Reset the string at the beginning of each loop
		PPB.displayString = ''

		PPB.updateBGColor()
		PPB.time()
		PPB.date()

		PPB.displayStringLength = len(PPB.displayString)*len(PPB.font[ord(' ')][0])			# Used to determine when a full string has been scrolled through
		PPB.writeString(PPB.textOrigin[0],PPB.textOrigin[1],PPB.displayString)

		# If the animation speed is not 0, then update the animation
		if PPB.animationSpeed != 0:
			PPB.updateTextAnimation()

		PPB.updateTextColor()
	