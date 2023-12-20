#!/usr/bin/env python3

# pylint: disable=no-member

import time
from config import * # pylint: disable=unused-wildcard-import
from mfrc522 import MFRC522
import sqlite3 as sql
from threading import Thread
import datetime
import os
from buzzer import beep
from leds import ledsAccept, ledsDeny

stopByGreenButton = False
stopByRedButton = False
greenButtonPressedTimestamp = 0
redButtonPressedTimestamp = 0
ACCEPT_ACCESS_COOLDOWN = 10000 #time in millis
BUTTON_PRESSED_COOLDOWN = 1500
DB_FILE_NAME = 'rfid_access_list.db'

def redButtonPressedCallback(channel):
    global stopByRedButton, redButtonPressedTimestamp
    stopByRedButton = True
    redButtonPressedTimestamp = int(time.time() * 1000)

def greenButtonPressedCallback(channel):
    global stopByGreenButton, greenButtonPressedTimestamp
    stopByGreenButton = True
    greenButtonPressedTimestamp = int(time.time() * 1000)

def runInThread(func):
    def wrapped():
        t = Thread(target=func)
        t.start()
    return wrapped

def prepareAccessList():
    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=greenButtonPressedCallback, bouncetime=200)
    connection = sql.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Access
              (CardID INTEGER PRIMARY KEY,
              Timestamp INTEGER)''')
    cards = []

    global stopByGreenButton
    MIFAREReader = MFRC522()
    cardsNumSet = set()

    while (not stopByGreenButton):
        (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
        if status == MIFAREReader.MI_OK:
            (status, uid) = MIFAREReader.MFRC522_Anticoll()
            if status == MIFAREReader.MI_OK:
                num = 0
                for i in range(0, len(uid)):
                    num += uid[i] << (i*8)
                if num not in cardsNumSet:
                    cardsNumSet.add(num)
                    timestamp = int(time.time() * 1000)
                    cards.append((num, timestamp))
                    beep(0.5)
                    time.sleep(0.5)

    cursor.executemany('INSERT INTO Access (CardID, Timestamp) VALUES (?,?,?)', cards)
    connection.commit()
    connection.close()
    GPIO.remove_event_detect(buttonGreen)
    stopByGreenButton = False

def acceptAccess(num, timestamp):
    timestampSeconds = timestamp / 1000
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    print(f'Accepted card with number: {num}, at time: {timeString}')
    ledsAccept(1)
    for _ in range(3):
        beep(0.25)  # Short beep (0.1 seconds)
        time.sleep(0.25)  # Pause between beeps
    

def denyAccess(num, timestamp):
    timestampSeconds = timestamp / 1000
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    print(f'Denied card with number: {num}, at time: {timeString}')
    ledsDeny(1)


def rfidRead():
    global stopByGreenButton, stopByRedButton
    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=runInThread(greenButtonPressedCallback), bouncetime=150)
    GPIO.add_event_detect(buttonRed, GPIO.FALLING, callback=runInThread(redButtonPressedCallback), bouncetime=150)
    MIFAREReader = MFRC522()

    connection = sql.connect(DB_FILE_NAME)
    cursor = connection.cursor

    while(not stopByGreenButton and not stopByRedButton):
        if (int(time.time() * 1000) - BUTTON_PRESSED_COOLDOWN >= redButtonPressedTimestamp):
            stopByRedButton = False
        if (int(time.time() * 1000) - BUTTON_PRESSED_COOLDOWN >= greenButtonPressedTimestamp):
            stopByGreenButton = False
        (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
        if status == MIFAREReader.MI_OK:
            (status, uid) = MIFAREReader.MFRC522_Anticoll()
            if status == MIFAREReader.MI_OK:
                num = 0
                for i in range(0, len(uid)):
                    num += uid[i] << (i*8)
                timestamp = int(time.time() * 1000)
                cursor.execute('SELECT * FROM Access WHERE CardID = ?', (num,))
                entry = cursor.fetchone()

                if (entry and timestamp >= entry[1] + ACCEPT_ACCESS_COOLDOWN):
                    cursor.execute('UPDATE Access SET Timestamp = ? WHERE CardID = ?', (timestamp, num))
                    connection.commit()
                    acceptAccess(num, timestamp)
                else:
                    denyAccess(num, timestamp)
    connection.close()

def delete_db_file():
    try:
        os.remove(DB_FILE_NAME)
        print(f"{DB_FILE_NAME} deleted successfully.")
    except FileNotFoundError:
        print(f"{DB_FILE_NAME} does not exist.")

def program():
    print('\nPlease configure the Database to store authorized RFIDs.')
    print('Place the cards you want to be marked as authorized' +
           'close to the reader (on the right side of the set).')
    
    prepareAccessList()

    print('The Access List has been configured successfully.')
    print('-------------------------------------------------\n\n\n')
    print('Place the card close to the reader (on the right side of the set).')

    rfidRead()

    delete_db_file()
    print('RFID reader is no more active. Program has terminated.')

if __name__ == "__main__":
    program()
    GPIO.cleanup() # pylint: disable=no-member