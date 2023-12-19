import time
import threading
import datetime

def sound(state):
    timestampSeconds = time.time()
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    timestampMillis = time.time()
    threadName = threading.current_thread().name
    if state:
        print(f'\033[93m[{threadName}, {timestampMillis}]  Buzzer STARTS making sound\033[0m')  # pylint: disable=no-member
    else:
        print(f'\033[93m[{threadName}, {timestampMillis}]  Buzzer STOPS making sound\033[0m')

def callback():
    sound(False)

def beep(duration):
    sound(True)
    timer = threading.Timer(duration, callback) #calls the callback after 'duration' time in seconds
    timer.start()

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