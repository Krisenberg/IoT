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
from http.server import HTTPServer, SimpleHTTPRequestHandler
# from mfrc522 import MFRC522
import config_constants as const
# from mqtt_clients import Client, SecretClient
# import server_functions as sf
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

class CustomHandler(SimpleHTTPRequestHandler):
    def setup(self):
        SimpleHTTPRequestHandler.setup(self)
        self.request.settimeout(30)
    def do_GET(self):
        if self.path.endswith(".css"):
            self.send_response(200)
            self.send_header("Content-type", "text/css")
            self.end_headers()
            with open('Project/website/styles.css', 'rb') as file:
                content = file.read()
                self.wfile.write(content)
        # Specify the custom path for your index.html file
        elif self.path == '/':
            # Your custom logic to serve the index.html file
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Open and read the content of your index.html file
            with open('Project/website/index.html', 'rb') as file:
                content = file.read()
                current_token = str(TOKEN_DATA.token)
                timestamp = time.time()
                time_to_token_change = (int) (TOKEN_DATA.token_change_timestamp + const.GENERATE_TOKEN_PERIOD - timestamp)
                js_time_to_change_set = f'var timeleft = {time_to_token_change};'
                js_time_to_change_set_bytes = js_time_to_change_set.encode('utf-8')
                js_code = f'$(document).ready(function() {{ $("#token").text({current_token}); }});'
                js_code_bytes = js_code.encode('utf-8')

                # Replace a bytes-like object in content with another bytes-like object
                content = content.replace(b'var timeleft = 0;', js_time_to_change_set_bytes + js_code_bytes)

            # Send the content as the response
            self.wfile.write(content)
        else:
            # If the path doesn't match, fall back to the default behavior
            super().do_GET()

PARSER = argparse.ArgumentParser(description='Program for the RFiD card presence system administrator', add_help=False)
TOKEN_DATA = TokenData()
EXIT_EVENT = threading.Event()
LOGGER = logging.getLogger(__name__)

SERVER_ADDRESS = ('', 8765)
HTTPD = HTTPServer(SERVER_ADDRESS, CustomHandler)
# HTTPD.timeout = 15

# client_main = Client(
#     broker=const.SERVER_BROKER,
#     publisher_topics_list=[const.MAIN_TOPIC_CHECK_RESPONSE, const.MAIN_TOKEN_CHECK_RESPONSE],
#     subscribers_topic_to_func_dict={
#         const.MAIN_TOPIC_ADD : sf.add_card_to_trusted_main,
#         const.MAIN_TOPIC_CHECK_REQUEST : sf.check_card_request_main,
#         const.MAIN_TOKEN_CHECK_REQUEST : sf.check_rfid_token_main
#     },
#     variables={}
# )

# client_secret_1 = SecretClient(
#     client_id=1,
#     broker=const.SERVER_BROKER,
#     publisher_topics_list=[const.SECRET_TOPIC_CHECK_RESPONSE, const.SECRET_TOKEN_CHECK_RESPONSE],
#     subscribers_topic_to_func_dict={
#         const.SECRET_TOPIC_ADD : sf.add_card_to_trusted_secret,
#         const.SECRET_TOPIC_CHECK_REQUEST : sf.check_card_request_secret,
#         const.SECRET_TOKEN_CHECK_REQUEST : sf.check_rfid_token_secret
#     },
#     variables={}
# )

# mqtt_clients = [client_main, client_secret_1]

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
    PARSER.add_argument('-h', '--help', action='store_true', help='Display help message')

def custom_help():
    print("\n\n")
    print("{:<10}{:<30}{}".format("-r", "--reader", "Specify the card reader"))
    print("{:<10}{:<30}{}".format("-lh", "--list-history", "Print card presence history from the specified reader"))
    print("{:<10}{:<30}{}".format("-t", "--token", "Print the current token"))
    print("{:<10}{:<30}{}".format("", "--exit", "Terminate this program"))
    print("{:<10}{:<30}{}".format("-d", "--debug", "Set the logging level to DEBUG"))
    print("{:<10}{:<30}{}".format("-i", "--info", "Set the logging level to INFO"))
    print("{:<10}{:<30}{}".format("-w", "--warning", "Set the logging level to WARNING"))
    print("{:<10}{:<30}{}".format("-e", "--error", "Set the logging level to ERROR"))
    print("{:<10}{:<30}{}".format("-c", "--critical", "Set the logging level to CRITICAL"))
    print("\n\n")
# def connect_mqtts():
#     for client in mqtt_clients:
#         client.connect_publishers()
#         client.connect_subscribers()

# def disconnect_mqtts():
#     for client in mqtt_clients:
#         client.disconnect_publishers()
#         client.disconnect_subscribers()

def run_threaded_web_server():
    while not EXIT_EVENT.is_set():
        HTTPD.handle_request()

def run_admin_cli():
    while not EXIT_EVENT.is_set():
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
        elif args.help:
            custom_help()
        elif args.exit:
            print('Terminating the program...')
            EXIT_EVENT.set()
        else:
            print(f'Unknown commands: {unknown}')

token_thread = threading.Thread(target=generate_tokens)
web_thread = threading.Thread(target=run_threaded_web_server)
input_thread = threading.Thread(target=run_admin_cli)
threads = [token_thread, web_thread, input_thread]

def run_server():
    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.INFO)
    config_parser()
    # connect_mqtts()

    for thr in threads:
        thr.start()
    
    while not EXIT_EVENT.is_set():
        continue

    for thr in threads:
        thr.join()

    # disconnect_mqtts()

if __name__ == "__main__":
    run_server()
    print('----------------------------------')
    print('FINISHED')
