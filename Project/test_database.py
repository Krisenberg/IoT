# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=import-error
# pylint: disable=line-too-long

#!/usr/bin/env python3

import time
import threading
import datetime
import logging
import argparse
import random
import config_constants as const
from terminal_colors import TerminalColors

class TokenData():
    def __init__(self):
        self.token = -1
        self.prev_token = -1
        self.token_change_timestamp = time.time()-const.GENERATE_TOKEN_PERIOD

    def check_token(self, token_str):
        current_timestamp = time.time()
        if current_timestamp - self.token_change_timestamp < const.TOKEN_CHANGE_COOLDOWN:
            return token_str == str(self.token) or token_str == str(self.prev_token)
        return token_str == str(self.token)

    def update_token(self):
        self.prev_token = self.token
        self.token = random.randint(0,99)
        self.token_change_timestamp = time.time()
        timestamp_iso = datetime.datetime.fromtimestamp(self.token_change_timestamp).strftime(const.ISO8601)
        LOGGER.info('%sGenerated new token at %s:%s %s  --->  %s%s', TerminalColors.YELLOW, timestamp_iso, TerminalColors.RED, self.prev_token, self.token, TerminalColors.RESET)

PARSER = argparse.ArgumentParser(description='Program for the RFiD card presence system administrator')
TOKEN_DATA = TokenData()
EXIT_EVENT = threading.Event()
LOGGER = logging.getLogger(__name__)

def generate_tokens():
    while not EXIT_EVENT.is_set():
        time_now = time.time()
        if time_now - TOKEN_DATA.token_change_timestamp >= const.GENERATE_TOKEN_PERIOD:
            TOKEN_DATA.update_token()

def check_token(token_str):
    return TOKEN_DATA.check_token(token_str)

def config_parser():
    PARSER.add_argument('-r', '--reader', help='Specify the card reader')
    PARSER.add_argument('-lh', '--list-history', action='store_true', help='Print card presence history from the specified reader')
    PARSER.add_argument('-t', '--token', action='store_true', help='Print the current token')
    PARSER.add_argument('--exit', action='store_true', help='Terminate this program')
    PARSER.add_argument('-d', '--debug', action="store_true", help="Set the logging level to DEBUG")
    PARSER.add_argument('-i', '--info', action="store_true", help="Set the logging level to INFO")
    PARSER.add_argument('-w', '--warning', action="store_true", help="Set the logging level to WARNING")
    PARSER.add_argument('-e', '--error', action="store_true", help="Set the logging level to ERROR")
    PARSER.add_argument('-c', '--critical', action="store_true", help="Set the logging level to CRITICAL")

def run_server():
    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.INFO)
    config_parser()

    program_exit_flag = False

    token_thread = threading.Thread(target=generate_tokens)
    token_thread.start()

    while not program_exit_flag:
        arguments = input('Command: ')
        args, unknown = PARSER.parse_known_args(arguments.split())
        if args.list_history:
            print('History print required!')
        elif args.token:
            token_change_datetime = datetime.datetime.fromtimestamp(TOKEN_DATA.token_change_timestamp).strftime(const.ISO8601)
            print(f'Token [{token_change_datetime}]:\t{TOKEN_DATA.token}')
        elif args.debug:
            LOGGER.setLevel(level=logging.DEBUG)
        elif args.info:
            LOGGER.setLevel(level=logging.INFO)
        elif args.warning:
            LOGGER.setLevel(level=logging.WARNING)
        elif args.error:
            LOGGER.setLevel(level=logging.ERROR)
        elif args.critical:
            LOGGER.setLevel(level=logging.CRITICAL)
        elif args.exit:
            print('Terminating the program...')
            program_exit_flag = True
        else:
            print(f'Unknown commands: {unknown}')
    EXIT_EVENT.set()
    token_thread.join()


if __name__ == "__main__":
    run_server()
    print('----------------------------------')
    print('FINISHED')
