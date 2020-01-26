from flask import Flask, request, render_template
import threading
from neopixel import *
import LEDUtil
import time

print "initializing..."

#Establish variables that will be used
hoursPrev = 99  #used for clock updating
minsPrev = 99   #used for clock updating
secsPrev = 99   #used for clock updating
colonLit = False

# Initialize the LED class, start up the LED strip
LED = LEDUtil.LEDStrip()

#Setup the flask object and get it going
app = Flask(__name__)

@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')

@app.route("/api/color", methods=['POST'])
def setBGColor():
    # Read the values from the POST
    program = request.form['color']
    red = int(request.form['red'])
    green = int(request.form['green'])
    blue = int(request.form['blue'])
    
    # Change the bg color accordingly
    if program == "solid":
        LED.bgColor = ["solid", Color(red,green,blue)]
    else:
        LED.bgColor = ["animation", program]
    return ""

def clock():
    global hoursPrev
    global minsPrev
    global secsPrev
    global colonLit

    while(True):
        # Write the BG. Will not overwrite text per the function
        if LED.bgColor[0] == "solid":
            LED.colorFill(LED.bgColor[1])
        elif LED.bgColor[0] == "animation":
            if LED.bgColor[1] == "rainbow":
                LED.rainbow()
            elif LED.bgColor[1] == "rainbowCycle":
                LED.rainbowCycle()

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
                LED.writeBall(8,4,LED.textColor,True)
                LED.writeBall(9,2,LED.textColor,True)
                LED.strip.show()
            else: 
                LED.writeBall(8,4,LED.textColor,False)     #Keep the color white, but we toggle the text to False so that it will be overwritten by the rainbow
                LED.writeBall(9,2,LED.textColor,False)     #Keep the color white, but we toggle the text to False so that it will be overwritten by the rainbow
                LED.strip.show()

            secsPrev = secs

        # Check to see if the minute has changed. If it has, write the new minute
        if mins != minsPrev:    
            # Convert the mins to a string so that we can parse the individual numbers for display
            minsStr = str(mins)

            # Write the actual numerals
            if mins < 10:
                LED.writeChar(10,1,0,LED.textColor)
                LED.writeChar(14,1,int(minsStr[0]),LED.textColor)
            else:
                LED.writeChar(10,1,int(minsStr[0]),LED.textColor)
                LED.writeChar(14,1,int(minsStr[1]),LED.textColor)
            minsPrev = mins

        # Check to see if the hour has changed. If it has, write the new hour
        if hours != hoursPrev:
            # If it is midnight, change the clock to 12
            if hours == 0:
                hours = 12
            
            # Convert the mins to a string so that we can parse the individual numbers for display
            hoursStr = str(hours)

            if hoursPrev >= 10 and hours < 10:
                LED.writeChar(0,1,'blank',LED.textColor)
                LED.writeChar(4,1,int(hoursStr[0]),LED.textColor)
            elif hours < 10:
                LED.writeChar(4,1,int(hoursStr[0]),LED.textColor)
            else:
                LED.writeChar(0,1,int(hoursStr[0]),LED.textColor)
                LED.writeChar(4,1,int(hoursStr[1]),LED.textColor)
            hoursPrev = hours

if __name__ == '__main__':
    x = threading.Thread(target=clock, args=())
    x.daemon = True
    x.start()
    
    app.run(host='0.0.0.0', port=80)
