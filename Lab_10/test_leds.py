#!/usr/bin/env python3

import time
import threading
import datetime
import logging
from terminal_colors import TerminalColors

def pixelsAccept():
    timestampSeconds = time.time()
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name
    logging.info(f'{TerminalColors.YELLOW}[{threadName}, {timeString}]  PIXELS BECAME GREEN{TerminalColors.RESET}')

def pixelsDeny():
    timestampSeconds = time.time()
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name
    logging.info(f'{TerminalColors.YELLOW}[{threadName}, {timeString}]  PIXELS BECAME RED{TerminalColors.RESET}')

def cleanPixels():
    timestampSeconds = time.time()
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name
    logging.info(f'{TerminalColors.YELLOW}[{threadName}, {timeString}]  pixels are clear{TerminalColors.RESET}')

def ledsAccept(duration):
    pixelsAccept()
    timer = threading.Timer(duration, cleanPixels) #calls the callback after 'duration' time in seconds
    timer.start()

def ledsDeny(duration):
    pixelsDeny()
    timer = threading.Timer(duration, cleanPixels) #calls the callback after 'duration' time in seconds
    timer.start()