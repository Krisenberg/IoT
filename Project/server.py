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
import argparse
import random
from buzzer import beepSequence
from leds import ledsAccept, ledsDeny
from terminal_colors import TerminalColors
from config_constants import *
from clients_MQTT import *
from server_functions import *

broker = SERVER_BROKER
parser = argparse.ArgumentParser(description='Program for the RFiD card presence system administrator')
token = None
prev_token = None
token_change_timestamp = time.time()-const.GENERATE_TOKEN_PERIOD
exit_event = threading.Event()
# client_main_add = mqtt.Client(client_id='server_main_add')
# client_main_check_request = mqtt.Client(client_id='server_main_check_request')
# client_main_check_response = mqtt.Client(client_id='server_main_check_response')

client_main = Client(broker=SERVER_BROKER,
                     publisher_topics_list=[MAIN_TOPIC_CHECK_RESPONSE, TOKEN_CHECK_RESPONSE],
                     subscribers_topic_to_func_dict={
                         MAIN_TOPIC_ADD : add_card_to_trusted_cards,
                         MAIN_TOPIC_CHECK_REQUEST : check_card_request_main,
                         TOKEN_CHECK_REQUEST : check_rfid_token
                     })

client_secret_add = mqtt.Client(client_id='server_secret_add')
client_secret_check_request = mqtt.Client(client_id='server_secret_check_request')
client_secret_check_response = mqtt.Client(client_id='server_secret_check_response')

def update_token():
    global token, prev_token, token_change_timestamp
    prev_token = token
    token = random.randint(0,99)
    token_change_timestamp = time.time()

def generate_tokens():
    while not exit_event.is_set():
        time_now = time.time()
        if (time_now - token_change_timestamp >= const.GENERATE_TOKEN_PERIOD):
            update_token()

def check_token(token_str):
    current_timestamp = time.time()

    if current_timestamp - token_change_timestamp < const.TOKEN_CHANGE_COOLDOWN:
        return token_str == str(token) or token_str == str(prev_token)
    else:
        return token_str == str(token)


def check_card_with_pin_request(client, userdata, message,):
    #TO-DO
    return

###################################### - main client

# def connect_broker_office_entrance_add_subscriber():
#     client_main_add.connect(broker)
#     client_main_add.on_message = add_card_to_trusted_cards
#     client_main_add.loop_start()
#     client_main_add.subscribe(MAIN_TOPIC_ADD)

# def disconnect_broker_office_entrance_add_subscriber():
#     client_main_add.loop_stop()
#     client_main_add.disconnect()

# def connect_broker_office_entrance_check_request_subscriber():
#     client_main_check_request.connect(broker)
#     client_main_check_request.on_message = check_card_request
#     client_main_check_request.loop_start()
#     client_main_check_request.subscribe(MAIN_TOPIC_CHECK_REQUEST)

# def disconnect_broker_office_entrance_check_request_subscriber():
#     client_main_check_request.loop_stop()
#     client_main_check_request.disconnect()

# def connect_broker_office_entrance_check_response_publisher():
#     client_main_check_response.connect(broker)

# def disconnect_broker_office_entrance_check_response_publisher():
#     client_main_check_response.disconnect()

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

# def connect_main_client():
#     connect_broker_office_entrance_add_subscriber()
#     connect_broker_office_entrance_check_request_subscriber()
#     connect_broker_office_entrance_check_response_publisher()

# def disconnect_main_client():
#     disconnect_broker_office_entrance_add_subscriber()
#     disconnect_broker_office_entrance_check_request_subscriber()
#     disconnect_broker_office_entrance_check_response_publisher()

def connect_secret_client():
    connect_broker_secret_entrance_add_subscriber()
    connect_broker_secret_entrance_check_request_subscriber()
    connect_broker_secret_entrance_check_response_publisher()

def disconnect_secret_client():
    disconnect_broker_secret_entrance_add_subscriber()
    disconnect_broker_secret_entrance_check_request_subscriber()
    disconnect_broker_secret_entrance_check_response_publisher()

def config_parser():
    global parser
    parser.add_argument('-r', '--reader', help='Specify the card reader')
    parser.add_argument('-lh', '--list-history', action='store_true', help='Print card presence history from the specified reader')
    parser.add_argument('-t', '--token', action='store_true', help='Print the current token')
    parser.add_argument('--exit', action='store_true', help='Terminate this program')

def connectMQTT():
    client_main.connect_publishers()
    client_main.connect_subscribers()

def disconnectMQTT():
    client_main.disconnect_publishers()
    client_main.disconnect_subscribers()

def run_server():
    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.INFO)
    config_parser()
    connectMQTT()

    program_exit_flag = False

    token_thread = threading.Thread(target=generate_tokens)
    token_thread.start()

    while not program_exit_flag:
        arguments = input('Command: ')
        args, unknown = parser.parse_known_args(arguments.split())
        if args.list_history:
            print('History print required!')
        elif args.token:
            token_change_datetime = datetime.datetime.fromtimestamp(token_change_timestamp).strftime('%c')
            print(f'Token [{token_change_datetime}]:\t{token}')
        elif args.exit:
            print('Terminating the program...')
            program_exit_flag = True
        else:
            print(f'Unknown commands: {unknown}')
    exit_event.set()
    token_thread.join()
    disconnectMQTT()


if __name__ == "__main__":
    run_server()
    print('----------------------------------')
    print('FINISHED')
