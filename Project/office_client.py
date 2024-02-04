# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=line-too-long
# pylint: disable=import-error

#!/usr/bin/env python3

import time
import os
from threading import Thread
from datetime import datetime
import logging
import lib.oled.SSD1331 as SSD1331
from config import GPIO, encoderLeft, encoderRight, buttonGreen, buttonRed, ws2812pin
from buzzer import beepSequence
from leds import ledsAccept, ledsDeny
from oled_screen import display_on_oled, set_oled, clear_oled
from terminal_colors import TerminalColors
import config_constants as const
from mqtt_clients import Client
from mfrc522 import MFRC522
import neopixel
import board
DISP = SSD1331.SSD1331()

def proceed_token_check_response(_client, userdata, message,):
    variables_dict = userdata['variables']
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if len(message_decoded) >= 1:
        token_response = message_decoded[0]
        variables_dict['tokenResponse'] = token_response
        variables_dict['isTokenResponsePresent'] = True
        if token_response==const.ACCEPT_MESSAGE:
            beepSequence(0.25, 0.25, 2)
            logging.info('Token check result: %s%s%s', TerminalColors.GREEN, const.ACCEPT_MESSAGE, TerminalColors.RESET)
        else:
            beepSequence(0.75, 0, 1)
            logging.info('Token check result: %s%s%s', TerminalColors.RED, const.DENY_MESSAGE, TerminalColors.RESET)

def proceed_check_response(_client, _userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if len(message_decoded) >= 1:
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

    time.sleep(0.05)
    # Checking if in range [0-7]
    variables['encoderNumber'] = max(0, min(7, variables['encoderNumber']))

    #dla próby
    if variables['encoderLeftPreviousState'] != encoder_left_current_state:
        variables['encoderLeftPreviousState'] = encoder_left_current_state

    if variables['encoderRightPreviousState'] != encoder_right_current_state:
        variables['encoderRightPreviousState'] = encoder_right_current_state

    pixelShow(variables['encoderNumber'])
    # display_on_oled(disp=DISP,
    #                 oled_cursor_position=variables['oledCursorPosition'],
    #                 encoder_number=variables['encoderNumber'])

def pixelShow(pixelIndex):
    pixels = neopixel.NeoPixel(board.D18, 8, brightness=1.0/32, auto_write=False)

    #może generować mruganie, ale bardziej niezawodne, przy szybkim kręceniu encoderem -> prawdopodobnie trzeba tego użyć
    #pixels.fill((0,0,0))
    #pixels[pixelIndex] = (0, 0, 255)
    #pixels.show()
    prev_index = (pixelIndex - 1) if (pixelIndex - 1) >=0 else 7
    pixels[(pixelIndex + 1) % 8] = (0, 0, 0)
    pixels[pixelIndex] = (0, 0, 255)
    pixels[prev_index] = (0, 0, 0)

    pixels.show()

def setPixels():
    pixels = neopixel.NeoPixel(board.D18, 8, brightness=1.0/32, auto_write=False)
    pixels.fill((0,0,0))
    pixels[0] = (0, 0, 255)
    pixels.show()

def cleanPixels():
    pixels = neopixel.NeoPixel(board.D18, 8, brightness=1.0/32, auto_write=False)
    pixels.fill((0,0,0))
    pixels.show()

def accept_access():
    ledsAccept(1)
    beepSequence(1,0,1)

def deny_access():
    ledsDeny(1)
    beepSequence(0.25, 0.25, 3)

def write_pin(variables):
    GPIO.add_event_detect(encoderLeft, GPIO.BOTH, callback=run_in_thread(encoder_callback, variables), bouncetime=300)
    GPIO.add_event_detect(encoderRight, GPIO.BOTH, callback=run_in_thread(encoder_callback, variables), bouncetime=300)

    pin = ""
    green_button_pressed_count = 0
    set_oled(disp=DISP)
    setPixels()
    display_on_oled(disp=DISP, image_name = variables['oledImage'])

    while green_button_pressed_count != 2:
        while not variables['clickedGreenButton']:
            continue
        variables['clickedGreenButton'] = False
        pin += str(variables['encoderNumber'])
        green_button_pressed_count += 1
        setPixels()
        variables['encoderNumber'] = 0

    clear_oled(disp=DISP)
    cleanPixels()
    GPIO.remove_event_detect(encoderLeft)
    GPIO.remove_event_detect(encoderRight)
    return pin

def add_new_trusted_card(client : Client, mifare_reader, variables):
    variables['oledImage'] = 'token'
    number_input = write_pin(variables)
    if client.is_main:
        client.publish(const.MAIN_TOKEN_CHECK_REQUEST, number_input)
    else:
        client.publish(const.SECRET_TOPIC_CHECK_REQUEST, number_input)

    while not variables['isTokenResponsePresent']:
        continue
    if variables['tokenResponse'] == const.ACCEPT_MESSAGE:
        if not client.is_main:
            variables['oledImage'] = 'pin'
            number_input = write_pin(variables)
        card_registered_flag = False
        variables['oledImage'] = 'rfid'
        set_oled(disp=DISP)
        display_on_oled(disp=DISP, image_name = variables['oledImage'])
        while(not variables['clickedRedButton'] and not card_registered_flag):
            (status, _) = mifare_reader.MFRC522_Request(mifare_reader.PICC_REQIDL)
            if status == mifare_reader.MI_OK:
                (status, uid) = mifare_reader.MFRC522_Anticoll()
                if status == mifare_reader.MI_OK:
                    num = 0
                    for i, elem in enumerate(uid):
                        num += elem << (i*8)
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                    if client.is_main:
                        client.publish(const.MAIN_TOPIC_ADD, f'{num}&{timestamp}')
                    else:
                        client.publish(const.SECRET_TOPIC_ADD, f'{num}&{number_input}&{timestamp}')
                    card_registered_flag = True
        clear_oled(disp=DISP)
        if variables['clickedRedButton']:
            logging.info('%sAborted the process of registering new trusted card%s', TerminalColors.RED, TerminalColors.RESET)

def rfid_reader(client : Client, mifare_reader, cards_timestamps_dict, variables):
    number_input = 0
    (status, _) = mifare_reader.MFRC522_Request(mifare_reader.PICC_REQIDL)
    if status == mifare_reader.MI_OK:
        (status, uid) = mifare_reader.MFRC522_Anticoll()
        if status == mifare_reader.MI_OK:
            num = 0
            for i, elem in enumerate(uid):
                num += elem << (i*8)
            if not client.is_main:
                variables['oledImage'] = 'pin'
                number_input = write_pin(variables)
            timestamp = int(time.time() * 1000)
            if not ((num in cards_timestamps_dict) and (timestamp - const.ACCEPT_ACCESS_COOLDOWN < cards_timestamps_dict[num])):
                if client.is_main:
                    client.publish(const.MAIN_TOPIC_CHECK_REQUEST, f'{num}&{timestamp}')
                else:
                    client.publish(const.SECRET_TOPIC_CHECK_REQUEST, f'{num}&{number_input}&{timestamp}')
            cards_timestamps_dict[num] = timestamp

def loop(client : Client, variables):
    mifare_reader = MFRC522()

    cards_timestamps_dict = {} # ! to be changed - regularly delete items from that dict

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

def run_client(client_identifier, is_main_client, client_logger):
    variables = {
        'clickedGreenButton' : False,
        'clickedRedButton' : False,
        'greenButtonPressedTimestamp' : 0,
        'redButtonPressedTimestamp' : 0,
        'encoderNumber' : 0,
        'isTokenResponsePresent' : False,
        'tokenResponse' : const.DENY_MESSAGE,
        'encoderLeftPreviousState' : GPIO.input(encoderLeft),
        'encoderRightPreviousState' : GPIO.input(encoderRight),
        'oledImage': ''
    }

    if is_main_client:
        client = Client(
            client_id=client_identifier,
            is_main=True,
            broker=const.SERVER_BROKER,
            publisher_topics_list=[const.MAIN_TOPIC_ADD, const.MAIN_TOPIC_CHECK_REQUEST, const.MAIN_TOKEN_CHECK_REQUEST],
            subscribers_topic_to_func_dict={
                const.MAIN_TOPIC_CHECK_RESPONSE : proceed_check_response,
                const.MAIN_TOKEN_CHECK_RESPONSE : proceed_token_check_response
            },
            variables=variables,
            logger=client_logger
        )
    else:
        client = Client(
            client_id=client_identifier,
            is_main=False,
            broker=const.SERVER_BROKER,
            publisher_topics_list=[const.SECRET_TOPIC_ADD, const.SECRET_TOPIC_CHECK_REQUEST, const.SECRET_TOKEN_CHECK_REQUEST],
            subscribers_topic_to_func_dict={
                const.SECRET_TOPIC_CHECK_RESPONSE : proceed_check_response,
                const.SECRET_TOKEN_CHECK_RESPONSE : proceed_token_check_response
            },
            variables=variables,
            logger=client_logger
        )

    client.connect_publishers()
    client.connect_subscribers()

    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=run_in_thread(green_button_pressed_callback, variables), bouncetime=300)
    GPIO.add_event_detect(buttonRed, GPIO.FALLING, callback=run_in_thread(red_button_pressed_callback, variables), bouncetime=300)

    loop(client, variables)

    client.disconnect_publishers()
    client.disconnect_subscribers()

    GPIO.remove_event_detect(buttonGreen)
    GPIO.remove_event_detect(buttonRed)
    GPIO.cleanup()

if __name__ == "__main__":
    CLIENT_ID = 1
    IS_MAIN = False
    logger_name = f'logger_client_{CLIENT_ID}'
    logger = logging.getLogger(CLIENT_ID)
    run_client(
        client_identifier=CLIENT_ID,
        is_main_client=IS_MAIN,
        client_logger=logger
    )
