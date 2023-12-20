#!/usr/bin/env python3

from config import *  # pylint: disable=unused-wildcard-import
import RPi.GPIO as GPIO
import time
import threading
import logging
from terminal_colors import TerminalColors

def sound(state):
    timestampMillis = time.time()
    threadName = threading.current_thread().name
    if state:
        logging.info(f'{TerminalColors.YELLOW}[{threadName}, {timestampMillis}]  Buzzer STARTS making sound{TerminalColors.RESET}')  # pylint: disable=no-member
    else:
        logging.info(f'{TerminalColors.YELLOW}[{threadName}, {timestampMillis}]  Buzzer STOPS making sound{TerminalColors.RESET}')
    GPIO.output(buzzerPin, not state)  # pylint: disable=no-member

def callback():
    sound(False)

# def beep(duration):
#     sound(True)

#     timer = threading.Timer(duration, callback) #calls the callback after 'duration' time in seconds
#     timer.start()
def beepSequenceHelper(singleBeepDuration, pauseDuration, count):
    for _ in range(count):
        # beep(singleBeepDuration)  # Short beep (0.1 seconds)
        sound(True)
        time.sleep(singleBeepDuration)  # Pause between beeps
        callback()
        time.sleep(pauseDuration)

def beepSequence(singleBeepDuration, pauseDuration, count):
    thread = threading.Thread(target=beepSequenceHelper, args=(singleBeepDuration, pauseDuration, count))
    thread.start()
    thread.join()