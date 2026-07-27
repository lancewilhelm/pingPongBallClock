#!/usr/bin/env python

import threading
import time
import socket

from flask import Flask
from flaskUtils import app
from LEDUtils import PPB
from werkzeug.serving import ThreadedWSGIServer, make_server


class IPv6OnlyWSGIServer(ThreadedWSGIServer):
	"""Keep the IPv6 listener separate so the IPv4 listener remains available."""

	def server_bind(self):
		self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
		return super().server_bind()


def serve(server):
	server.serve_forever()

if __name__ == '__main__':
	# Bind independent IPv4 and IPv6 listeners. Tailscale is IPv6-only on PPBC,
	# while the local Wi-Fi network is IPv4-only.
	servers = [
		make_server('0.0.0.0', 5000, app, threaded=True),
		IPv6OnlyWSGIServer('::', 5000, app),
	]
	for server in servers:
		threading.Thread(target=serve, args=(server,), daemon=True).start()
	
	while(True):

		# Reset the string at the beginning of each loop
		PPB.displayString[0] = ''
		PPB.displayString[1] = ''

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
		for i in range(PPB.lineCount):
			if PPB.animationSpeed[i] != 0:
				PPB.updateTextAnimation(i)

		# Write the display string text state if the string is different than last loop
		PPB.updateDisplayString()

		# Update the actual ball color light
		PPB.updateBoardColors()
