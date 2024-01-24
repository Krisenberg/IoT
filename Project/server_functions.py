# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=import-error
# pylint: disable=line-too-long

import logging
import config_constants as const
from terminal_colors import TerminalColors
import database as db
from server import client_main, client_secret_1, check_token

def add_card_to_trusted_main(_client, _userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if len(message_decoded) == 2:
        num = message_decoded[0]
        timestamp = message_decoded[1]
        db.add_card_main_access(num, timestamp)

def check_card_request_main(_client, _userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if len(message_decoded) == 2:
        num = message_decoded[0]
        timestamp = message_decoded[1]
        check = db.check_register_card_main_access(num, timestamp)
        if check:
            client_main.publish(const.MAIN_TOPIC_CHECK_RESPONSE, const.ACCEPT_MESSAGE)
        else:
            client_main.publish(const.MAIN_TOPIC_CHECK_RESPONSE, const.DENY_MESSAGE)

def check_rfid_token_main(_client, _userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if len(message_decoded) == 1:
        token = message_decoded[0]
        check = check_token(token)
        if check:
            client_main.publish(const.MAIN_TOKEN_CHECK_RESPONSE, const.ACCEPT_MESSAGE)
        else:
            client_main.publish(const.MAIN_TOKEN_CHECK_RESPONSE, const.DENY_MESSAGE)

def add_card_to_trusted_secret(_client, _userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if len(message_decoded) == 4:
        sercet_id = message_decoded[0]
        num = message_decoded[1]
        pin = message_decoded[2]
        timestamp = message_decoded[3]
        db.add_card_secret_access(sercet_id, num, pin, timestamp)
        logging.info('%s[Secret_1_access]%s Registered card with number: %s and %s at time: %s as a trusted one.%s',
                     TerminalColors.BLUE, TerminalColors.YELLOW, num, pin, timestamp, TerminalColors.RESET)

def check_card_request_secret(_client, _userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if len(message_decoded) == 3:
        sercet_id = message_decoded[0]
        num = message_decoded[1]
        pin = message_decoded[2]
        timestamp = message_decoded[3]
        check = db.check_register_card_secret_access(sercet_id, num, pin, timestamp)
        if check:
            client_secret_1.publish(const.SECRET_TOPIC_CHECK_RESPONSE, const.ACCEPT_MESSAGE)
        else:
            client_secret_1.publish(const.SECRET_TOPIC_CHECK_RESPONSE, const.DENY_MESSAGE)

def check_rfid_token_secret(_client, _userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8")))
    if len(message_decoded) == 2:
        _ = message_decoded[0]
        token = message_decoded[1]
        check = check_token(token)
        if check:
            client_secret_1.publish(const.SECRET_TOKEN_CHECK_RESPONSE, const.ACCEPT_MESSAGE)
        else:
            client_secret_1.publish(const.SECRET_TOKEN_CHECK_RESPONSE, const.DENY_MESSAGE)
