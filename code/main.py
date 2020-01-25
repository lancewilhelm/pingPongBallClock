from neopixel import *
import LEDUtil

#Establish variables that will be used
hoursPrev = 99  #used for clock updating
minsPrev = 99   #used for clock updating
secsPrev = 99   #used for clock updating

# Initialize the LED class, start up the LED strip
LED = LEDUtil.LEDStrip()

# Write the Initial BG
bgcolor = Color(255,0,0)
LED.colorFill(bgcolor)

while(True):
    # Get the current local time and parse it out to usable variables
    t = time.localtime()
    hours = t.tm_hour
    mins = t.tm_min
    secs = t.tm_sec

    # Convert 24h time to 12h time
    if hours > 12:
        hours -= 12
    
    # Convert the hours and mins to strings so that we can parse the individual numbers for display
    hoursStr = str(hours)

    # Check to see if the minute has changed. If they have, write the new minutes
    if mins != minsPrev:    
        # Convert the mins to a string so that we can parse the individual numbers for display
        minsStr = str(mins)

        # Write the colon in the middle
        LED.writeBall(8,4,Color(125,125,125))
        LED.writeBall(8,2,Color(125,125,125))
        LED.strip.show()

        # Write the actual numerals
        if mins < 10:
            LED.writeChar(10,1,0,bgcolor)
            LED.writeChar(14,1,int(minsStr[0]),bgcolor)
        else:
            LED.writeChar(10,1,int(minsStr[0]),bgcolor)
            LED.writeChar(14,1,int(minsStr[1]),bgcolor)
        minsPrev = mins

    # Check to see if the hour has changed. If they have, write the new minutes
    if hours != hoursPrev:
        if hours < 10:
            LED.writeChar(4,1,int(hoursStr[0]),bgcolor)
        else:
            LED.writeChar(0,1,int(hoursStr[0]),bgcolor)
            LED.writeChar(4,1,int(hoursStr[1]),bgcolor)
        hoursPrev = hours
