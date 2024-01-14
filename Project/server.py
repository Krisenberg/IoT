#!/usr/bin/env python3

# pylint: disable=no-member

import paho.mqtt.client as mqtt
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

broker = "localhost"
client = mqtt.Client()

stopByGreenButton = False
stopByRedButton = False
greenButtonPressedTimestamp = 0
redButtonPressedTimestamp = 0
ACCEPT_ACCESS_COOLDOWN = 5000 #time in millis
BUTTON_PRESSED_COOLDOWN = 1500
DB_FILE_NAME = 'rfid_server_history.db'

def redButtonPressedCallback(channel):
    global stopByRedButton, redButtonPressedTimestamp
    stopByRedButton = True
    redButtonPressedTimestamp = int(time.time() * 1000)

def greenButtonPressedCallback(channel):
    global stopByGreenButton, greenButtonPressedTimestamp
    stopByGreenButton = True
    greenButtonPressedTimestamp = int(time.time() * 1000)

def prepareHistoryDB():
    try:
        os.remove(DB_FILE_NAME)
        logging.info(f"{TerminalColors.YELLOW}{DB_FILE_NAME} deleted successfully.{TerminalColors.RESET}")
    except FileNotFoundError:
        logging.info(f"{TerminalColors.RED}{DB_FILE_NAME} does not exist.{TerminalColors.RESET}")
    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=greenButtonPressedCallback, bouncetime=200)
    connection = sql.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS History
              (CardID text,
              Timestamp text PRIMARY KEY,
              Result text)''')
    connection.commit()
    connection.close()
    
def addEntryToHistory(client, userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split(".")
    if message_decoded[0] != "Client connected" and message_decoded[0] != "Client disconnected":
        num = message_decoded[0]
        timestamp = message_decoded[1]
        result = message_decoded[2]
        connection = sql.connect(DB_FILE_NAME)
        cursor = connection.cursor()
        cursor.execute('INSERT INTO History (CardID, Timestamp, Result) VALUES (?,?,?)', (num, timestamp, result))
        connection.commit()
        connection.close()
        if (result == "Accepted"):
            print(f'{TerminalColors.GREEN} Accepted card with number: {num}, at time: {timestamp}{TerminalColors.RESET}')
        else:
            print(f'{TerminalColors.RED} Denied card with number: {num}, at time: {timestamp}{TerminalColors.RESET}')
    else:
        # print(message_decoded[0] + " : " + message_decoded[1])
        print(message_decoded[0])

def connect_to_broker():
    client.connect(broker)
    client.on_message = addEntryToHistory
    client.loop_start()
    client.subscribe("history/add")

def disconnect_from_broker():
    client.loop_stop()
    client.disconnect()

def list_10_history_entries(count):
    print("-----------------------------------")
    print(f'Last {count} entries:')
    connection = sql.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM History LIMIT ?', (count,))
    entries = cursor.fetchall()
    for i, entry in enumerate(entries):
        print(f'{i+1}, {entry}')
    connection.close()


def mainLoop():
    flag = True

    while(flag):
        user_input = input("Input: ")
        if (user_input == "exit"):
            flag = False
        if (user_input == "l"):
            list_10_history_entries(10)

def run_server():
    prepareHistoryDB()
    connect_to_broker()
    mainLoop()
    disconnect_from_broker()

if __name__ == "__main__":
    run_server()


# def addCartToDB(num, timestamp):
#     connection = sql.connect(DB_FILE_NAME)
#     cursor = connection.cursor()
#     cursor.execute('SELECT * FROM Access WHERE CardID = ?', (num,))
#     entry = cursor.fetchone()
#     if (entry):
#         if (timestamp >= entry[1] + ACCEPT_ACCESS_COOLDOWN):
#             cursor.execute('UPDATE Access SET Timestamp = ? WHERE CardID = ?', (timestamp, num))
#             connection.commit()
#             acceptAccess(num, timestamp)