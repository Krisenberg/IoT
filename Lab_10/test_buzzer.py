import time
import threading
import datetime
import logging
from terminal_colors import TerminalColors

def sound(state):
    timestampSeconds = time.time()
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    timestampMillis = time.time()
    threadName = threading.current_thread().name
    if state:
        logging.info(f'{TerminalColors.YELLOW}[{threadName}, {timestampMillis}]  Buzzer STARTS making sound{TerminalColors.RESET}')  # pylint: disable=no-member
    else:
        logging.info(f'{TerminalColors.YELLOW}[{threadName}, {timestampMillis}]  Buzzer STOPS making sound{TerminalColors.RESET}')

def callback():
    sound(False)

def beep(duration):
    sound(True)
    timer = threading.Timer(duration, callback) #calls the callback after 'duration' time in seconds
    timer.start()

def beepSequenceHelper(singleBeepDuration, pauseDuration, count):
    for _ in range(count):
        sound(True)
        time.sleep(singleBeepDuration)
        callback()
        time.sleep(pauseDuration)

def beepSequence(singleBeepDuration, pauseDuration, count):
    thread = threading.Thread(target=beepSequenceHelper, args=(singleBeepDuration, pauseDuration, count))
    thread.start()
    thread.join()