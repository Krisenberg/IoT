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
from config_constants import *

broker = SERVER_BROKER
client_main_add = mqtt.Client(client_id='server_main_add')
client_main_check_request = mqtt.Client(client_id='server_main_check_request')
client_main_check_response = mqtt.Client(client_id='server_main_check_response')

client_secret_add = mqtt.Client(client_id='server_secret_add')
client_secret_check_request = mqtt.Client(client_id='server_secret_check_request')
client_secret_check_response = mqtt.Client(client_id='server_secret_check_response')

    
def check_card_request(client, userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if (len(message_decoded) > 1):
        num = message_decoded[0]
        timestamp = message_decoded[1]
        connection = sql.connect(DB_FILE_NAME)
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM Office_access WHERE Card_number = ?', (num,))
        entry = cursor.fetchone()
        if (entry):
            cursor.execute('SELECT * FROM Office_entry_history WHERE Card_number = ? ORDER BY Timestamp DESC LIMIT 1', (num,))
            entry = cursor.fetchone()
            if (not entry or timestamp >= entry[1] + ACCEPT_ACCESS_COOLDOWN):
                cursor.execute('INSERT INTO Office_entry_history (Card_number, Timestamp, Result) VALUES (?,?,?)', (num, timestamp, ACCEPT_MESSAGE))
                client_main_check_response.publish(MAIN_TOPIC_CHECK_RESPONSE, ACCEPT_MESSAGE)
                logging.info(f'{TerminalColors.GREEN} Accepted card with number: {num}, at time: {timestamp}.{TerminalColors.RESET}')
            else:
                cursor.execute('INSERT INTO Office_entry_history (Card_number, Timestamp, Result) VALUES (?,?,?)', (num, timestamp, DENY_MESSAGE))
                client_main_check_response.publish(MAIN_TOPIC_CHECK_RESPONSE, DENY_MESSAGE)
                logging.info(f'{TerminalColors.RED} Denied card with number: {num}, at time: {timestamp}.{TerminalColors.RESET}')
            connection.commit()
        else:
            client_main_check_response.publish(MAIN_TOPIC_CHECK_RESPONSE, DENY_MESSAGE)
            logging.info(f'{TerminalColors.RED} Denied card with number: {num}, at time: {timestamp}.{TerminalColors.RESET}')
        connection.close()


def check_card_with_pin_request(client, userdata, message,):
    #TO-DO
    return

def add_card_to_trusted_cards(client, userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if (len(message_decoded) > 1):
        num = message_decoded[0]
        timestamp = message_decoded[1]
        connection = sql.connect(DB_FILE_NAME)
        cursor = connection.cursor()
        cursor.execute('INSERT INTO Office_access (Card_number, Registered) VALUES (?,?)', (num, timestamp))
        connection.commit()
        connection.close()
        logging.info(f'{TerminalColors.YELLOW} Registered card with number: {num}, at time: {timestamp} as a trusted one.{TerminalColors.RESET}')

def add_card_to_trusted_cards_with_pin(client, userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if (len(message_decoded) > 1):
        num = message_decoded[0]
        pin = message_decoded[1]
        timestamp = message_decoded[2]
        connection = sql.connect(DB_FILE_NAME)
        cursor = connection.cursor()
        cursor.execute('INSERT INTO Secret_room_access (Card_number, PIN, Registered) VALUES (?,?,?)', (num, pin, timestamp))
        connection.commit()
        connection.close()
        logging.info(f'{TerminalColors.YELLOW} Registered card with number: {num}, with pin{pin} at time: {timestamp} as a trusted one.{TerminalColors.RESET}')

###################################### - main client

def connect_broker_office_entrance_add_subscriber():
    client_main_add.connect(broker)
    client_main_add.on_message = add_card_to_trusted_cards
    client_main_add.loop_start()
    client_main_add.subscribe(MAIN_TOPIC_ADD)

def disconnect_broker_office_entrance_add_subscriber():
    client_main_add.loop_stop()
    client_main_add.disconnect()

def connect_broker_office_entrance_check_request_subscriber():
    client_main_check_request.connect(broker)
    client_main_check_request.on_message = check_card_request
    client_main_check_request.loop_start()
    client_main_check_request.subscribe(MAIN_TOPIC_CHECK_REQUEST)

def disconnect_broker_office_entrance_check_request_subscriber():
    client_main_check_request.loop_stop()
    client_main_check_request.disconnect()

def connect_broker_office_entrance_check_response_publisher():
    client_main_check_response.connect(broker)

def disconnect_broker_office_entrance_check_response_publisher():
    client_main_check_response.disconnect()

###################################### - secret client

def connect_broker_secret_entrance_add_subscriber():
    client_secret_add.connect(broker)
    client_secret_add.on_message = add_card_to_trusted_cards
    client_secret_add.loop_start()
    client_secret_add.subscribe(MAIN_TOPIC_ADD)

def disconnect_broker_secret_entrance_add_subscriber():
    client_secret_add.loop_stop()
    client_secret_add.disconnect()

def connect_broker_secret_entrance_check_request_subscriber():
    client_secret_check_request.connect(broker)
    client_secret_check_request.on_message = check_card_with_pin_request
    client_secret_check_request.loop_start()
    client_secret_check_request.subscribe(SECRET_TOPIC_CHECK_REQUEST)

def disconnect_broker_secret_entrance_check_request_subscriber():
    client_secret_check_request.loop_stop()
    client_secret_check_request.disconnect()

def connect_broker_secret_entrance_check_response_publisher():
    client_secret_check_response.connect(broker)

def disconnect_broker_secret_entrance_check_response_publisher():
    client_secret_check_response.disconnect()

########################
    
def mainLoop():
    flag = True

    while(flag):
        user_input = input()
        if (user_input == "exit"):
            flag = False

def connect_main_client():
    connect_broker_office_entrance_add_subscriber()
    connect_broker_office_entrance_check_request_subscriber()
    connect_broker_office_entrance_check_response_publisher()

def disconnect_main_client():
    disconnect_broker_office_entrance_add_subscriber()
    disconnect_broker_office_entrance_check_request_subscriber()
    disconnect_broker_office_entrance_check_response_publisher()

def connect_secret_client():
    connect_broker_secret_entrance_add_subscriber()
    connect_broker_secret_entrance_check_request_subscriber()
    connect_broker_secret_entrance_check_response_publisher()

def disconnect_secret_client():
    disconnect_broker_secret_entrance_add_subscriber()
    disconnect_broker_secret_entrance_check_request_subscriber()
    disconnect_broker_secret_entrance_check_response_publisher()

def run_server():
    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.INFO)

    connect_main_client()
    connect_secret_client()

    mainLoop()

    disconnect_main_client
    disconnect_secret_client()

if __name__ == "__main__":
    run_server()
