#!/usr/bin/env python3

from config import *  # pylint: disable=unused-wildcard-import
import RPi.GPIO as GPIO
import time
import threading

def sound(state):
    GPIO.output(buzzerPin, not state)  # pylint: disable=no-member

def callback():
    sound(False)

def beep(duration):
    sound(True)

    timer = threading.Timer(duration, callback) #calls the callback after 'duration' time in seconds
    timer.start()