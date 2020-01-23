#include <Adafruit_NeoPixel.h>

// constants won't change. They're used here to 
// set pin numbers:
const int ledPin = 5;     // the number of the neopixel strip
const int numLeds = 256;

//Adafruit_NeoPixel pixels = Adafruit_NeoPixel(8, ledPin);
Adafruit_NeoPixel strip = Adafruit_NeoPixel(numLeds, ledPin, NEO_GRB + NEO_KHZ800);

void setup() {
  strip.begin();
  strip.setBrightness(255); // 1/3 brightness
}

void loop() {
    for(int i=0; i<strip.numPixels(); i=i+2){
        strip.setPixelColor(i,strip.Color(0,255,0));
    }
    strip.show();
  delay(1000);
}

