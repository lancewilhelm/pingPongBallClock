# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
import time

from neopixel import *

import argparse
import signal
import sys
import math

import Utils

def signal_handler(signal, frame):
    colorWipe(self.strip, Color(0,0,0))
    sys.exit(0)

# LED strip configuration:
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
LED_COUNT      = 256
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
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

    def updateFrame(self, animationEnd):
        self.animationFrame += 1
        self.animationEnd = animationEnd
        if(self.animationFrame>=self.animationEnd):
            self.animationFrame = 0
        return self.animationFrame

    def clearPixels(self):
        #print ('Clearing')
        for i in range(self.numBalls):
            self.strip.setPixelColor(i*2, Color(0,0,0))
        self.strip.show()

    def customColor(self,color):
        red = color[0]
        green = color[1]
        blue = color[2]
        stripColor = Color(red,green,blue)
        for i in range(self.numBalls):
            self.strip.setPixelColor(i*2,stripColor)
        self.strip.show()

    def chasing(self):
        #clearPixels(strip)
        #Purple
        x = self.updateFrame(self.numBalls)
        #print x
        endPixel = x + 50
        #purple
        for i in range(x,endPixel):
            self.strip.setPixelColor(i*2 % self.numBalls, Color(255,0,255))
            #Serial.println("setting pixel colors for 50");

        #green
        for i in (x+(self.numBalls/2),endPixel+(self.numBalls/2)):
            self.strip.setPixelColor(i*2 % self.numBalls, Color(100,255,0))
            #Serial.println("setting pixel colors for 50");

        #clear purple
        for i in range(1,5):
            self.strip.setPixelColor(x - i, Color(0,0,0))

        #clear green
        for i in range(1,5):
            self.strip.setPixelColor((x+(self.numBalls/2) - i) % self.numBalls, Color(0,0,0))

        self.strip.show()
        #print ('sleep')
        #time.sleep(0.005)
        return self.numBalls

    def colorWipe(self,color, wait_ms=50):
        """Wipe color across display a pixel at a time."""
        i = self.updateFrame(self.numBalls)
        self.strip.setPixelColor(i*2, color)
        self.strip.show()
        time.sleep(wait_ms/1000.0)

    def theaterChase(self,color, wait_ms=50, iterations=1):
        """Movie theater light style chaser animation."""
        for j in range(iterations):
            for q in range(3):
                for i in range(0, self.numBalls, 3):
                    self.strip.setPixelColor((i+q)*2, color)
                self.strip.show()
                time.sleep(wait_ms/1000.0)
                for i in range(0, self.numBalls, 3):
                    self.strip.setPixelColor((i+q)*2, 0)

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

    def breathing(self):
        x = self.updateFrame(200)

        y = int(127.5*math.cos((math.pi/50)*(x-50))+127.5)

        if(x < 100):
            for j in range(self.numBalls):
                self.strip.setPixelColor(j, Color(y,0,y))
            self.strip.show()
        else:
            for j in range(self.numBalls):
                self.strip.setPixelColor(j, Color(y/2,y,0))
            self.strip.show()

    def flashGrey(self):
        j = self.updateFrame(100)

        for i in range(self.numBalls):
            if(j == 0):
                self.strip.setPixelColor(i*2, Color(50,50,50))
            if(j == 50):
                self.strip.setPixelColor(i*2, Color(0,0,0))
        self.strip.show()

    def rowStep(self):
        j = self.updateFrame(7)

        if j == 0:
            self.clearPixels()

        for i in row[j]:
            self.strip.setPixelColor(i*2, Color(255,0,0))

        time.sleep(1)