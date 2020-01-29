
# Ping Pong Ball Clock

Raspberry Pi code for the Ping Pong Ball Clock Project

Author: Lance Wilhelm (PlanetaryMotion)

---

## Video

I will be creating a YouTube video documenting the build. It will likely only brush over the firmware. When finished I will post that link here.

## Inspiration

A reddit post originally tripped me off to the project. This was linked a [thingiverse](https://www.thingiverse.com/thing:4091854) project which detailed some 3D printed parts for a ping pong ball clock. Upon further investigation I found an [instructable](https://www.instructables.com/id/Ping-Pong-Ball-LED-Clock/) project that laid out designs that did not involve 3D printing and optimized the LED placement. I used this instructable project as the basis for the hardware design. However, I knew from the start that I was going to control the clock using a raspberry pi (zero) and that I would build upon a previous project that controlled LEDs using a local web app.

## Software Design Concept

This firmware is centered in python because of how easy it is to use and a couple easy to use and essential libraries:

- Neopixel libraries
- Flask (web server)

The layout of the LED strips called for a font libraries and character writing functions to be written from scratch. This project only pulled from a previous project the code to be able to light up an LED. 

The the following images gave me a concept of how I was going to program the LED display with each vertical red line in the first image being an LED strip:
![layout concept](imgs/layout&#32;visualizer-01.jpg)
![layout concept](imgs/layout&#32;visualizer-02.jpg)
![layout concept](imgs/layout&#32;visualizer-03.jpg)
![layout concept](imgs/layout&#32;visualizer-04.jpg)

## Implementation

Font libraries and things related to the layout can be found in [Utils](code/Utils.py). 

The functions that drive almost every single part of the lighting and logic and display can be found in [LEDUtils](code/LEDUtils.py).

The [flaskUtils](code/flaskUtils.py) file contains all of the api views that respond to POST and GET requests from the web app.

Other things that serve the web app are found in [templates](code/templates/), [static](code/static/)

---

# Usage

**Instalation instructions coming soon**

Please fork/clone this repo and make it your own. I would love to see some pull requests. This is a just a side hobby of mine so it may take me some time to get around to reviewing and merging. Also, FYI, not a developer IRL. This is just what I do for fun. Learning as I go. Feel free to contact me! 