#!/usr/bin/env python3

import time
import threading
import datetime

def pixelsAccept():
    timestampSeconds = time.time()
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name
    print(f'[{threadName}, {timeString}]  PIXELS BECAME GREEN')

def pixelsDeny():
    timestampSeconds = time.time()
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name
    print(f'[{threadName}, {timeString}]  PIXELS BECAME RED')

def cleanPixels():
    timestampSeconds = time.time()
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name
    print(f'[{threadName}, {timeString}]  pixels are clear')

def ledsAccept(duration):
    pixelsAccept()
    timer = threading.Timer(duration, cleanPixels) #calls the callback after 'duration' time in seconds
    timer.start()

def ledsDeny(duration):
    pixelsDeny()
    timer = threading.Timer(duration, cleanPixels) #calls the callback after 'duration' time in seconds
    timer.start()