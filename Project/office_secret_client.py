# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=line-too-long
# pylint: disable=import-error

#!/usr/bin/env python3

import time
from threading import Thread
from datetime import datetime
import logging
import lib.oled.SSD1331 as SSD1331
from config import GPIO, encoderLeft, encoderRight, buttonGreen, buttonRed
from buzzer import beepSequence
from leds import ledsAccept, ledsDeny
from oled_screen import display_on_oled, set_oled, clear_oled
from terminal_colors import TerminalColors
import config_constants as const
from mqtt_clients import SecretClient
from mfrc522 import MFRC522

DISP = SSD1331.SSD1331()

def proceed_token_check_response(_client, userdata, message,):
    variables_dict = userdata['variables']
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if len(message_decoded) == 1:
        token_response = message_decoded[0]
        variables_dict['tokenResponse'] = token_response
        variables_dict['isTokenResponsePresent'] = True
        if token_response==const.ACCEPT_MESSAGE:
            beepSequence(0.25, 0.25, 2)
            logging.info('Token check result: %s%s%s', TerminalColors.GREEN, const.ACCEPT_MESSAGE, TerminalColors.RESET)
        else:
            beepSequence(0.75, 0, 1)
            logging.info('Token check result: %s%s%s', TerminalColors.RED, const.ACCEPT_MESSAGE, TerminalColors.RESET)

def proceed_check_response(_client, _userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if len(message_decoded) == 1:
        check_response = message_decoded[0]
        if check_response==const.ACCEPT_MESSAGE:
            accept_access()
            logging.info('Card check result: %s%s%s', TerminalColors.GREEN, const.ACCEPT_MESSAGE, TerminalColors.RESET)
        else:
            deny_access()
            logging.info('Card check result: %s%s%s', TerminalColors.RED, const.DENY_MESSAGE, TerminalColors.RESET)

def run_in_thread(func, variables):
    def wrapped(channel):
        t = Thread(target=func(channel, variables))
        t.start()
    return wrapped

def red_button_pressed_callback(_channel, variables):
    variables['clickedRedButton'] = True
    variables['redButtonPressedTimestamp'] = int(time.time() * 1000)

def green_button_pressed_callback(_channel, variables):
    variables['clickedGreenButton'] = True
    variables['greenButtonPressedTimestamp'] = int(time.time() * 1000)

def encoder_callback(_, variables):
    encoder_left_current_state = GPIO.input(encoderLeft)
    encoder_right_current_state = GPIO.input(encoderRight)

    if variables['encoderLeftPreviousState'] == 1 and encoder_left_current_state == 0:
        variables['encoderNumber'] += 1
    elif variables['encoderRightPreviousState'] == 1 and encoder_right_current_state == 0:
        variables['encoderNumber'] -= 1

    # Checking if in range [0-9]
    variables['encoderNumber'] = max(0, min(9, variables['encoderNumber']))

    variables['encoderLeftPreviousState'] = encoder_left_current_state
    variables['encoderRightPreviousState'] = encoder_right_current_state

    display_on_oled(disp=DISP,
                    oled_cursor_position=variables['oledCursorPosition'],
                    encoder_number=variables['encoderNumber'])

def accept_access():
    ledsAccept(1)
    beepSequence(1,0,1)

def deny_access():
    ledsDeny(1)
    beepSequence(0.25, 0.25, 3)

def write_pin(variables):
    GPIO.add_event_detect(encoderLeft, GPIO.BOTH, callback=run_in_thread(encoder_callback, variables), bouncetime=100)
    GPIO.add_event_detect(encoderRight, GPIO.BOTH, callback=run_in_thread(encoder_callback, variables), bouncetime=100)

    variables['oledCursorPosition'] = 0
    pin = ""
    green_button_pressed_count = 0
    set_oled(disp=DISP)

    while green_button_pressed_count != 2:
        while not variables['clickedGreenButton']:
            continue
        variables['clickedGreenButton'] = False
        pin += str(variables['encoderNumber'])
        variables['oledCursorPosition'] += 1
        green_button_pressed_count += 1

    clear_oled(disp=DISP)
    GPIO.remove_event_detect(encoderLeft)
    GPIO.remove_event_detect(encoderRight)
    return pin

def add_new_trusted_card(client : SecretClient, mifare_reader, variables):
    token_input = write_pin(variables)
    client.publish(const.SECRET_TOKEN_CHECK_REQUEST, token_input)
    logging.info('%sSent request to check the token: %s%s', TerminalColors.YELLOW, token_input, TerminalColors.RESET)
    while not variables['isTokenResponsePresent']:
        continue
    if variables['tokenResponse'] == const.ACCEPT_MESSAGE:
        card_registered_flag = False
        while(not variables['clickedRedButton'] and not card_registered_flag):
            (status, _) = mifare_reader.MFRC522_Request(mifare_reader.PICC_REQIDL)
            if status == mifare_reader.MI_OK:
                (status, uid) = mifare_reader.MFRC522_Anticoll()
                if status == mifare_reader.MI_OK:
                    num = 0
                    for i, elem in enumerate(uid):
                        num += elem << (i*8)
                    pin_input = write_pin(variables)
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                    client.publish(const.SECRET_TOPIC_ADD, f'{num}&{pin_input}&{timestamp}')
                    logging.info('%sSent request to the server to register a card with number: %i at time: %s%s', TerminalColors.YELLOW, num, timestamp, TerminalColors.RESET)
                    card_registered_flag = True

def rfid_reader(client : SecretClient, mifare_reader, cards_timestamps_dict, variables):
    (status, _) = mifare_reader.MFRC522_Request(mifare_reader.PICC_REQIDL)
    if status == mifare_reader.MI_OK:
        (status, uid) = mifare_reader.MFRC522_Anticoll()
        if status == mifare_reader.MI_OK:
            num = 0
            for i, elem in enumerate(uid):
                num += elem << (i*8)
            pin_input = write_pin(variables)
            timestamp = int(time.time() * 1000)
            send_request_flag = True
            if ((num in cards_timestamps_dict) and (timestamp - const.ACCEPT_ACCESS_COOLDOWN < cards_timestamps_dict[num])):
                send_request_flag = False
            if send_request_flag:
                client.publish(const.SECRET_TOPIC_CHECK_REQUEST, f'{num}&{pin_input}&{timestamp}')
                logging.info('%sSent request to the server to check a card with number: %i at time: %s%s', TerminalColors.YELLOW, num, timestamp, TerminalColors.RESET)
            cards_timestamps_dict[num] = timestamp

def loop(client : SecretClient, variables):
    mifare_reader = MFRC522()

    cards_timestamps_dict = dict() # ! to be changed - regularly delete items from that dict

    while(not variables['clickedRedButton'] or not variables['clickedGreenButton']):
        if int(time.time() * 1000) - const.BUTTON_PRESSED_COOLDOWN >= variables['redButtonPressedTimestamp']:
            variables['clickedRedButton'] = False
        if int(time.time() * 1000) - const.BUTTON_PRESSED_COOLDOWN >= variables['greenButtonPressedTimestamp']:
            variables['clickedGreenButton'] = False
        if variables['clickedRedButton']:
            variables['clickedRedButton'] = False
            add_new_trusted_card(client, mifare_reader, variables)
        else:
            rfid_reader(client, mifare_reader, cards_timestamps_dict, variables)

def run_secret_client():
    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.INFO)

    variables = {
        'clickedGreenButton' : False,
        'clickedRedButton' : False,
        'greenButtonPressedTimestamp' : 0,
        'redButtonPressedTimestamp' : 0,
        'oledCursorPosition' : 0,
        'encoderNumber' : 0,
        'isTokenResponsePresent' : False,
        'tokenResponse' : const.DENY_MESSAGE,
        'encoderLeftPreviousState' : GPIO.input(encoderLeft),
        'encoderRightPreviousState' : GPIO.input(encoderRight)
    }

    client = SecretClient(
        client_id=1,
        broker=const.SERVER_BROKER,
        publisher_topics_list=[const.SECRET_TOPIC_ADD, const.SECRET_TOPIC_CHECK_REQUEST, const.SECRET_TOKEN_CHECK_REQUEST],
        subscribers_topic_to_func_dict={
            const.SECRET_TOPIC_CHECK_RESPONSE : proceed_check_response,
            const.SECRET_TOKEN_CHECK_RESPONSE : proceed_token_check_response
        },
        variables=variables
    )

    client.connect_publishers()
    client.connect_subscribers()

    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=run_in_thread(green_button_pressed_callback, variables), bouncetime=100)
    GPIO.add_event_detect(buttonRed, GPIO.FALLING, callback=run_in_thread(red_button_pressed_callback, variables), bouncetime=100)

    loop(client, variables)

    client.disconnect_publishers()
    client.disconnect_subscribers()

    GPIO.cleanup()

if __name__ == "__main__":
    run_secret_client()
