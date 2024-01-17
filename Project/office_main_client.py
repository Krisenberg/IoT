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
import paho.mqtt.client as mqtt
from config_constants import *

stopByGreenButton = False
stopByRedButton = False
greenButtonPressedTimestamp = 0
redButtonPressedTimestamp = 0

broker = OFFICE_ENTRANCE_BROKER
client_main_add = mqtt.Client(client_id='client_main_add')
client_main_check_request = mqtt.Client(client_id='client_main_check_request')
client_main_check_response = mqtt.Client(client_id='client_main_check_response')


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

def addNewTrustedCard():
    MIFAREReader = MFRC522()
    cardsNumSet = set()

    flag = True

    while (flag):
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
                    client_main_add.publish(MAIN_TOPIC_ADD, f"{num}&{timestamp}")
                    beepSequence(0.5, 0.0, 1)
                    time.sleep(0.5)
                    flag - False

    time.sleep(0.5)

# def acceptAccess(num, timestamp):
#     timestampSeconds = timestamp / 1000
#     timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
#     threadName = threading.current_thread().name
#     print(f'{TerminalColors.GREEN}[{threadName}]  Accepted card with number: {num}, at time: {timeString}{TerminalColors.RESET}')
#     call_card(f'{num}.{timeString}.Accepted')
#     ledsAccept(1)
#     beepSequence(1,0,1)
    

# def denyAccess(num, timestamp):
#     timestampSeconds = timestamp / 1000
#     timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
#     threadName = threading.current_thread().name
#     print(f'{TerminalColors.RED}[{threadName}]  Denied card with number: {num}, at time: {timeString}{TerminalColors.RESET}')
#     call_card(f'{num}.{timeString}.Denied')
#     ledsDeny(1)
#     beepSequence(0.25, 0.25, 3)

def acceptAccess():
    ledsAccept(1)
    beepSequence(1,0,1)
    

def denyAccess():
    ledsDeny(1)
    beepSequence(0.25, 0.25, 3)

def check_card_response(client, userdata, message,):
    if (message == ACCEPT_MESSAGE):
        acceptAccess()
    else:
        denyAccess()


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
        if (stopByRedButton):
            addNewTrustedCard()
        (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
        if status == MIFAREReader.MI_OK:
            (status, uid) = MIFAREReader.MFRC522_Anticoll()
            if status == MIFAREReader.MI_OK:
                num = 0
                for i in range(0, len(uid)):
                    num += uid[i] << (i*8)
                timestamp = int(time.time() * 1000)
                client_main_check_request.publish(MAIN_TOPIC_CHECK_REQUEST, str(num) + '&' + str(timestamp),)


def connect_broker_office_entrance_add_publisher():
    client_main_add.connect(broker)

def disconnect_broker_office_entrance_add_publisher():
    client_main_add.disconnect()

def connect_broker_office_entrance_check_request_publisher():
    client_main_check_request.connect(broker)

def disconnect_broker_office_entrance_check_request_publisher():
    client_main_check_request.loop_stop()
    client_main_check_request.disconnect()

def connect_broker_office_entrance_check_response_subscriber():
    client_main_check_response.on_message = check_card_response
    client_main_check_response.loop_start()
    client_main_check_response.subscribe(MAIN_TOPIC_CHECK_REQUEST)
    client_main_check_response.connect(broker)

def disconnect_broker_office_entrance_check_response_subscriber():
    client_main_check_response.loop_stop()
    client_main_check_response.disconnect()


def run_main_client():
    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.INFO)

    connect_broker_office_entrance_add_publisher()
    connect_broker_office_entrance_check_request_publisher()
    connect_broker_office_entrance_check_response_subscriber()

    rfidRead()

    disconnect_broker_office_entrance_add_publisher()
    disconnect_broker_office_entrance_check_request_publisher()
    disconnect_broker_office_entrance_check_response_subscriber()

if __name__ == "__main__":
    run_main_client()
    GPIO.cleanup() # pylint: disable=no-member