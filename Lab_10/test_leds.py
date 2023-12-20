#!/usr/bin/env python3

import time
import threading
import datetime
import logging
from terminal_colors import TerminalColors

def pixelsAccept():
    timestampMillis = time.time()
    threadName = threading.current_thread().name
    logging.info(f'{TerminalColors.YELLOW}[{threadName}, {timestampMillis}]  PIXELS ARE GREEN{TerminalColors.RESET}')

def pixelsDeny():
    timestampMillis = time.time()
    threadName = threading.current_thread().name
    logging.info(f'{TerminalColors.YELLOW}[{threadName}, {timestampMillis}]  PIXELS ARE RED{TerminalColors.RESET}')

def cleanPixels():
    timestampMillis = time.time()
    threadName = threading.current_thread().name
    logging.info(f'{TerminalColors.YELLOW}[{threadName}, {timestampMillis}]  pixels are clear{TerminalColors.RESET}')

def ledsAccept(duration):
    pixelsAccept()
    timer = threading.Timer(duration, cleanPixels) #calls the callback after 'duration' time in seconds
    timer.start()

def ledsDeny(duration):
    pixelsDeny()
    timer = threading.Timer(duration, cleanPixels) #calls the callback after 'duration' time in seconds
    timer.start()

# def ledsAcceptHelper(ledsOnDuration, pauseDuration, count):
#     for _ in range(count):
#         pixelsAccept()
#         time.sleep(ledsOnDuration)  # Pause between beeps
#         cleanPixels()
#         time.sleep(pauseDuration)

# def ledsAccept(ledsOnDuration, pauseDuration, count):
#     thread = threading.Thread(target=ledsAcceptHelper, args=(ledsOnDuration, pauseDuration, count))
#     thread.start()
#     thread.join()

# def ledsDenyHelper(ledsOnDuration, pauseDuration, count):
#     for _ in range(count):
#         pixelsDeny()
#         time.sleep(ledsOnDuration)  # Pause between beeps
#         cleanPixels()
#         time.sleep(pauseDuration)

# def ledsDeny(ledsOnDuration, pauseDuration, count):
#     thread = threading.Thread(target=ledsDenyHelper, args=(ledsOnDuration, pauseDuration, count))
#     thread.start()
#     thread.join()