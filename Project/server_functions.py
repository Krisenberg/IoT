import logging
import sqlite3 as sql
from config_constants import *
from terminal_colors import TerminalColors
import database as db
from server import client_main, check_token

def add_card_to_trusted_cards(client, userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if (len(message_decoded) > 1):
        num = message_decoded[0]
        timestamp = message_decoded[1]
        db.add_card_main_access(num, timestamp)
        logging.info(f'{TerminalColors.BLUE}[Main_access]{TerminalColors.YELLOW} Registered card with number: {num}, at time: {timestamp} as a trusted one.{TerminalColors.RESET}')


def add_card_to_secret_1(client, userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if (len(message_decoded) > 1):
        num = message_decoded[0]
        pin = message_decoded[1]
        timestamp = message_decoded[2]
        db.add_card_secret_1_access(num, pin, timestamp)
        logging.info(f'{TerminalColors.YELLOW} Registered card with number: {num}, with pin{pin} at time: {timestamp} as a trusted one.{TerminalColors.RESET}')

def check_card_request_main(client, userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8"))).split("&")
    if (len(message_decoded) > 1):
        num = message_decoded[0]
        timestamp = message_decoded[1]
        check = db.check_register_card_main_access(num, timestamp)
        if check:
            client_main.publish(MAIN_TOPIC_CHECK_RESPONSE, ACCEPT_MESSAGE)
        else:
            client_main.publish(MAIN_TOPIC_CHECK_RESPONSE, DENY_MESSAGE)

def check_rfid_token(client, userdata, message,):
    message_decoded = (str(message.payload.decode("utf-8")))
    if (len(message_decoded) > 1):
        token = message_decoded[0]
        check = check_token(token)
        if check:
            client_main.publish(TOKEN_CHECK_RESPONSE, ACCEPT_MESSAGE)
        else:
            client_main.publish(TOKEN_CHECK_RESPONSE, DENY_MESSAGE)

        # connection = sql.connect(DB_FILE_NAME)
        # cursor = connection.cursor()
        # cursor.execute('SELECT * FROM Office_access WHERE Card_number = ?', (num,))
        # entry = cursor.fetchone()
        # if (entry):
        #     cursor.execute('SELECT * FROM Office_entry_history WHERE Card_number = ? ORDER BY Timestamp DESC LIMIT 1', (num,))
        #     entry = cursor.fetchone()
        #     if (not entry or timestamp >= entry[1] + ACCEPT_ACCESS_COOLDOWN):
        #         cursor.execute('INSERT INTO Office_entry_history (Card_number, Timestamp, Result) VALUES (?,?,?)', (num, timestamp, ACCEPT_MESSAGE))
        #         client_main_check_response.publish(MAIN_TOPIC_CHECK_RESPONSE, ACCEPT_MESSAGE)
        #         logging.info(f'{TerminalColors.GREEN} Accepted card with number: {num}, at time: {timestamp}.{TerminalColors.RESET}')
        #     else:
        #         cursor.execute('INSERT INTO Office_entry_history (Card_number, Timestamp, Result) VALUES (?,?,?)', (num, timestamp, DENY_MESSAGE))
        #         client_main_check_response.publish(MAIN_TOPIC_CHECK_RESPONSE, DENY_MESSAGE)
        #         logging.info(f'{TerminalColors.RED} Denied card with number: {num}, at time: {timestamp}.{TerminalColors.RESET}')
        #     connection.commit()
        # else:
        #     client_main_check_response.publish(MAIN_TOPIC_CHECK_RESPONSE, DENY_MESSAGE)
        #     logging.info(f'{TerminalColors.RED} Denied card with number: {num}, at time: {timestamp}.{TerminalColors.RESET}')
        # connection.close()