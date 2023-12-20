#!/usr/bin/env python3

# pylint: disable=no-member

import time
from config import * # pylint: disable=unused-wildcard-import
from mfrc522 import MFRC522
import sqlite3 as sql
from threading import Thread
import datetime
import os
import logging
import threading
from buzzer import beepSequence
from leds import ledsAccept, ledsDeny
from terminal_colors import TerminalColors

stopByGreenButton = False
stopByRedButton = False
greenButtonPressedTimestamp = 0
redButtonPressedTimestamp = 0
ACCEPT_ACCESS_COOLDOWN = 5000
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
    def wrapped(channel):
        t = Thread(target=func(channel))
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
                    logging.info(f'{TerminalColors.YELLOW}Card number {num} has been added to the database.{TerminalColors.RESET}')
                    beepSequence(0.5, 0.0, 1)
                    time.sleep(0.5)

    cursor.executemany('INSERT INTO Access (CardID, Timestamp) VALUES (?,?)', cards)
    connection.commit()
    connection.close()
    GPIO.remove_event_detect(buttonGreen)
    stopByGreenButton = False
    time.sleep(0.5)

def acceptAccess(num, timestamp):
    timestampSeconds = timestamp / 1000
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name
    print(f'{TerminalColors.GREEN}[{threadName}]  Accepted card with number: {num}, at time: {timeString}{TerminalColors.RESET}')
    ledsAccept(1)
    beepSequence(1,0,1)
    

def denyAccess(num, timestamp):
    timestampSeconds = timestamp / 1000
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name
    print(f'{TerminalColors.RED}[{threadName}]  Denied card with number: {num}, at time: {timeString}{TerminalColors.RESET}')
    ledsDeny(1)
    beepSequence(0.25, 0.25, 3)


def rfidRead():
    global stopByGreenButton, stopByRedButton
    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=runInThread(greenButtonPressedCallback), bouncetime=100)
    GPIO.add_event_detect(buttonRed, GPIO.FALLING, callback=runInThread(redButtonPressedCallback), bouncetime=100)
    MIFAREReader = MFRC522()

    connection = sql.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    unauthorizedCards = dict()

    while(not stopByRedButton or not stopByGreenButton):
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

                if (entry):
                    if (timestamp >= entry[1] + ACCEPT_ACCESS_COOLDOWN):
                        cursor.execute('UPDATE Access SET Timestamp = ? WHERE CardID = ?', (timestamp, num))
                        connection.commit()
                        acceptAccess(num, timestamp)
                else:
                    if (num in unauthorizedCards.keys()):
                        if (timestamp >= unauthorizedCards[num] + ACCEPT_ACCESS_COOLDOWN):
                            unauthorizedCards[num] = timestamp
                            denyAccess(num, timestamp)
                    else:
                        unauthorizedCards[num] = timestamp
                        denyAccess(num, timestamp)
                        
                # else:
                #     denyAccess(num, timestamp)
                # time.sleep(0.5)
    connection.close()

def delete_db_file():
    try:
        os.remove(DB_FILE_NAME)
        logging.info(f"{TerminalColors.YELLOW}{DB_FILE_NAME} deleted successfully.{TerminalColors.RESET}")
    except FileNotFoundError:
        logging.info(f"{TerminalColors.RED}{DB_FILE_NAME} does not exist.{TerminalColors.RESET}")

def program():
    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.CRITICAL)

    delete_db_file()
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