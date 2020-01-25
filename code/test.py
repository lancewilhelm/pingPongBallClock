import LEDUtil

LED = LEDUtil.LEDStrip()

LED.colorFill(Color(255,0,0))

while(True):
    LED.clock()

