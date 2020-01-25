from neopixel import *
import LEDUtil
import time

#Establish variables that will be used
hoursPrev = 99  #used for clock updating
minsPrev = 99   #used for clock updating
secsPrev = 99   #used for clock updating
colonLit = False

# Initialize the LED class, start up the LED strip
LED = LEDUtil.LEDStrip()

while(True):
    # Write the BG. Will not overwrite text per the function
    LED.rainbow()

    # Get the current local time and parse it out to usable variables
    t = time.localtime()
    hours = t.tm_hour
    mins = t.tm_min
    secs = t.tm_sec

    # Convert 24h time to 12h time
    if hours > 12:
        hours -= 12

    # Check to see if the second has changed. If it has, changed the colonLit activation
    if secs != secsPrev:
        colonLit ^= True  #flip the colonLit bool

        if colonLit:
            LED.writeBall(8,4,Color(125,125,125),True)
            LED.writeBall(8,2,Color(125,125,125),True)
            LED.strip.show()
        else: 
            LED.writeBall(8,4,Color(125,125,125),False)     #Keep the color white, but we toggle the text to False so that it will be overwritten by the rainbow
            LED.writeBall(8,2,Color(125,125,125),False)     #Keep the color white, but we toggle the text to False so that it will be overwritten by the rainbow
            LED.strip.show()

        secsPrev = secs

    # Check to see if the minute has changed. If it has, write the new minute
    if mins != minsPrev:    
        # Convert the mins to a string so that we can parse the individual numbers for display
        minsStr = str(mins)

        # Write the actual numerals
        if mins < 10:
            LED.writeChar(10,1,0)
            LED.writeChar(14,1,int(minsStr[0]))
        else:
            LED.writeChar(10,1,int(minsStr[0]))
            LED.writeChar(14,1,int(minsStr[1]))
        minsPrev = mins

    # Check to see if the hour has changed. If it has, write the new hour
    if hours != hoursPrev:
        # Convert the mins to a string so that we can parse the individual numbers for display
        hoursStr = str(hours)

        if hours < 10:
            LED.writeChar(4,1,int(hoursStr[0]))
        else:
            LED.writeChar(0,1,int(hoursStr[0]))
            LED.writeChar(4,1,int(hoursStr[1]))
        hoursPrev = hours
