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
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
        # Intialize the library (must be called once before other functions).
        self.numBalls = 128
        self.strip.begin()
        self.animationFrame = 0
        self.animationEnd = 1

    def writeBall(self,x,y,color):
        # Do not proceed if bad coordinates (could maybe replace with try/catch)
        if x < 0 or x >= 20 or y < 0 or y >= 7:
            return

        # If the color is different than what the buffer has stored, write it and show it
        if buffer[y][x] != color:
            self.strip.setPixelColor((row[y][x])*2,color)
            buffer[y][x] = color

    def writeChar(self,x,y,char,bgcolor,color=Color(125,125,125),):
        for j in range(len(slanted[char])):
            for i in range(len(slanted[char][-(j+1)])): #Using -j to access the font row the way it was written in the font file. It is easier to write the font file visually. This accommodates that.
                if slanted[char][-(j+1)][i]:
                    self.writeBall(x+i,y+j,color)
                else:
                    self.writeBall(x+i,y+j,bgcolor)
        self.strip.show()

    def updateFrame(self, animationEnd):
        self.animationFrame += 1
        self.animationEnd = animationEnd
        if(self.animationFrame>=self.animationEnd):
            self.animationFrame = 0
        return self.animationFrame

    def colorFill(self,color):
        for i in range(7):
            for j in range(20):
                self.writeBall(j,i,color)
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

    def clock(self):
        # Write the Initial BG
        bgcolor = Color(255,0,0)

        # Get the current local time and parse it out to usable variables
        t = time.localtime()
        hours = t.tm_hour
        mins = t.tm_min
        if hours > 12:
            hours -= 12
        
        hoursStr = str(hours)
        minsStr = str(mins)

        if mins != self.minsPrev:    
            # Write the BG

            # Write the colon in the middle
            self.writeBall(8,4,Color(125,125,125))
            self.writeBall(8,2,Color(125,125,125))
            self.strip.show()

            # Write the actual numerals
            if hours < 10:
                # self.writeChar(1,1,0)
                self.writeChar(4,1,int(hoursStr[0]),bgcolor)
            else:
                self.writeChar(0,1,int(hoursStr[0]),bgcolor)
                self.writeChar(4,1,int(hoursStr[1]),bgcolor)

            if mins < 10:
                self.writeChar(10,1,0,bgcolor)
                self.writeChar(14,1,int(minsStr[0]),bgcolor)
            else:
                self.writeChar(10,1,int(minsStr[0]),bgcolor)
                self.writeChar(14,1,int(minsStr[1]),bgcolor)

            self.minsPrev = mins
