# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
import time

from neopixel import *
from Utils import *

import argparse
import signal
import sys
import math

def signal_handler(signal, frame):
    colorWipe(self.strip, Color(0,0,0))
    sys.exit(0)

# LED strip configuration:
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
LED_COUNT      = 256
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 125     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_GRB   # Strip type and colour ordering

class LEDStrip:
    def __init__(self):
        # Intialize the library (must be called once before other functions).
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
        self.strip.begin()

        self.numBalls = 128
        self.numRows = 7
        self.numCols = 20
        self.animationFrame = 0
        self.animationEnd = 1

        # Set up the ball objects
        self.setupBalls()

    def setupBalls(self):
        for y in range(self.numRows):
            for x in range(self.numCols):
                self.ball[y][x] = Ball([y,x])    #passes [row,col]

    def writeBall(self,col,row,color):
        # Do not proceed if bad coordinates (could maybe replace with try/catch)
        if col < 0 or col >= 20 or row < 0 or row >= 7:
            return

        # If the color is different than what the buffer has stored, write it and show it
        if buffer[row][col] != color:
            self.strip.setPixelColor((row[y][x])*2,color)
            buffer[row][col] = color

    def writeChar(self,col,row,char,bgcolor,color=Color(125,125,125),):
        for y in range(len(slanted[char])):
            for x in range(len(slanted[char][-(y+1)])): #Using -j to access the font row the way it was written in the font file. It is easier to write the font file visually. This accommodates that.
                if slanted[char][-(y+1)][x]:
                    self.writeBall(col+x,row+y,color)
                else:
                    self.writeBall(col+x,row+y,bgcolor)
        self.strip.show()

    def updateFrame(self, animationEnd):
        self.animationFrame += 1
        self.animationEnd = animationEnd
        if(self.animationFrame>=self.animationEnd):
            self.animationFrame = 0
        return self.animationFrame

    def colorFill(self,color):
        for y in range(self.numRows):
            for x in range(self.numCols):
                self.writeBall(x,y,color)
        self.strip.show()

    def wheel(self,pos):
        """Generate rainbow colors across 0-255 positions."""
    	if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Color(0, pos * 3, 255 - pos * 3)

    def rainbow(self,wait_ms=20):
        """Draw rainbow that fades across all pixels at once."""
        j = self.updateFrame(256)

        for i in range(self.numBalls):
            self.strip.setPixelColor(i*2, self.wheel(((i*2)+j) & 255))
        self.strip.show()
        time.sleep(wait_ms/1000.0)

    def rainbowCycle(self,wait_ms=20):
        """Draw rainbow that uniformly distributes itself across all pixels."""
        j = self.updateFrame(256)

        for i in range(self.numBalls):
            self.strip.setPixelColor(i*2, self.wheel((((i*2)/(self.numBalls*2))+j) & 255))
        self.strip.show()
        time.sleep(wait_ms/1000.0)
