#!/bin/bash
#let's get neopixel set up
sudo apt-get update
sudo apt-get install build-essential python-dev git scons swig
git clone https://github.com/jgarff/rpi_ws281x.git
cd rpi_ws281x
scons
cd python
sudo python setup.py install

#let's install screen
sudo apt-get install screen

#let's get flask installed
sudo apt-get install python-pip

#let's give python permission to alter gpio pins without sudo
sudo chown pi /dev/mem
