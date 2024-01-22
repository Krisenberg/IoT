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
from PIL import Image, ImageDraw, ImageFont
import lib.oled.SSD1331 as SSD1331

clickedGreenButton = False
clickedRedButton = False
greenButtonPressedTimestamp = 0
redButtonPressedTimestamp = 0

broker = SECRET_ROOM_BROKER
client_secret_add = mqtt.Client(client_id='client_secret_add')
client_secret_check_request = mqtt.Client(client_id='client_secret_check_request')
client_secret_check_response = mqtt.Client(client_id='client_secret_check_response')

oledCursorPosition = 0
disp = SSD1331.SSD1331()

encoderNumber = 0
encoderLeftPreviousState = GPIO.input(encoderLeft)
encoderRightPreviousState = GPIO.input(encoderRight)

def runInThread(func):
    def wrapped(channel):
        t = Thread(target=func(channel))
        t.start()
    return wrapped

def redButtonPressedCallback(channel):
    global clickedRedButton, redButtonPressedTimestamp
    clickedRedButton = True
    redButtonPressedTimestamp = int(time.time() * 1000)

def greenButtonPressedCallback(channel):
    global clickedGreenButton, greenButtonPressedTimestamp
    clickedGreenButton = True
    greenButtonPressedTimestamp = int(time.time() * 1000)

def encoderCallback(channel):
    global encoderNumber, encoderLeftPreviousState, encoderRightPreviousState
    encoderLeftCurrentState = GPIO.input(encoderLeft)
    encoderRightCurrentState = GPIO.input(encoderRight)
    
    if encoderLeftPreviousState == 1 and encoderLeftCurrentState == 0:
        encoderNumber += 1
    elif encoderRightPreviousState == 1 and encoderRightCurrentState == 0:
        encoderNumber -= 1

    encoderNumber = max(0, min(9, encoderNumber))  # Checking if in range (0-9)
    #ostatnio to górne nie działało, więc dla bezpieczeństwa:
    if(encoderNumber < 0):
        encoderNumber = 0
    if(encoderNumber > 9):
        encoderNumber = 9

    encoderLeftPreviousState = encoderLeftCurrentState
    encoderRightPreviousState = encoderRightCurrentState

    displayOnOLED()

def writePin():
    GPIO.add_event_detect(encoderLeft, GPIO.BOTH, callback=runInThread(encoderCallback), bouncetime=100)
    GPIO.add_event_detect(encoderRight, GPIO.BOTH, callback=runInThread(encoderCallback), bouncetime=100)
    # nie wiem czy potrzebne:
    # GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=runInThread(greenButtonPressedCallback), bouncetime=100)

    global encoderNumber, clickedGreenButton, oledCursorPosition
    oledCursorPosition = 0
    pin = ""
    greenButtonPressedCount = 0
    setOled()

    while(greenButtonPressedCount != 2):
        while(not clickedGreenButton):
            if (int(time.time() * 1000) - BUTTON_PRESSED_COOLDOWN >= greenButtonPressedTimestamp):
                clickedGreenButton = False
        clickedGreenButton = False
        pin += str(encoderNumber)
        oledCursorPosition += 1
        greenButtonPressedCount += 1

    clearOled()
    return pin


def setOled():
    global disp
    disp.Init()
    disp.clear()
    image = Image.new("RGB", (disp.width, disp.height), "WHITE")
    draw = ImageDraw.Draw(image)
    fontLarge = ImageFont.truetype('./lib/oled/Font.ttf', 20)

    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

    draw.text((8, 0), '0', font=fontLarge, fill="WHITE")
    draw.text((8, 30),'0', font=fontLarge, fill="WHITE")

def clearOled():
    global disp
    disp.clear()
    disp.reset()

# printing digits of PIN on oled, while choosing. Cursor postion is set in addPin(), after clicking green button
def displayOnOLED():
    global encoderNumber, oledCursorPosition, disp

    image = Image.new("RGB", (disp.width, disp.height), "WHITE")
    draw = ImageDraw.Draw(image)
    fontLarge = ImageFont.truetype('./lib/oled/Font.ttf', 20)

    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

    if oledCursorPosition == 0:
        draw.text((8, 0), f'{encoderNumber:02d}', font=fontLarge, fill="WHITE")
    else:
        draw.text((8, 30), f'{encoderNumber:02d}', font=fontLarge, fill="WHITE")

    # disp.clear()
    # disp.reset()
        
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
                    #dodawanie pinu
                    pin = writePin()
                    client_secret_add.publish(SECRET_TOPIC_ADD, f"{num}&{pin}&{timestamp}")
                    beepSequence(0.5, 0.0, 1)
                    time.sleep(0.5)
                    flag - False
    time.sleep(0.5)

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
    global clickedGreenButton, clickedRedButton
    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=runInThread(greenButtonPressedCallback), bouncetime=100)
    GPIO.add_event_detect(buttonRed, GPIO.FALLING, callback=runInThread(redButtonPressedCallback), bouncetime=100)

    MIFAREReader = MFRC522()

    connection = sql.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    unauthorizedCards = dict()

    while(not clickedRedButton or not clickedGreenButton):
        if (int(time.time() * 1000) - BUTTON_PRESSED_COOLDOWN >= redButtonPressedTimestamp):
            clickedRedButton = False
        if (int(time.time() * 1000) - BUTTON_PRESSED_COOLDOWN >= greenButtonPressedTimestamp):
            clickedGreenButton = False
        if clickedRedButton:
            addNewTrustedCard()
            clickedRedButton = False
        #TO-DO - analogicznie do office_main_client.py, sprawdzanie karty ale z pinem


def connect_broker_office_entrance_add_publisher():
    client_secret_add.connect(broker)

def disconnect_broker_office_entrance_add_publisher():
    client_secret_add.disconnect()

def connect_broker_office_entrance_check_request_publisher():
    client_secret_check_request.connect(broker)

def disconnect_broker_office_entrance_check_request_publisher():
    client_secret_check_request.loop_stop()
    client_secret_check_request.disconnect()

def connect_broker_office_entrance_check_response_subscriber():
    client_secret_check_response.on_message = check_card_response
    client_secret_check_response.loop_start()
    client_secret_check_response.subscribe(SECRET_TOPIC_CHECK_REQUEST)
    client_secret_check_response.connect(broker)

def disconnect_broker_office_entrance_check_response_subscriber():
    client_secret_check_response.loop_stop()
    client_secret_check_response.disconnect()


def run_secret_client():
    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.INFO)
    
    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=runInThread(greenButtonPressedCallback), bouncetime=100)

    connect_broker_office_entrance_add_publisher()
    connect_broker_office_entrance_check_request_publisher()
    connect_broker_office_entrance_check_response_subscriber()

    rfidRead()

    disconnect_broker_office_entrance_add_publisher()
    disconnect_broker_office_entrance_check_request_publisher()
    disconnect_broker_office_entrance_check_response_subscriber()

if __name__ == "__main__":
    run_secret_client()
    GPIO.cleanup()