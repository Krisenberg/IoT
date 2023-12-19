#!/usr/bin/env python3

import time
import threading
import datetime

def pixelsAccept():
    timestampSeconds = time.time()
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name
    print(f'\033[93m[{threadName}, {timeString}]  PIXELS BECAME GREEN\033[0m')

def pixelsDeny():
    timestampSeconds = time.time()
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name
    print(f'\033[93m[{threadName}, {timeString}]  PIXELS BECAME RED\033[0m')

def cleanPixels():
    timestampSeconds = time.time()
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name
    print(f'\033[93m[{threadName}, {timeString}]  pixels are clear\033[0m')

def ledsAccept(duration):
    pixelsAccept()
    timer = threading.Timer(duration, cleanPixels) #calls the callback after 'duration' time in seconds
    timer.start()

def ledsDeny(duration):
    pixelsDeny()
    timer = threading.Timer(duration, cleanPixels) #calls the callback after 'duration' time in seconds
    timer.start()